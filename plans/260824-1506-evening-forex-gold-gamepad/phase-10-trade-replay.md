---
title: "Phase 10: Trade replay"
status: todo
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
        Replay.svelte  (order FSM hard-LOCKED)
        Lightweight Charts + marker layer + event rail
        LS scrub / RS zoom / A play / D-pad speed / LB-RB step / B exit
        <audio> memo playback synced to the playhead
```

## Related Code Files

- Create: `apps/gateway/src/replay/routes.ts` (`GET /api/replay/:cid`, `GET /api/replay/index`)
- Create: `apps/gateway/src/replay/routes.test.ts` (missing tape, missing memo, gzip round-trip)
- Create: `apps/web/src/replay/Replay.svelte` (route shell, FSM lock)
- Create: `apps/web/src/replay/Timeline.svelte` (playhead, event rail, memo pins)
- Create: `apps/web/src/replay/Markers.ts` (entry/exit/MFE/MAE/arm/cancel marker layer)
- Create: `apps/web/src/replay/transport.ts` (play/pause/scrub/speed; audio sync)
- Create: `apps/web/src/replay/resample.ts` (1 Hz -> displayed timeframe)
- Create: `apps/web/src/replay/resample.test.ts` (integer-price OHLC aggregation is lossless)
- Modify: `apps/web/src/App.svelte` (route `/replay/:cid`, FSM lock on entry, unlock on exit)
- Modify: `apps/web/src/deck/OutcomePanel.svelte` (trade rows link to replay)
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

- [ ] `/api/replay/:cid` + index route
- [ ] gzip columnar round-trip test
- [ ] Chart + entry/exit/MFE/MAE markers
- [ ] Client-side resample, lossless on integer prices
- [ ] Transport: scrub, play, speed
- [ ] Event rail (arm, cancel, fire, tag, tilt band)
- [ ] Grade panel
- [ ] Memo audio synced to the playhead
- [ ] FSM hard-locked on the route

## Success Criteria

- [ ] Opening `/replay/:cid` for a closed trade paints the tape with entry, exit, MFE and MAE marked
- [ ] An ARM that was cancelled before the fire is visible on the event rail at its real timestamp
- [ ] Scrubbing with LS moves the playhead smoothly and the memo audio follows and re-syncs
- [ ] **No order can be placed from the replay route** — the FSM is locked and the pad cannot fire
- [ ] A trade with no memo replays normally, with no audio controls
- [ ] A trade whose memo transcript failed still plays its audio
- [ ] LB/RB step to the previous and next trade of the same evening
- [ ] One evening of five trades adds under ~100 KB of tape

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
