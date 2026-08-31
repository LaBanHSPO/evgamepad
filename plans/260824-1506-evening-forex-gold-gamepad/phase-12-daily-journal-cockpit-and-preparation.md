---
title: "Phase 12: Daily Journal Cockpit and Preparation"
status: in-progress
phase: 12
priority: P1
effort: 24h
dependencies: [11]
---

# Phase 12: Daily Journal Cockpit and Preparation

## Overview

Complete the focused single-player journal: prepare the evening, inspect the daily record, find
repeatable edges and execution mistakes, and move from a closed session into a concrete review.
This is still one IC Markets cTrader demo account, desktop Chrome, dark-only. It is not a general
multi-account journal platform.

## Context Links

- [plan.md](./plan.md)
- [Phase 2 — trade plan, fills, conversion, tape](./phase-02-ctrader-exec-and-socket-gateway.md)
- [Phase 6 — deterministic performance metrics](./phase-06-performance-and-psychology-deck.md)
- [Phase 7 — playbook and grades](./phase-07-playbook-and-trade-grading.md)
- [Phase 10 — replay](./phase-10-trade-replay.md)
- [Phase 11 — Process Score](./phase-11-process-score-and-radar-deck.md)

## Requirements

### Preparation cockpit

- Functional: `/journal/today` is the entry point before a session and the landing page after close.
- Functional: four timezone-aware market clocks — Sydney (`Australia/Sydney`), Tokyo
  (`Asia/Tokyo`), London (`Europe/London`), New York (`America/New_York`) — use IANA zones so DST
  is never a hard-coded UTC offset.
- Functional: five-item readiness checklist with defaults: sleep/energy, emotional calm,
  focus/distraction, acceptance of tonight's risk cap, and plan/news reviewed. Each item is
  yes/no plus an optional note. Readiness is advisory and never blocks unlock or trading.
- Functional: position-size calculator takes account equity, risk USD or percent, symbol, entry,
  and stop. It calls the phase 2 quote-to-deposit conversion and lot-rounding functions, then shows
  requested lots, broker-rounded lots, actual risk USD, and any configured cap. Applying the value
  only changes the HUD preview; LT+RT is still required to trade.
- Functional: durable daily analysis entry: thesis, instruments, key levels, invalidation, event
  risks, tags, and notes. Link the stored phase 4 session plan; the model never silently writes or
  edits player-authored analysis.
- Functional: attach local PNG/JPEG/WebP chart screenshots to a daily analysis or trade review.
  This is manual attachment only — no TradingView scraping or unofficial quote API.

### Journal dashboard and history

- Functional: period filter `week | month | custom`; the single configured cTrader account appears
  as a read-only identity chip, not a multi-account selector.
- Functional: process-first day heatmap. Default colour encodes Process Score/adherence and activity;
  P/L colouring is available only inside the deliberate Outcome tab.
- Functional: selecting a day shows session count, trade count, readiness, Process Score, check-in,
  daily analysis, mistakes, and the day's trades. Dollar P/L remains behind Outcome.
- Functional: latest ten trades show symbol, side, timeframe, playbook, plan classification, R,
  execution-stage scores, and a replay thumbnail/link.
- Functional: `/journal/history` supports filters for period, playbook/setup, symbol, timeframe,
  buy/sell, market session, plan classification, mistake, and win/loss/breakeven.
- Functional: `/journal/trade/:cid` shows the immutable trade plan, fill/close facts, SL/TP changes,
  grade, memos, attachments, mistakes, replay link, and Actual vs Plan comparison.
- Functional: dashboard metrics include profit factor, average win, average loss, win rate, return,
  max drawdown, average R, and Process Consistency. Outcome metrics never lead the page.
- Functional: Process Consistency over the latest 20 eligible sessions is
  `clamp(0, 100, 0.5 * mean(ProcessScore) + 0.5 * (100 - mean absolute deviation from the median))`.
  Always show `n`; below five sessions render `not enough sessions yet`.

### Trade quality and learning

