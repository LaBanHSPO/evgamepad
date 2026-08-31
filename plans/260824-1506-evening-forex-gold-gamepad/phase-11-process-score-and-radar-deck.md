---
title: "Phase 11: Process Score and radar deck"
status: in-progress
phase: 11
priority: P1
effort: 8h
dependencies: [4, 6, 7, 8, 9, 10]
---

# Phase 11: Process Score and radar deck

## Overview

TradeZella's Zella Score gives the player one number to chase. That is the right game mechanic and
the wrong inputs — win rate and profit factor are outcome, and chasing them is exactly the outcome
anxiety this plan exists to treat.

This phase ships the same mechanic on **five process-only axes**, with one property that makes it
work: **a correctly-declined evening scores at least as well as a well-traded one.** The dead-tape
zero-trade evening scores **100**; the busy, well-executed evening scores **98**. Freezing in a rich
tape scores 70. Overtrading a dead tape scores 65.

No streaks. No levels. No cross-session accumulator exists anywhere in the schema.

## Context Links

- [plan.md](./plan.md)
- [Phase 4 — sentinel publishes numeric opportunity quality](./phase-04-ai-desk-sentinel-news-volman.md)
- [Phase 6 — process panel, pure metric functions, low-N discipline](./phase-06-performance-and-psychology-deck.md)
- [Phase 7 — grades supply Adherence](./phase-07-playbook-and-trade-grading.md)
- [Phase 8 — memo evidence](./phase-08-voice-capture-whisper-and-coach.md)
- [Phase 9 — tilt is a retrospective here, never a score input](./phase-09-tilt-telemetry-and-adaptive-friction.md)
- [Phase 10 — replay-open evidence](./phase-10-trade-replay.md)
- Steenbarger: markets do not offer equal opportunity every night. **Cite, do not paste.**

## Requirements

### Axes

- Functional: five axes, weights summing to 1.00 (boot-fail otherwise, phase 1):

  | axis | definition | w |
  |---|---|---|
  | **Adherence** | required playbook rules passed / required rules evaluated, over all fires tonight | 0.30 |
  | **Selectivity** | how well trade count matched the tape's opportunity quality | 0.25 |
  | **Risk discipline** | per fire: lots <= cap, SL present at entry, R within `r_unit_usd` +/- tol, `max_positions` respected, `min_seconds_between_orders` respected | 0.20 |
  | **Preparation** | plan acknowledged before first fire, pre check-in, >=1 playbook selected, >=1 memo | 0.15 |
  | **Review** | post check-in, memos on >=2/3 of trades, >=1 replay opened, checklists answered | 0.10 |

- Non-functional: win rate, profit factor, P/L and R **are not axes**. Every input is process-side
- Non-functional: **tilt is not an input** (phase 9 decision). It renders on this deck as a session
  retrospective only
- Functional: memo sub-items are evidence only when `voice.enabled` and capture was available. If
  voice is disabled or the browser has no usable mic, drop those sub-items and renormalise the axis;
  do not punish a supported degradation mode. If voice was available and the player skipped it,
  the sub-item remains a genuine miss

### Selectivity — the mechanism that makes standing down pay

- Functional: from the phase 4 sentinel's numeric `opportunity_quality` (OQ in `[0,1]`), averaged
  over the session:

```
expected      = round(OQ * score.trades_max)          # trades_max default 6
band          = [max(0, expected - 1), expected + 1]
Selectivity0  = 100                                    if fires in band
              = clamp(100 - 25 * distance_outside_band, 0, 100)
declineCredit = min(15, 5 * declines_during_standdown)
Selectivity   = min(100, Selectivity0 + declineCredit)
```

- Functional: `declines_during_standdown` reuses the **existing phase 3 stood-down counter** — an ARM
  cancelled while a stand-down condition was live (T-15 high-impact event, spread over cap, no
  playbook rule set satisfied, tilt >= 0.60, outside the window). One counter, not a second one
- Non-functional: `declineCredit` caps at 15 so cancels cannot be farmed; Selectivity cannot exceed 100

### Vacuous axes

- Functional: with zero fires, Adherence and Risk Discipline have **no denominator**. Scoring them 0
  punishes standing down (forbidden); scoring them 100 is free points for doing nothing. Correct
  answer: **drop vacuous axes and renormalise the weights over the axes that have evidence**
- Functional: dropped axes render on the radar as a dashed **"n/a — no trades"** ring, never as a
  zero spoke
- Functional: on a zero-trade evening, Review's trade-dependent sub-items are replaced by
  trade-independent ones (post check-in, >=1 memo tonight, and >=1 eligible past trade replayed).
  If no past trade exists yet, drop the replay item and renormalise rather than making a first
  session fail an impossible requirement

