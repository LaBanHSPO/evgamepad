# EVGamePad — Design System (single-file spec)

> Consolidated reference. Everything in `readme.md`, `tokens/*.css`, and the component `.d.ts` files, in one document.
> Generated 2026-08-29. Source of truth for code remains `styles.css` + `components/`.

---

## 1. PRODUCT

EVGamePad is a **trading journal you drive with a game controller, reviewed by AI agents.** Traders bind capture actions (log, tag, size, commit) to a gamepad so a fill can be journalled without leaving the chart, and a small crew of agents reads those fills against the trader's own rule set — blocking bad size, tagging setups, and writing the session review.

Art direction from the brief: **Matrix film × Contra (NES)**. A phosphor-green CRT terminal as the base layer, with arcade sprite colour and hard-edged sprite shadows for moments of action. It should read like a trading terminal that boots into an arcade cabinet, not like a SaaS dashboard. Current balance is roughly **80% terminal / 20% arcade**.

### 1.1 Sources

Authored **from the written brief only**. No codebase, Figma file, screenshots, or brand assets were provided — everything here is a proposal, not a recreation.

| Source | Status |
|---|---|
| Company description | "EVGamePad — trading journal with AI Agents and GamePad" (chat brief) |
| Art direction note | "matrix film theme + contra game" (chat brief) |
| Codebase / repo | none supplied |
| Figma file | none supplied |
| Logo / brand assets | none supplied |
| Fonts | none supplied — Google Fonts substitutes in use |
| Product copy | none supplied — sample copy written to the tone rules below |

### 1.2 Substitutions to confirm

1. **Fonts.** Standing in: **Press Start 2P** (arcade display), **JetBrains Mono** (all UI, data, body), **VT323** (terminal/agent voice), loaded from Google Fonts in `tokens/fonts.css`. Drop licensed binaries in `assets/fonts/` and replace the `@import` with local `@font-face`.
2. **Iconography.** Standing in: **Lucide** (`lucide-static@0.417.0`), fetched once per glyph and inlined as SVG by the `Icon` component so it inherits `currentColor`. For production, vendor used glyphs into `assets/icons/` and repoint `CDN` in `Icon.jsx`.
3. **Logo.** No mark supplied and none drawn. Wherever a logo would go, the wordmark **EVGAMEPAD** is set in the display face (`EV` phosphor, `GAMEPAD` arcade red) — see `guidelines/brand-wordmark.card.html`.
4. **Charts.** Honest placeholders (grid veil + stop/target lines). The equity curve is a token-coloured bar series, not a chart library.

---

## 2. CONTENT FUNDAMENTALS

**Voice.** A terminal that respects you. Short declaratives, present tense, no hedging and no cheerleading. The product knows the trader's numbers and states them.

**Person.** The product addresses the trader as **you**; agents speak as **I / we** only when they must own a judgement ("I blocked this order"). The company says **we** in marketing, never in the app.

**Casing — the one rule that carries the whole system:**
- **UPPERCASE + 0.18em tracking** for every label, tab, button, badge, column head, nav item. Labels are never sentence case.
- **Sentence case** for every sentence: body copy, notes, agent output, tooltips longer than two words, error messages.
- **Title Case is never used.** Not in headings, not in nav, not in buttons.
- **lowercase** for agent identifiers and tags (`risk-warden`, `fomo`, `orb`) — they are handles, not names.

**Numbers.** R multiples to two decimals with an explicit sign (`+2.40R`, `-1.10R`). Currency with thousands separators and no sign colour on neutral totals. Times 24-hour (`09:31`). Percentages whole unless below 10%. Never write "profit" where a number will do.

**Agent output** is terminal lines, one clause per line, prefixed `> `:

```
> three contracts on a 0.6R setup — rule 4 caps you at one.
> entry was 41s after the signal bar closed.
> same pattern cost you -4.3R over the last 12 sessions.
```

Agents cite evidence in the same breath as the verdict. They never apologise, never say "great job", never use "just" or "simply".

