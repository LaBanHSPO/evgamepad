---
title: "Phase 6: Performance and psychology deck"
status: todo
phase: 6
priority: P1
effort: 17h
dependencies: [2, 3, 5]
---

# Phase 6: Performance and psychology deck

## Overview

The point of the game is **confidence and enjoyment**, not the money. This phase ships
the surface that proves improvement over time: a **process-first** deck (rule adherence,
trades correctly declined, opportunity quality, self check-in) with an **outcome tab**
behind a deliberate click (month-over-month return, Sharpe, profit factor, average R).

Grounded in Brett Steenbarger's trading-psychology work: trading is a *performance*
activity; anxiety about the result pulls attention off the process; noise in the process
degrades decisions; and **markets do not offer equal opportunity every night** — a flat
evening in a dead tape is a good evening, and the deck must say so.

## Context Links

- [plan.md](./plan.md)
- [Phase 2 — journal, account, fills](./phase-02-ctrader-exec-and-socket-gateway.md)
- [Phase 3 — HUD process cues](./phase-03-web-game-and-8bitdo-client-agent.md)
- [Phase 4 — sentinel supplies opportunity quality](./phase-04-ai-desk-sentinel-news-volman.md)
- Steenbarger: *The Daily Trading Coach*, *Trading Psychology 2.0*, *Enhancing Trader Performance*. **Cite. Do not paste book text.** (same rule as the Volman lens)

## Requirements

### Data (both sources — validated decision)

- Functional: `session_equity` — one row per evening: `session_id`, `opened_at`, `closed_at`, `balance_open`, `equity_open`, `balance_close`, `equity_close`, pulled from the cTrader account, not computed locally
- Functional: `trade_closed` — one row per closed position: `cid`, `position_id`, `symbol`, `side`, `lots`, `entry_price`, `exit_price`, `opened_at`, `closed_at`, `pnl_usd`, `r_multiple`, `setup_tag` (Volman tag at entry, nullable), `adherence` JSON
- Functional: `session_process` — `session_id`, `checkin_pre` (1-5), `checkin_post` (1-5), `note` (one line, typed by the player, never LLM-written), `declined_count`, `adherence_score`
- Functional: session return = `(equity_close - equity_open) / equity_open`; the return **series** is per session, never per trade
- Non-functional: cTrader stays the source of truth for money; the deck never re-derives balance from fills

### Process panel (default view)

- Functional: **adherence score** per session — fraction of fires that satisfied every rule: named setup present, not inside T-15 of a high-impact event, lot at or under cap, inside the evening window, at or under `max_positions`
- Functional: **trades declined** — count of arms cancelled during a stand-down condition. Framed as a positive; Steenbarger's "not trading is a position"
- Functional: **opportunity quality** of the evening from the phase 4 sentinel (spread state, range expansion, event density) so a flat night in a dead tape reads as **discipline, not failure**
- Functional: **this month vs last month** on adherence, declined-rate, and check-in average — the primary "am I improving?" answer
- Functional: **check-in** — 1-5 self rating at session open and close, two pad taps, skippable; plotted against adherence, not against P/L
- Functional: the **Process Score radar** (phase 11) lives on this panel — five process-only axes,
  vacuous axes dropped and renormalised rather than scored zero. The game layer's home is the deck,
  never the HUD; there is deliberately no live score to watch mid-session
- Functional: **per-playbook stats** (phase 7): n, adherence, expectancy in R, average MFE/MAE,
  average efficiency. Process figures here by default; outcome figures stay behind the tab click
- Functional: **tilt retrospective** (phase 9): bands over the session and their top drivers,
  correlated against adherence, never against P/L. Tilt is a retrospective here and is **not** an
  input to the score
- Non-functional: no streaks, no leaderboard, no badge that punishes standing down
<!-- Updated: Validation Session 4 - journal layer surfaces land on the process panel -->

### Outcome panel (second tab, deliberate click)

- Functional: month-over-month **return %**, **profit factor**, **average R**, **win rate**, **max drawdown**, and **Sharpe** from the session return series
- Functional: per-setup breakdown by Volman `setup_tag`, and per-playbook breakdown by `playbook_id` (phase 7)
- Functional: Sharpe shows sample size and renders a **"not enough sessions yet"** state below `deck.min_sessions_for_sharpe` (default 30). ~20 sessions/month means the first two months of Sharpe are noise and the deck must say so rather than print a confident number
- Non-functional: outcome numbers never appear on the process panel, and never in a notification
- Non-functional: every panel carries the demo / entertainment / not-advice line

### Serving and access

- Functional: deck at `/deck` in the same web app, same origin, served by the gateway (phase 5 decision)
- Functional: plain HTTP `GET /api/deck/*` JSON — this is not realtime and does not belong on the game socket
- Functional: copilot gains one read-only tool `get_progress`; it may coach the **process**, and still cannot place, close, or write

## Architecture

```
cTrader account + fills ──► ev-gateway journal
                              session_equity   (open/close equity per evening)
                              trade_closed     (pnl, R, setup tag, adherence)
                              session_process  (check-in, note, declined)
                                    │
                              deck/metrics.ts  (pure functions, unit-tested)
                                    │
                              GET /api/deck/*  ──► /deck  ProcessPanel | OutcomePanel
                                    │
                              copilot get_progress (read-only, process coaching)
```