- Functional: Actual vs Plan compares planned risk/target R and SL/TP snapshot with realised R and
  recorded amendments. It must not claim the planned target would have been hit; label the surface
  `Actual vs Plan`, not `theoretical profit`.
- Functional: four groups are derived only with evidence:
  `planned-win`, `planned-loss`, `impulsive/revenge-loss`, `impulsive/revenge-win`.
  Clean non-`__unplanned__` fires default to planned; dirty/unplanned fires ask the player to confirm
  `planned | impulsive | revenge | unknown`. Unknown is excluded from the four-group chart.
- Functional: deterministic before/during/after execution scores, each `0..100` with unknown inputs
  dropped and weights renormalised. Before uses plan/readiness/grade; during uses size, initial SL,
  SL/TP amendments and rule adherence; after uses checklist, memo, post check-in, and replay review.
  No LLM computes these scores.
- Functional: built-in mistake taxonomy plus custom mistakes. Built-ins include oversize, no initial
  SL, worsened SL, early discretionary exit, chased entry, revenge re-entry, event-window trade,
  outside-session trade, wrong/no playbook, and skipped review.
- Functional: mistake trend shows frequency, affected trades, and one optional active improvement
  focus. No streak, badge, or penalty mechanic.
- Functional: `/system` stores the player's trading philosophy and core principles; `/playbooks`
  remains the setup library owned by phase 7.

### Data and API

- Functional: migration `009-journal-cockpit.sql` owns `readiness_check`, `daily_analysis`,
  `journal_attachment`, `trade_review`, `mistake_definition`, and `mistake_occurrence`.
- Functional: journal routes are plain same-origin HTTP:
  `GET /api/journal/overview|days|history|trade/:cid`,
  `GET|PUT /api/journal/today`, `POST /api/journal/attachments`, and
  `GET|PUT /api/journal/system`.
- Functional: all filter queries are parameterised and paginated; default history page size 50,
  maximum 200.
- Non-functional: desktop Chrome and dark theme only. No mobile/responsive delivery and no light mode.
- Non-functional: one cTrader demo account. No MT5, broker import, multi-market, or multi-account UI.

## Architecture

```text
phase 2 facts + phase 6 metrics + phase 7 grades + phase 8 memos
        + phase 10 replay + phase 11 score
                         |
               journal/query_service.py
                         |
          /api/journal/* + attachment storage
                         |
 /journal/today | /journal/history | /journal/trade/:cid | /system
```

The journal reads immutable broker facts and appends player review. A review can annotate a trade;
it cannot rewrite fills, prices, R conversion inputs, or execution events.

## Related Code Files

- Create: `apps/gateway/db/migrations/009-journal-cockpit.sql`
- Create: `apps/gateway/journal/query_service.py`
- Create: `apps/gateway/journal/metrics.py`
- Create: `apps/gateway/journal/test_metrics.py`
- Create: `apps/gateway/journal/routes.py`
- Create: `apps/gateway/journal/attachments.py`
- Create: `apps/web/src/journal/Today.tsx`
- Create: `apps/web/src/journal/WorldSessions.tsx`
- Create: `apps/web/src/journal/ReadinessChecklist.tsx`
- Create: `apps/web/src/journal/PositionSizeCalculator.tsx`
- Create: `apps/web/src/journal/Heatmap.tsx`
- Create: `apps/web/src/journal/History.tsx`
- Create: `apps/web/src/journal/TradeDetail.tsx`
- Create: `apps/web/src/journal/TradeQuality.tsx`
- Create: `apps/web/src/journal/MistakeTrends.tsx`
- Create: `apps/web/src/journal/SystemPrinciples.tsx`
- Modify: `apps/web/src/App.tsx` (journal routes)
- Modify: `apps/web/src/game-overlay/GameOverlay.tsx` (Journal and System destinations)
- Modify: `apps/gateway/copilot/tools.py` (read-only journal aggregates; no write tool)
- Modify: `README.md` (daily journal loop)

## Implementation Steps