**Buttons and labels.** Verb first, two words maximum: `LOG TRADE`, `COMMIT SESSION`, `ASK AGENT`, `REBIND`. The one sanctioned piece of arcade language is **INSERT COIN** for the primary marketing CTA, plus **READY PLAYER ONE** as a closing line. References stay at that level — no "dodge the bullets", no "there is no spoon", no "wake up".

**Errors** state what happened and what to do, in that order, no exclamation marks: "Broker sync failed. Reconnect the feed and retry the import."

**Emoji: never.** Status is carried by colour, a glowing dot, or a lucide glyph. Unicode arrows (`→`) and em dashes are allowed in data strings (`18412.25 → 18461.00`); an em dash for empty values (`—`).

**Numbers over adjectives.** "Median review time 4m 12s, down 71%" beats "dramatically faster". If a claim has no number behind it, cut it.

---

## 3. VISUAL FOUNDATIONS

**Palette.** Near-black surfaces (`#040604` app → `#080C08` panel → `#0D130D` raised → `#131B13` input well), one hero colour — **phosphor green `#00FF41`** — and a small Contra sprite set (red `#E8202A`, orange `#FF8A00`, yellow `#FFD400`, cyan `#22E0FF`, magenta `#FF3DA6`). Neutrals are green-tinted greys so nothing reads as pure grey. Maximum **two** background values per layout. An arcade colour is never a large fill except on the `arcade` button and the pressed pad glyph.

**Colour semantics are locked.** Green = profit and long. Red = loss and short. Magenta = AI agent. Yellow = warning / approaching a limit. Cyan = informational and neutral tags. Nothing else may claim those meanings.

**Type.** Three faces, three jobs. Press Start 2P for arcade display moments only (wordmark, hero, one CTA) — never below 12px, never a paragraph, never more than three lines. JetBrains Mono for everything else including body copy: an all-monospace system is what makes a journal of numbers feel native. VT323 at 16px+ for agent output and logs. Body copy 14/1.5, max 64ch. Labels 10–11px uppercase at 0.18em.

**Numerals.** `font-variant-numeric: tabular-nums` on every figure, right-aligned in tables, two decimals on R. Column alignment down the page is a brand asset.

**Spacing & layout.** 4px grid with a 2px sub-step for hairline work. Panel padding 16, header strip 8/12, control gap 8, grid gap 16, section padding 56/32. Controls 24/32/40px, table rows 36px, HUD bars 44px, sidebar 216px, content max 1280px. Dense on purpose: a session should fit one screen. Fixed elements: sidebar, top session HUD, bottom pad-hint bar — pad hints are always visible, because the pad is always connected.

**Backgrounds.** Flat near-black. Never a photograph, never an illustration, **never a gradient as a hero background**. Texture comes from four veils at 0.4–0.6 opacity: `--veil-scanline` (terminal/agent panels), `--veil-grid` (24px graticule behind charts and hero), `--veil-vignette` (hero edges), `--protect-bottom` (text over busy areas). Matrix code rain appears **only** as hero/section texture at ≤0.35 opacity (`ui_kits/site/CodeRain.jsx`). Never put a veil behind numbers.

**Borders.** 1px is the only edge weight; default phosphor at 16% alpha, 42% for focus and emphasis. Panels are separated by hairlines, not elevation. A **2px left keyline** is the system's selection mark — selected rows, agent turns, toasts, tags, nav items.

**Shadows — two systems, no third.** (1) **Phosphor glow** (`--glow-xs` → `--glow-lg`, `--glow-text`) signals state: focus, live, positive P&L, featured plan. (2) **Sprite shadow** (`2px 2px 0 #000`, never blurred) gives arcade elements NES weight: arcade button, pad glyphs, toasts. Inputs use an inset well shadow. A soft grey drop shadow is off-brand.

**Corner radii.** 0 by default. 1–3px for rare cases; above 3px reads as a web app. Pill radius is reserved for status dots and A/B/X/Y face buttons.

**Cards.** Square, `--surface-panel` fill, 1px hairline border, no shadow, no rounding. Optional 34px header strip (uppercase phosphor title, muted meta, right-aligned icon actions); optional footer strip on `--black-1`. Body padding 16 (12 dense, 0 when holding rows).

