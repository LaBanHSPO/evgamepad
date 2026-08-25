---
title: Replan cTrader Ubuntu Docker
date: 2026-08-24
summary: Replaced paper+MT5 with cTrader Open API on Ubuntu Docker; gamepad and AI desk kept.
---

# Replan cTrader Ubuntu Docker

## What happened
User: replan, do not use MT5 or paper trading, use cTrader on Ubuntu VPS (Docker).

## Decision
- ev-exec talks Protobuf to demo.ctraderapi.com:5035
- compose on Ubuntu; exec unpublished; existing TLS :443 → 127.0.0.1:8444
- Boot-fail on live host/account
- Volume converted from HUD lots via symbol spec
- Gamepad, protocol, AI desk, TradingView VIP webhooks unchanged

## Next steps
User reviews plan.md then cook when ready.

> Historical work record — not durable authority. Prefer docs/specs/ADRs for current decisions.