### Persistence and auditability

- Functional: `session_score(session_id, adherence, selectivity, risk_discipline, preparation, review, oq_mean, n_fires, na_axes JSON, weights_version, total)`
- Functional: store the axis **inputs**, not just the total, so a weight change recomputes
  retroactively and every number on the deck is auditable
- Non-functional: the score is a **pure function over rows**, matching phase 6's existing discipline.
  No LLM computes a number that appears on the deck

### Deck surface

- Functional: radar chart of the five axes on the phase 6 **ProcessPanel** — the game layer lives on
  the deck, not on the HUD
- Functional: per-playbook stats table: n, adherence, expectancy in R, avg MFE/MAE, avg efficiency.
  Process figures default; outcome figures stay behind phase 6's existing deliberate tab click
- Functional: month-over-month ProcessScore **distribution** with n — never a streak, never a
  "days since"
- Functional: tilt retrospective: bands over the session, top drivers, correlated against adherence
  (not against P/L)
- Functional: copilot `get_progress` extended with the axes so it can coach a specific axis
- Non-functional: every panel keeps the demo / entertainment / not-advice line

## Architecture

```
trade_grade (7) ─┐
risk rules (2)   ├─> score/session.py (pure)  -> session_score row
sentinel OQ (4)  │        drop vacuous axes, renormalise
stood-down (3)   │
checkins/memos  ─┘
                          |
              GET /api/score/session/:id
                          |
              ProcessPanel radar + per-playbook table + tilt retrospective
                          |
              copilot get_progress (read-only, still no order tool)
```

## Worked calibration (must be reproduced by the unit tests)

**Active good evening.** OQ 0.72 -> expected 4, band [3,5]. Four fires (3 win, 1 loss — irrelevant).

| axis | working | value |
|---|---|---|
| Adherence | 5/5, 5/5, 4/5, 5/5 = 19/20 | 95 |
| Selectivity | 4 in [3,5] -> 100, +2 declines, capped | 100 |
| Risk discipline | 20 checks, one fire had no SL at entry -> 19/20 | 95 |
| Preparation | 4/4 | 100 |
| Review | 4/4 | 100 |

`0.30*95 + 0.25*100 + 0.20*95 + 0.15*100 + 0.10*100 = 28.5 + 25 + 19 + 15 + 10 =` **97.5 -> 98**

The displayed total is the axis-weighted sum rounded half-up to an integer. Store the unrounded value.

**Dead tape, zero trades.** OQ 0.18 -> expected 1, band [0,2]. Zero fires.

| axis | working | value |
|---|---|---|
| Adherence | no fires | **n/a** |
| Selectivity | 0 in [0,2] -> 100, +3 declines, capped | 100 |
| Risk discipline | no fires | **n/a** |
| Preparation | 4/4 | 100 |
| Review | 3/3 (trade-independent variant) | 100 |

`(0.25*100 + 0.15*100 + 0.10*100) / (0.25+0.15+0.10) = 50 / 0.50 =` **100**

**Two calibration checks proving it is not a free lunch:**

- *Froze in a rich tape* (OQ 0.72, 0 fires): distance outside band = 3 -> Selectivity0 = 25, +15
  credit = 40 -> `(0.25*40 + 0.15*100 + 0.10*100)/0.50 =` **70**. Lower, and the axis names why —
  timidity is a smaller sin than recklessness
- *Overtraded a dead tape* (OQ 0.18, 5 fires, Adherence 80, Risk 70, Review 60):
  `24 + 6.25 + 14 + 15 + 6 =` **65**. Correctly mediocre

## Related Code Files

- Create: `apps/gateway/score/session.py` (pure axes, vacuous-axis renormalisation)
- Create: `apps/gateway/score/test_session.py` (the four worked examples above, to the point)
- Create: `apps/gateway/score/routes.py` (`GET /api/score/session/:id`, `GET /api/score/month`)
- Create: `apps/gateway/db/migrations/008-score.sql`
- Create: `apps/web/src/deck/ScoreRadar.tsx` (5 spokes, dashed n/a ring)
- Create: `apps/web/src/deck/PlaybookStats.tsx`
- Create: `apps/web/src/deck/TiltRetro.tsx`
- Modify: `apps/web/src/deck/ProcessPanel.tsx` (radar + tables)
- Modify: `apps/gateway/journal/writer.py` (`session_score` writes)
- Modify: `apps/gateway/copilot/tools.py` (`get_progress` returns the axes)
- Modify: `apps/gateway/deck/metrics.py` (share pure helpers; do not duplicate)
- Modify: `config/default.yaml` (`score.weights`, `score.trades_max`, `score.band_width`)
- Modify: `README.md` (what the score rewards and what it deliberately ignores)