**Transparency & blur.** Exactly three places: the modal veil (`rgba(0,0,0,.88)` + 6px blur), the sticky site header (86% black + 6px blur), and alpha fills for selected/hover (8–32% phosphor). Data never sits on a blurred surface.

**Hover / press / focus.** Hover = 8% phosphor wash plus text shift grey → phosphor; never a background lighter than `--black-3`, never a scale. Press = **1px translate down-right** (the sprite settling), never a scale. Focus = 2px phosphor ring plus `--glow-sm`; never removed. Disabled = `--black-3` fill, `--grey-700` text, no glow.

**Motion.** Mechanical and short: 60–180ms, `steps()` or linear, no bounce or spring. Four sanctioned motions: caret **blink** (1s, steps(1)), CRT **flicker** (4s, idle only), **scan** sweep on panel enter, **live pulse** ring on status dots. Toggle knobs snap in 2 steps. Numbers never animate — faked motion on money reads as latency.

**Imagery.** No photography. If introduced it must be cool-toned, high-contrast, heavily green-graded, with visible grain — treated, never naturalistic. Product screenshots are the preferred "image".

---

## 4. TOKENS

All tokens are CSS custom properties on `:root`, split across `tokens/*.css` and imported by `styles.css`.

### 4.1 Colour — `tokens/colors.css`

**Base: deep terminal blacks**

| Token | Value | Use |
|---|---|---|
| `--black-0` | `#000000` | sprite shadow only |
| `--black-1` | `#040604` | app background |
| `--black-2` | `#080C08` | panel |
| `--black-3` | `#0D130D` | raised panel / row hover |
| `--black-4` | `#131B13` | input well |
| `--black-5` | `#1B241B` | hairline-adjacent fill |

**Phosphor green ramp (Matrix code rain)**

| Token | Value | | Token | Value |
|---|---|---|---|---|
| `--phos-100` | `#D2FFDE` | | `--phos-600` | `#00A62A` |
| `--phos-200` | `#8CFFAC` | | `--phos-700` | `#00751D` |
| `--phos-300` | `#3DFF6E` | | `--phos-800` | `#004B13` |
| `--phos-400` | `#00FF41` ← signature | | `--phos-900` | `#00280A` |
| `--phos-500` | `#00D636` | | `--phos-950` | `#001706` |

**Arcade accents (Contra sprite palette)**

| Token | Value | | Token | Value |
|---|---|---|---|---|
| `--arcade-red` | `#E8202A` | | `--arcade-cyan` | `#22E0FF` |
| `--arcade-red-dim` | `#8E1119` | | `--arcade-blue` | `#1668FF` |
| `--arcade-orange` | `#FF8A00` | | `--arcade-magenta` | `#FF3DA6` |
| `--arcade-yellow` | `#FFD400` | | | |

**Neutrals (green-tinted)** — `--grey-100 #E8EFE8`, `--grey-300 #A8B6A8`, `--grey-500 #6E7C6E`, `--grey-700 #3F4A3F`, `--grey-900 #212821`

**Alpha utilities** — `--phos-a08/.08`, `--phos-a16/.16`, `--phos-a32/.32`, `--phos-a64/.64` (all `rgba(0,255,65,…)`), `--black-a64/.64`, `--black-a88/.88`

**Semantic aliases**

