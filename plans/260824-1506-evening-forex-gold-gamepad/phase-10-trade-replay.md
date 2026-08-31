---
title: "Phase 10: Trade replay"
status: in-progress
phase: 10
priority: P1
effort: 12h
dependencies: [2, 7]
---

# Phase 10: Trade replay

## Overview

TradeZella's trade replay, on the hardware you already trade with: scrub your executed trade back
through the tape with the left stick, watch the ARM you cancelled forty seconds before you fired,
see where MFE and MAE actually sat, and hear the memo you recorded play at the moment you recorded
it. This is the review surface that turns a closed position into a lesson.

The tape it plays comes from phase 2's ring buffer, frozen per trade at close time. A zero-trade
evening writes zero tape; there is no firehose to prune.

Phase 8 is **optional** here — without voice, replay works exactly the same minus the memo audio.

## Context Links

- [plan.md](./plan.md)
- [Phase 2 — 1 Hz bid+ask ring buffer, per-trade freeze, MFE/MAE, R definition](./phase-02-ctrader-exec-and-socket-gateway.md)
- [Phase 7 — grades render on the replay timeline](./phase-07-playbook-and-trade-grading.md)
- [Phase 8 — seekable `.ogg` archive, `durMs`](./phase-08-voice-capture-whisper-and-coach.md)
- Lightweight Charts (already the HUD chart library)

## Requirements

### The stored artifact (phase 2 writes it, this phase reads it)

- Functional: `trade_tape(tape_id PK, cid, position_id, symbol, t0, dt_s DEFAULT 1, n, digits, bars BLOB, events BLOB, created_at)`
- Functional: `bars` is `gzip(JSON columnar)`: `{bid_o:[], bid_h:[], bid_l:[], bid_c:[], ask_o:[], ask_h:[], ask_l:[], ask_c:[], n_ticks:[]}`,
  prices as the protocol's **scaled integers**, never floats
- Functional: window is `[opened_at - tape.pre_roll_s (300), closed_at + tape.post_roll_s (300)]`.
  Both sides are stored because a long's excursion is measured on the **bid** and a short's on the
  **ask**; bid-only would be a silent asymmetry bug in MAE
- Functional: `events` is `gzip(JSON [{ts, kind, ...}])`, **denormalised at freeze time** from pad
  telemetry, memos, signals, sentinel and grades: `arm`, `cancel`, `fire`, `ack`, `sl_move`, `memo`,
  `volman_tag`, `tv_signal`, `tilt_band_change`. This is what makes it coaching rather than charting
- Non-functional: one row per trade, not one row per sample. Replay always reads the whole window at
  once — there is no "slice one trade's tape" query — so a sample table would buy ~9,000 rows an
  evening and an index for nothing. One row = one read, one gunzip, straight into the chart, and the
  same JSON shape goes over the wire with `Content-Encoding: gzip`
- Non-functional: ~12-20 KB per trade, ~1.6 MB/month. `tape.retention_days: 730` is hygiene, not a
  size constraint

### Serving

- Functional: `GET /api/replay/:cid` — single row read, returns bars + events + the `trade_closed`
  row (entry, exit, lots, R, MFE/MAE, efficiency, playbook, `tilt_at_entry`) + memo index
- Functional: `GET /api/replay/index?from=&to=` — the trade list that drives LB/RB stepping
- Non-functional: plain HTTP, same origin, existing token. Not on the game socket — this is not
  realtime, exactly as the phase 6 deck routes already establish

### The replay surface

- Functional: route `/replay/:cid`, linked from the deck's trade table and from a closed-trade toast
- Functional: the order FSM is **hard `LOCKED`** on this route; replay bindings are live only here
- Functional: bindings

  | input | action |
  |---|---|
  | LS X | scrub (velocity-based, deadzone 0.2) |
  | RS X | zoom the window in seconds |
  | A | play / pause |
  | D-pad U/D | speed 0.5x / 1x / 2x / 4x |
  | LB / RB | previous / next trade |
  | B | exit |

- Functional: markers — entry (up triangle), exit (down triangle), MFE and MAE dots, arm/cancel ticks
  on the time axis, memo pins. Hovering or scrubbing onto an event shows its one-line label
- Functional: resample 1 Hz bars client-side to the displayed timeframe; never fetch a second series
- Functional: the phase 7 grade for this `cid` renders beside the chart — the rules that passed, the
  rules that failed, and whether it was `clean`
- Functional: memo audio via `<audio src="/api/voice/:id/audio">` (the seekable `.ogg`), `play()` when
  the playhead crosses `ts`, pause and reset when scrubbed away, `playbackRate` follows speed to 2x
  then mutes
- Non-functional: duration comes from the stored `durMs`, **never** `audio.duration` — Chrome's
  MediaRecorder WebM reports `Infinity`
- Non-functional: without phase 8, memo pins simply do not exist; nothing else changes

## Architecture

