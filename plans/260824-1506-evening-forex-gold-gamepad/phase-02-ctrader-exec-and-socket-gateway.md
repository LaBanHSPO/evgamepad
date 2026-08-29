---
title: "Phase 2: cTrader broker link and socket gateway"
status: todo
phase: 2
priority: P1
effort: 22h
dependencies: [1]
---

# Phase 2: cTrader broker link and socket gateway

## Overview

Run **cTrader Open API** and the game WebSocket in the **same** `ev-gateway` process, through the
native Python client (`ctrader-open-api` / OpenApiPy). Spots, M5 bars, market orders, positions, and
P/L are **Spotware demo**. No in-process matching. No MT5. No sidecar — the module that checks risk
is the module that calls the broker.

## Prerequisites (blocks implementation)

- [ ] cTrader ID created
- [ ] **IC Markets** cTrader **demo** account opened under it
- [ ] Open API application registered and approved at connect.spotware.com
- [ ] `.env` populated per the phase 1 README flow (manual consent; no helper ships)
- [ ] A real `SymbolsList` + `SymbolById` dump captured to `apps/gateway/broker/fixtures/`

<!-- Updated: Validation Session 2 - broker named, OAuth is manual -->

## Context Links

- [plan.md](./plan.md)
- [research](./research/researcher-05-ctrader-docker.md)
- https://help.ctrader.com/open-api/
- https://help.ctrader.com/open-api/messages/
- https://github.com/spotware/OpenApiPy
- https://github.com/spotware/openapi-proto-messages

## Requirements