| Group | Tokens |
|---|---|
| Surfaces | `--surface-app` → `black-1` · `--surface-panel` → `black-2` · `--surface-raised` → `black-3` · `--surface-well` → `black-4` · `--surface-overlay` → `black-a88` · `--surface-hover` → `phos-a08` · `--surface-selected` → `phos-a16` |
| Text | `--text-primary` → `phos-100` · `--text-body` → `grey-100` · `--text-secondary` → `grey-300` · `--text-muted` → `grey-500` · `--text-disabled` → `grey-700` · `--text-accent` → `phos-400` · `--text-inverse` → `black-1` · `--text-terminal` → `phos-300` |
| Lines | `--line-hairline` `rgba(0,255,65,.16)` · `--line-strong` `.42` · `--line-solid` → `phos-700` · `--line-neutral` → `grey-900` |
| Trading | `--pnl-up` → `phos-400` · `--pnl-up-bg` → `phos-a16` · `--pnl-down` → `arcade-red` · `--pnl-down-bg` `rgba(232,32,42,.16)` · `--pnl-flat` → `grey-500` · `--side-long` → `phos-400` · `--side-short` → `arcade-red` |
| Status | `--status-live` green · `--status-warn` yellow · `--status-danger` red · `--status-info` cyan · `--status-agent` magenta |
| Gamepad | `--pad-a` green · `--pad-b` red · `--pad-x` cyan · `--pad-y` yellow · `--pad-shoulder` → `grey-300` |

### 4.2 Typography — `tokens/typography.css`

**Families**

| Token | Stack | Job |
|---|---|---|
| `--font-display` | `"Press Start 2P", "Courier New", monospace` | arcade HUD, sparse |
| `--font-core` | `"JetBrains Mono", ui-monospace, monospace` | everything UI |
| `--font-terminal` | `"VT323", "JetBrains Mono", monospace` | agent logs, rain |
| `--font-data` | `"JetBrains Mono", ui-monospace, monospace` | tabular numerals |

**Sizes** — `--text-2xs 10` · `xs 11` · `sm 12` · `md 13` · `base 14` · `lg 16` · `xl 20` · `2xl 26` · `3xl 34` · `4xl 46` · `5xl 64` (px)

**Arcade display sizes** (Press Start 2P runs ~30% large for its px size) — `--display-sm 12` · `md 16` · `lg 24` · `xl 36`

**Weights** — `--weight-light 300` · `regular 400` · `medium 500` · `bold 700` · `black 800`

**Line heights** — `--leading-tight 1.1` · `snug 1.3` · `normal 1.5` · `loose 1.7`

**Tracking** — `--tracking-tight -0.01em` · `normal 0` · `wide 0.06em` · `wider 0.12em` · `caps 0.18em` (uppercase HUD labels)

### 4.3 Spacing & metrics — `tokens/spacing.css`

**Scale** (4px grid, 2px sub-step) — `--space-0` · `px 1` · `2` · `4` · `6` · `8` · `12` · `16` · `20` · `24` · `32` · `40` · `48` · `64` · `96`

**Component metrics** — `--control-h-sm 24` · `--control-h-md 32` · `--control-h-lg 40` · `--control-pad-x 12` · `--row-h 36` · `--sidebar-w 216` · `--rail-w 52` · `--panel-pad 16` · `--hud-h 44`

**Layout** — `--max-content 1280px` · `--max-prose 64ch` · `--grid-gap 16px`

### 4.4 Effects — `tokens/effects.css`

**Radii** — `--radius-none 0` · `xs 1px` · `sm 2px` · `md 3px` · `pill 999px` (status dots and pad glyphs only)

**Borders** — `--border-hairline` `1px solid var(--line-hairline)` · `--border-strong` (line-strong) · `--border-solid` (line-solid) · `--border-neutral` (line-neutral) · `--border-w 1px` · `--border-w-thick 2px`

**Glow** (the only emphasis "shadow")

```
--glow-xs   0 0 4px  rgba(0,255,65,.30)
--glow-sm   0 0 8px  rgba(0,255,65,.28)
--glow-md   0 0 16px rgba(0,255,65,.26)
--glow-lg   0 0 32px rgba(0,255,65,.22)
--glow-red  0 0 12px rgba(232,32,42,.35)
--glow-text 0 0 6px  rgba(0,255,65,.55)
```

**Sprite shadow** (hard arcade offset, never blurred) — `--sprite-shadow 2px 2px 0 var(--black-0)` · `--sprite-shadow-lg 4px 4px 0`

**Inset well** — `--inset-well: inset 0 0 0 1px rgba(0,255,65,.10), inset 0 2px 8px rgba(0,0,0,.6)`

**Veils**