```
GET /api/replay/:cid
   -> one trade_tape row -> gunzip -> {bars, events}
   -> trade_closed row (R, MFE/MAE, efficiency, playbook, tilt_at_entry)
   -> voice_memo index for this cid
                |
        Replay.tsx  (order FSM hard-LOCKED)
        Lightweight Charts + marker layer + event rail
        LS scrub / RS zoom / A play / D-pad speed / LB-RB step / B exit
        <audio> memo playback synced to the playhead
```

## Related Code Files

- Create: `apps/gateway/replay/routes.py` (`GET /api/replay/:cid`, `GET /api/replay/index`)
- Create: `apps/gateway/replay/test_routes.py` (missing tape, missing memo, gzip round-trip)
- Create: `apps/web/src/replay/Replay.tsx` (route shell, FSM lock)
- Create: `apps/web/src/replay/Timeline.tsx` (playhead, event rail, memo pins)
- Create: `apps/web/src/replay/Markers.ts` (entry/exit/MFE/MAE/arm/cancel marker layer)
- Create: `apps/web/src/replay/transport.ts` (play/pause/scrub/speed; audio sync)
- Create: `apps/web/src/replay/resample.ts` (1 Hz -> displayed timeframe)
- Create: `apps/web/src/replay/resample.test.ts` (integer-price OHLC aggregation is lossless)
- Modify: `apps/web/src/App.tsx` (route `/replay/:cid`, FSM lock on entry, unlock on exit)
- Modify: `apps/web/src/deck/OutcomePanel.tsx` (trade rows link to replay)
- Modify: `README.md` (replay controls)

## Implementation Steps

1. `GET /api/replay/:cid` against a hand-built fixture tape; assert the gzip columnar round-trip.
2. Static render first: chart + entry/exit/MFE/MAE markers, no transport.
3. Resampling with integer-price OHLC aggregation; unit tests.
4. Transport: playhead, play/pause, speed, velocity scrub off LS.
5. Event rail and marker labels from `events`.
6. Grade panel beside the chart (phase 7).
7. Memo audio sync, `durMs`-based, muted above 2x.
8. LB/RB stepping via the index route; B exits and restores the FSM.

## Todo

- [x] `/api/replay/:cid` + index route
- [x] gzip columnar round-trip test
- [x] Chart + entry/exit/MFE/MAE markers
- [x] Client-side resample, lossless on integer prices
- [x] Transport: scrub, play, speed
- [x] Event rail (arm, cancel, fire, tag, tilt band)
- [x] Grade panel
- [x] Memo audio synced to the playhead *(sync built and tested; the memos themselves land with
      phase 8 — see Deviations)*
- [x] FSM hard-locked on the route *(delivered as "not mounted at all" — see Deviations)*

## Success Criteria

- [x] Opening the replay surface for a closed trade paints the tape with entry, exit, MFE and MAE marked
- [x] An ARM that was cancelled before the fire is visible on the event rail at its real timestamp
- [x] Scrubbing with LS moves the playhead smoothly and the memo audio follows and re-syncs
- [x] **No order can be placed from the replay route** — the route mounts no agent and no socket
- [x] A trade with no memo replays normally, with no audio controls
- [ ] A trade whose memo transcript failed still plays its audio — **needs phase 8**; the audio path
      keys on the memo id and never reads the transcript, so it will hold, but it cannot be proved
      without a memo to fail
- [x] LB/RB step to the previous and next trade of the same evening
- [x] One evening of five trades adds under ~100 KB of tape

## Verification Status

Gateway `uv run pytest -q`: **337 passed, 1 skipped** (the skip is phase 2's broker volume test,
still waiting on a real cTrader dump); `uv run ruff check .` clean. Web `npm test`: **128 passed**
(35 new); `npx tsc --noEmit` and `npm run build` clean, protocol drift gate included.

| Claim | Proof |
|---|---|
| What phase 2 writes is what phase 10 reads | `replay/test_routes.py` drives ticks through the real `TapeRing`, fills and closes through the real `TradeRecorder`, and freezes through the real freeze path before reading a single byte back. A hand-built fixture would only have proved the reader agrees with itself |
| No order can be placed from a replay | The route mounts no agent and no socket. `replay.test.ts` asserts every replay module imports neither `../agent` nor `../net/ws`, that the binding table produces only transport actions, and that the only `fetch` calls on the surface are the two `/api/replay/*` reads |
| Nothing on the replay path writes | `test_every_statement_replay_runs_is_a_select` parses every `execute(` in the repository and fails on any verb but `SELECT` |
| Resampling is lossless on integer prices | Tick counts are conserved across all five timeframes; the first open and last close survive every fold; buckets land on wall-clock boundaries so two trades on one evening line up |
| Both sides of the book survive | The served tape carries bid and ask separately, `sideForTrade` picks the side the position exits on, and the round-trip test asserts ask > bid on the same bar |
| The cancelled arm keeps its real timestamp | `test_an_arm_cancelled_before_the_fire_is_on_the_rail` asserts the exact millisecond and the reason text |
| Tilt contributes crossings, not samples | Six samples spanning three bands produce three events |
| Replay degrades rather than blanking | Separate tests for a trade with no tape, a corrupt blob, and a pre-phase-10 event shape — all three still serve the markers |
| The tape stays small | Five trades on one evening, measured off the real blobs, assert one row per trade and under 100 KB total |

