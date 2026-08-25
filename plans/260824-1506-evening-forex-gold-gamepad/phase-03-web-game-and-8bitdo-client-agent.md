---
title: "Phase 3: Web game and 8BitDo client agent"
status: todo
phase: 3
priority: P1
effort: 16h
dependencies: [2]
---

# Phase 3: Web game and 8BitDo client agent

## Overview

Ship the evening game: Chrome HUD + **client agent** that turns 8BitDo Ultimate 2 input into protocol intents. Look like a game, not a terminal. Tab must stay focused.

## Context Links

- [plan.md](./plan.md)
- [cTrader exec and socket gateway](./phase-02-ctrader-exec-and-socket-gateway.md)
- Hardware: [8BitDo Ultimate 2 Wireless](https://www.8bitdo.com/ultimate-2-wireless-controller/)
- Gamepad API: [MDN](https://developer.mozilla.org/en-US/docs/Web/API/Gamepad_API)

## Requirements

- Functional: detect pad (`mapping === "standard"`), wake on first button (spec privacy gesture)
- Functional: rAF poll `navigator.getGamepads()` — never cache the Gamepad object
- Functional: clutch + arm + confirm FSM; analog sticks **never** submit orders
- Functional: **Default LT hold (hysteresis 0.80/0.50) + RT rising-edge**. L4/R4 only after a first-run probe proves those indices change. Empty `mapping` + 8BitDo `id` still accepted.
- Functional: buy / sell / close / panic-flatten; lot step; D-pad cycles **XAUUSD / EURUSD / GBPUSD / USDJPY**; timeframe; session lock
<!-- Updated: Validation Session 1 - four-symbol basket -->
- Functional: Lightweight Charts candles + last price + **20 EMA**; DOM HUD for bid/ask, lot, P/L, clutch meter, confirm overlay, session timer, **sentinel strip placeholder**, **copilot desk placeholder**
- Functional: rumble best-effort (`vibrationActuator`); visual confirm always
- Functional: `visibilitychange` and `gamepaddisconnected` cancel arm and set `visible`/`pad` false immediately (do not wait for rAF)
- Functional: reconnect with same unacked `cid`; `ws.onclose` → LOCKED but **keep** that cid; FIRE timeout → unknown, block new fire until cid resolves
- Functional: HUD **Flatten** button (keyboard/click) that does not need the pad; close/panic bypass dead-man
- Functional: **process cues in the HUD** — live adherence badge (named setup present, outside T-15, lot at cap, inside window), a **stood-down counter** that reads as a win, and the sentinel's opportunity-quality state so a dead tape looks like a dead tape
- Functional: **open P/L is shown in R (risk units) by default**, dollars behind a toggle. Steenbarger's point: watching the money mid-trade is what pulls attention off the process
- Functional: **session check-in** — 1-5 self rating on session open and close, two pad taps, skippable, written to the phase 6 journal; never blocks the evening starting
- Functional: the FSM emits **telemetry on every transition**, batched at 1 Hz on the `session` channel as `pad.telemetry` (never per-frame): `clutchMs`, `armMs`, `clutchCycles`, `armFlips`, `btnRateHz`, `lotStepsSince`, `ttfMs`, plus a 1 Hz idle heartbeat. Cheap to design in now, expensive to retrofit — phase 9 has no other source
- Functional: **push-to-talk on the `LB + RB` chord** (phase 8). Both bumpers down inside a 120 ms window suppresses both timeframe actions and enters PTT; a single-bumper timeframe change therefore fires **on release** when the other bumper was never down during the press. Both are non-order inputs, so a chord misfire costs a chart zoom, never a position. Keyboard `V` hold is an equal-status fallback
- Functional: PTT is a **parallel** state machine that emits no order-FSM transition of its own, is enterable only from `IDLE` or `LOCKED`, and on entering `CLUTCH` performs a graceful stop-and-submit rather than a discard
- Functional: **playbook cycle on `Menu + D-pad U/D`** and a 5th `[Memo]` tab in the copilot desk. The **active desk tab decides** whether a transcript becomes a journal memo or an `ai.ask` — so voice needs zero extra bindings and the destination is visible before the player speaks
- Functional: the ARM confirm overlay shows the **live playbook grade** (phase 7): `BUY 0.10 XAUUSD @ 2345.12 / [M5 second-chance break] 4/5 rules OK · ✗ price > 1.5 ATR from EMA20`. Seeing the grade before committing is the point of the feature
- Functional: the fire predicate takes **`confirmHoldMs` as a parameter** so phase 9's friction is a config value rather than a rewrite; the FSM gains no new states and `fsm.test.ts` stays valid
- Functional: mic acquisition and the `MediaRecorder` mime probe live in the Settings overlay (Menu), behind an explicit "enable mic" button; a **tilt pip** sits in the HUD
- Functional: the stood-down counter is generalised to emit `stand_down` with its live condition list, so phase 11's Selectivity axis reuses this counter instead of adding a second one
<!-- Updated: Validation Session 4 - journal layer capture, PTT chord, playbook grade in the overlay -->
<!-- Updated: Validation Session 3 - process cues in HUD; end goal is confidence, not P/L -->
- Functional: WS token lives in **memory** this session (paste once); never `localStorage`, never `VITE_*`
- Non-functional: quote **text** at 10–20 Hz max, not 60 Hz framework state
- Non-functional: desktop Chrome first; rumble optional on Firefox/Safari
- Non-functional: dev runs the Vite dev server with `/ws` proxied to `127.0.0.1:8444`; **production is same-origin** — the gateway serves `dist` at `/` and the socket at `/ws`, so the memory-only token and `default-src 'self'` hold without a CORS carve-out
- Non-functional: entertainment copy in chrome: **cTrader demo**, not advice, not live

## Architecture

```
rAF poll → deadzone 0.12 → rising edge → FSM → intent queue (ULID cid) → WS
visibility / disconnect → LOCKED (client) + ping flags (server dead-man)
```

### FSM

```
LOCKED  --unlock chord (View tap)--► IDLE
IDLE    --hold clutch--► CLUTCH
CLUTCH  --A/B/X/Y--► ARMED (preview + weak rumble)
ARMED   --confirm click--► FIRE (one intent) --ack--► IDLE
any: confirm-up / clutch-up / B-while-idle / hidden / unplug → CANCEL
```

Fire = two hands: clutch held **and** confirm rising edge **and** an armed side. No 400 ms countdown. Intent payload includes `clutch: true` and `armedAt` (pong-corrected). Drain the intent queue on CANCEL. `ws.onclose` does not mint a new cid.

### 8BitDo Ultimate 2 map (Xbox labels)

**Default (always works on standard 17-button Xbox mapping)**

| Input | Intent |
|-------|--------|
| LT hold (0.80 on / 0.50 off) | Clutch |
| RT click | Confirm-to-fire |
| A | Arm BUY |
| B | Arm SELL (also cancel when not clutched) |
| X | Arm CLOSE |
| Y | Arm PANIC FLATTEN + LOCK |
| D-pad U/D | Lot step (idle **and** clutched — never bind lot to LT) |
| D-pad L/R | Cycle symbol highlight; A **without clutch** applies symbol |
| LB / RB | Timeframe down / up (fires **on release**; see the chord below) |
| LB + RB hold | Push-to-talk — journal memo, or ask the coach when an AI desk tab is active |
| Menu + D-pad U/D | Cycle the active playbook |
| LS | Pan chart |
| RS X/Y | Preview SL / TP only |
| View | Session lock / unlock |
| Menu | Settings overlay |
| L3+R3 hold 1.5s | Panic flatten + lock (backup chord) |

**Optional extras (only if probe sees L4/R4 change)**

L4 = clutch alias, R4 = confirm alias. Do not steal LT for lot size.

First-run calibration overlay: “hold L4, then RT”. If L4 never moves, stay on LT/RT. Nintendo-layout A/B swap is a settings toggle (default Xbox).

**Voice never reaches the order path.** `voice.bindings` resolving to LT/RT/A/B/X/Y is a phase 1
boot-fail, and PTT is only enterable from `IDLE` or `LOCKED`. This is structural, not a convention.

Mac link: **2.4G dongle** is primary — it presents an XInput-class pad, so Chrome reports
`mapping: "standard"` and the table above holds. **Wired USB** is the fallback. Bluetooth on
the Ultimate 2 Wireless needs **macOS 26+**; this Mac is macOS 15.6, so BT is documented but
is not the supported path. Chrome, focused window.

<!-- Updated: Validation Session 2 - 8BitDo Ultimate 2 BT on Apple requires macOS 26+ -->

### HUD (evening game)

Dark, high contrast, 2–3 colors (bid/ask/flat). Big last price, **P/L in R (dollars one toggle away)**, one primary symbol, one lot, one position strip, clutch meter, adherence badge, stood-down counter, tilt pip, confirm overlay (`BUY 0.10 XAUUSD @ 2345.12` + the live playbook grade), sentinel strip stub, copilot desk stub (5 tabs incl. `[Memo]`), session countdown.

The **Process Score lives on the deck, not the HUD** (phase 11) — there is deliberately no live score
to watch mid-session.

Not a DOM-dense Bloomberg clone.

## Related Code Files

- Create: `apps/web/src/pad/poll.ts`
- Create: `apps/web/src/pad/fsm.ts`
- Create: `apps/web/src/pad/map.ts` (standard + extra-button detect)
- Create: `apps/web/src/net/ws.ts`
- Create: `apps/web/src/hud/Chart.svelte`
- Create: `apps/web/src/hud/PriceTape.svelte`
- Create: `apps/web/src/hud/ConfirmOverlay.svelte`
- Create: `apps/web/src/hud/PositionStrip.svelte`
- Create: `apps/web/src/hud/SessionBar.svelte`
- Create: `apps/web/src/hud/AdherenceBadge.svelte` (adherence + stood-down counter)
- Create: `apps/web/src/hud/SentinelBar.svelte` (stub until phase 4)
- Create: `apps/web/src/hud/CopilotDesk.svelte` (tabs stub until phase 4)
- Create: `apps/web/src/App.svelte`
- Create: `apps/web/src/pad/telemetry.ts` (transition fields + 1 Hz batching)
- Create: `apps/web/src/pad/fsm.test.ts`
- Create: `apps/web/src/pad/chord.test.ts` (LB+RB vs single bumper; fire-on-release)
- Modify: `README.md` (dongle pairing + wired fallback, map, “tab must stay focused”)

## Implementation Steps

1. Pad poller + mapping probe (log `id`, `mapping`, button count). Detect L4/R4 vs fallback.
2. FSM unit tests: held A does not spam; stick drift never fires; hide cancels arm.
3. WS client: hello, ping with `{visible,pad,clutch}`, seq gap resync, cid retry.
4. Chart: LWC `series.update` from `candle` + last from `quote`.
5. HUD numbers via `textContent` / signals sampled 15 Hz, not per tick store updates.
6. Telemetry fields on every transition; 1 Hz batch on `session`.
7. `LB + RB` chord with bumper fire-on-release; unit-test that PTT emits no order transition.
8. `confirmHoldMs` threaded through the fire predicate as a parameter (default 0 = rising edge).
9. Confirm overlay renders the phase 7 grade; `Menu + D-pad U/D` playbook picker.
6. Confirm overlay + rumble on arm/fill/reject.
7. Settings: lot, symbol list, clutch deadzone, rumble on/off.
8. Manual matrix: 8BitDo via **2.4G dongle** on Mac Chrome — connect, trade, unplug, hide tab. Repeat wired as the fallback path.

## Todo

- [ ] Pad poll + extra-button detect
- [ ] FSM tests
- [ ] WS client + dead-man flags
- [ ] LWC + DOM HUD
- [ ] Confirm overlay + rumble
- [ ] Adherence badge, stood-down counter, R-first P/L toggle, check-in
- [ ] Pad telemetry fields + 1 Hz batch
- [ ] LB+RB chord PTT; bumpers fire on release; PTT emits no order transition
- [ ] `confirmHoldMs` as a fire-predicate parameter
- [ ] Playbook picker + `[Memo]` desk tab + grade in the confirm overlay
- [ ] Mic enable + mime probe in Settings; tilt pip
- [ ] README dongle pairing + wired fallback + map
- [ ] Manual 8BitDo pass

## Success Criteria

- [ ] Clutch+A+confirm opens **cTrader demo** XAUUSD; fill rumbles; P/L from cTrader
- [ ] Unplug or Cmd-Tab hiding the tab locks orders (server reject + HUD lock)
- [ ] Held buttons do not spray orders
- [ ] Symbol/lot/timeframe work without accidental fills
- [ ] Default HUD shows P/L in R; dollars require one deliberate toggle
- [ ] Cancelling an arm during a stand-down condition increments the stood-down counter
- [ ] Works with standard 17-button pad (LT/RT); extras optional
- [ ] Unplug still allows HUD Flatten; FIRE timeout does not double-send
- [ ] Tapping `LB` alone still changes timeframe and starts no recording; `LB + RB` starts one
- [ ] PTT cannot be entered from `CLUTCH` or `ARMED`, and entering `CLUTCH` mid-recording submits
      the memo without cancelling the arm
- [ ] The confirm overlay names the active playbook and its rule count before the fire
- [ ] `fsm.test.ts` passes unchanged after `confirmHoldMs` is introduced

## Risk Assessment

- **Chord misfires as a timeframe change** — signal: the chart jumps when starting a memo. Response:
  120 ms window plus fire-on-release, unit-tested in both directions.
- **Telemetry floods the socket** — signal: `pad.telemetry` at frame rate. Response: 1 Hz batching is
  a requirement, not an optimisation; assert the message rate in a test.
- **`LB + RB` is uncomfortable to hold** — signal: the player stops recording memos. Response:
  keyboard `V` is equal-status; L4/R4 paddles are the alternative if the probe found them.

- **L4/R4 not in `mapping: "standard"`** — signal: extras never fire. Response: **default is already LT/RT**; extras are opt-in after probe.
- **Dongle enumerates non-standard** — signal: `mapping !== "standard"` in the first-run probe. Response: the probe already logs `id` / `mapping` / button count; fall back to wired USB before hand-authoring an index map.
- **Chrome unfocused stops Xbox-class input on some OS** — signal: pad dead while another app focused. Response: product rule “Chrome stays focused”; show lock. No native helper in this plan.
- **Firefox rumble null** — signal: `vibrationActuator` missing. Response: flash overlay is canonical.
- **Stick-to-order temptation** — if anyone binds RS to send, accidental trades. Response: code review must keep analog off the fire path.

## Security Considerations

- Token in memory this session only. CSP `default-src 'self'`. Never `{@html}` on copilot/journal strings.
- No broker passwords in the browser. Exec sidecar stays on the VPS.

## Next Steps

Phase 4 fills SentinelBar, NewsRail, and CopilotDesk (Plan / Research / News / Advise) plus the Volman overlay. Stubs in this phase may render empty.
