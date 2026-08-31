---
title: "Phase 6: Performance and psychology deck"
status: in-progress
phase: 6
priority: P1
effort: 14h
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
- Functional: reserve extension slots on the ProcessPanel for the phase 11 radar/per-playbook table
  and tilt retrospective, but render them only after those phases exist. This phase closes with its
  own process trends and outcome metrics; no future-phase surface is an acceptance dependency
- Non-functional: no streaks, no leaderboard, no badge that punishes standing down
<!-- Updated: Validation Session 4 - journal layer surfaces land on the process panel -->

### Outcome panel (second tab, deliberate click)

- Functional: month-over-month **return %**, **profit factor**, **average R**, **win rate**, **max drawdown**, and **Sharpe** from the session return series
- Functional: per-setup breakdown by the available Volman `setup_tag`. Per-playbook breakdown is an
  explicit phase 11 extension after phase 7 supplies graded playbook evidence
- Functional: Sharpe shows sample size and renders a **"not enough sessions yet"** state below `deck.min_sessions_for_sharpe` (default 30). ~20 sessions/month means the first two months of Sharpe are noise and the deck must say so rather than print a confident number
- Non-functional: outcome numbers never appear on the process panel, and never in a notification
- Non-functional: every panel carries the demo / entertainment / not-advice line

### Serving and access

- Functional: deck at `/deck` in the same web app, same origin, served by the gateway (phase 5 decision)
- Functional: plain HTTP `GET /api/deck/*` JSON — this is not realtime and does not belong on the game socket
- Functional: copilot gains one read-only tool `get_progress`; it may coach the **process**, and still cannot place, close, or write
- Functional: migration `004-deck.sql` owns only deck-specific indices/views or cached aggregates.
  Core trade/equity tables come from phase 2 and `session_process` comes from phase 3; they are not
  recreated here

## Architecture

```
cTrader account + fills ──► ev-gateway journal
                              session_equity   (open/close equity per evening)
                              trade_closed     (pnl, R, setup tag, adherence)
                              session_process  (check-in, note, declined)
                                    │
                              deck/metrics.py  (pure functions, unit-tested)
                                    │
                              GET /api/deck/*  ──► /deck  ProcessPanel | OutcomePanel
                                    │
                              copilot get_progress (read-only, process coaching)
```

Metrics are **pure functions over rows**. No LLM computes a number that appears on the
deck; the copilot may only narrate numbers the deck already produced.

## Related Code Files

- Create: `apps/gateway/db/migrations/004-deck.sql` (deck-specific indices/views only)
- Create: `apps/gateway/deck/metrics.py` (adherence, R, profit factor, drawdown, Sharpe)
- Create: `apps/gateway/deck/test_metrics.py` (fixture months; Sharpe low-N guard)
- Create: `apps/gateway/deck/routes.py` (`GET /api/deck/summary|process|outcome`)
- Create: `apps/web/src/deck/Deck.tsx` (tabs, process default)
- Create: `apps/web/src/deck/ProcessPanel.tsx`
- Create: `apps/web/src/deck/OutcomePanel.tsx`
- Modify: `apps/gateway/copilot/tools.py` (add `get_progress`, read-only; phase 11 extends it with the score axes)
- Modify: `apps/gateway/copilot/prompt.py` (process-over-outcome coaching stance)
- Modify: `apps/web/src/App.tsx` (route `/deck`)
- Modify: `config/default.yaml` (`deck.min_sessions_for_sharpe`, adherence rule weights)
- Modify: `README.md` (what the deck is for; what it deliberately refuses to show)

## Implementation Steps

1. Apply `004-deck.sql`, then consume phase 2 equity/trade rows and phase 3 process/check-in rows.
   Do not recreate or take ownership of those tables.
2. `metrics.py` pure functions with fixture months — including a two-session month that
   must render the low-N Sharpe state rather than a number.
3. Adherence evaluation: reuse the phase 2 risk rules as the rule set so the deck scores
   exactly what the gateway enforced. No second, drifting definition.
4. `GET /api/deck/*` on the gateway, same origin, no auth beyond the existing token.
5. ProcessPanel: adherence trend, declined count, opportunity quality, check-in vs
   adherence, this-month-vs-last-month deltas.
6. OutcomePanel behind a tab click: return %, Sharpe (+ sample size), profit factor,
   average R, drawdown, per-setup table.
