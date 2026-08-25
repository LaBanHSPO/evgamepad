---
title: "Research: VPS, broker, AI"
date: 2026-08-24
---

# Research: VPS + broker + AI

Summary of the VPS/broker/copilot researcher. User locked **paper first, adapter later**.

## Execution ranking (for later demo)

1. MT5 Python IPC on a Windows VPS in the same Equinix as the demo shard (LD4 or NY4 after ping).
2. cTrader Open API (Linux OK; talks to Spotware cloud, colocation weaker).
3. OANDA v20 REST (best DX, extra HTTP latency).

v1 is **PaperAdapter** on the existing VPS. Same `ExecutionAdapter` interface.

## What actually cuts latency

Same building as the broker shard, logged-in terminal, native persistent socket, no CDN on the order port. Home WS (15–80 ms) still dominates a gamepad toy. Colocation is for always-on fills later, not nanoseconds.

Gold: 1.00 lot often 100 oz; read `trade_contract_size`; filling mode is the #1 MT5 fail (`10030`).

## AI

Never on the hot path. SpaceXAI (`XAI_API_KEY`, `https://api.x.ai/v1`). Tools: snapshot/journal only. No place/close.

## Citations

- https://www.mql5.com/en/docs/python_metatrader5/mt5ordersend_py
- https://help.ctrader.com/open-api/connection/
- https://docs.x.ai/developers/quickstart