- Functional: persistent Protobuf connection over **TCP** to `demo.ctraderapi.com:5035` (OpenApiPy's transport), opened by the gateway itself
- Functional: **OpenApiPy is Twisted-based and the gateway is asyncio.** Install
  `twisted.internet.asyncioreactor` before any module imports `reactor`, so the broker client and the
  web server share one event loop. Boot-fail loudly if a default reactor was already installed —
  a silently mismatched reactor is the failure mode that looks like "the socket is just slow"
- Functional: broker callbacks are **contained** at the module boundary. An exception in a Protobuf
  callback becomes an `order.reject` or a `maint` frame; it may never escape into the reactor and
  take the process down. With the sidecar gone this process is also the HUD and the journal
- Functional: `ProtoHeartbeatEvent` so the proxy stays up
- Functional: app auth + account auth; **refresh** a manually provisioned OAuth token. Boot-fail with a pointer to the phase 1 README when `CT_REFRESH_TOKEN` is absent
- Functional: refuse if account `isLive` or host is live
- Functional: `ProtoOASymbolsListReq` → `ProtoOALightSymbol` → map `XAUUSD|EURUSD|GBPUSD|USDJPY` (IC Markets, unsuffixed) to `symbolId`
- Functional: `ProtoOASymbolByIdReq` → `ProtoOASymbol` → read `minVolume`, `stepVolume`,
  `maxVolume`, `digits`, `pipPosition`, and `lotSize`; resolve the light symbol's `baseAssetId` and
  `quoteAssetId` through the asset list. **`SymbolsList` does not carry the full symbol spec** —
  volume conversion, price scaling, and risk currency conversion depend on these records
<!-- Updated: Validation Session 2 - SymbolsList returns ProtoOALightSymbol, not volume specs -->
- Functional: `ProtoOASubscribeSpotsReq` + live trendbars; gateway conflates quotes to the browser at 10–20 Hz
- Functional: `ProtoOAGetTrendbarsReq` M5 history for chart seed
- Functional: MARKET `ProtoOANewOrderReq` uses `relativeStopLoss` / `relativeTakeProfit` in
  cTrader's 1/100000 distance units; absolute `stopLoss` / `takeProfit` are not supported for this
  order type. `clientMsgId` = ULID `cid`
- Functional: `ProtoOAAmendPositionSLTPReq` changes absolute SL/TP on an existing position after a
  clutch+confirm action. `ProtoOAClosePositionReq` closes the full position; panic flatten closes
  every position then locks. No pending orders and no partial close in this product
- Functional: cid SQLite `UNIQUE` **pending** before send; reboot replays cid + `ProtoOAReconcileReq` for positions (cTrader is source of truth)
- Functional: risk: IANA session, max lots, max positions, max daily loss (from cTrader equity), clutch on intent, dead-man locks **opens** only
- Functional: journal also records what phase 6 measures — an equity snapshot from the cTrader
  account at session open and close, a `trade_plan` snapshot at FIRE, append-only `position_event`
  rows for fill/SL/TP amendments/close, and a `trade_closed` row on every full close. Capture symbol,
  side, timeframe, market session, playbook/setup, planned entry, relative and planned absolute
  SL/TP, planned risk/reward, fill/close facts, lots, P/L, and adherence. cTrader remains the money
  source of truth; never re-derive balance from summed fills
<!-- Updated: Validation Session 3 - phase 6 needs a session equity series and closed-trade rows -->
- Functional: the risk rule set is **exported**, not private — phase 6 scores adherence with the same rules the gateway enforced, never a second definition. Phase 7 moves these rules into `apps/gateway/method/rules.py` and `risk/rules.py` imports them; **that extraction must be behaviour-preserving, and this phase's tests are the regression gate**
- Functional: **R is defined once, here, in the module `risk/rules.py` imports.** Protocol volume is
  cents of units, so `units = protocolVolume / 100`; raw stop risk is
  `units * abs(entry - sl)` in the symbol's quote asset. Convert that value through cTrader's
  quote-to-USD conversion chain at entry before naming it `R_usd` (`XAUUSD` is already USD;
  `USDJPY` requires JPY -> USD). Store rate, chain/source, and timestamp with the plan so the number
  is auditable. When no SL exists at entry only, use `risk.r_unit_usd` (default $20). The HUD,
  `trade_closed.r_multiple`, MFE/MAE, phase 9, phase 11, and the phase 12 calculator all call this
  one function
<!-- Updated: Validation Session 4 - phase 6 required r_multiple but no phase ever defined R -->
- Functional: **tape ring buffer** — 1 Hz bid+ask OHLC per subscribed symbol (`{ts_s, bid_o..bid_c, ask_o..ask_c, n_ticks}`, prices as scaled integers), built from the spot stream **before** the 10-20 Hz browser conflation, held in a `tape.ring_minutes` (90) RAM ring of roughly 1 MB. Always running, so pre-roll exists whether or not a position is open
- Functional: on position close, a job at `closed_at + tape.post_roll_s` freezes `[opened_at - pre_roll_s, closed_at + post_roll_s]` into **one** `trade_tape` row (gzipped columnar bars + denormalised events) and computes MFE/MAE from the same window. Only windows around actual trades are persisted — a zero-trade evening writes zero tape. Flush on shutdown and at session end with whatever post-roll exists
- Functional: MFE/MAE use the correct side — LONG measures excursion on the **bid** (`max(bid_h)`, `min(bid_l)`), SHORT on the **ask** (`min(ask_l)`, `max(ask_h)`). Storing one side only would be a silent asymmetry bug
- Functional: migration `001-core-trading.sql` owns only the phase 2 core: cid reservation,
  sessions/equity, `trade_plan`, `position_event`, `trade_closed`, and `trade_tape`. The phase 1
  runner bootstraps its own `schema_migration` ledger before applying `001`.
  Every later phase owns a versioned additive migration; the runner tracks each applied id, not a
  single maximum version
- Functional: reserve the `intent.open` reject reason `cooldown` for phase 9, and assert now that `close` and `panic` are exempt from every open-only gate
<!-- Updated: Validation Session 4 - journal layer capture must exist from day one -->
- Functional: parameterized SQL; symbol allowlist; 64KiB frames; Origin allowlist
- Functional: `resync` / `snap`; one WS per token
- Non-functional: never 60 Hz quote text to the HUD
- Non-functional: copilot `ai.ask` replies `{disabled:true}` until phase 4
- Non-functional: historical trendbar calls stay under 5 req/s

## Architecture

```
game WSS → ev-gateway (Python, one process, one event loop)
              api/    ws, rest, static HUD
              risk/   risk, cid, seq
              journal/ plan, events, tape
              broker/ ctrader-open-api (OpenApiPy / Twisted on asyncioreactor)
                    ProtoOA* ↔ demo.ctraderapi.com:5035
```

An approved intent reaches the broker by **direct call**, not by a socket. The 9101 TCP JSON hop,
its framing, its reconnect logic, and its two-process failure matrix are all gone.

Official protocol volume is expressed in **0.01 of a unit**. HUD speaks lots. The broker module
converts using `ProtoOASymbol.lotSize` and broker min/step/max from `SymbolByIdReq` — never from
`SymbolsListReq`. Document the mapping in logs at subscribe time.

Spot prices in protocol are 1/100000 of a price unit (`123000` → `1.23`). Scale with `digits` from the symbol.

`label` on orders: `evgp` + short cid (cTrader label length limits).

## Related Code Files

- Create: `apps/gateway/broker/ctrader.py` (connect, heartbeat, auth, spots, trendbars,
  new/close/amend-position-SLTP; owns the callback containment boundary)
- Create: `apps/gateway/broker/reactor_setup.py` (installs `asyncioreactor` before any `reactor`
  import; boot-fails if a different reactor is already installed)
- Create: `apps/gateway/broker/volume.py` (lots ↔ protocol volume)
- Create: `apps/gateway/broker/conversion.py` (asset graph and timestamped quote-to-USD conversion)
- Create: `apps/gateway/broker/test_ctrader.py` (volume + price scaling fixtures)
- Create: `apps/gateway/api/ws.py`
- Create: `apps/gateway/risk/rules.py`
- Create: `apps/gateway/risk/session.py`
- Create: `apps/gateway/journal/writer.py` (cid ledger + phase 2 plan/events/equity/closed-trade/tape writes)
- Create: `apps/gateway/risk/r.py` (**the** R definition; imported by the risk rules, the HUD payloads, and the deck)
- Create: `apps/gateway/db/migrations/001-core-trading.sql`
- Create: `apps/gateway/journal/tape/ring.py` (1 Hz bid+ask ring, pre-conflation tap)
- Create: `apps/gateway/journal/tape/freeze.py` (window extraction, gzip columnar, MFE/MAE)
- Create: `apps/gateway/journal/tape/test_freeze.py` (long vs short excursion sides; short post-roll on shutdown)
- Modify: `apps/gateway/main.py`

## Implementation Steps

1. Reactor first: `asyncioreactor` installed at import time, with a test that proves the gateway
   refuses to start on a mismatched reactor. Everything else in this phase depends on it.
2. Volume/price unit tests from documented examples; gold fixture once a real symbol/asset dump is
   captured (record a demo fixture in `apps/gateway/broker/fixtures/`).
3. Broker: connect, heartbeat, app+account auth, `isLive` guard, symbol map — `SymbolsListReq` for ids,
   then `SymbolByIdReq` for volume/digits/lot size and the asset list for conversion.
4. Spots + M5 subscribe; in-process `snapshot` / quote stream.
5. `place` with relative SL/TP, full `close`, and absolute position-SLTP amendment with
   `clientMsgId`; map execution events to `OrderAck`/position events.
6. Gateway WS: welcome, quote conflation, intents, cid UNIQUE, risk, dead-man, session.unlock.
7. Reconnect: **one** client reconnects to Spotware and then `Reconcile` → `pos.snap`. There is no
   longer an exec↔gateway link that can be up while the broker link is down, so the reconnect state
   machine has one axis instead of two.
8. Callback containment: prove a raised exception inside a Protobuf callback yields `order.reject`
   or `maint` and leaves the WS, the HUD, and the journal running.
9. Tests: duplicate cid; overlapping retry; fire 50ms after clutch-down with last ping clutch=false still sends one order; live host refused.
10. R definition + unit tests: XAUUSD identity conversion, USDJPY JPY->USD conversion, broker step
   rounding, a timestamped conversion audit record, and the no-SL fallback.
11. Tape ring on the pre-conflation spot path; freeze job on close; MFE/MAE with long and short fixtures.
12. Apply `001-core-trading.sql`; prove the phase 1 runner is idempotent and records this migration.

## Todo

- [ ] `asyncioreactor` installed before any `reactor` import; mismatch boot-fails
- [ ] Open API auth + heartbeat
- [ ] Broker callback containment boundary
- [ ] Symbol/asset map + SymbolById lot/volume specs + quote-to-USD conversion
- [ ] Spots + M5
- [ ] MARKET open with relative SL/TP + absolute position amendment + full close/panic + cid
- [ ] Gateway risk + dead-man
- [ ] Session equity snapshot + closed-trade rows
- [ ] Reconcile on reconnect
- [ ] R defined once and imported everywhere
- [ ] 1 Hz tape ring + per-trade freeze + MFE/MAE
- [ ] `001-core-trading.sql` for phase-owned core tables
- [ ] `cooldown` reject reason reserved; close/panic exempt
- [ ] Demo-only guards

## Success Criteria

- [ ] `wscat` to gateway (local compose) sees **cTrader** bid/ask on XAUUSD
- [ ] Clutch-shaped `intent.open` 0.01 XAUUSD produces a **demo** position (`Reconcile` agrees)
- [ ] New MARKET order sends relative SL/TP only; a later SL/TP edit uses
      `ProtoOAAmendPositionSLTPReq`; both require the confirmed action contract
- [ ] Volume conversion asserted against IC Markets' real `minVolume`/`stepVolume` fixture, not a guess
- [ ] Duplicate cid does not double
- [ ] 3s silence → opens reject; close/panic still allowed
- [ ] ICT session window; daily loss close-only
- [ ] Pointing config at live host does not send `NewOrder`
- [ ] A closed long and a closed short both produce correct MFE/MAE from the right side of the book
- [ ] One evening of five trades adds under ~100 KB of tape; a zero-trade evening adds none
- [ ] `r_multiple` is non-null for every closed trade, with and without an SL at entry
- [ ] USDJPY risk converts JPY to USD using the captured entry-time rate; XAUUSD uses identity
      conversion; both retain rate/source/timestamp in the plan
- [ ] Fresh boot applies `001-core-trading.sql` once and contains no tables owned by later phases
- [ ] The gateway serves the HUD, accepts a WS, and streams cTrader quotes **from one process** —
      `docker compose ps` shows a single container
- [ ] A forced exception inside a broker callback produces a reject/maint frame and does **not**
      terminate the process; the socket stays up and the journal keeps writing
- [ ] Importing the app under a non-asyncio reactor exits non-zero with a named error

## Risk Assessment

- **Volume scale wrong on gold** — signal: margin call on 0.01. Response: log protocol volume; cap by `maxVolume`; start 0.01 only after a successful 0.01 round-trip you verify in cTrader web.
- **Demo vs live token mix-up** — signal: `isLive true`. Response: exit.
- **Twisted and asyncio fight over the loop** — signal: quotes arrive in bursts, awaits never resume,
  or the WS heartbeat stalls while the broker socket is healthy. This is the **most likely way this
  phase fails**, and it is new: the sidecar used to keep the two runtimes in separate processes.
  Response: `asyncioreactor` installed before any `reactor` import, verified by a boot check and a
  test; if it cannot be made to hold, the documented fallback is to run the OpenApiPy client in a
  dedicated thread with a `run_coroutine_threadsafe` bridge — still one process, still no sidecar.
- **Twisted + Docker signals** — OpenApiPy is Twisted. Response: `tini` in the gateway image, SIGTERM closes the protobuf socket and drains the WS.
- **One process, one blast radius** — signal: a broker bug takes the HUD and the journal with it.
  Response: the containment boundary above, tested in step 8. This is the cost of removing the
  sidecar and it is paid deliberately, not ignored.
- **5/s history limit** — seed M5 once per symbol per session, then live bars.
- **R silently means two things** — signal: the HUD's R and the deck's R disagree on the same trade.
  Response: one module, one asset-conversion path, timestamped inputs, and no second formula.
- **Tape tapped after conflation** — signal: `n_ticks` is always 1 and the wiggle is gone. Response:
  the ring subscribes to the raw spot stream; conflation is a browser concern only.
- **Freeze job never runs** (shutdown inside the post-roll window) — signal: a trade with no tape.
  Response: flush on shutdown and at session end; `n` is stored so a short window renders correctly.
- If Spotware is down — `maint` + lock opens; do not invent prices.

## Security Considerations

- Access token has `trading` scope — treat like a password. Refresh on volume, not in git.
- Exec unpublished. Gateway loopback.
- Phase 2 remote try = SSH tunnel, not `0.0.0.0`.

## Next Steps

Phase 3 HUD consumes these quotes. Phase 5 is compose on the real Ubuntu box.
