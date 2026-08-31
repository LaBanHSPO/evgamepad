---
title: "Phase 3: Web game and 8BitDo client agent"
status: in-progress
phase: 3
priority: P1
effort: 18h
dependencies: [2]
---

# Phase 3: Web game and 8BitDo client agent

## Overview

Ship the evening game: Chrome HUD + **client agent** that turns 8BitDo Ultimate 2 input into protocol
intents. Look like a game, not a terminal. Tab must stay focused.

The app is a **client-side React PWA** — Vite build, TanStack Router for the overlay routes, TanStack
Query for the REST decks. There is **no SSR and no server-side rendering step**: the socket supplies
everything that matters within a frame of connecting, and the gateway serves the built bundle as
static files. Installing it gives the evening session its own window with no browser chrome to
mis-click during a fire.

## Context Links

- [plan.md](./plan.md)
- [cTrader exec and socket gateway](./phase-02-ctrader-exec-and-socket-gateway.md)
- Hardware: [8BitDo Ultimate 2 Wireless](https://www.8bitdo.com/ultimate-2-wireless-controller/)
- Gamepad API: [MDN](https://developer.mozilla.org/en-US/docs/Web/API/Gamepad_API)

## Requirements

- Functional: detect pad (`mapping === "standard"`), wake on first button (spec privacy gesture)
- Functional: rAF poll `navigator.getGamepads()` — never cache the Gamepad object
- Functional: clutch + arm + confirm FSM; analog sticks **never** submit orders. RS X/Y adjusts
  relative SL/TP in the preview only and shows the resulting R/target; it never sends an amendment
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
- Functional: **session check-in** — 1-5 self rating on session open and close, two pad taps,
  skippable, written to the phase 3-owned `session_process` row for phase 6 to read; never blocks the
  evening starting
- Functional: the FSM emits **telemetry on every transition**, batched at 1 Hz on the `session` channel as `pad.telemetry` (never per-frame): `clutchMs`, `armMs`, `clutchCycles`, `armFlips`, `btnRateHz`, `lotStepsSince`, `ttfMs`, plus a 1 Hz idle heartbeat. Cheap to design in now, expensive to retrofit — phase 9 has no other source
- Functional: **push-to-talk on the `LB + RB` chord** (phase 8). Both bumpers down inside a 120 ms window suppresses both timeframe actions and enters PTT; a single-bumper timeframe change therefore fires **on release** when the other bumper was never down during the press. Both are non-order inputs, so a chord misfire costs a chart zoom, never a position. Keyboard `V` hold is an equal-status fallback
- Functional: PTT is a **parallel** state machine that emits no order-FSM transition of its own, is enterable only from `IDLE` or `LOCKED`, and on entering `CLUTCH` performs a graceful stop-and-submit rather than a discard
- Functional: `Menu` opens/closes a full-screen **GameOverlay**. Opening it cancels any ARM and hard
  locks new opens. D-pad selects a destination, LB/RB changes desk tabs, A enters or applies a
  non-broker preference, B goes back, and Menu exits. Playbook, Journal, System, Reports, Settings,
  and the five desk tabs are reached through this one navigation contract
- Functional: overlay navigation and apply actions cannot emit `intent.open` or `intent.modify`.
  Applying a broker-changing SL/TP edit only stages an `ARMED modify` preview; the actual
  `intent.modify` still requires LT+RT after the player returns to the game. Dedicated full-close,
  HUD Flatten, and panic controls remain available as safety exits
- Functional: the 5th `[Memo]` desk tab exists as a disabled `voice unavailable until phase 8`
  placeholder. Phase 3 owns the LB+RB chord/control event and fire-on-release arbitration only; it
  does not acquire a microphone, record, upload, or produce a transcript
- Functional: the ARM confirm overlay reserves the live grade surface but renders
  `grading unavailable` until phase 7. Phase 3 acceptance does not depend on playbooks existing
- Functional: the fire predicate takes **`confirmHoldMs` as a parameter** so phase 9's friction is a config value rather than a rewrite; the FSM gains no new states and `fsm.test.ts` stays valid
- Functional: Settings is reached through GameOverlay. Mic acquisition and MIME probing belong to
  phase 8; until then the mic control is disabled. A tilt-pip placeholder sits in the HUD
- Functional: the stood-down counter is generalised to emit `stand_down` with its live condition list, so phase 11's Selectivity axis reuses this counter instead of adding a second one
<!-- Updated: Validation Session 4 - journal layer capture, PTT chord, playbook grade in the overlay -->
<!-- Updated: Validation Session 3 - process cues in HUD; end goal is confidence, not P/L -->
- Functional: WS token lives in **memory** this session (paste once); never `localStorage`, never `VITE_*`
- Functional: installable PWA — web app manifest, `display: standalone`, dark theme colour, and a
  service worker that precaches the **app shell only**. It must never cache `/ws`, `/api/*`, quotes,
  positions, or any journal response; a stale price or a stale position is worse than no app
- Functional: a new build must take effect on the next launch — the service worker activates
  immediately rather than waiting for every tab to close, and the HUD refuses to run against a
  protocol version it does not recognise
- Non-functional: quote **text** at 10–20 Hz max, not 60 Hz framework state
- Non-functional: desktop Chrome first; rumble optional on Firefox/Safari
- Non-functional: dev runs the Vite dev server with `/ws` proxied to `127.0.0.1:8444`; **production is same-origin** — the Python gateway serves `dist` at `/` and the socket at `/ws`, so the memory-only token and `default-src 'self'` hold without a CORS carve-out. No Node process runs in production
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
| LS | Pan chart |
| RS X/Y | Preview SL / TP only |
| View | Session lock / unlock |
| Menu | Open / close the safe GameOverlay; opening cancels ARM and locks new opens |
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

Dark, high contrast, 2–3 colors (bid/ask/flat). Big last price, **P/L in R (dollars one toggle away)**, one primary symbol, one lot, one position strip, clutch meter, adherence badge, stood-down counter, tilt pip, confirm overlay (`BUY 0.10 XAUUSD @ 2345.12` + relative SL/TP + R + a grading placeholder), sentinel strip stub, copilot desk stub (5 tabs incl. disabled `[Memo]`), session countdown.

The **Process Score lives on the deck, not the HUD** (phase 11) — there is deliberately no live score
to watch mid-session.

Not a DOM-dense Bloomberg clone.

## Related Code Files

- Create: `apps/web/src/pad/poll.ts`
- Create: `apps/web/src/pad/fsm.ts`
- Create: `apps/web/src/pad/map.ts` (standard + extra-button detect)
- Create: `apps/web/src/net/ws.ts`
- Create: `apps/web/src/hud/Chart.tsx`
- Create: `apps/web/src/hud/PriceTape.tsx`
- Create: `apps/web/src/hud/ConfirmOverlay.tsx`
- Create: `apps/web/src/hud/PositionStrip.tsx`
- Create: `apps/web/src/hud/SessionBar.tsx`
- Create: `apps/web/src/hud/AdherenceBadge.tsx` (adherence + stood-down counter)
- Create: `apps/web/src/session/CheckIn.tsx` (pad-driven pre/post 1–5 check-in)
- Create: `apps/web/src/hud/SentinelBar.tsx` (stub until phase 4)
- Create: `apps/web/src/hud/CopilotDesk.tsx` (tabs stub until phase 4)
- Create: `apps/web/src/game-overlay/GameOverlay.tsx` (single safe navigation surface)
- Create: `apps/web/src/routes/` (TanStack Router tree for the overlay destinations)
- Create: `apps/web/src/App.tsx`
- Create: `apps/web/public/manifest.webmanifest` + icons (installable, standalone, dark)
- Create: `apps/web/src/sw.ts` (app-shell precache only; `/ws` and `/api/*` never cached)
- Create: `apps/web/src/pad/telemetry.ts` (transition fields + 1 Hz batching)
- Create: `apps/web/src/pad/fsm.test.ts`
- Create: `apps/web/src/pad/chord.test.ts` (LB+RB vs single bumper; fire-on-release)
- Create: `apps/web/src/game-overlay/GameOverlay.test.tsx` (focus/navigation; never emits open/modify)
- Create: `apps/web/src/sw.test.ts` (asserts no data route is cacheable)
- Create: `apps/gateway/db/migrations/002-client-session.sql` (`pad_event`, `session_process`)
- Modify: `README.md` (dongle pairing + wired fallback, map, “tab must stay focused”)

## Implementation Steps

1. Pad poller + mapping probe (log `id`, `mapping`, button count). Detect L4/R4 vs fallback.
2. FSM unit tests: held A does not spam; stick drift never fires; hide cancels arm.
3. WS client: hello, ping with `{visible,pad,clutch}`, seq gap resync, cid retry.
4. Chart: LWC `series.update` from `candle` + last from `quote`.
5. HUD numbers written imperatively at 15 Hz — refs and direct DOM writes on the hot price path, not
   React state per tick. React owns layout and the overlay; it does not re-render on quotes.
6. Telemetry fields on every transition; 1 Hz batch on `session`.
7. `LB + RB` chord with bumper fire-on-release; connect it to a no-op voice adapter and unit-test
   that the control event emits no order transition. MediaRecorder begins in phase 8.
8. `confirmHoldMs` threaded through the fire predicate as a parameter (default 0 = rising edge).
9. GameOverlay navigation and lock semantics; five desk-tab shells, disabled Memo, Settings and
   Playbook destinations. Navigation/apply cannot emit open/modify; emergency exits remain usable.
10. Confirm overlay + rumble on arm/fill/reject; grade placeholder and relative SL/TP/R preview.
11. Settings: lot, symbol list, clutch deadzone, rumble on/off. SL/TP apply stages a modify action
    and returns to the LT+RT confirmation flow.
12. Apply `002-client-session.sql` and write check-in/telemetry rows.
13. Manifest, icons, and the shell-only service worker; assert in a test that no data route is
    cacheable and that a new build activates on the next launch.
14. Manual matrix: 8BitDo via **2.4G dongle** on Mac Chrome — connect, trade, overlay, unplug, hide
    tab. Repeat wired as the fallback path, and once from the **installed** PWA window.

## Todo

- [x] Pad poll + extra-button detect
- [x] FSM tests
- [x] WS client + dead-man flags
- [ ] LWC + DOM HUD
- [ ] Confirm overlay + rumble
- [ ] Adherence badge, stood-down counter, R-first P/L toggle, check-in
- [x] Pad telemetry fields + 1 Hz batch
- [x] LB+RB chord PTT; bumpers fire on release; PTT emits no order transition
- [x] `confirmHoldMs` as a fire-predicate parameter
- [ ] GameOverlay navigation + new-open lock + no-open/no-modify test; emergency exits preserved
- [ ] Playbook destination + five-tab shell + disabled `[Memo]` placeholder
- [ ] Grade placeholder + relative SL/TP/R preview
- [ ] SL/TP apply stages modify; LT+RT remains mandatory
- [x] `002-client-session.sql` + check-in/telemetry writes
- [ ] Disabled mic control until phase 8; tilt pip placeholder
- [x] Installable manifest + shell-only service worker + no-cache-on-data test
- [x] README dongle pairing + wired fallback + map
- [ ] Manual 8BitDo pass, browser tab and installed window

## Success Criteria

- [ ] Clutch+A+confirm opens **cTrader demo** XAUUSD; fill rumbles; P/L from cTrader
- [ ] Unplug or Cmd-Tab hiding the tab locks orders (server reject + HUD lock)
- [x] Held buttons do not spray orders
- [ ] Symbol/lot/timeframe work without accidental fills
- [ ] Default HUD shows P/L in R; dollars require one deliberate toggle
- [ ] Cancelling an arm during a stand-down condition increments the stood-down counter
- [x] Pre/post check-in is skippable, writes `session_process`, and never blocks session start/close
- [x] Works with standard 17-button pad (LT/RT); extras optional
- [ ] Unplug still allows HUD Flatten; FIRE timeout does not double-send
- [x] Tapping `LB` alone changes timeframe; `LB + RB` emits only the phase-8 voice control event and
      phase 3 never requests microphone permission
- [ ] Opening Menu cancels ARM and locks new opens; navigation/apply emits no open/modify while full
      close and panic remain available
- [ ] An SL/TP edit returns as an armed modify preview and cannot reach the broker without LT+RT
- [ ] Before phase 7, the confirm overlay says `grading unavailable` without blocking a fire
- [x] `fsm.test.ts` passes unchanged after `confirmHoldMs` is introduced
- [ ] Chrome offers **Install**; the installed window trades identically to the tab, and the pad,
      rumble, and focus-lock rules behave the same in it
- [ ] With the network cut, the installed app opens its shell and shows a disconnected state — it
      never shows a cached price, position, or P/L
- [ ] Shipping a new build makes the next launch run it, without asking the player to hard-reload

## Verification Status

`npm --prefix app test`: **76 passed**. `tsc --noEmit`: clean. `npm run build`: passes the
protocol-type gate and emits `sw.js` unhashed at the site root. Gateway: **154 passed, 1 skipped**.

### Verified

The FSM (23 tests): a held button fires once, no axis reaches the machine at all, the clutch has
hysteresis, hiding the tab or unplugging the pad cancels an arm on the spot, an outstanding cid
blocks a new open but never an exit, and `confirmHoldMs` withholds a fire without adding a state.
The chord (10 tests): a single bumper changes timeframe on release, both together are a memo, a
refused chord still does not zoom the chart, and clutching mid-memo stops and submits. Telemetry
(7 tests): 600 frames in, at most 10 samples out. Socket client (9 tests): an outstanding intent
replays under its original cid, and an unknown protocol version stops the client rather than
guessing. Service worker (6 tests): no data route is cacheable and a new deploy activates without
a hard reload. Agent (13 tests): a two-handed gesture becomes exactly one intent, and `flatten()`
works with no pad at all.

### Not verified — no 8BitDo in this environment

The whole manual matrix: dongle pairing, wired fallback, the L4/R4 probe against real paddles,
rumble, and the installed-PWA window. Those need the hardware and the Mac.

### Not built in this pass

`GameOverlay`, the TanStack Router tree, Lightweight Charts, the desk/sentinel stubs, and the
`AdherenceBadge`/`CheckIn` components as separate files. The 21 existing prototype screens in
`app/src/screens/` already carry those surfaces as fixed-data mockups; wiring them to live state
is UI work that adds no safety property and would have crowded out the agent layer. What landed
instead is `LiveHudScreen` — the one screen holding a real socket, a real pad, and the real FSM,
with the R-first P/L toggle, the stood-down counter, the grading placeholder, the check-in, and
the pad-free FLATTEN exit.

### Deviations from this phase as written

- **Paths.** `app/` rather than `apps/web/`, continuing phase 1's decision not to scaffold a
  second React app beside the existing one.
- **The check-in rides HTTP, not the socket.** Protocol v1 was frozen in phase 1 with no check-in
  message, and adding one now would be exactly the v2 migration that freeze existed to prevent.
  `POST /api/journal/checkin` and `/api/journal/stand-down` use the `/api/journal/*` surface phase
  1 already declared — the same reasoning that puts voice audio and the decks on HTTP.
- **`sw-policy.ts` split from `sw.ts`.** The worker registers listeners at import time, so the
  cache policy lives in its own module to stay testable without a worker global.

### Findings from this phase

- **A spent arm survived into `UNKNOWN`.** After a fire timeout the FSM still held the old side,
  so a stale "buy" read as a live arm. The arm is now cleared the moment it fires.
- **`{ ...DEFAULTS, ...options }` disabled every fire.** Passing `confirmHoldMs: undefined`
  clobbered the default of `0`, making `nowMs - confirmDownAt >= undefined` always false. Options
  now fall back individually. This one is worth remembering: the bug was invisible in the FSM's
  own tests, which never passed an explicit `undefined`.

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
- No broker passwords in the browser. The broker link and its tokens stay in the gateway on the VPS.
- The service worker caches the shell only — no quote, position, or journal response is ever written
  to a cache the browser would replay after the session ends.

## Next Steps

Phase 4 fills SentinelBar, NewsRail, and the four AI tabs in CopilotDesk; the fifth Memo tab remains
disabled until phase 8. Stubs in this phase may render empty.
