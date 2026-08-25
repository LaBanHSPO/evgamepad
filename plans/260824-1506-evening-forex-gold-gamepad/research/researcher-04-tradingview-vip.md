---
title: "Research: TradingView VIP vs the game"
date: 2026-08-24
---

# TradingView VIP — what it can and cannot feed the game

## Facts

- A retail VIP/Premium/Ultimate plan does **not** include a quotes API. There is no key that dumps Supercharts ticks into `ev-gateway`.
- Extra exchange realtime data is **only on tradingview.com**, not widgets, not a custom game ([pricing FAQ](https://www.tradingview.com/pricing/)).
- Charting Library / Advanced Charts is a **separate** license. You plug **your** data into TV charts — not the reverse.
- Lightweight Charts (already in the game) is Apache-2 and also needs **our** feed (paper / later MT5).
- Official automation for paid plans: **Pine alerts → HTTPS webhook POST** ([help](https://www.tradingview.com/support/solutions/43000529348-how-to-configure-webhook-alerts/)). Needs 2FA. JSON body if the message is valid JSON.
- Scraping TV websockets/DOM, bots, extensions, “unofficial APIs” violate ToS §3 and get the account banned ([support](https://www.tradingview.com/support/solutions/43000674726-why-is-my-account-banned-due-to-suspicious-activity/)). Do not do this.

## Max-value layout (locked)

```
Monitor 1: TradingView Supercharts (VIP)     Monitor 2 / same Mac: game HUD + 8BitDo
  M5 XAUUSD + EMA20 + drawings                 clutch-confirm execution
  calendar, news, screeners                    sentinel + copilot desk
  Pine Volman-style alerts ──webhook──► VPS    signal.item kind=tv
                                               NEVER auto place()
```

VIP is the **analysis cockpit**. The game is the **execution toy**. Webhooks are the only official pipe.

## What webhooks carry (signals, not fills)

Typed JSON from Pine `alert()` / `alertcondition`, e.g. range-break, EMA pullback, session open. Gateway verifies `TV_WEBHOOK_SECRET`, maps to `signal.item`, copilot/sentinel display it. Player still clutch+confirms. `auto_trade: true` boot-fails.

Manual CSV export from TV (human click) may seed the paper replay tape. That is manual use, not scraping.

## Citations

- https://www.tradingview.com/support/solutions/43000529348-how-to-configure-webhook-alerts/
- https://www.tradingview.com/support/solutions/43000674726-why-is-my-account-banned-due-to-suspicious-activity/
- https://www.tradingview.com/pricing/
- https://www.tradingview.com/free-charting-libraries/
