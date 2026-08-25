---
title: "Research: copilot desk, Volman lens, news, sentinel, signals"
date: 2026-08-24
---

# Research: AI desk for the evening game

The original request was a **near-realtime AI bot** that researches, plans, advises, and monitors the trading journey. Phase 4 as first written only narrated the paper tape. That is not the product.

## What the desk is

Four **player-visible** jobs, plus two **engines** that feed them.

| Surface | Job | LLM? |
|---------|-----|------|
| **Market sentinel** | Always-on strip: spread, session, next event, structure tag, lock | No (deterministic) |
| **Market news** | Headlines for gold/FX this session, cited | Yes, SpaceXAI `web_search` |
| **Trusted signals** | Allowlisted calendar + structure + optional named X accounts | Mixed |
| **Volman lens** | 5-minute price-action checklist on the chart | Detectors local; LLM cites them |
| **Plan** | Once at session start | Yes |
| **Research** | On demand / idle | Yes |
| **Advise** | On ask / after fill | Yes |
| **Monitor** | 30–60s | Cheap model or rules |

AI still **cannot** place, close, or modify. Sentinel and signals can **warn**; they cannot fire.

## Bob Volman — what we may encode

Publicly discussed across *Forex Price Action Scalping* and *Understanding Price Action* (5-minute). **Do not copy book text into the repo.** Encode a **method profile** + detectors, cite the books in the HUD.

**Lens we ship (entertainment, 5-minute — matches Lightweight Charts):**

- Naked chart + **20 EMA** (config `ema_period`, default 20; some UPA summaries use 25 — keep configurable).
- Trade **buildups / ranges** and **breaks** of a clear signal bar, not random EMA crosses.
- **False breaks** are first-class (he spends time on why typical breakouts fail).
- **Volatility contraction** before a break matters more than “more indicators”.
- Setups discussed in public notes/videos (names only, our own detectors):
  - double-doji break
  - first break
  - second break (break + pullback test)
  - block break
  - range break
  - inside-range break
  - advanced range break
- Scalping book also used ~70-tick charts, ~10 pip target / 6–7 pip stop on EURUSD. Gold is not EURUSD: **stops in ticks from ATR/range**, not 10 pips. 70-tick is out of v1 (no tick chart).

**Evening ICT 18:00–23:30** = 11:00–16:30 UTC. That is London continuation into NY open — a real Volman-style 5m window, not a dead Asia scalp.

## News

SpaceXAI built-in tool `web_search` ([docs](https://docs.x.ai/developers/tools/web-search)):

- `allowed_domains` **max 5**. Default: `forexfactory.com`, `reuters.com`, `kitco.com`, `federalreserve.gov`, `fxstreet.com`.
- Citations required on every `ai.advice` / `news.item`.
- Runs only in `ev-copilot` child process.

Do not scrape random blogs. Do not put news on the order path.

## Calendar / trusted signals

Forex Factory publishes a **weekly export** (ICS/CSV/JSON/XML) from the calendar page, hosted at `nfs.faireconomy.media/ff_calendar_thisweek.json`. Not a documented public API. Use:

- cache ≥ 6h (community warning: do not fetch per tick)
- filter currency in `{USD,EUR,GBP,JPY,XAU}` and impact `high` (and `medium` if gold)
- convert to `Asia/Ho_Chi_Minh`
- config flag `signals.calendar.source: ff_weekly | off`

If FF blocks or ToS is a problem: fall back to `config/calendar.yaml` the player edits.

**Trusted** means **allowlist**, not “the internet agrees”:

1. High-impact calendar (above)
2. Local Volman detectors
3. `web_search` only on those 5 domains
4. Optional `x_search` **only** if `signals.x_accounts` is non-empty (default empty)

No paid signal shop, no copy-trading feed.

## Sentinel (not an LLM)

1–5s loop, structured `sentinel.tick`:

- `spread` vs `max_spread` → `wide|ok`
- `session_remain_s`
- `next_event` {title, impact, t_minus_s} from calendar
- `volman` {setup, quality, note} from M5 detectors
- `lock` from session/dead-man
- `news_age_s`

HUD paints this without waiting for Grok. Copilot **reads** the last tick as a tool `get_sentinel`.

## Citations

- https://docs.x.ai/developers/tools/web-search
- https://docs.x.ai/developers/tools/overview
- https://www.forexfactory.com/calendar (weekly JSON export)
- Volman books: *Forex Price Action Scalping*; *Understanding Price Action* (5-minute). Method profile is ours; not a reprint.