```
--veil-scanline  repeating-linear-gradient(180deg, transparent 0 2px, rgba(0,0,0,.22) 2px 3px)
--veil-grid      24px phosphor graticule, rgba(0,255,65,.05) both axes
--veil-vignette  radial-gradient(120% 90% at 50% 0%, transparent 40%, rgba(0,0,0,.72) 100%)
--protect-bottom linear-gradient(180deg, transparent, rgba(0,0,0,.85))
```

**Blur** — `--blur-overlay blur(6px)` · `--blur-heavy blur(14px)`

**Focus** — `--focus-ring: 0 0 0 1px var(--black-1), 0 0 0 2px var(--phos-400)`

**Z-index** — `--z-hud 20` · `--z-dropdown 40` · `--z-overlay 60` · `--z-toast 80`

### 4.5 Motion — `tokens/motion.css`

**Durations** — `--dur-instant 60ms` · `fast 110ms` · `med 180ms` · `slow 320ms` · `rain 1400ms`

**Easings** — `--ease-step steps(4,end)` · `--ease-step-2 steps(2,end)` · `--ease-linear linear` · `--ease-out cubic-bezier(.2,.8,.3,1)` · `--ease-in cubic-bezier(.6,0,1,1)`

**Transition shorthand** — `--transition-control` animates background-color, color, border-color, box-shadow at `--dur-fast`/`--ease-out`.

**Keyframes** — `ev-blink` (caret), `ev-flicker` (CRT idle), `ev-scan` (panel-enter sweep), `ev-pulse` (live dot ring).

### 4.6 Fonts — `tokens/fonts.css`

Single Google Fonts `@import`: `Press+Start+2P`, `JetBrains+Mono` (100–800, italic), `VT323`, `display=swap`. Replace with local `@font-face` when licensed files arrive.

---

## 5. ICONOGRAPHY

- **Set:** Lucide (substitute), pinned to `lucide-static@0.417.0`, rendered through `Icon` so every glyph inherits `currentColor`.
- **Delivery:** each glyph is fetched once from the pinned CDN and inlined as SVG (cross-origin CSS masks are dropped by browsers). No icon font, no hand-drawn SVG — and none should be drawn.
- **Sizes:** 12 / 14 / 16 / 20 / 24px (`xs`–`xl`). 14px inside 24–32px controls, 16px in headers, 20–24px in marketing feature cards. Stroke stays at Lucide's 2px default; never mix in a filled set.
- **Working vocabulary:** `list` (journal), `chart-candlestick` (trade), `bot` (agent), `gamepad-2` (pad), `trending-up`/`trending-down` (P&L), `target` (win rate), `shield` (rules), `timer`, `database`, `terminal`, `filter`, `download`, `plus`, `check`, `x`, `chevron-*`, `arrow-*`, `pencil`, `bell`, `settings`, `send`, `triangle-alert`, `info`.
- **Non-icon glyph vocabulary:** the **gamepad glyph set** (`GamepadKey`) is the product's own icon system — coloured circles for A/B/X/Y, chevron arrows for the d-pad, square shoulder keys for LB/RT/START. Use it, not text, whenever a binding is referenced.
- **Unicode as icons:** `→` in price transitions, `—` for empty values, `>` as the agent line prefix, `·` as a meta separator. That is the whole list.
- **Emoji: never.**

---

## 6. COMPONENTS

19 primitives across 7 groups. Each lives in `components/<group>/` with `.jsx`, `.d.ts`, `.prompt.md`, and one specimen card per directory. All props extend the matching `React.HTMLAttributes`.

### 6.1 `core/`

**Button** — square uppercase action control.
`variant?: "primary" | "secondary" | "ghost" | "danger" | "arcade"` · `size?: "sm"|"md"|"lg"` · `icon?`, `iconAfter?` (lucide names) · `fullWidth?` · `disabled?`
`arcade` is the Contra-styled variant — **one hero CTA per view, maximum.**

**IconButton** — square icon-only control for toolbars, table rows, HUD chrome.
`icon` (required) · `size?: "sm"|"md"|"lg"` · `variant?: "ghost"|"outline"` · `active?` (persistent selected) · `label?` (a11y, falls back to icon name)

