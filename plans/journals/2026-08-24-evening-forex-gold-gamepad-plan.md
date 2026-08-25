---
title: Evening forex gold gamepad plan
date: 2026-08-24
summary: "Greenfield plan: paper-first VPS socket game with 8BitDo Ultimate 2 and SpaceXAI copilot; red-team applied."
---

# Evening forex gold gamepad plan

## What happened
User asked for a web game to trade forex/gold in the evening with a gamepad, a near-realtime AI copilot, and a client-agent ↔ VPS socket architecture with low-latency VPS→broker. Repo was empty. User locked paper simulator first (broker adapter later), 8BitDo Ultimate 2 Wireless, and an existing VPS.

## Decision
- Paper engine on the existing VPS; exec sidecar protocol is the broker seam (MT5 later).
- Chrome + Svelte HUD; in-tab client agent; tab must stay focused.
- Default clutch/confirm = LT/RT; L4/R4 only after probe.
- SpaceXAI copilot in a child process; research uses replay tape; no order tools.
- Gateway binds 127.0.0.1:8444; Caddy TLS; cid UNIQUE pending; IANA timezone required.

Red-team accepted bind/TLS, cid reservation, clutch-on-intent, durable book, HUD flatten. Rejected mTLS, native daemon, and implementing MT5 in this plan.

## Next steps
User reviews plan at plans/260824-1506-evening-forex-gold-gamepad/plan.md then either `/ak:plan validate` or `/ak:cook`.

> Historical work record — not durable authority. Prefer docs/specs/ADRs for current decisions.
