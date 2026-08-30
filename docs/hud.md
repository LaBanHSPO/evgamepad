# The HUD (phase 3)

The evening game: an installable, client-side React PWA that turns 8BitDo
Ultimate 2 input into protocol intents. It is served by the gateway as static
files — no SSR, no Node at runtime.

Two entries share one bundle. `/` is the game. `/?prototype` is the
click-through screen deck the design work produced, kept because it is the
reference the HUD is built against.

## Run it

```bash
# gateway with the in-process mock broker
EV_WS_TOKEN=dev EV_CONFIG=config/mock.yaml uv run python -m apps.gateway.main

# the HUD, in another shell
pnpm -C app install
pnpm -C app dev        # 5173, proxies /ws and /api to 127.0.0.1:8444
pnpm -C app test       # 101 tests
pnpm -C app build      # emits app/dist, which the gateway serves at /
```

Paste `EV_WS_TOKEN` into the gate. It is held **in memory for this session
only** — a `#private` class field, never `localStorage`, never a `VITE_*` build
constant, so it cannot survive into an error report or outlive the evening.

## Controller map

| Input | Action |
|-------|--------|
| `LT` hold (on 0.80 / off 0.50) | Clutch |
| `RT` click | Confirm to fire |
| `A` / `B` | Arm buy / arm sell (`B` also cancels a live ARM) |
| `X` / `Y` | Arm close / arm panic-flatten |
| D-pad ↑↓ | Lot step |
| D-pad ←→ | Cycle symbol |
| `LB` / `RB` | Timeframe, **on release** |
| `LB` + `RB` | Push-to-talk (phase 8 control event only) |
| `View` | Session lock / unlock |
| `Menu` | Open / close the safe GameOverlay |

Link the pad with the **2.4G dongle** (wired USB is the fallback). Bluetooth on
the Ultimate 2 needs macOS 26+, so it is not the supported path here. **Chrome
must stay focused** — an unfocused window stops receiving pad input on some
systems, and the HUD shows the lock rather than pretending otherwise.

L4/R4 paddles are opt-in aliases, enabled only when a first-run probe sees those
indices actually change. They are never assumed from the pad's `id`, so a pad
without them keeps the LT/RT default.

## What the safety story rests on

Each of these is a test, not a convention:

**A fire takes two hands.** Clutch held, an armed side, and a *rising edge* on
confirm. A held button cannot spray orders; the machine leaves ARMED on the
first fire. `fsm.test.ts`.

**An analog stick can never fire.** Sticks are not inputs to the FSM at all —
the `Inputs` type has no axis fields. They pan the chart and stage an SL/TP
preview, nothing more.

**Losing the tab or the pad cancels immediately.** `visibilitychange` and
`gamepaddisconnected` synthesise a frame rather than waiting for rAF, which
never fires in a hidden tab.

**The overlay can never place an order.** `game-overlay/model.ts` has no
order-emitting effect in its union, and `overlay.test.ts` asserts it. An SL/TP
edit stages a preview that still needs LT+RT back in the game. Full close and
panic stay on screen while the menu is open.

**Push-to-talk is a parallel machine.** Enterable only from `IDLE` or `LOCKED`,
and reaching for the clutch mid-memo submits rather than discards. Phase 3 owns
the control event only — no microphone is acquired.

**A reconnect does not mint a new cid.** An unacked fire keeps its cid across
`onclose`, so a retry collides with the gateway's ledger instead of opening a
second position. A timeout is reported as *unknown*, not failed, and new fires
stay blocked until it resolves.

**The service worker caches the shell only.** Every `/api/*` and `/ws` route is
refused, so an offline app opens its shell and shows disconnected — it never
shows a stale price, position, or P/L. `sw.test.ts` sweeps the data routes.

**Telemetry is batched at 1 Hz.** `telemetry.test.ts` asserts that five seconds
of 60 fps input produces at most five socket frames. Phase 9 has no other
source for tilt, and an evening that was not recorded cannot be replayed.

## Process, not P/L

Open P/L is shown **in R by default**, dollars one deliberate click away —
watching the money mid-trade is what pulls attention off the process. The R
comes from the gateway's own per-position `rMultiple`; the HUD never divides a
constant into the dollars, because a second R definition in the browser is how
the HUD and the journal end up disagreeing about one trade. If a position has
no R yet (one reconciled from cTrader after a restart), the figure falls back to
dollars rather than reporting a partial sum as complete.

Cancelling into a bad tape **increments a stand-down counter**, which reads as a
win because it is one. Each event keeps the conditions that were failing, so
phase 11's Selectivity axis reuses this counter rather than adding a second.

The Process Score is deliberately absent from the HUD. It lives on the deck
(phase 11) — there is no live score to watch mid-session.

## Rendering

React owns layout and the overlay. It **does not re-render on quotes**: prices
land in a ref and `PriceTape` writes `textContent` at 15 Hz from its own rAF
loop. A 60 Hz `setState` per tick would re-render the confirm overlay under a
live ARM.

## Fonts and CSP

`default-src 'self'` with no third-party origin, so the webfonts are
**self-hosted** in `app/public/fonts` rather than imported from Google. A remote
font would violate the CSP and leave the installed PWA without its typeface
whenever the network is gone. Latin subsets only.

## Not done in phase 3

No Lightweight Charts candle chart yet — the price tape is live, the chart is
not. The sentinel strip and copilot desk are labelled shells until phase 4, the
confirm overlay says `grading unavailable` until phase 7, and the Memo tab is
disabled until phase 8. The manual 8BitDo pass (dongle, wired, installed PWA
window) needs real hardware and has not been run.
