---
title: "Phase 9: Tilt telemetry and adaptive friction"
status: todo
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
- [Phase 2 — dead-man locks opens only; one predicate in `risk.ts`](./phase-02-ctrader-exec-and-socket-gateway.md)
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
  implemented **once** in `risk.ts`, not duplicated
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
journal (losses, lots, grades)           ├─> tilt/score.ts (pure)  -> tilt_sample rows
voice AnalyserNode + transcript (opt.)   ─┘          |
                                                     v
                                    band -> HUD pip + driver sentence
                                         -> confirmHoldMs (client friction)
                                         -> risk.ts open-only gate (server block)
```

## Related Code Files

- Create: `apps/gateway/src/tilt/score.ts` (pure composition, renormalisation, bands)
- Create: `apps/gateway/src/tilt/score.test.ts` (weights sum; missing components renormalise; tilt=1.0 never blocks close/panic)
- Create: `apps/gateway/src/tilt/baseline.ts` (rolling 30-session medians per player)
- Create: `apps/web/src/hud/TiltPip.svelte` (band colour + top-driver sentence)
- Create: `apps/web/src/voice/arousal.ts` (AnalyserNode RMS; optional, phase 8)
- Modify: `apps/gateway/src/risk.ts` (open-only friction gate reusing the dead-man predicate)
- Modify: `apps/web/src/pad/fsm.ts` (consume `confirmHoldMs`; no new states)
- Modify: `apps/web/src/hud/ConfirmOverlay.svelte` (driver + R when hot)
- Modify: `apps/gateway/src/copilot/prompt.ts` (one monitor advice at the hot band)
- Modify: `apps/gateway/src/journal.ts` (`tilt_sample` writes; `trade_closed.tilt_at_entry`)
- Modify: `config/default.yaml` (`tilt.*`)
- Modify: `README.md` (what tilt measures, what it can and cannot do)

## Implementation Steps

1. `score.ts` pure functions and fixtures first, including the renormalisation cases.
2. Baselines from the journal; guard the cold-start month (fewer than 5 sessions -> behavioural
   components only, voice weight redistributed).
3. `tilt_sample` rows at 1 Hz plus `tilt_at_entry` frozen onto every fire.
4. HUD pip and the driver sentence; confirm overlay additions at the hot band.
5. `confirmHoldMs` threaded through the existing fire predicate — parameter, not new state.
6. Server cooldown gate in `risk.ts` reusing the dead-man open-only predicate.
7. Memo/acknowledge halving of recency terms.
8. Safety tests: `tilt = 1.0` and assert panic flatten executes and `intent.close` is accepted.

## Todo

- [ ] Pure tilt composition + renormalisation fixtures
- [ ] Own-baseline rolling medians + cold-start guard
- [ ] `pad.telemetry` consumption at 1 Hz
- [ ] HUD pip + top-driver sentence
- [ ] `confirmHoldMs` friction (client) at the hot band
- [ ] Server cooldown gate, opens only, reusing the dead-man predicate
- [ ] Memo/acknowledge halves recency
- [ ] tilt=1.0 cannot block close or panic
- [ ] `tilt.enabled: false` removes it cleanly

## Success Criteria

- [ ] With `tilt = 1.0` forced, panic flatten still executes and `intent.close` is still accepted
- [ ] `tilt.gate_close: true` refuses to boot
- [ ] Two losing trades then a double-size re-entry inside 60 s pushes the band to hot and names
      "revenge sizing" as the top driver
- [ ] At the hot band, firing requires a 750 ms confirm hold; closing does not change at all
- [ ] At the scorched band, `intent.open` is rejected with `reason: 'cooldown'` and the HUD counts down
- [ ] Recording a memo during cooldown measurably lowers the score
- [ ] A reconnect during cooldown **allows** trading if the clock is unusable (fails open)
- [ ] The phase 3 `fsm.test.ts` suite passes unchanged
- [ ] Tilt appears nowhere in the phase 11 Process Score inputs

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
