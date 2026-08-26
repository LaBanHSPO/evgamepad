---
title: "Phase 12: Daily Journal Cockpit and Preparation"
status: todo
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
               journal/query-service.ts
                         |
          /api/journal/* + attachment storage
                         |
 /journal/today | /journal/history | /journal/trade/:cid | /system
```

The journal reads immutable broker facts and appends player review. A review can annotate a trade;
it cannot rewrite fills, prices, R conversion inputs, or execution events.

## Related Code Files

- Create: `apps/gateway/src/db/migrations/009-journal-cockpit.sql`
- Create: `apps/gateway/src/journal/query-service.ts`
- Create: `apps/gateway/src/journal/metrics.ts`
- Create: `apps/gateway/src/journal/metrics.test.ts`
- Create: `apps/gateway/src/journal/routes.ts`
- Create: `apps/gateway/src/journal/attachments.ts`
- Create: `apps/web/src/journal/Today.svelte`
- Create: `apps/web/src/journal/WorldSessions.svelte`
- Create: `apps/web/src/journal/ReadinessChecklist.svelte`
- Create: `apps/web/src/journal/PositionSizeCalculator.svelte`
- Create: `apps/web/src/journal/Heatmap.svelte`
- Create: `apps/web/src/journal/History.svelte`
- Create: `apps/web/src/journal/TradeDetail.svelte`
- Create: `apps/web/src/journal/TradeQuality.svelte`
- Create: `apps/web/src/journal/MistakeTrends.svelte`
- Create: `apps/web/src/journal/SystemPrinciples.svelte`
- Modify: `apps/web/src/App.svelte` (journal routes)
- Modify: `apps/web/src/game-overlay/GameOverlay.svelte` (Journal and System destinations)
- Modify: `apps/gateway/src/copilot/tools.ts` (read-only journal aggregates; no write tool)
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

- [ ] Journal cockpit migration + immutable-fact boundary
- [ ] Four DST-aware market clocks
- [ ] Five-item readiness + daily analysis + chart attachments
- [ ] Position-size calculator reusing phase 2 conversion
- [ ] Process-first heatmap + day drill-down + latest ten
- [ ] Filterable history + complete trade detail
- [ ] Actual vs Plan + four quality groups
- [ ] Before/during/after scores
- [ ] Mistake taxonomy, custom mistakes, and trend
- [ ] Process Consistency metric with low-N state
- [ ] Philosophy/core-principles surface
- [ ] Read-only copilot aggregate extension

## Success Criteria

- [ ] `/journal/today` supports prepare -> trade -> close -> review without leaving the app shell
- [ ] London/New York clocks change correctly across DST while Tokyo remains stable
- [ ] Position sizing for XAUUSD and USDJPY matches the phase 2 conversion fixtures and broker steps
- [ ] Clicking a heatmap day opens its analysis, readiness, score, mistakes, and trades
- [ ] History filters combine without returning a trade outside the requested dimensions
- [ ] Latest ten trades link to full detail and replay; missing tape degrades to marker-only detail
- [ ] A moved-worse SL and an early discretionary close appear in Actual vs Plan and mistake trends
- [ ] Unknown plan intent is excluded from the four-group chart rather than guessed
- [ ] Before/during/after scores drop unknown inputs instead of treating them as zero
- [ ] Process Consistency prints `n` and refuses a confident score below five sessions
- [ ] Player text and attachments cannot change fills, execution events, or broker-derived P/L

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
