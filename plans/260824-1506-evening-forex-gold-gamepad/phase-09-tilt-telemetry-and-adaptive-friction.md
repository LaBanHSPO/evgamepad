---
title: "Phase 9: Tilt telemetry and adaptive friction"
status: in-progress
phase: 9
priority: P1
effort: 10h
dependencies: [2, 3, 7]
---

# Phase 9: Tilt telemetry and adaptive friction

## Overview

Edgewonk asks you to rate your own emotional state after the fact. We can do better: the gamepad is
already telling us. Re-entry 40 seconds after a loss, lot size double the session median, six clutch
cycles before an arm, buy-sell-buy flipping while armed — these are **measured behaviours**, not
inferred feelings, and they are exactly the ones that precede a bad evening.

Two design rules make this a safety mechanism instead of a gimmick:

1. **Tilt is never an input to the Process Score.** Taxing the evening for a bad ten minutes would
   reintroduce the punishment this whole plan exists to avoid.
2. **Tilt can only ever slow down an open.** It can never gate, delay, or add friction to a close, a
   panic flatten, the HUD Flatten button, or a session lock.

## Context Links

- [plan.md](./plan.md)
- [Phase 2 — dead-man locks opens only; one predicate in `risk/rules.py`](./phase-02-ctrader-exec-and-socket-gateway.md)
- [Phase 3 — FSM telemetry fields, `confirmHoldMs` parameter, tilt pip](./phase-03-web-game-and-8bitdo-client-agent.md)
- [Phase 7 — grades supply the rule-break signal](./phase-07-playbook-and-trade-grading.md)
- [Phase 8 — voice arousal (optional, 5%)](./phase-08-voice-capture-whisper-and-coach.md)
- Steenbarger on process noise degrading decisions. **Cite, do not paste.**

## Requirements

### Signals (all measurable; nothing inferred)

- Functional: from the phase 3 FSM, batched at 1 Hz on the `session` channel as `pad.telemetry` —
  never per-frame: `{ ts, from, to, sym, lots, reason?, clutchMs, armMs, clutchCycles, armFlips, btnRateHz, lotStepsSince, ttfMs }`
  plus a 1 Hz heartbeat `{ idleMs, inputsLast60s, symbolSwitchesLast5m }`
- Functional: from the journal, zero new capture: `secondsSinceLastLoss`, `lossesTonight`,
  `lotEscalation = pending_lots / median(session lots)`, `reentrySpeed`, `openRate` vs session
  median, `ruleBreaks` in the last 3 fires (phase 7 grades), `outsideSetup`
- Functional: from voice (phase 8), **only two** defensible measures, each a deviation from the
  player's **own rolling 30-session baseline**, never a population claim: `speechRate_z` (transcript
  words / recording seconds) and `loudness_z` (mean RMS dBFS from an `AnalyserNode` on the same PTT
  stream). Contributes only when a memo exists in the last 10 minutes; otherwise its weight
  redistributes
- Non-functional: **no keyword scoring, no profanity detection, no affect classification, no LLM in
  the score.** That is the pseudo-science line and it is not crossed

### Composition

- Functional: `tilt = clamp01( sum(w_i * s_i) )`, every `s_i` in `[0,1]`, weights summing to 1.00,
  missing components renormalise the remainder:

  | component | s_i | w |
  |---|---|---|
  | revenge_size | `clamp01(lotRatio - 1)` | 0.25 |
  | reentry_speed | 1 at <60 s after a losing close, linear to 0 at 600 s | 0.20 |
  | rule_break_recency | adherence failures in the last 3 fires / 3 | 0.20 |
  | hesitation | `clamp01((clutchCycles - 1)/3)`, mean of last 3 arms | 0.10 |
  | arm_flip | `clamp01(armFlips/2)`, mean of last 3 arms | 0.10 |
  | input_aggression | `clamp01((btnRateHz - base)/base)`, base = session median | 0.10 |
  | voice_arousal | `clamp01((max(speechRate_z, loudness_z) - 1)/2)` | 0.05 |

- Functional: every component is a **nameable behaviour**. The HUD always renders the top
  contributor as a sentence ("re-entered 40 s after a loss"), never a bare number alone
