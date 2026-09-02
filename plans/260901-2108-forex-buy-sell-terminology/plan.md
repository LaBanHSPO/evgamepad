---
title: "Use buy and sell terminology"
description: "Replace semantic long/short direction wording with forex buy/sell terminology across the product surfaces."
status: completed
priority: P2
effort: 1h
tags: [frontend, docs, terminology]
blockedBy: []
blocks: []
created: 2026-09-01
---

# Use buy and sell terminology

## Brainstorm contract

- **Outcome:** Every trading-direction label, sample, type, and style token uses `buy` or `sell`
  instead of `long` or `short`.
- **Constraints:** Preserve the existing protocol values (`buy | sell`) and all trading behavior.
  Keep established forex terms such as order, position, trade, entry, exit, lots, bid, ask, SL, and
  TP.
- **Non-goals:** Do not replace ordinary English uses of “long” or “short,” such as duration,
  length, concise copy, or “PLAY THE LONG GAME.” Do not rename unrelated navigation properties.
- **Acceptance:** No semantic trading-direction `long` or `short` remains in maintained app code,
  tests, README, or product documentation; typecheck, tests, and build pass.

## Phases

| # | Phase | Status | Dependencies |
|---|---|---|---|
| 1 | [Rename direction terminology](./phase-01-rename-direction-terminology.md) | Complete | None |

