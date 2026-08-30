# EVGamePad

React implementation of the Claude Design handoff in `../project`. Built from
`Prototype.dc.html` and `HudA.dc.html`; the prototype's own rule holds here —
**screens are real, data is fixed**.

```bash
npm install
npm run dev      # http://localhost:5173
npm run build    # tsc + vite build → dist/
npm run typecheck
```

## What is implemented

All 20 prototype screens plus the session HUD's six states — 26 views. The
sidebar groups them in the order a session runs, which is the ordering the
design chat settled on.

| Group | Screens |
| --- | --- |
| 1 · Before the session | Attract screen, Boot sequence, Pre-session |
| 2 · In session | Session HUD, HUD on matrix art, Fire on city art, Agent desk, Trade detail, Size calculator |
| Session state | Safe, Armed, Result unknown, Stale price, Close only, Locked |
| 3 · After the session | Session clear, Session over, Report, Journal, Replay, History, Process score |
| 4 · Setup & reference | Gamepad, Data, Settings, Philosophy |

Each screen is a fixed artboard at the prototype's own size: 1440×810 for the
artwork screens, 1440×860 for the app screens, 1280×860 for Process score.

Nothing from the prototype is left out. The one gap is the prototype's own:
mistake-type filtering and the report's mistake-types section are drawn as
explicitly unavailable, because `execution-learning` has no spec yet.

## Layout

```
src/
  ds/            13 design-system components, ported 1:1 from the _ds bundle
  components/    CodeRain, the chiptune BGM engine, repeated markup shapes
  screens/       one file per artboard
  data/          fixed screen data, transcribed from the prototype
  styles/        design tokens (copied verbatim) + prototype keyframes
public/
  uploads/       background artwork
  sprites/       Contra-style sprites
```

## Notes on the port

- **Design system.** `src/ds` reproduces every component the screens use from
  `_ds_bundle.js` — AgentMessage, Badge, Button, Checkbox, GamepadKey, Icon,
  Input, MeterBar, PnLValue, StatTile, Switch, Tag, TradeRow — as typed React
  components. Styling is unchanged, including the inline-style approach, so
  values stay comparable to the bundle. The bundle's other eight components
  (Card, Dialog, Toast, Tooltip, Radio, Select, Tabs, IconButton) are unused by
  these screens and were not ported. The token CSS files are copied verbatim.
- **Icons.** The bundle's `Icon` fetched each lucide glyph from a CDN at
  runtime. Here the glyph bodies are inlined from lucide-static 0.417.0 — the
  same version the bundle pinned — so icons render offline and on first paint.
- **Fixed inputs.** Form controls render fixed state, so `Input`, `Checkbox` and
  `Switch` mark their inputs `readOnly` when no handler is passed, rather than
  tripping React's controlled-input warning.
- **BGM.** The chiptune is generated with WebAudio, as in the prototype: square
  lead over triangle bass on a 125ms step, no audio file. Nothing plays until
  PLAY is pressed. The Attract and city-art screens drive one shared engine, as
  they did when both read from the prototype's single root component.
- **City-art layout.** Kept as the design chat converged on it after many
  rounds: all order figures in one 298px left rail, right side clear for the
  citadel, and the framing plate in its own top-right z-index-4 strip — at
  z-index 1 the hero sprite covered it regardless of `bottom`.
- **Motion.** All the prototype's `@keyframes` live in `src/styles/global.css`;
  the token-level ones (`ev-blink` and friends) come from `tokens/motion.css`
  untouched. Every animation uses `steps()`, per the system's motion rule, and
  no figure animates.
- **Fonts** load from Google Fonts via the design system's `tokens/fonts.css`,
  unchanged. Press Start 2P, JetBrains Mono and VT323 are the brief's
  stand-ins — if licensed faces arrive, swap the `@import` for `@font-face`.