- Functional: all baselines are the player's own rolling medians
- Non-functional: tilt is **never persisted as a trait** — per-session state plus `tilt_sample` rows
  for the deck's retrospective
- Non-functional: `consecutiveLossesTonight` is an input signal only and is **never rendered as a
  streak**

### Bands and intervention

- Functional:

  | band | HUD | friction |
  |---|---|---|
  | < 0.35 calm | tilt pip green | none |
  | 0.35-0.60 warm | pip amber + one line naming the top driver | **none** — a warning that costs nothing is one you keep listening to |
  | 0.60-0.80 hot | pip red + driver line; confirm overlay adds the driver and the trade's R; copilot `monitor` emits one advice | **friction 1:** ARM -> FIRE requires confirm **held 750 ms** instead of a rising edge |
  | >= 0.80 scorched | countdown + "log a memo" prompt | **friction 2:** opens soft-blocked for `tilt.cooldown_s` (300) |

- Functional: a memo recorded during a cooldown, or an explicit acknowledge, **halves the recency
  terms**. Narrating it is the intervention, so the productive alternative is rewarded rather than
  the door merely being locked
- Functional: `tilt` message on the `session` channel: `{ score, band, top[], cooldownUntil? }`

### FSM safety invariants (all testable)

- Functional: friction applies **only** to `intent.open`. `intent.close`, `intent.panic`, the HUD
  Flatten button and `session.lock` are never gated. Same predicate as the existing dead-man rule,
  implemented **once** in `risk/rules.py`, not duplicated
- Non-functional: config **boot-fails on `tilt.gate_close: true`** (phase 1) — a structural
  guarantee, not a code convention
- Functional: the client enforces the *UX* friction (hold-to-fire); the server enforces the *block*
  (reject with `reason: 'cooldown'`). The client is never the security boundary, and the server never
  adds a millisecond to a close
- Functional: tilt **never moves the FSM**. It changes exactly two things — the `confirmHoldMs`
  parameter of the fire predicate, and whether `intent.open` is accepted. `LOCKED/IDLE/CLUTCH/ARMED/FIRE`
  transitions stay byte-identical, so the phase 3 `fsm.test.ts` suite remains valid unchanged
- Functional: cooldown **fails open** on reconnect — recomputed from `cooldown_until`, and allowed if
  the clock is unusable. Deliberately the opposite of the dead-man, which fails closed: that one is
  about unattended input, this one is about a judgement call
- Functional: `tilt.enabled: false` removes it entirely

## Architecture

```
pad FSM  --1 Hz batch-->  pad.telemetry  ─┐
journal (losses, lots, grades)           ├─> tilt/score.py (pure)  -> tilt_sample rows
voice AnalyserNode + transcript (opt.)   ─┘          |
                                                     v
                                    band -> HUD pip + driver sentence
                                         -> confirmHoldMs (client friction)
                                         -> risk/rules.py open-only gate (server block)
```

## Related Code Files

- Create: `apps/gateway/tilt/score.py` (pure composition, renormalisation, bands)
- Create: `apps/gateway/tilt/test_score.py` (weights sum; missing components renormalise; tilt=1.0 never blocks close/panic)
- Create: `apps/gateway/tilt/baseline.py` (rolling 30-session medians per player)
- Create: `apps/gateway/db/migrations/007-tilt.sql`
- Create: `apps/web/src/hud/TiltPip.tsx` (band colour + top-driver sentence)
- Create: `apps/web/src/voice/arousal.ts` (AnalyserNode RMS; optional, phase 8)
- Modify: `apps/gateway/risk/rules.py` (open-only friction gate reusing the dead-man predicate)
- Modify: `apps/web/src/pad/fsm.ts` (consume `confirmHoldMs`; no new states)
- Modify: `apps/web/src/hud/ConfirmOverlay.tsx` (driver + R when hot)
- Modify: `apps/gateway/copilot/prompt.py` (one monitor advice at the hot band)
- Modify: `apps/gateway/journal/writer.py` (`tilt_sample` writes; `trade_closed.tilt_at_entry`)
- Modify: `config/default.yaml` (`tilt.*`)
- Modify: `README.md` (what tilt measures, what it can and cannot do)

## Implementation Steps

1. Apply `007-tilt.sql`; implement `score.py` pure functions and fixtures, including the
   renormalisation cases.