Metrics are **pure functions over rows**. No LLM computes a number that appears on the
deck; the copilot may only narrate numbers the deck already produced.

## Related Code Files

- Create: `apps/gateway/src/deck/schema.sql` (three tables + indices)
- Create: `apps/gateway/src/deck/metrics.ts` (adherence, R, profit factor, drawdown, Sharpe)
- Create: `apps/gateway/src/deck/metrics.test.ts` (fixture months; Sharpe low-N guard)
- Create: `apps/gateway/src/deck/routes.ts` (`GET /api/deck/summary|process|outcome`)
- Create: `apps/web/src/deck/Deck.svelte` (tabs, process default)
- Create: `apps/web/src/deck/ProcessPanel.svelte`
- Create: `apps/web/src/deck/OutcomePanel.svelte`
- Create: `apps/web/src/deck/CheckIn.svelte` (pad-driven 1-5)
- Modify: `apps/gateway/src/journal.ts` (write the three tables)
- Modify: `apps/gateway/src/copilot/tools.ts` (add `get_progress`, read-only; phase 11 extends it with the score axes)
- Modify: `apps/gateway/src/copilot/prompt.ts` (process-over-outcome coaching stance)
- Modify: `apps/web/src/App.svelte` (route `/deck`)
- Modify: `config/default.yaml` (`deck.min_sessions_for_sharpe`, adherence rule weights)
- Modify: `README.md` (what the deck is for; what it deliberately refuses to show)

## Implementation Steps

1. Schema + journal writes: equity snapshot at session open/close from the cTrader
   account; `trade_closed` row on every close; `session_process` on check-in.
2. `metrics.ts` pure functions with fixture months — including a two-session month that
   must render the low-N Sharpe state rather than a number.
3. Adherence evaluation: reuse the phase 2 risk rules as the rule set so the deck scores
   exactly what the gateway enforced. No second, drifting definition.
4. `GET /api/deck/*` on the gateway, same origin, no auth beyond the existing token.
5. ProcessPanel: adherence trend, declined count, opportunity quality, check-in vs
   adherence, this-month-vs-last-month deltas.
6. OutcomePanel behind a tab click: return %, Sharpe (+ sample size), profit factor,
   average R, drawdown, per-setup table.
7. Check-in overlay driven by the pad; skippable; never blocks the evening starting.
8. Copilot `get_progress` + prompt stance; assert in tests it still has no write or order tool.

## Todo

- [ ] Three tables + journal writes
- [ ] metrics.ts + fixture tests incl. low-N Sharpe
- [ ] Adherence reuses phase 2 risk rules
- [ ] `/api/deck/*` routes
- [ ] ProcessPanel (default) with month-over-month deltas
- [ ] OutcomePanel behind a click
- [ ] Pad check-in + one-line note
- [ ] Copilot `get_progress`, still no order tools
- [ ] Process Score radar on the process panel (phase 11)
- [ ] Per-playbook stats table (phase 7)
- [ ] Tilt retrospective, not a score input (phase 9)
- [ ] README: what the deck refuses to show

## Success Criteria

- [ ] Opening `/deck` lands on the **process** panel; no dollar figure is visible until a tab is clicked
- [ ] A month with fewer than `min_sessions_for_sharpe` sessions renders "not enough sessions yet", not a Sharpe number
- [ ] An evening with zero trades in a dead tape scores **well** on the deck (high declined-rate, low opportunity quality, adherence intact)
- [ ] This-month-vs-last-month deltas render for adherence, declined-rate, check-in average, return %, and average R
- [ ] `session_equity` figures reconcile against the cTrader account, not against summed fills
- [ ] Copilot can narrate the deck and still has no `place`/`close`/write tool
- [ ] Every panel shows the demo / entertainment / not-advice line
- [ ] The radar renders dropped axes as a dashed "n/a — no trades" ring, never a zero spoke
- [ ] Tilt appears as a retrospective and nowhere in the score inputs

## Risk Assessment

- **Gamifying P/L reintroduces the anxiety we are treating** — signal: the player opens the deck to check money mid-session. Response: process panel is the default and the only linked view; outcome is a click; no notification ever carries a dollar figure.
- **Sharpe on ~20 samples is noise** — signal: a confident 2.4 after three weeks. Response: hard low-N state below 30 sessions; always print the sample size next to the number.
- **Adherence definition drifts from what the gateway enforces** — signal: deck says a fire broke a rule the gateway allowed. Response: one rule set, imported from phase 2 risk, not re-implemented.
- **Check-in becomes a chore and gets skipped** — signal: `checkin_pre` null for a fortnight. Response: two pad taps, skippable, and the deck degrades to adherence-only rather than nagging.
- **Judging a flat evening as failure** — signal: the deck shows a blank month as bad. Response: opportunity quality is a first-class axis; declined trades count upward.

## Security Considerations

- Deck routes are same-origin behind the existing token; no new public surface.
- The one-line session note is player text — escape it, never `{@html}`.
- `get_progress` returns aggregates, never account credentials or the raw journal.

## Next Steps

Play the months. The deck is the scoreboard that was actually asked for.