**Icon** — lucide glyph taking `currentColor`.
`name` (lucide-static kebab-case, e.g. `chart-candlestick`) · `size?: "xs"|"sm"|"md"|"lg"|"xl" | number` · `color?`

**Card** — square hairline panel, optional uppercase header strip. No rounding, no drop shadow.
`title?` · `meta?` · `actions?` (usually IconButtons) · `footer?` · `padding?` (CSS) · `tone?: "panel"|"raised"|"well"` · `scanlines?`

**Badge** — small uppercase status label, read-only.
`tone?: "neutral"|"live"|"up"|"down"|"warn"|"info"|"agent"` · `dot?` (leading glowing dot)

**Tag** — removable/selectable metadata chip for setups, mistakes, emotions.
`onRemove?` (shows an x affordance) · `color?` (2px left keyline = category) · `selected?`

**StatTile** — KPI cell for the journal HUD; one metric, tabular numerals.
`label` · `value` · `delta?` (e.g. `"+0.8R"`) · `tone?: "neutral"|"up"|"down"` · `icon?` · `sub?`

### 6.2 `forms/`

**Input** — recessed single-line field. Values render tabular; right-align numerics.
`label?` (uppercase micro-label) · `hint?` · `error?` (replaces hint, turns the field red) · `icon?` · `suffix?` (unit, e.g. `USD`, `R`) · `size?: "sm"|"md"|"lg"` · `align?: "left"|"right"`

**Select** — native select in the well treatment with a lucide chevron.
`options: Array<string | {value, label}>` (required) · `label?` · `size?` · `hint?`

**Checkbox** — 14px square; checked = phosphor fill with a black tick.
`label?` · `description?` (muted second line) · `checked?`

**Radio** — single choice. The dot is the one place a pill radius is allowed.
`label?` · `description?` · `checked?` · `name?`

**Switch** — square-track toggle for instant-effect settings. Knob snaps in 2 steps, no glide.
`label?` · `checked?` · `size?: "sm"|"md"`

### 6.3 `navigation/`

**Tabs** — view switcher.
`tabs: Array<string | {value, label, icon?, count?}>` · `value` · `onChange?` · `variant?: "underline" | "segmented"`
`underline` for page-level sections, `segmented` for in-panel ranges.

### 6.4 `feedback/`

**Dialog** — centred modal over a blurred black veil. Absolutely positioned; give the host a relative wrapper.
`open?` · `title` · `subtitle?` · `footer?` (right-aligned actions) · `onClose?` · `width?` (px, default 480) · `tone?: "default"|"danger"` (danger switches frame and glow to arcade red)

**Toast** — transient notification. Left keyline carries the tone; hard sprite shadow, no blur.
`tone?: "success"|"error"|"warn"|"info"|"agent"` · `title` · `message?` · `action?` (usually a ghost Button) · `onClose?`

**Tooltip** — hover label for icon-only controls. Wraps its trigger; no arrow, no animation.
`label` · `shortcut?` (keyboard or pad shortcut as a kbd chip) · `placement?: "top"|"bottom"|"left"|"right"`

**MeterBar** — segmented arcade meter for risk used, discipline score, agent confidence, streaks. The Contra energy bar, and the reason no smooth progress bar exists here.
`value` · `max?` · `label?` · `segments?` (default 20) · `tone?: "phos"|"warn"|"danger"|"info"` · `showValue?`

### 6.5 `trading/`

**PnLValue** — signed result figure. Sign decides colour and glow; never hard-code P&L colours yourself.
`value: number|string` · `unit?` (default `"R"`) · `size?: "xs"–"xl"` · `showSign?` · `showArrow?` · `precision?` (default 2)

**TradeRow** — one trade in the journal table. 36px tall, hairline separated, 2px phosphor keyline when selected.
`time` (`"09:31"`) · `symbol` · `side?: "long"|"short"` · `size?` · `entry?` · `exit?` · `result: number` · `tags?: Array<string | {label, color?}>` · `status?` (`"open"` renders a live badge) · `selected?`

### 6.6 `agents/`