2. Baselines from the journal; guard the cold-start month (fewer than 5 sessions -> behavioural
   components only, voice weight redistributed).
3. `tilt_sample` rows at 1 Hz plus `tilt_at_entry` frozen onto every fire.
4. HUD pip and the driver sentence; confirm overlay additions at the hot band.
5. `confirmHoldMs` threaded through the existing fire predicate — parameter, not new state.
6. Server cooldown gate in `risk/rules.py` reusing the dead-man open-only predicate.
7. Memo/acknowledge halving of recency terms.
8. Safety tests: `tilt = 1.0` and assert panic flatten executes and `intent.close` is accepted.

## Todo

- [x] `007-tilt.sql` + pure tilt composition + renormalisation fixtures
- [x] Own-baseline rolling medians + cold-start guard
- [x] `pad.telemetry` consumption at 1 Hz
- [x] HUD pip + top-driver sentence
- [x] `confirmHoldMs` friction (client) at the hot band
- [x] Server cooldown gate, opens only, reusing the dead-man predicate
- [x] Memo/acknowledge halves recency
- [x] tilt=1.0 cannot block close or panic
- [x] `tilt.enabled: false` removes it cleanly

## Success Criteria

- [x] With `tilt = 1.0` forced, panic flatten still executes and `intent.close` is still accepted
- [x] `tilt.gate_close: true` refuses to boot
- [x] Two losing trades then a double-size re-entry inside 60 s pushes the band to hot and names
      "revenge sizing" as the top driver
- [x] At the hot band, firing requires a 750 ms confirm hold; closing does not change at all
- [x] At the scorched band, `intent.open` is rejected with `reason: 'cooldown'` and the HUD counts down
- [x] Recording a memo during cooldown measurably lowers the score *(composition proved; the feed lands with phase 8 — see Deviations)*
- [x] A reconnect during cooldown **allows** trading if the clock is unusable (fails open)
- [x] The phase 3 `fsm.test.ts` suite passes unchanged
- [x] Tilt appears nowhere in the phase 11 Process Score inputs

## Verification Status

Gateway `uv run pytest -q`: **316 passed, 1 skipped** (the skip is phase 2's broker volume test,
which waits on a real cTrader dump). `uv run ruff check .`: clean. Web `npm test`: **93 passed**;
`npx tsc --noEmit` and `npm run build` (protocol drift gate included): clean.

Where each safety claim is actually proved:

| Claim | Proof |
|---|---|
| `tilt = 1.0` never blocks a close or a panic | `tilt/test_score.py::test_with_tilt_forced_to_one_a_close_and_a_panic_still_execute` scores 1.0 and asserts `evaluate_exit()` runs **no** rules; `api/test_ws.py::test_tilt_at_one_still_lets_a_close_and_a_panic_through` drives both intents through the real socket with the tracker maxed |
| Open-only by construction, not by convention | The cooldown is a `scope="risk"` entry in the one `method/rules.py` registry. `risk/rules.py` builds `OPEN_RULES` from `rules_for("risk")` and `evaluate_exit` iterates nothing, so no close can reach the gate even by mistake |
| `tilt.gate_close: true` refuses to boot | `test_config.py` parametrised boot-fail case, from phase 1 |
| The cooldown fails open | `cooldown_active` returns `False` for a missing `cooldown_until` **and** for an unusable clock (`test_the_cooldown_fails_open`); `test_a_reconnect_with_no_cooldown_recorded_allows_trading` drives the same case through the gate, and `test_an_expired_cooldown_stops_blocking` through the real socket |
| Tilt never reaches the Process Score | `test_tilt_never_reaches_the_process_score` reads `deck/metrics.py` and fails on the word |
| The FSM is unchanged | `fsm.test.ts` (23 tests) passes untouched; `tilt.test.ts` greps `pad/fsm.ts` and fails if the word appears. Tilt reaches the client only as `agent.setConfirmHoldMs()` — a parameter of the existing fire predicate |
| Friction is described in terms of opens only | `tilt.test.ts` asserts `BAND_FRICTION` contains "fire" and none of close / panic / flatten / lock |
| The desk sees aggregates only | `test_the_desk_only_ever_sees_tilt_aggregates` pins the shared cell to exactly `{band, score, top}`; `test_copilot.py` asserts `get_tilt` carries no money or component key, and that the tool is simply absent when tilt is off |
| The two copies of `confirm_hold_ms` cannot drift | `tilt.test.ts` parses `config/default.yaml` and fails the web build if it stops matching `HOT_HOLD_MS` |

