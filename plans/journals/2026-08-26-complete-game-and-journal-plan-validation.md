---
title: Complete game and journal plan validation
date: 2026-08-26
summary: Validated and expanded the plan into a complete single-account game and daily journal journey.
---

# Complete game and journal plan validation

## What happened

Audited the 11-phase plan against a complete end-to-end game journey and the supplied Vietnamese research on a trading journal web app. The audit found 13 contract or coverage failures: stale controller architecture, conflicting Menu mappings and desk-tab counts, phase-local acceptance depending on later phases, incomplete dependencies, duplicate schema ownership, invalid cTrader MARKET SL/TP assumptions, a dimensionally wrong USDJPY R formula, missing daily-journal surfaces, and no whole-product release gate.

## Decisions

The user selected 1A, 2A, 3A, 4A, 5A, 6B, and 7A:

- One focused IC Markets cTrader demo account.
- Full daily journal cockpit.
- MARKET orders with relative SL/TP, absolute position protection amendments, full close, and panic; no pending orders or partial closes.
- Menu opens one safe GameOverlay; navigation/apply cannot open or modify a position, while dedicated close/panic exits remain available.
- CSV/JSON, browser PDF, manifested backup/restore, and explicit delete-all; no history import.
- Desktop Chrome, dark-only.
- Preserve and correct phases 1-11; add phases 12-14.

## Changes to the plan

- Corrected cTrader symbol/asset, relative protection, amendment, volume, and quote-to-USD risk contracts.
- Added auditable trade plans and append-only position events.
- Introduced phase-owned migrations 001-010 with a separate migration-ledger bootstrap.
- Replaced competing Menu shortcuts with GameOverlay and made phases 3, 5, and 6 independently closable.
- Corrected phase 7, 8, and 11 dependencies.
- Added phase 12 for preparation, heatmap/history, Actual vs Plan, execution scores, mistakes, and system principles.
- Added phase 13 for safe settings, reports, exports, backup/restore, and deletion.
- Added phase 14 for the real first-run-to-recovery target-hardware release gate.
- Updated README and plan index to 14 phases, 284 tasks, and 203 hours (about 26 working days).

## Validation

- AgentKit plan validation: valid.
- AgentKit index: 14 phases.
- Dependency check: no missing, forward, or cyclic dependency.
- Relative-link check across README, plan, and 14 phase files: zero broken links.
- Canonical stale-contract scan: zero matches.
- git diff check: clean at validation time.
- Ten empirical claims remain intentionally unverified until their phase 2/5/8/14 hardware, broker, VPS, and release gates.

## Next step

Execute the accepted plan from phase 1 with `/ak:cook /Users/bwork/Documents/dev/gh_evgamepad/plans/260824-1506-evening-forex-gold-gamepad/plan.md`. Implementation has not started.

> Historical work record — not durable authority. Prefer docs/specs/ADRs for current decisions.