## Implementation Steps

1. `session.py` pure axes, with the four worked examples as the first tests written.
2. Vacuous-axis drop and renormalisation; assert the dead-tape evening scores >= the active one.
3. Selectivity against the phase 4 numeric OQ; fall back to three buckets (dead/normal/rich ->
   expected 1/3/5) if the sentinel's components resist normalisation.
4. Apply `008-score.sql`; write `session_score` at session close, storing inputs; recompute-on-read for old rows when
   `weights_version` differs.
5. Radar component with the dashed n/a ring.
6. Per-playbook table and tilt retrospective on the ProcessPanel.
7. `get_progress` extension; re-assert the copilot still has no write or order tool.

## Todo

- [x] Pure axes + the four worked examples as tests
- [x] Vacuous axes drop and renormalise
- [x] Selectivity from numeric OQ *(the bucket fallback was not needed — see Deviations)*
- [x] `008-score.sql`; `session_score` stores inputs, not just the total
- [x] Radar with dashed n/a ring
- [x] Per-playbook stats table
- [x] Tilt retrospective (not an input)
- [x] `get_progress` returns axes, still no order tool
- [x] Month-over-month distribution with n

## Success Criteria

- [x] The dead-tape zero-trade evening scores **100** and the active good evening scores **98** —
      reproduced exactly by the unit tests
- [x] Freezing in a rich tape scores 70; overtrading a dead tape scores 65
- [x] A zero-trade evening shows Adherence and Risk Discipline as a dashed **n/a** ring, not a zero spoke
- [x] Changing `score.weights` in config recomputes historical scores from stored inputs
- [x] `score.weights` not summing to 1.0 refuses to boot
- [x] No dollar figure appears on the ProcessPanel, radar included
- [x] Nothing in the schema accumulates across sessions — no streak, no level, no "days since"
- [x] Tilt appears as a retrospective and is absent from the score inputs
- [x] Copilot can coach a named axis and still has no `place` / `close` / write tool

## Verification Status

Gateway `uv run pytest -q`: **386 passed, 1 skipped** (the skip is phase 2's broker volume test,
still waiting on a real cTrader dump); `uv run ruff check .` clean. Web `npm test`: **137 passed**
(9 new); `npx tsc --noEmit` and `npm run build` clean.

| Claim | Proof |
|---|---|
| The four worked calibrations | `score/test_session.py` reproduces 98 / 100 / 70 / 65 exactly, and asserts the *ordering* separately: a correctly-declined evening ≥ a well-traded one, and timidity > recklessness |
| Vacuous axes drop rather than score | Adherence and Risk Discipline return `None` at zero fires; the dead-tape evening renormalises to exactly 100, not 50. A separate test proves one bad fire gives both a real denominator, so nothing hides behind renormalisation |
| An unplanned evening has no adherence denominator either | A fire with no playbook evaluates no required rule; dividing by nothing is not a score of nothing |
| No outcome input | `test_no_outcome_figure_reaches_the_score` reads `session.py` past its own docstring and fails on pnl / profit / win_rate / equity / balance / usd / r_multiple |
| Tilt is not an input | `test_tilt_is_not_an_input` greps the score module and both input dataclasses. Phase 9's guard was **retargeted** from `deck/metrics.py` to the score itself — see Deviations |
| Nothing accumulates | `test_the_schema_has_nowhere_to_accumulate_across_sessions` walks every table's every column via `PRAGMA table_info` and fails on streak / level / badge / days_since / consecutive |
| A weight change recomputes history | A stored evening re-served under a weighting of `adherence: 1.0` returns that axis exactly. The routes recompute on read rather than returning the stored total |
| Vacuous axes are stored as NULL, not 0 | Asserted against the written row, alongside the `na_axes` JSON |
| The risk context is the one frozen at the fire | A fire under an 0.02 cap fails `within_lot_cap` even though today's config allows 0.10 |
| A missing column is not a breach | An unrecorded cap passes rather than inventing a violation |
| No money on the process side | `score.test.ts` strips comments and fails on usd/pnl/balance/equity/profit, plus any `$` that is not a template placeholder, across the radar, the ProcessPanel and the tilt retro |
| The n/a ring, not a zero spoke | The polygon uses `axis.value ?? 100`, so a vacuous axis never dips toward the centre, and its ring is dashed and labelled with the axis's own reason |
| Outcome columns stay behind the click | The process-side effect is asserted not to fetch `playbooks/outcome`; only `openOutcome` does |
| The desk gains the axes and no tool | `get_progress` folds in `axes_summary`, which is asserted to carry no money word; the phase 4 forbidden-verb test still passes unchanged |

