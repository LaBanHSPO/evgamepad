---
title: "Research: cTrader Open API on Ubuntu Docker"
date: 2026-08-24
---

# cTrader Open API — Ubuntu + Docker

Replaces paper engine and MT5. Linux-native. No Windows terminal.

## Official path

- Docs: https://help.ctrader.com/open-api/
- Endpoints: https://help.ctrader.com/open-api/proxies-endpoints/
- Auth: https://help.ctrader.com/open-api/account-authentication/
- Protos: https://github.com/spotware/openapi-proto-messages
- Python SDK: https://github.com/spotware/OpenApiPy

| | Demo | Live |
|--|------|------|
| Protobuf TCP/WS | `demo.ctraderapi.com:5035` | `live.ctraderapi.com:5035` |
| JSON | `:5036` | `:5036` |

v1: **Protobuf on 5035**, demo host only. Boot-fail if host is live or trader `isLive`.

Auth: OAuth2 (`trading` scope) → `ProtoOAApplicationAuthReq` (clientId/secret) → `ProtoOAAccountAuthReq` (ctidTraderAccountId + accessToken). Refresh token persisted on a Docker volume.

Heartbeat: `ProtoHeartbeatEvent` so the proxy does not drop the socket.

Spots: `ProtoOASubscribeSpotsReq` → `ProtoOASpotEvent` (bid/ask in 1/100000 of a price unit). Trendbars: `ProtoOAGetTrendbarsReq` + live trendbar subscribe (needs spots first).

Orders: `ProtoOANewOrderReq` MARKET. Volume is **0.01 of a unit** (not “lots”). Convert from HUD lots using **symbol spec at connect** (`minVolume`, step). `clientMsgId` = our `cid`. Close: `ProtoOAClosePositionReq`. Positions: `ProtoOAReconcileReq` on boot/reconnect.

Limits: 50 req/s non-historical, 5 req/s historical per connection.

## Docker (Ubuntu VPS)

No official “trading sidecar” image we must use. We compose our own:

```
ev-exec     Python OpenApiPy (Twisted) — only process that talks to Spotware
ev-gateway  Node — risk, cid, WSS to the game
ev-copilot  Node child or third service
```

Host `:443` (existing TLS) → `127.0.0.1:8444`. Compose publishes gateway on loopback only. Exec has **no published ports**.

Spotware also has `ctrader-console-docker` (Windows console in a container) — **not** the Open API path. Skip.

## Not in this plan

Paper matcher. MT5. Wine. Windows VPS. Scraping TradingView for quotes.