1. Add migration and query contracts; keep broker facts immutable and review data append-only.
2. Implement world-session clocks, readiness checklist, daily analysis, and attachment storage.
3. Reuse phase 2 conversion/rounding for the position-size calculator; prove USDJPY conversion.
4. Implement period/day/history queries with all requested dimensions and pagination.
5. Implement Actual vs Plan and the four evidence-backed quality groups.
6. Implement before/during/after scores, mistake taxonomy, custom mistakes, and trend metrics.
7. Build process-first heatmap, day drill-down, latest-ten list, history, and trade detail.
8. Add `/system` philosophy/principles and link the existing playbook library.
9. Extend read-only copilot context with aggregates only; re-run the no-write/no-order allowlist test.

## Todo

- [x] Journal cockpit migration + immutable-fact boundary
- [x] Four DST-aware market clocks
- [x] Five-item readiness + daily analysis + chart attachments
- [x] Position-size calculator reusing phase 2 conversion
- [x] Process-first heatmap + day drill-down + latest ten
- [x] Filterable history + complete trade detail
- [x] Actual vs Plan + four quality groups
- [x] Before/during/after scores
- [x] Mistake taxonomy, custom mistakes, and trend
- [x] Process Consistency metric with low-N state
- [x] Philosophy/core-principles surface
- [x] Read-only copilot aggregate extension

## Success Criteria

- [x] `/journal/today` supports prepare -> trade -> close -> review without leaving the app shell
- [x] London/New York clocks change correctly across DST while Tokyo remains stable
- [x] Position sizing for XAUUSD and USDJPY matches the phase 2 conversion fixtures and broker steps
- [x] Clicking a heatmap day opens its analysis, readiness, score, mistakes, and trades
- [x] History filters combine without returning a trade outside the requested dimensions
- [x] Latest ten trades link to full detail and replay; missing tape degrades to marker-only detail
- [x] A moved-worse SL and an early discretionary close appear in Actual vs Plan and mistake trends
- [x] Unknown plan intent is excluded from the four-group chart rather than guessed
- [x] Before/during/after scores drop unknown inputs instead of treating them as zero
- [x] Process Consistency prints `n` and refuses a confident score below five sessions
- [x] Player text and attachments cannot change fills, execution events, or broker-derived P/L

## Verification Status

Gateway `uv run pytest -q`: **461 passed, 1 skipped** (the skip is phase 2's broker volume test,
still waiting on a real cTrader dump); `uv run ruff check .` clean. Web `npm test`: **163 passed**
(26 new); `npx tsc --noEmit` and `npm run build` clean. The journal is a lazy chunk — 8.4 KB
gzipped, so the HUD's bundle is unchanged.

| Claim | Proof |
|---|---|
| The journal cannot rewrite a broker fact | `test_no_journal_write_can_touch_a_broker_fact` parses every INSERT/UPDATE/DELETE in the service and fails if one names `trade_plan`, `trade_closed`, `position_event`, `trade_tape`, `trade_grade`, `cid_reservation` or `session_equity`; a second test writes a review, a mistake and an analysis, then asserts the execution payload is byte-identical |
| DST is real, not arithmetic | `offsetMinutes` is derived from the zone itself. London 0 → +60, New York −300 → −240 across the two dates; Tokyo is 540 on both, which it must be — Japan has not observed DST since 1951 |
| Sizing agrees with the broker | XAUUSD converts by identity and gives exactly 1 lot for $200 over a $2 stop; USDJPY goes through the graph at 1/150 and gives 0.6 lots. Rounding is asserted to go **down**, and the reported risk is recomputed from the rounded volume |
| A guess is refused, not made | A stop at the entry, a risk below the broker minimum, and an unpriceable quote each return a reason and no size — never a zero or a rate of 1.0 |
| History filters cannot leak | Four filters combined return exactly the matching trade; an unrecognised key cannot reach the SQL (asserted with a DROP TABLE payload); every value goes through a bound parameter |
| No counterfactual | `actual_vs_plan` is asserted against its payload *and* against the module source with comments and docstrings stripped, so no code path can promise what the market would have done |
| Intent is confirmed, never inferred | `test_no_combination_of_evidence_ever_derives_impulsive_or_revenge` sweeps the whole input space; the four-group chart counts the unclassified separately and says so |
| Unknown is not zero | A captured miss scores 50 where an uncaptured input scores 100 over a smaller denominator, and the dropped inputs are named on the panel |
| Mistakes separate proof from judgement | The three intent mistakes are asserted non-derivable; a sync replaces only `auto` rows; a player can withdraw their own judgement but not a derived one |
| Attachments cannot name a path | The bytes decide the type (an SVG and an HTML document are both refused through the real route); the id is a server-generated ULID; a `../../etc/passwd` label round-trips as a label and creates no directory |
| The desk gets counts, not words | `get_journal` is pinned to five keys, and a test writes a private thesis and review note then asserts neither appears in the aggregate |
| Process Consistency | Matches the formula exactly on a worked case (median 100, mean 84, MAD 16 → 84), rewards steadiness over the same average, reads only the last 20, and always prints `n` |

