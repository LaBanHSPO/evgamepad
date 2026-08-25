---
title: "Research: client, gamepad, socket"
date: 2026-08-24
---

# Research: client + gamepad + socket

Summary of the client-side researcher. Full argument lived in the session; this file is the durable extract.

## Stack

Vite + TypeScript + Svelte 5 + TradingView Lightweight Charts + raw Gamepad API + native WebSocket JSON. No native helper in v1. No Next.js.

## Gamepad facts

- Events exist only for connect/disconnect. Buttons/axes must be polled on rAF.
- Do not cache the `Gamepad` object. Require `mapping === "standard"` in v1.
- Rumble: Chrome `vibrationActuator`; Firefox/Safari optional.
- Hidden tab pauses rAF. Dead-man must use `visibilitychange`, not rAF timeout.
- Analog sticks must never submit orders. Clutch + arm + confirm FSM.

## 8BitDo Ultimate 2

- Xbox layout. Mac: Bluetooth (2.4G dongle is Windows-oriented).
- Extra L4/R4 bumpers: preferred clutch/confirm if visible; else LT/RT.
- Ultimate Software can remap extras if Chrome hides them.

## Socket

Envelope `{v,t,seq,ts,cid,p}`. Idempotent ULID `cid`. Heartbeat carries `{visible, pad, clutch}`. Quotes conflated 10–20 Hz. AI 1–5s, off fire path.

## Citations

- https://developer.mozilla.org/en-US/docs/Web/API/Gamepad_API
- https://www.8bitdo.com/ultimate-2-wireless-controller/
- https://github.com/tradingview/lightweight-charts