**AgentMessage** — one turn in an agent conversation. Agent turns render in the terminal face, user turns in core mono.
`author?: "agent"|"user"` · `name?` (defaults `"agent"`/`"you"`) · `model?` (e.g. `"risk-warden v2"`) · `time?` · `confidence?` (0–1, badge) · `streaming?` (appends blinking caret)

### 6.7 `gamepad/`

**GamepadKey** — controller glyph for binding hints. A/B/X/Y as coloured circles, d-pad as arrows, anything else (LB, RT, START) as a square shoulder key.
`button?` · `label?` (action beside the glyph) · `size?: "sm"|"md"|"lg"` · `pressed?` (fills, glows, nudges 1px)

### 6.8 Intentional additions

No source defined a component inventory, so the set is the standard one plus five brand-specific primitives the product cannot be shown without:

| Addition | Why |
|---|---|
| `Icon` | Centralises the substituted Lucide set so glyph delivery is swappable and recolourable |
| `StatTile` | Every journal view opens with a KPI row; otherwise each screen re-invents the metric cell |
| `MeterBar` | The Contra energy bar; segmented risk / discipline / confidence, so no smooth progress bar is needed |
| `PnLValue` / `TradeRow` | P&L colour and sign rules must live in one place, and the journal table is the product's core object |
| `AgentMessage` | Agent output has its own typeface, prefix and colour rules; a generic chat bubble would break them |
| `GamepadKey` | Controller bindings are the shortcut vocabulary and appear on every screen |

Deliberately **not** built (no source, no current need): Avatar, Breadcrumb, Accordion, Pagination, DatePicker, table primitives beyond `TradeRow`.

---

## 7. UI KITS

**`ui_kits/app/`** — journal app click-through at 1360px: shell, journal, trade detail, agent console, pad bindings. Fixed sidebar (216px), top session HUD (44px), bottom pad-hint bar. See `ui_kits/app/README.md`.

**`ui_kits/site/`** — marketing site: landing with code-rain hero (`CodeRain.jsx`, ≤0.35 opacity), pricing. Sticky header at 86% black + 6px blur. See `ui_kits/site/README.md`.

Both kits reflow at narrow widths (transcript flex-weights, TradeRow prices stack entry/exit, StatTile values clip and scale), but the system is desktop-first. If mobile or an overlay HUD is a product surface, the component set changes.

---

## 8. FILE MANIFEST

```
styles.css              entry point consumers link — @import lines only
readme.md               narrative version of this document
design_system.md        this file — consolidated single-page spec
SKILL.md                Agent Skills wrapper
thumbnail.html          homepage tile

tokens/
  fonts.css             webfont imports
  colors.css            ramps + semantic aliases
  typography.css        families, sizes, weights, leading, tracking
  spacing.css           scale, control metrics, layout
  effects.css           radii, borders, glow, sprite shadow, veils, focus, z
  motion.css            durations, easings, keyframes

guidelines/             22 specimen cards
  colors: phosphor, blacks, arcade, neutrals, trading semantics, status, gamepad
  type:   display, core, terminal, HUD labels, numerals
  spacing: scale, control heights, in use
  brand:  wordmark, radii, borders, glow, veils, motion, surface stack

components/             19 primitives (.jsx + .d.ts + .prompt.md + group card)
  core/       Button IconButton Icon Card Badge Tag StatTile
  forms/      Input Select Checkbox Radio Switch
  navigation/ Tabs
  feedback/   Dialog Toast Tooltip MeterBar
  trading/    PnLValue TradeRow
  agents/     AgentMessage
  gamepad/    GamepadKey

ui_kits/
  app/        journal click-through
  site/       marketing site

assets/                 empty — no logos, illustrations or imagery were supplied
```

---

## 9. OPEN QUESTIONS

1. **Real font files, logo/mark, and repo or Figma access** — the single biggest upgrade to this system.
2. **Matrix vs. Contra prominence** — currently ~80/20 toward terminal. Say the word and arcade goes louder (chunkier pixels, brighter energy palette).
3. **Desktop-first confirmed?** — or are mobile / overlay HUD real product surfaces?