## Deviations

- **Attachments ride a raw request body, not multipart.** `python-multipart` is not installed, and
  the security posture is identical either way: the magic bytes decide the type, the server
  generates the name, and the byte cap is enforced before anything is written. The route is the
  one the plan names (`POST /api/journal/attachments`); the metadata rides query parameters. This
  avoided adding a dependency for a single-file upload.
- **`journal/routes.py` is `journal/query_service.py` plus routes in `main.py`.** The same call
  phase 11 made: every route in this build is registered in `main.py`, and the repository pattern
  is what phases 6, 7, 10 and 11 already use.
- **The web screens are nav entries, not `/journal/*` routes.** The app has no router (phase 3's
  decision). The journal is registered as "Journal (real gateway)" and "System (real gateway)"
  beside the existing prototype screens, which are untouched. The shell's own tabs cover today /
  dashboard / history / trade, and the trade view hands a cid to the replay screen — so the review
  loop the phases were building toward (dashboard → trade → the tape it happened on) is complete.
- **`readiness_check` is one row per item.** The plan describes five named items with a note each;
  a row per item means a sixth is a data change rather than a migration, and it lets `NULL` record
  a *declined* item distinctly from "no".
- **The playbook table's split, again.** Per-playbook process figures were delivered in phase 11
  behind `/api/deck/playbooks`; this phase did not duplicate them into the journal.
- **`mid_prices()` was extracted while wiring the calculator.** The sizing route needed the same
  price map the fill path builds, and the fill path was building it inline. One builder now serves
  both — sizing a trade against one rate and recording it against another would have been a real
  bug rather than a tidy-up.
- **Memos are absent, as everywhere else.** Phase 8 is deferred, so `has_memo` is `None` (not
  captured) rather than `False` (a miss), and the trade detail's `memos` is an empty list. The
  after-stage score drops the item and renormalises, which is the same path the plan specifies for
  a browser with no usable microphone.
- **Phase 9's `key_levels` collision.** Phase 11's guard forbade the token `level` anywhere in the
  schema; phase 12's `daily_analysis.key_levels` holds chart price levels. The guard now matches
  whole snake_case tokens instead of substrings, which is what it always meant.

## Risk Assessment

- **Analytics invent causality** — signal: Actual vs Plan says a target “would have won”. Response:
  compare recorded plan with actual execution only; never assert counterfactual market outcomes.
- **DST clocks drift** — signal: London/New York off by one hour after a clock change. Response: IANA
  zones and date-boundary fixtures; no fixed offsets.
- **Mistake automation mislabels intent** — signal: a clean discretionary trade is called revenge.
  Response: automatic evidence may suggest; impulsive/revenge requires player confirmation.
- **Attachments fill disk** — signal: journal volume exceeds configured threshold. Response: MIME,
  dimension and byte caps; show storage use; include attachments in phase 13 backup.

## Security Considerations

- Attachment names never become paths; server generates ULIDs, validates magic bytes, and stores
  outside the web root. No SVG or HTML upload.
- All player text is escaped and length-capped. No `{@html}`.
- Journal APIs use the existing same-origin bearer and never return cTrader credentials.

## Next Steps

Phase 13 adds reports, settings, backup/restore, export, and deletion around this complete journal.