7. Render the phase 3 check-in rows in the trends; do not create a second capture flow.
8. Copilot `get_progress` + prompt stance; assert in tests it still has no write or order tool.

## Todo

- [x] `004-deck.sql` indices/views over phase 2/3-owned rows
- [x] metrics.py + fixture tests incl. low-N Sharpe
- [x] Adherence reuses phase 2 risk rules
- [x] `/api/deck/*` routes
- [x] ProcessPanel (default) with month-over-month deltas
- [x] OutcomePanel behind a click
- [x] Phase 3 check-in + one-line note rendered without duplicate capture
- [x] Copilot `get_progress`, still no order tools
- [x] README: what the deck refuses to show

## Success Criteria

- [x] Opening `/deck` lands on the **process** panel; no dollar figure is visible until a tab is clicked
- [x] A month with fewer than `min_sessions_for_sharpe` sessions renders "not enough sessions yet", not a Sharpe number
- [x] An evening with zero trades in a dead tape is framed as disciplined, not missing data
- [x] This-month-vs-last-month deltas render for adherence, declined-rate, check-in average, return %, and average R
- [ ] `session_equity` figures reconcile against the cTrader account, not against summed fills
- [x] Copilot can narrate the deck and still has no `place`/`close`/write tool
- [x] Every panel shows the demo / entertainment / not-advice line

## Verification Status

Gateway: **232 passed, 1 skipped**. Web: **81 passed**. `ruff check` and `tsc --noEmit` clean;
`npm run build` passes. The gateway boots and applies `004-deck.sql`.

### Verified

**The money is not on the process panel.** A test serialises the whole `/api/deck/process`
response and asserts that none of `pnl`, `equity`, `balance`, `usd`, `return`, `profit`,
`drawdown`, or `sharpe` appears anywhere in it. A source test asserts the Deck opens on the
process tab and does not fetch `/api/deck/outcome` until the tab is clicked — a glance cannot
show you the money, it takes a decision.

**Adherence cannot drift from the gate.** `GATEWAY_ADHERENCE_RULES` is derived from phase 2's
`OPEN_RULES` by id, and a test fails if any of them is not a real gateway rule. The two process
expectations the gateway never enforced (`named_setup`, `event_guard`) are labelled `process`
rather than `gateway`, so the deck can never claim a fire broke a rule the gate allowed.

**A quiet evening is a result.** An evening with no fires has adherence `None`, not `0.0`; a
dead-tape evening returns "standing down was the read". Declined trades count upward and are
reported per session so a busy month and a quiet one compare.

**The Sharpe guard.** Below `deck.min_sessions_for_sharpe` (30) the deck returns
`not enough sessions yet` plus how many sessions it has of how many it needs. A flat return
series is refused rather than dividing by zero. The sample size travels with every number.

**`get_progress` is money-free.** The desk's one journal tool returns process aggregates, and a
test serialises its output to assert no money field can leak through it.

### Deviations from this phase as written

- **The adherence inputs are captured at fire time**, in six new `trade_plan` columns added by
  `004-deck.sql`. Reconstructing `inside_window`, `positions_at_fire`, or the caps from config at
  read time would score a trade against *tonight's* rules rather than the ones it was taken under.
  A plan row predating the migration falls back to today's caps and is visibly untagged.
- **`session_process` gained `note`, `adherence_score`, and `opportunity_quality`** by additive
  ALTER rather than being recreated. Phase 3 still owns the table.
- **The deck lives in the existing `app/`** as a screen in the shell, not at a router path — this
  app has no router, consistent with phases 1 and 3.
- **`session_process.adherence_score` is not yet written.** The deck computes adherence live from
  the fires; the column exists for the cached-aggregate path but nothing populates it, because
  live computation over a few hundred rows is not yet slow enough to justify a cache that could
  disagree with the rules.

### Not verified

Nothing here needs the broker, the pad, or the desk provider — the deck reads the journal. But it
has never been run against a **real** evening's rows, because no real evening has been traded.
Every fixture above is synthetic. The first live session is what will show whether
`session_equity` reconciles against the cTrader account, which is that criterion's real test.

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

Phase 7 adds playbook evidence; phases 9 and 11 later extend this surface with tilt retrospective,
per-playbook statistics, and the Process Score radar without reopening phase 6 acceptance.