## Deviations

- **The two ways out of a cooldown are wired to nothing until phase 8.** `score_tilt` halves the
  recency terms on a memo or an acknowledgement, proved by `test_a_memo_halves_the_recency_terms`
  and `test_an_acknowledgement_halves_them_too`, and `TiltTracker.observe_memo` /
  `.acknowledge` set the flags. Neither has a caller: both interventions are memo-shaped and the
  memo pipeline is phase 8's. Nobody is trapped meanwhile — the cooldown is 300 s, it fails open,
  and it never touched an exit — but until phase 8 resumes, waiting is the only way out. This is
  recorded in the phase 8 doc as work its resume owes.
- **Voice contributes nothing yet.** Phase 8 is deferred, so `TiltTracker.inputs()` passes
  `speech_rate_z`, `loudness_z` and `seconds_since_memo` as `None`. That is the *measured* path, not
  a stub: the component drops out and its 0.05 renormalises across the behavioural six, exactly as a
  memo-less evening already does. `apps/web/src/voice/arousal.ts` from the file list belongs to
  phase 8 and was not written — writing an `AnalyserNode` with no PTT stream to attach it to would
  be scaffolding, not behaviour. `score.py` and `test_score.py` already cover the voice component
  end to end; only its feed is missing.
- **The confirm overlay shows the evening's realised R, not the prospective trade's.** The plan
  asks for "the trade's R". The pad fires market orders and the agent sends no `relativeSl`, so
  there is no stop distance from which a prospective R could be computed — any number there would
  be invented. What is shown instead is real and broker-sourced: the driver sentence plus `dayPnl`
  converted at the HUD's R unit. A prospective R becomes computable when a stop model lands.
- **The hot-band desk advice is edge-triggered and fire-and-forget.** The plan says "one advice" at
  the hot band. It fires on the *crossing* into hot or scorched, not per telemetry batch, and runs
  as its own task so a desk speaking over the network can never sit between an intent and the
  broker. A failing desk is logged and the tilt frame ships regardless.
- **The migration ledger skips 006.** `007-tilt.sql` follows `005`; 006 was never issued. The
  ledger is per-id rather than a high-water mark, so the gap is legal and the file says so in its
  header — this is recorded here so a later reader does not go looking for a lost migration.
- **`RECENT_ARMS` is defined in both `score.py` and `tracker.py`.** The scorer documents the window
  its component sentences describe; the tracker owns the actual `deque` maxlen. They are the same
  number for the same reason, and only the tracker's value has any runtime effect.

## Risk Assessment

- **Tilt blocks an exit during a fast move** — the one genuinely dangerous failure. Signal: any
  rejection of a close. Response: one open-only predicate shared with the dead-man, a boot-fail on
  `gate_close`, and a forced-tilt test asserting close and panic both work.
- **False positives make the player disable it** — signal: hot band on a calm evening. Response: the
  warm band costs nothing, all baselines are the player's own, and every alert names its driver so a
  wrong one is obviously wrong.
- **Voice arousal is pseudo-science** — signal: it cannot be validated against the player's own
  baseline. Response: capped at 0.05, renormalises away, and is **deleted rather than defended** if
  a month of data does not support it.
- **Cold start has no baseline** — signal: wild scores in week one. Response: behavioural components
  only below 5 sessions; the pip renders neutral rather than guessing.
- **Friction becomes a way to punish** — signal: the player reads the pip as a scolding. Response:
  tilt is excluded from the score, the copy names behaviour not character, and the cooldown offers a
  memo as the way out.

## Security Considerations

- `tilt_sample` rows are behavioural telemetry about one local player; they never leave the box and
  are never sent to the LLM as anything but aggregates via the phase 4 `get_tilt` read-only tool.
- Driver sentences are generated from a fixed string table, not from player text, so nothing
  untrusted reaches the HUD through this path.

## Next Steps

Phase 11 renders tilt's session history on the deck as a **retrospective**, still not as a score input.