## Deviations

- **Phase 4's opportunity quality was computed but never persisted.** `session_process.opportunity_quality`
  existed as a column from phase 6 with nothing writing it, so Selectivity had no tape to compare
  against. Phase 11 adds `score/opportunity.py`, a running mean sampled on the same 1 Hz clock that
  already drives tilt, written once at session close. An evening that was never sampled reads as
  `None` and makes Selectivity **vacuous** — an unsampled tape and a dead one must stay
  distinguishable, and guessing between them would be the exact kind of invented number the axis
  detail exists to prevent.
- **The three-bucket fallback was not needed.** The plan allowed falling back to dead/normal/rich if
  the sentinel's numeric quality resisted normalisation. It did not: phase 4 already produces a
  weighted `quality` in `[0,1]`, so the numeric path is the one that shipped and the fallback would
  have been unused code.
- **Phase 9's tilt guard was retargeted, not relaxed.** It read `deck/metrics.py` and failed on the
  word "tilt". Phase 11 requires a tilt *retrospective* on the deck, so the old guard would have
  forbidden a thing the plan asks for. The invariant was always about what the score **consumes**,
  not what the deck may show, so it now greps `score/session.py` and both input dataclasses — the
  place the rule actually lives — and a second test asserts the retrospective is set against
  adherence and carries no money word.
- **Recording a replay open is a write, so it lives on the score surface.** Phase 10's guarantee is
  that `/api/replay/*` is read-only, asserted by a test that fails on any statement but `SELECT`.
  The Review axis needs to know a trade was reviewed, so that write goes to
  `POST /api/score/evidence/replay` instead. Phase 10's gateway-side guard is untouched; its
  client-side fetch guard was widened to allow that one target and tightened to assert no order
  path is ever reached.
- **Memo evidence is gated on capture being *built*, not just enabled.** `voice.enabled` ships
  `true`, but phase 8 is deferred and no capture path exists. Treating a memo as a miss would score
  the install rather than the evening, which the plan explicitly forbids, so `VOICE_CAPTURE_BUILT`
  in `score/repository.py` is `False` until phase 8 lands and the memo sub-items drop out and
  renormalise. Phase 8's note records the flip.
- **The playbook table's `n` and adherence are the process figures; expectancy, MFE, MAE and
  efficiency ride the outcome tab.** The plan asks for one table with both. Splitting it was the
  only way to keep phase 6's rule that outcome data is not even *fetched* until the deliberate
  click. Efficiency is `None` — not zero — for a trade that never went your way: calling that zero
  would blame the exit for the entry.
- **The radar is hand-written SVG.** Five points and two rings is less code than configuring a chart
  library, and the dashed n/a ring is not a thing chart libraries draw. It also keeps the deck out
  of the lazily-loaded replay chunk that carries Lightweight Charts.
- **`score/routes.py` is `score/repository.py` plus routes in `main.py`.** The plan names a routes
  module; the repository pattern is what phases 6, 7 and 10 already use, and every route in this
  build is registered in `main.py`. Following the existing convention beat adding a fourth shape.

## Risk Assessment

- **The score becomes the anxiety P/L used to be** — signal: the player refreshes the deck
  mid-session. Response: the score is computed at session **close** only and lives on the deck, never
  on the HUD; there is no live score to watch.
- **Decline farming** — signal: dozens of ARM-cancels an evening. Response: credit caps at 15 and
  Selectivity cannot exceed 100; the counter only increments during a genuine stand-down condition.
- **`trades_max: 6` and the +/-1 band are uncalibrated for this player** — signal: Selectivity pinned
  at 100 or never reaching it. Response: both are config, `session_score` stores its inputs, and the
  first month is explicitly provisional.
- **OQ cannot be made a defensible 0-1 number** — signal: the sentinel's components need arbitrary
  constants. Response: fall back to three buckets; the formula is unchanged, only the resolution drops.
- **Renormalisation hides a bad evening** — signal: an evening with one terrible fire scores high
  because most axes were vacuous. Response: axes are only vacuous at **zero** fires; one fire gives
  Adherence and Risk Discipline a real denominator.

## Security Considerations

- `/api/score/*` is same-origin behind the existing token.
- `get_progress` returns aggregates only — never the raw journal, never credentials.
- Scores are computed server-side from stored rows; the client never submits a score.

## Next Steps

Phase 12 turns this score and its evidence into the daily journal cockpit. This is the number the
game was actually asking for — and the one evening it rates highest is the one where you correctly
did nothing.