## Deviations

- **"FSM hard-`LOCKED`" is delivered as "the FSM is not mounted".** The plan asks App.tsx to lock
  the order FSM on entry and unlock on exit. Selecting a screen already unmounts the previous one,
  so arriving at replay destroys the live HUD's agent, its poller and its socket outright. That is
  strictly stronger than a lock — there is no FSM left to unlock, and no object on the route capable
  of constructing an intent — so a lock/unlock pair would have been ceremony around a guarantee that
  already holds. Both halves are asserted in `replay.test.ts` rather than left to the reader.
- **Phase 2's stored format is fixed-width records, not `gzip(JSON columnar)`.** The plan describes
  the artifact as gzipped columnar JSON; what phase 2 actually shipped is a gzipped JSON header line
  followed by fixed-width `struct` records, which is denser for the same data. Phase 10 reads that
  and serves **columnar JSON over the wire**, which is what the plan's client-side contract needed.
  No format change was made — an already-frozen tape is not worth rewriting.
- **The freeze's event denormalisation was phase 10's to finish.** The plan lists it under "phase 2
  writes it", but phase 2 shipped `events_for(position_id)`, which carries only fill/amend/close.
  Arms, cancels, signals and tilt bands are keyed by *session*, not position, so `journal/tape/events.py`
  now joins all four sources at freeze time. Tapes frozen before this change still replay — `normalise`
  reads the old shape.
- **No memos, and no `voice/arousal.ts`.** Phase 8 is deferred. The transport's audio sync is built
  and tested in full (offset from `durMs`, silence outside the span, hold while scrubbing, mute above
  2x), and `memos` is served as an empty array — which is exactly what "this trade has no memo" looks
  like, and the surface is required to render identically without one. The `<audio>` element is not
  rendered when there is no cue.
- **MFE and MAE are price lines, not dots.** The plan asks for dots. The freeze stores the excursion
  *extremes*, not the moment they occurred, so a dot would need a timestamp nobody recorded. A
  horizontal line at the price is exactly what is known. They print in R only when a recorded stop
  makes R knowable; otherwise the price distance prints as itself rather than as an invented R.
- **The deck's outcome panel was not modified.** It aggregates by setup and has no per-trade rows to
  hang a link on — phase 6 deliberately kept per-trade money off it. Adding a trade table there to
  satisfy a link would contradict that design, so the trade picker lives on the replay surface,
  fed by the same `/api/replay/index` that LB/RB steps through.
- **Lightweight Charts is a new dependency, loaded lazily.** The plan calls it "already the HUD chart
  library"; it was not installed — the HUD writes prices imperatively and draws no chart. Adding it
  eagerly cost the HUD ~60 KB gzipped for a screen most evenings never open, so the replay screen is
  a `React.lazy` chunk. The main bundle is unchanged at ~95 KB gzipped; replay's 61 KB loads on
  demand and is cached by the service worker like any other hashed asset. `npm audit --omit=dev`
  reports zero vulnerabilities.
- **The screen is a nav entry, not a `/replay/:cid` route.** The app has no router (phase 3's
  decision); screens are a nav list and the live surfaces sit alongside the prototype ones. Replay
  is registered as "Replay (real gateway)" beside the existing prototype screen, which is left
  untouched. `Replay` still accepts a `cid` prop, so a router drops in without touching the surface.

## Risk Assessment

- **An order fires from the replay route** — signal: any `intent` emitted while `/replay` is mounted.
  Response: hard FSM lock on route entry, asserted in a test, plus replay bindings scoped to the route.
- **1 Hz is too coarse to see the entry** — signal: the entry candle hides the actual fill. Response:
  the fill price and timestamp are drawn from `trade_closed`, not inferred from bars; the bar is
  context, the marker is truth. If it still reads badly, `tape.dt_s` is config and the ring can go to
  2 Hz for ~2x the storage.
- **Tape missing for an old trade** — signal: 404 on replay of a pre-phase-2 trade. Response: the
  route degrades to a marker-only static view built from `trade_closed`; it never blanks.
- **Memo audio drifts against the playhead** — signal: the memo plays over the wrong bar. Response:
  `durMs` is authoritative, re-sync on every scrub, mute above 2x rather than pitch-shift.
- **Post-roll never arrives** (shutdown before `close + post_roll_s`) — signal: a short tape.
  Response: flush on shutdown and at session end with whatever post-roll exists; `n` is stored, so a
  short window renders correctly rather than erroring.

## Security Considerations

- Replay routes are same-origin behind the existing token; no new public surface.
- Event labels come from a fixed table; memo transcripts rendered beside the timeline are player text
  and are escaped, never `{@html}`.
- `GET /api/voice/:id/audio` resolves its path from the DB row (phase 8), never from the URL.

## Next Steps

Phase 11's Review axis credits opening a replay — reviewing is part of the process being scored.
