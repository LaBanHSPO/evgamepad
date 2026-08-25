---
title: "Phase 2: cTrader exec and socket gateway"
status: todo
phase: 2
priority: P1
effort: 17h
dependencies: [1]
---

# Phase 2: cTrader exec and socket gateway

## Overview

Run **cTrader Open API** in `ev-exec` and the game WebSocket in `ev-gateway`. Spots, M5 bars, market orders, positions, and P/L are **Spotware demo**. No in-process matching. No MT5.

## Prerequisites (blocks implementation)

- [ ] cTrader ID created
- [ ] **IC Markets** cTrader **demo** account opened under it
- [ ] Open API application registered and approved at connect.spotware.com
- [ ] `.env` populated per the phase 1 README flow (manual consent; no helper ships)
- [ ] A real `SymbolsList` + `SymbolById` dump captured to `apps/exec/fixtures/`

<!-- Updated: Validation Session 2 - broker named, OAuth is manual -->

## Context Links

- [plan.md](./plan.md)
- [research](./research/researcher-05-ctrader-docker.md)
- https://help.ctrader.com/open-api/
- https://help.ctrader.com/open-api/messages/
- https://github.com/spotware/OpenApiPy
- https://github.com/spotware/openapi-proto-messages

## Requirements

- Functional: persistent Protobuf connection over **TCP** to `demo.ctraderapi.com:5035` (OpenApiPy's transport)
- Functional: `ProtoHeartbeatEvent` so the proxy stays up
- Functional: app auth + account auth; **refresh** a manually provisioned OAuth token. Boot-fail with a pointer to the phase 1 README when `CT_REFRESH_TOKEN` is absent
- Functional: refuse if account `isLive` or host is live
- Functional: `ProtoOASymbolsListReq` → `ProtoOALightSymbol` → map `XAUUSD|EURUSD|GBPUSD|USDJPY` (IC Markets, unsuffixed) to `symbolId`
- Functional: `ProtoOASymbolByIdReq` → `ProtoOASymbol` → read `minVolume`, `stepVolume`, `maxVolume`, `digits`, `pipPosition`. **`SymbolsList` does not carry these** — it returns light symbols only. Volume conversion and price scaling both depend on this second call
<!-- Updated: Validation Session 2 - SymbolsList returns ProtoOALightSymbol, not volume specs -->
- Functional: `ProtoOASubscribeSpotsReq` + live trendbars; gateway conflates quotes to the browser at 10–20 Hz
- Functional: `ProtoOAGetTrendbarsReq` M5 history for chart seed
- Functional: market `ProtoOANewOrderReq`; `clientMsgId` = ULID `cid`
- Functional: close `ProtoOAClosePositionReq`; panic flatten = close all then lock
- Functional: cid SQLite `UNIQUE` **pending** before send; reboot replays cid + `ProtoOAReconcileReq` for positions (cTrader is source of truth)
- Functional: risk: IANA session, max lots, max positions, max daily loss (from cTrader equity), clutch on intent, dead-man locks **opens** only
- Functional: journal also records what phase 6 measures — an equity snapshot from the cTrader account at session open and close, and a `trade_closed` row (pnl, entry/exit, lots, setup tag, adherence flags) on every close. cTrader stays the money source of truth; never re-derive balance from summed fills
<!-- Updated: Validation Session 3 - phase 6 needs a session equity series and closed-trade rows -->
- Functional: the risk rule set is **exported**, not private — phase 6 scores adherence with the same rules the gateway enforced, never a second definition. Phase 7 moves these rules into `packages/method/src/rules.ts` and `risk.ts` imports them; **that extraction must be behaviour-preserving, and this phase's tests are the regression gate**
- Functional: **R is defined once, here, in the module `risk.ts` imports.** `R_usd = lots x contract_size x |entry - sl|` when an SL exists at entry, otherwise `risk.r_unit_usd` (config, default $20). The HUD's "P/L in R", `trade_closed.r_multiple`, MFE/MAE in R, phase 9's per-trade risk check and phase 11's Risk Discipline axis all read that one function. Without a single definition they drift
<!-- Updated: Validation Session 4 - phase 6 required r_multiple but no phase ever defined R -->
- Functional: **tape ring buffer** — 1 Hz bid+ask OHLC per subscribed symbol (`{ts_s, bid_o..bid_c, ask_o..ask_c, n_ticks}`, prices as scaled integers), built from the spot stream **before** the 10-20 Hz browser conflation, held in a `tape.ring_minutes` (90) RAM ring of roughly 1 MB. Always running, so pre-roll exists whether or not a position is open
- Functional: on position close, a job at `closed_at + tape.post_roll_s` freezes `[opened_at - pre_roll_s, closed_at + post_roll_s]` into **one** `trade_tape` row (gzipped columnar bars + denormalised events) and computes MFE/MAE from the same window. Only windows around actual trades are persisted — a zero-trade evening writes zero tape. Flush on shutdown and at session end with whatever post-roll exists
- Functional: MFE/MAE use the correct side — LONG measures excursion on the **bid** (`max(bid_h)`, `min(bid_l)`), SHORT on the **ask** (`min(ask_l)`, `max(ask_h)`). Storing one side only would be a silent asymmetry bug
- Functional: journal schema lands on day one, so phases 7-11 need no migration: `voice_memo`, `trade_tape`, `pad_event`, `tilt_sample`, `playbook`, `playbook_rule`, `trade_grade`, `session_score`; `trade_closed` gains `mfe_r`, `mae_r`, `efficiency`, `playbook_id`, `tilt_at_entry`, `tape_id`
- Functional: reserve the `intent.open` reject reason `cooldown` for phase 9, and assert now that `close` and `panic` are exempt from every open-only gate
<!-- Updated: Validation Session 4 - journal layer capture must exist from day one -->
- Functional: parameterized SQL; symbol allowlist; 64KiB frames; Origin allowlist
- Functional: `resync` / `snap`; one WS per token
- Non-functional: never 60 Hz quote text to the HUD
- Non-functional: copilot `ai.ask` replies `{disabled:true}` until phase 4
- Non-functional: historical trendbar calls stay under 5 req/s

## Architecture

```
game WSS → ev-gateway (Node)
              risk, cid, seq, journal
              → TCP JSON ev-exec:9101
                    OpenApiPy / protobuf
                    ProtoOA* ↔ demo.ctraderapi.com:5035
```

Official volume: **0.01 of a unit**. HUD speaks lots. Exec converts using `ProtoOASymbol` from `SymbolByIdReq` — never from `SymbolsListReq`. Document the mapping in logs at subscribe time.

Spot prices in protocol are 1/100000 of a price unit (`123000` → `1.23`). Scale with `digits` from the symbol.

`label` on orders: `evgp` + short cid (cTrader label length limits).

## Related Code Files

- Create: `apps/exec/src/ctrader.py` (connect, heartbeat, auth, spots, trendbars, new/close)
- Create: `apps/exec/src/volume.py` (lots ↔ protocol volume)
- Create: `apps/exec/src/ctrader.test.py` (volume + price scaling fixtures)
- Create: `apps/gateway/src/ws.ts`
- Create: `apps/gateway/src/risk.ts`
- Create: `apps/gateway/src/session.ts`
- Create: `apps/gateway/src/journal.ts` (cid ledger + `session_equity` / `trade_closed` rows for phase 6 + the phase 7-11 tables)
- Create: `apps/gateway/src/r.ts` (**the** R definition; imported by `risk.ts`, the HUD payloads, and the deck)
- Create: `apps/gateway/src/tape/ring.ts` (1 Hz bid+ask ring, pre-conflation tap)
- Create: `apps/gateway/src/tape/freeze.ts` (window extraction, gzip columnar, MFE/MAE)
- Create: `apps/gateway/src/tape/freeze.test.ts` (long vs short excursion sides; short post-roll on shutdown)
- Modify: `apps/gateway/src/main.ts`
- Modify: `compose.yaml` (exec depends_on nothing public)

## Implementation Steps

1. Volume/price unit tests from documented examples; gold fixture once a real `SymbolsList` dump is captured (record a demo fixture in `apps/exec/fixtures/`).
2. Exec: connect, heartbeat, app+account auth, `isLive` guard, symbol map — `SymbolsListReq` for ids, then `SymbolByIdReq` for volume/digits.
3. Spots + M5 subscribe; sidecar `snapshot` / quote stream.
4. `place`/`close` with `clientMsgId`; map execution events to `OrderAck`.
5. Gateway WS: welcome, quote conflation, intents, cid UNIQUE, risk, dead-man, session.unlock.
6. Reconnect: exec reconnects Spotware independently; gateway `Reconcile` → `pos.snap`.
7. Tests: duplicate cid; overlapping retry; fire 50ms after clutch-down with last ping clutch=false still sends one order; live host refused.
8. R definition + unit tests (with and without an SL at entry).
9. Tape ring on the pre-conflation spot path; freeze job on close; MFE/MAE with long and short fixtures.
10. Full journal schema created up front; assert every phase 7-11 table exists after first boot.

## Todo

- [ ] Open API auth + heartbeat
- [ ] Symbol map (SymbolsList) + volume spec (SymbolById) + convert
- [ ] Spots + M5
- [ ] Market open/close + cid
- [ ] Gateway risk + dead-man
- [ ] Session equity snapshot + closed-trade rows
- [ ] Reconcile on reconnect
- [ ] R defined once and imported everywhere
- [ ] 1 Hz tape ring + per-trade freeze + MFE/MAE
- [ ] Full journal schema on day one (no later migration)
- [ ] `cooldown` reject reason reserved; close/panic exempt
- [ ] Demo-only guards

## Success Criteria

- [ ] `wscat` to gateway (local compose) sees **cTrader** bid/ask on XAUUSD
- [ ] Clutch-shaped `intent.open` 0.01 XAUUSD produces a **demo** position (`Reconcile` agrees)
- [ ] Volume conversion asserted against IC Markets' real `minVolume`/`stepVolume` fixture, not a guess
- [ ] Duplicate cid does not double
- [ ] 3s silence → opens reject; close/panic still allowed
- [ ] ICT session window; daily loss close-only
- [ ] Pointing config at live host does not send `NewOrder`
- [ ] A closed long and a closed short both produce correct MFE/MAE from the right side of the book
- [ ] One evening of five trades adds under ~100 KB of tape; a zero-trade evening adds none
- [ ] `r_multiple` is non-null for every closed trade, with and without an SL at entry
- [ ] Every phase 7-11 table exists after a fresh boot

## Risk Assessment

- **Volume scale wrong on gold** — signal: margin call on 0.01. Response: log protocol volume; cap by `maxVolume`; start 0.01 only after a successful 0.01 round-trip you verify in cTrader web.
- **Demo vs live token mix-up** — signal: `isLive true`. Response: exit.
- **Twisted + Docker signals** — OpenApiPy is Twisted. Response: one process, `tini`, SIGTERM closes the protobuf socket.
- **5/s history limit** — seed M5 once per symbol per session, then live bars.
- **R silently means two things** — signal: the HUD's R and the deck's R disagree on the same trade.
  Response: one module, imported; no second formula anywhere.
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
