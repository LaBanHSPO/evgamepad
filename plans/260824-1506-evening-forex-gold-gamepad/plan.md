---
title: "Evening Forex Gold Gamepad"
description: "Complete desktop game and journal: 8BitDo trades one cTrader demo account; preparation, execution, review, reports, and recovery stay off the order hot path."
status: pending
priority: P1
effort: 26d
tags: [feature, frontend, backend, api, experimental]
blockedBy: []
blocks: []
created: 2026-08-24
---

# Evening Forex Gold Gamepad

## Overview

Build a desktop Chrome web game: trade **forex/gold on a configurable cTrader demo** with an **8BitDo Ultimate 2 Wireless**. The client agent speaks WebSocket to a **gateway on an Ubuntu VPS (Docker)**. That gateway’s only broker is **cTrader Open API** (Spotware). A near-realtime **AI desk** (sentinel, news, Volman M5, research / plan / advise / monitor) stays off the order path. **No paper matcher. No MT5. No Windows terminal.**

On top of the game sits a **complete daily trading journal** built for one focused player: prepare
with readiness, analysis, news and position sizing; grade and narrate the session; replay and review
each trade; inspect process-first heatmaps, history, mistakes and Actual vs Plan; then export a
report or back up and restore the record. The journal borrows the useful ideas from Edgewonk and
TradeZella without becoming a multi-account SaaS product. None of its AI, voice, analytics, or data
tools can place, close, or modify an order.

## Brainstorm contract

- **Outcome:** One uninterrupted loop on a single IC Markets cTrader demo account: first run ->
  prepare -> gamepad trade with planned protection -> close/settle -> daily review -> history/report
  -> backup/restore. **The end goal is confidence and enjoyment — improving decision quality, not
  the money.** Every evening leaves a reviewable record graded against the player's playbook,
  narrated in their voice, replayable bar by bar, scored on process, and owned by the player.
<!-- Updated: Validation Session 4 - journal layer added -->
<!-- Updated: Validation Session 3 - end goal restated as confidence and enjoyment -->
- **Constraints:** Ubuntu VPS + Docker. cTrader Open API only. One IC Markets demo account
  (boot-fail on live). Existing TLS on 443. 8BitDo Ultimate 2. Desktop Chrome, dark theme only.
  `Asia/Ho_Chi_Minh` 18:00–23:30. SpaceXAI copilot server-side. Entertainment, not alpha.
- **Non-goals:** Paper simulator. MT5 or broker-history import. Pending orders or partial closes.
  Multiple accounts/markets, mobile delivery, light mode, catalog administration, Wine, live money,
  multiplayer/SaaS/copy-trading, native HID helper, auto-trading AI, scraping Supercharts,
  guaranteed profit, gamified streak/level/badge pressure, Edgewonk what-if simulation, cloud STT,
  voice or AI on the order path, voice navigation, or a third compose service.
- **Acceptance:** See Success Criteria.

## Scope Challenge

- Existing code: empty repo; previous plan assumed paper then MT5 — **superseded**.
- Requested scope: replan onto cTrader + Ubuntu Docker; keep gamepad, protocol, AI desk, TV VIP.
- Complexity: 14 phases spanning broker execution, controller UX, local voice, deterministic
  analytics, journal operations, and a real target-environment release gate.
- Selected mode: **HOLD FOCUSED SCOPE** — deliver the full game+journal experience, but only for one
  cTrader demo account on desktop dark mode. User explicitly selected this boundary.

## Decisions (locked)

| Decision | Choice | Why |
|----------|--------|-----|
| Execution | **cTrader Open API** on `demo.ctraderapi.com:5035` (Protobuf) | User: no paper, no MT5. Linux-native. |
| Host | Ubuntu VPS, **Docker Compose** | User. Exec has no published ports. |
| Live | **Refuse** | Entertainment. Boot-fail if live host or `isLive`. |
| Pad | 8BitDo Ultimate 2, default LT/RT | Unchanged. |
| Client-agent | In-tab pad FSM; Chrome focused | Unchanged. |
| Transport | WSS JSON `{v,t,seq,ts,ch,cid,p}` | Unchanged. |
| Bind | Gateway `127.0.0.1:8444`; existing VPS TLS :443 | Unchanged. |
| Timezone | `Asia/Ho_Chi_Minh` 18:00–23:30 | Validated. |
| Symbols | XAUUSD, EURUSD, GBPUSD, USDJPY | Validated. Size: $10k feel is **cTrader demo balance**, max 0.10 lot gold still a **risk gate**. |
| AI desk | Sentinel + news + Volman + copilot child | Unchanged. |
| TradingView VIP | Dual-screen + Pine webhook signals | Unchanged. Never auto-trade. |
| End goal | **Confidence + enjoyment**, not P/L | User. Steenbarger: outcome anxiety pulls attention off process. |
| Deck priority | **Process first**, outcome behind a click | Validated. Money never on the default view. |
| Deck data | Session equity snapshots **and** closed-trade rows | Validated. Sharpe needs a time series; R-multiple needs per-trade. |
| Flatten | Panic-on-disconnect off; HUD Flatten | Unchanged. |
| Pad link | **2.4G dongle** primary; wired USB fallback | Validated. BT on the Ultimate 2 needs macOS 26; this Mac is 15.6. |
| Copilot process | **Node child forked by `ev-gateway`** | Validated. Not a third container; phase 4 files already live in `apps/gateway/src/copilot/`. |
| Broker | **IC Markets** cTrader demo | Validated. Plain XAUUSD/EURUSD/GBPUSD/USDJPY, no suffix handling. |
| Web serving | Gateway serves `dist` at `/`, socket at `/ws` | Validated. Single origin makes CSP + Origin allowlist trivially true. |
| OAuth | Manual consent once → paste into `.env`; exec refreshes | Validated. No auth helper in v1. |
| Images | Dockerfiles land in phase 1 | Validated. Compose had three services and zero build files. |
| Journal layer | **Playbook + grading, voice memos, trade replay, tilt-meter, process score** | User: inherit the best of Edgewonk and TradeZella. What-if simulator cut. |
| Voice role | **Journal memos + ask-the-coach only** | Never navigation, never execution. Enforced by a binding boot-fail, not convention. |
| Speech-to-text | **Browser capture -> whisper.cpp on the VPS** | Audio never leaves the box. No cloud STT code path exists to misconfigure. |
| STT process | **`spawn` child of `ev-gateway`**, `nice` + `taskset` + concurrency 1 | VPS is 4+ vCPU / 4 GB+. Compose stays at two services, same reasoning as the copilot child. |
| Coach TTS | Browser `speechSynthesis`, **default off** | VPS CPU is the scarce resource; the text is already on screen. Piper is a documented drop-in. |
| Game layer | **One process-weighted score**, five process-only axes | Standing down raises it. No streaks, no levels, no cross-session accumulator. |
| Rule definitions | **One registry, two consequences** | `risk` rules are enforced; `playbook` rules are graded and can never block a fire. |
| Tilt | Safety mechanism, **never a score input**; opens only | Taxing the evening for a bad ten minutes would reintroduce the punishment being treated. |
| Product boundary | **One focused IC Markets cTrader demo account** | Complete experience beats breadth; no multi-account/multi-market administration in this plan. |
| Order lifecycle | MARKET with **relative SL/TP**; absolute SL/TP amendments; full close/panic | Matches cTrader contracts. No pending orders or partial closes. |
| Navigation | `Menu` opens a **safe GameOverlay** | One deterministic route to desk, playbook, journal, reports, system, and settings; opening cancels ARM and locks new opens, while dedicated close/panic exits remain. |
| Daily journal | Readiness, analysis, calculator, heatmap/history, Actual vs Plan, execution scores, mistakes, principles | User chose the full focused cockpit rather than a lightweight memo layer. |
| Data ownership | CSV + JSON + browser PDF + manifested backup/restore/delete | Complete local data lifecycle; no broker/MT5 history import. |
| Presentation | **Desktop Chrome, dark-only** | Explicit v1 scope; no mobile or light-mode commitment. |
| Schema evolution | **Phase-owned migrations `001`–`010`** | Prevent duplicate table ownership and allow fresh/upgrade/restore verification. |

## Architecture

```text
  8BitDo Ultimate 2 --2.4G--> Mac Chrome (focused, desktop dark UI)
                               pad FSM + HUD + copilot desk
                               |
                          WSS TLS  existing :443
                               |
  Ubuntu VPS  docker compose
    ev-gateway   127.0.0.1:8444   risk, cid UNIQUE, journal, HUD build at /, socket at /ws
       ├─ copilot child process   (no order tools)
       └─ whisper.cpp child       (batch, nice + taskset, concurrency 1, no order tools)
    ev-exec      Python OpenApiPy
         |  Protobuf TCP 5035  (no published container port)
         v
    demo.ctraderapi.com     cTrader demo account
```

**Hot path:** pad → intent `{clutch, armedAt, relativeSl?, relativeTp?}` → WSS → cid reserve → risk
→ MARKET `ProtoOANewOrderReq` → execution event → ack → rumble. Existing-position SL/TP edits use
`ProtoOAAmendPositionSLTPReq` after a new LT+RT confirmation.
**Cold path:** sentinel 1–5s. Copilot 1–30s. TV webhook → `signal.item` only.  
**Journal path (colder still, never on the order socket):** readiness/analysis + plan snapshot ->
trade facts/events -> voice memo -> tape freeze -> score -> daily review/heatmap/history -> report or
backup. HTTP owns journal/media/data operations. The score becomes final only after close-time jobs
settle.

Spotware, not the VPS building, is the matching engine. Docker on Ubuntu does **not** buy Equinix-to-broker nanoseconds; it buys always-on exec without Windows.

## Latency budget (honest)

| Segment | Target |
|---------|--------|
| Pad poll → intent | <16 ms |
| Home → VPS WS | 15–80 ms (dominant) |
| Gateway risk | <5 ms |
| VPS → Spotware demo ack | tens of ms typical; not colocated MT5 |
| AI advice | 1–5 s, never blocks fire |

## Goals

| # | Goal | Priority |
|---|------|----------|
| 1 | Protocol + config + Docker skeleton; cTrader secrets; demo-only boot | P1 |
| 2 | `ev-exec` + gateway: spots, M5 bars, MARKET open with relative SL/TP, amend protection, full close/panic on **cTrader demo** | P1 |
| 3 | 8BitDo HUD against live cTrader quotes | P1 |
| 4 | AI desk + TV webhooks | P1 |
| 5 | Compose on Ubuntu behind existing TLS | P1 |
| 6 | Performance deck: adherence, declined trades, month-over-month improvement | P1 |
| 7 | Playbook + rule registry: every fire graded against its own rules, before it fires | P1 |
| 8 | Voice: push-to-talk memos and ask-the-coach, transcribed locally | P1 |
| 9 | Tilt-meter from pad telemetry, with friction on opens only | P1 |
| 10 | Trade replay: scrub the tape, see MFE/MAE, hear the memo | P1 |
| 11 | Process Score: five process-only axes where standing down scores well | P1 |
| 12 | Daily journal cockpit: preparation, heatmap/history, Actual vs Plan, execution quality, mistakes, system principles | P1 |
| 13 | Reports/settings/data ownership: browser PDF, CSV/JSON, backup/restore/delete | P1 |
| 14 | End-to-end first-run-to-recovery release gate on real demo infrastructure and target hardware | P1 |

## Phases

| # | Phase | Status |
|---|-------|--------|
| 1 | [Repo, protocol, Docker config](./phase-01-repo-protocol-docker-config.md) | Pending |
| 2 | [cTrader exec and socket gateway](./phase-02-ctrader-exec-and-socket-gateway.md) | Pending |
| 3 | [Web game and 8BitDo client agent](./phase-03-web-game-and-8bitdo-client-agent.md) | Pending |
| 4 | [AI desk: sentinel, news, Volman, research / plan / advise](./phase-04-ai-desk-sentinel-news-volman.md) | Pending |
| 5 | [Ubuntu Docker deploy](./phase-05-ubuntu-docker-deploy.md) | Pending |
| 6 | [Performance and psychology deck](./phase-06-performance-and-psychology-deck.md) | Pending |
| 7 | [Playbook, rule registry, and trade grading](./phase-07-playbook-and-trade-grading.md) | Pending |
| 8 | [Voice: capture, upload, whisper.cpp, coach TTS](./phase-08-voice-capture-whisper-and-coach.md) | Pending |
| 9 | [Tilt telemetry and adaptive friction](./phase-09-tilt-telemetry-and-adaptive-friction.md) | Pending |
| 10 | [Trade replay](./phase-10-trade-replay.md) | Pending |
| 11 | [Process Score and radar deck](./phase-11-process-score-and-radar-deck.md) | Pending |
| 12 | [Daily journal cockpit and preparation](./phase-12-daily-journal-cockpit-and-preparation.md) | Pending |
| 13 | [Reports, settings, and data portability](./phase-13-reports-settings-and-data-portability.md) | Pending |
| 14 | [End-to-end session journey and release gate](./phase-14-end-to-end-session-journey-and-release-gate.md) | Pending |

**Recommended delivery order:** `1 -> 2 -> ... -> 14`. Phase frontmatter records the minimum direct
dependencies, but acceptance proceeds sequentially because migrations `001`–`010`, overlay
contracts, and release evidence build on one another. No early phase requires a later phase to close.

```
1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13 → 14
```

Total: **203h ≈ 26 working days** before empirical blockers or deployment lead time.

## Research

- [Client / gamepad / socket](./research/researcher-01-client-gamepad-socket.md)
- [VPS / broker / AI](./research/researcher-02-vps-broker-ai.md) — MT5/paper ranking **superseded**
- [Copilot desk](./research/researcher-03-copilot-volman-news-sentinel.md)
- [TradingView VIP](./research/researcher-04-tradingview-vip.md)
- [cTrader Docker](./research/researcher-05-ctrader-docker.md)

## Success Criteria

- [ ] 8BitDo clutch+confirm opens a **cTrader demo** MARKET position with relative SL/TP, amends
      absolute position SL/TP, fully closes, and panics; fill rumbles; P/L comes from cTrader
- [ ] Quotes/candles are **Spotware spots + trendbars**, not a simulator
- [ ] Hidden tab / unplug locks **new** opens; evening window, max lot, max daily loss on the gateway
- [ ] Docker Compose on Ubuntu: gateway loopback, exec unpublished, existing :443 TLS
- [ ] Live host or live account → process **does not** trade
- [ ] Copilot desk + TV webhook signals; neither can `place`
- [ ] README: cTID OAuth, 8BitDo pair, dual-screen TV
- [ ] Chrome loads the HUD from the VPS origin (gateway-served `dist`), same origin as `/ws`
- [ ] `/deck` opens on the **process** panel; no dollar figure until a tab is clicked
- [ ] An evening with zero trades in a dead tape scores well, not badly
- [ ] Month-over-month deltas render for adherence, declined-rate, return %, and average R
- [ ] The ARM confirm overlay names the active playbook and its rule count **before** the fire
- [ ] A failing **playbook** rule lets the trade through; a failing **risk** rule still rejects it
- [ ] Holding `LB + RB` records a memo; releasing shows a transcript; tapping `LB` alone still only changes timeframe
- [ ] Killing `whisper-cli` mid-run leaves the audio stored, linked to the trade, and playable in replay
- [ ] `voice.stt.mode: cloud`, `voice.bindings: [RT]`, `tilt.gate_close: true` and mis-summed score weights each refuse to boot
- [ ] With tilt forced to 1.0, panic flatten still executes and `intent.close` is still accepted
- [ ] `/replay/:cid` paints entry, exit, MFE and MAE, shows a cancelled ARM on the event rail, and **cannot place an order**
- [ ] The dead-tape zero-trade evening scores **100** and a busy well-executed evening scores **98**
- [ ] `Menu` opens one safe GameOverlay; opening cancels ARM/locks new opens, navigation/apply emits
      no open/modify, dedicated close/panic still work, and an SL/TP apply still requires LT+RT
- [ ] `/journal/today` completes prepare -> trade -> close -> review with readiness, analysis,
      position sizing, DST-aware session clocks, heatmap/day detail, latest ten, history, and trade detail
- [ ] Actual vs Plan, four evidence-backed quality groups, before/during/after scores, mistake
      taxonomy/trends, and personal principles are deterministic and auditable
- [ ] Browser PDF, streamed CSV/JSON, manifested backup/restore, and explicit delete-all work without
      exporting secrets; no trade-history import endpoint exists
- [ ] The real target-hardware journey proves first run -> preparation -> demo execution ->
      settle/review -> report/export -> disposable restore/delete, with failure evidence recorded
- [ ] Nothing in the schema accumulates across sessions — no streak, no level, no "days since"

## Open questions

- Exact public origin hostname (phase 5 inspect).
- Panic-on-disconnect flatten stays **off**.
- `score.trades_max: 6` and the ±1 Selectivity band are **uncalibrated** for this player. `session_score`
  stores its axis inputs, so the first month is provisional and recalibrates retroactively.
- Voice arousal (5% of tilt) is the weakest component. If a month of data does not support it against
  the player's own baseline, **delete it rather than defend it**.
- `voice.hold_stream: true` keeps the tab's recording indicator lit all evening in exchange for
  200-400 ms lower PTT latency. Toggle exists; decide before phase 8 ships.

## Replan note — 2026-08-24

User reversed paper-first and MT5. **Source of truth is this file + phases after this note.** Ignore older “PaperAdapter / Mt5Adapter / GBM” prose in journals.

## Validation Log

### Session 2 — 2026-08-24

**Trigger:** `/ak:plan validate plans/260824-1506-evening-forex-gold-gamepad` after the cTrader replan.
**Questions asked:** 7

#### Verification Results

- Claims checked: 22
- Verified: 16 | Failed: 6 | Unverified: 0
- Tier: Full (5 phases)
- `ak plan validate --json` → `valid: true` (format was never the problem)
- Failures:
  - `phase-02:31` — `ProtoOASymbolsListReq` claimed to carry min/step volume. Spotware docs: it returns `ProtoOALightSymbol` (`symbolId, symbolName, enabled, baseAssetId, quoteAssetId, symbolCategoryId, description, sortingNumber`); `minVolume/stepVolume/maxVolume/digits/pipPosition` require `ProtoOASymbolByIdReq` → `ProtoOASymbol`. `phase-01:104` already said `ProtoOASymbol`, so the two phases contradicted each other.
  - `phase-03:87` — "Mac pairing: **Bluetooth**" is not supported on this hardware. 8BitDo's Apple support for the Ultimate 2 Wireless requires macOS 26+; this machine is Darwin 24.6 → macOS 15.6.
  - `plan.md:60` + `phase-05:39` vs `phase-04:22,88` vs `phase-01:109` — `ev-copilot` described three ways: compose service, gateway child, and absent from the compose skeleton.
  - all phases — no Dockerfile created anywhere, yet `phase-01` asserts `docker compose config` and `phase-05` runs `compose up -d` on three images.
  - `phase-05:39` — `:443 /` proxied to the gateway, but nothing in any phase serves the built Vite/Svelte SPA.
  - `phase-01:110` vs `phase-01:25` — `packages/exec/src/sidecar-protocol.ts` created under a workspace package the requirements never declared.

#### Questions & Answers

1. **[Risks]** Verification found the 8BitDo Ultimate 2 Wireless only gained official Apple/Bluetooth support on macOS 26+; this Mac is Darwin 24.6 (macOS 15.6). Phase 3 currently says "Mac pairing: Bluetooth". What is the primary connection path?
   - Options: 2.4G dongle primary (Recommended) | Wired USB primary | Bluetooth + upgrade Mac to macOS 26
   - **Answer:** 2.4G dongle primary
   - **Rationale:** The dongle presents an XInput-class pad, so `mapping: "standard"` holds and the existing LT/RT map table survives untouched. Wired USB is the documented fallback; no OS upgrade becomes a phase 3 prerequisite.

2. **[Architecture]** `ev-copilot` is described three ways: plan.md architecture and phase 5's diagram show it as a compose service; phase 4 says "ev-copilot child" and puts every file under `apps/gateway/src/copilot/`; phase 1's compose skeleton defines only gateway + exec. Which is real?
   - Options: Node child of ev-gateway (Recommended) | Third compose service | Child now, service later
   - **Answer:** Node child of ev-gateway
   - **Rationale:** Matches phase 4's file layout and wording, keeps compose at two services, and one fewer image to build. Hot-path isolation is enforced by `copilot.on_hot_path: false` and the read-only tool allowlist, not by a container.

3. **[Assumptions]** No phase creates a Dockerfile — not in phase 1's file list, not in phase 5's. Yet phase 1's success criterion is `docker compose config` and phase 5 runs `compose up -d` with three images. Where do build files land?
   - Options: Dockerfiles in phase 1 (Recommended) | Dockerfiles in phase 5 | Bind-mount dev, images in phase 5
   - **Answer:** Dockerfiles in phase 1
   - **Rationale:** Phase 1 already owns `compose.yaml`; the skeleton is not validatable without real build contexts. `tini` in the exec image also pre-answers phase 2's Twisted/SIGTERM risk.

4. **[Architecture]** Phase 5 proxies existing :443 `/` or `/ws` to the gateway, but no phase makes anything serve the built Svelte SPA. `apps/web` is a Vite app with no production serving story. Who serves it?
   - Options: Gateway serves static build (Recommended) | Vite dev server on the Mac | Separate static container
   - **Answer:** Gateway serves static build
   - **Rationale:** One origin for HUD and socket, so phase 3's `default-src 'self'` CSP and phase 2's Origin allowlist become trivially true and the memory-only WS token has one home. Dev keeps a Vite server with `/ws` proxied.

5. **[Risks]** Phase 2 says "persist/refresh OAuth token" and phase 1 says "README: OAuth outline" — but no phase implements getting the *first* token. cTrader Open API needs an authorization-code round-trip in a browser against a registered redirect URI. How is the initial token obtained?
   - Options: Manual once, paste into .env (Recommended) | Small CLI helper in phase 1 | Helper in phase 2 with the exec work
   - **Answer:** Manual once, paste into .env
   - **Rationale:** Zero auth code ships. `ev-exec` refreshes only, and boot-fails with a README pointer when `CT_REFRESH_TOKEN` is missing rather than half-starting.

6. **[Scope]** plan.md lists the cTrader broker as an open question and calls it "only needed for symbol suffixes". It's stronger than that: the Open API app, the demo account, and the token all hang off a specific broker under one cTrader ID — phase 2 cannot connect without it. How do we resolve it?
   - Options: Mark it a phase 2 entry blocker (Recommended) | I'll name the broker now | Leave as an open question
   - **Answer:** I'll name the broker now

7. **[Scope]** Which broker holds the cTrader demo account?
   - Options: Pepperstone | IC Markets | FxPro | Not opened yet
   - **Answer:** IC Markets
   - **Rationale:** Symbols are plain and unsuffixed, so no suffix handling is needed. Tight demo spreads make the `max_spread: 0.80` gold gate realistic rather than decorative. Phase 2 gains a prerequisite checklist instead of an open question.

#### Confirmed Decisions

- Pad link: 2.4G dongle primary, wired USB fallback, BT documented as macOS 26+ only
- Copilot: Node child forked by `ev-gateway`; compose stays two services
- Images: Dockerfiles for gateway, exec (+`tini`), and the web build stage land in phase 1
- Web serving: gateway serves `apps/web/dist` at `/`, socket at `/ws`, single origin
- OAuth: manual consent once → `.env`; exec refreshes only
- Broker: IC Markets cTrader demo, unsuffixed symbols
- Corrections: `SymbolByIdReq` supplies volume specs; `packages/exec` declared in the workspace

#### Impact on Phases

- **Phase 1:** `packages/exec` declared; three Dockerfiles added; `static_dir`/`ws_path` in the config sketch; build step inserted (steps renumbered to 6); success criteria now include `docker compose build`; README credential walkthrough added; effort 6h → 8h.
- **Phase 2:** Prerequisites block added (cTrader ID, IC Markets demo, approved Open API app, populated `.env`, captured fixtures); symbol requirement split into `SymbolsListReq` (ids) + `SymbolByIdReq` (volume/digits); transport pinned to TCP 5035; OAuth reworded to refresh-only; volume-fixture success criterion added.
- **Phase 3:** Mac link paragraph rewritten to dongle-primary; dongle-enumerates-non-standard risk added; dev/prod origin note added; README todo reworded.
- **Phase 4:** Copilot restated as a child forked by `ev-gateway`; enforcement is the `on_hot_path` boot-fail and the tool allowlist. No file moves.
- **Phase 5:** `ev-copilot` branch removed from the diagram; gateway serves `dist` at `/` and `/ws`; web build baked into the gateway image; same-origin success criterion added; effort 6h → 7h.

#### Whole-Plan Consistency Sweep

Re-read `plan.md` and all five phase files after propagation.

- `ev-copilot` as a compose service or third container: **0 remaining** (phase 4 child wording and the research file's "Node child or third service" note are the only mentions; the research file is a dated input, not authority)
- `SymbolsListReq` claimed to carry volume specs: **0 remaining**
- Bluetooth as the primary Mac pad link: **0 remaining**
- Every compose service has a Dockerfile in phase 1's file list: **yes** (gateway, exec, web build stage)
- Broker: IC Markets everywhere; the "which broker" open question is deleted
- Same-origin serving agrees across plan.md decisions, phase 3 requirements, and phase 5 requirements/criteria

Three stale spots the first propagation pass missed, found by the sweep and fixed:

- `phase-01` risk said "convert only after `SymbolsList`" → now `SymbolById`
- `phase-03` manual test matrix step 8 said "Bluetooth 8BitDo on Mac Chrome" → now dongle, wired repeat
- `phase-05` runbook said "Chrome, Bluetooth, TV" → now "Chrome, pad dongle, TV"

**Unresolved contradictions: none.**

### Session 3 — 2026-08-24 (scope addition)

**Trigger:** Mid-session user message — the end goal of the game is **confidence and enjoyment, not profit**; apply Brett Steenbarger's trading psychology (performance domains; outcome anxiety pulling focus off process; process noise degrading decisions; markets not offering equal opportunity every night) and ship a dashboard showing month-over-month improvement in return rate, profit/risk ratio, and a Sharpe / risk-adjusted measure.
**Questions asked:** 3

#### Questions & Answers

1. **[Scope]** Where should the psychology + improvement layer live in the plan?
   - Options: New phase 6 (Recommended) | Fold into phase 4 | Split: HUD cues in phase 3, dashboard in phase 6
   - **Answer:** Split — HUD process cues in phase 3, dashboard in phase 6
   - **Rationale:** In-session nudges belong where the player is looking (HUD); multi-month statistics need their own surface and cannot be computed until several evenings exist. Costs edits across three phases instead of one.

2. **[Architecture]** Steenbarger's point is that outcome anxiety costs process focus. Which metrics does the dashboard lead with?
   - Options: Process first, outcome second (Recommended) | Both side by side | Outcome first (Sharpe, return, R/R)
   - **Answer:** Process first, outcome second
   - **Rationale:** Default view is adherence, declined trades, opportunity quality, and check-in. Money sits behind a deliberate tab click and never appears in a notification. This also pushed the HUD's open P/L to **R-first with a dollar toggle** — flagged as an inference from this answer, easy to veto.

3. **[Architecture]** Sharpe and return rate need a periodic return series; nothing currently stores equity over time. Where does the data come from?
   - Options: Session equity snapshots (Recommended) | Compute from closed trades | Both
   - **Answer:** Both
   - **Rationale:** Session equity open/close from the cTrader account gives an honest per-evening return series for Sharpe and return %; a `trade_closed` table gives R-multiple, profit factor, and per-Volman-setup breakdowns. Adds a third table and roughly 3-4h.

#### Confirmed Decisions

- End goal restated in the brainstorm contract: confidence and enjoyment, improving decision quality
- New **phase 6 — Performance and psychology deck** (P1, 14h, depends on 2/3/5)
- Deck is process-first; outcome behind a tab; no leaderboards, no streaks, nothing that punishes standing down
- Journal gains `session_equity`, `trade_closed`, `session_process`
- Risk rules are exported from phase 2 so the deck scores exactly what the gateway enforced
- Sharpe renders a "not enough sessions yet" state below 30 sessions rather than a confident number from ~20 samples

#### Impact on Phases

- **Phase 2:** journal records session equity snapshots and closed-trade rows; risk rule set exported rather than private; new todo and success item.
- **Phase 3:** adherence badge, stood-down counter, opportunity-quality state, pad check-in; open P/L now R-first with a dollar toggle; HUD description and success criteria updated.
- **Phase 4:** copilot method profile gains a process-over-outcome coaching stance; sentinel publishes an opportunity-quality state consumed by both HUD and deck.
- **Phase 6 (new):** the deck itself — schema, pure metric functions, `/api/deck/*`, `/deck` route, copilot `get_progress` read-only tool.
- **plan.md:** Outcome line, four decision rows, goal 6, phase 6 row, four success criteria, non-goals extended, effort 6d → 8d.

#### Whole-Plan Consistency Sweep

- Money-first framing in the HUD ("fat P/L"): **removed**, now R-first with a toggle
- Phase 6 linked from Goals, Phases table, and Success Criteria: **yes**
- Deck adherence rules and gateway risk rules: one shared definition, stated in both phases
- Effort reconciled: 8+12+12+16+7+14 = 69h ≈ 8d
- `ak plan validate` → `valid: true`; `ak plan status` → 0/6 phases, 92 tasks

**Unresolved contradictions: none.**

### Session 4 — 2026-08-25 (scope addition: trading journal layer)

**Trigger:** `/ak:brainstorm` — "refer Edgewonk, Tradezella, i want my product inherit best features
about Trading journal app, focus on AI + user voice + better UX for trader like a game experience
with gamepad".
**Questions asked:** 6

#### Questions & Answers

1. **[Scope]** What should the voice channel actually do in the game?
   - Options: Journal memos only | Journal + ask the coach (Recommended) | Journal + coach + navigation | Voice can also place trades
   - **Answer:** Journal + ask the coach
   - **Rationale:** Voice solves the real problem (you cannot type while trading) and is the natural
     input for the copilot that already exists. Navigation would put a probabilistic transcriber on
     state changes; execution would put it on the order path, which the plan already forbids for the
     AI. Enforced by a `voice.bindings` boot-fail and by PTT being enterable only from `IDLE`/`LOCKED`.

2. **[Architecture]** Where does speech-to-text run, and does the coach talk back?
   - Options: Browser Web Speech API | Record in browser -> Whisper on the VPS (Recommended) | Cloud STT + TTS API | Text-first now, voice later
   - **Answer:** Record in browser -> Whisper on the VPS
   - **Rationale:** Audio never leaves the box, no per-word cost, and jargon accuracy is tunable with a
     prompt-bias list. `voice.stt.mode` boot-fails outside `{local, off}` so there is no cloud path to
     misconfigure. TTS is browser `speechSynthesis`, default off — VPS CPU is the scarce resource.

3. **[Architecture]** How gamified should the scoring be, given the plan bans streaks and leaderboards?
   - Options: Process-weighted score, no streaks (Recommended) | Full arcade XP/levels/badges/streaks | No score at all | Score + cosmetic unlocks
   - **Answer:** Process-weighted score, no streaks
   - **Rationale:** Five process-only axes; win rate and profit factor are deliberately excluded.
     Vacuous axes are dropped and renormalised rather than scored zero, so a zero-trade dead-tape
     evening scores 100 against a busy well-executed evening's 98. Streak mechanics would create
     pressure to trade a dead tape — the exact behaviour this plan exists to prevent.

4. **[Scope]** Which Edgewonk/TradeZella features should be inherited?
   - Options (multi-select): Playbook + rule adherence | Trade replay | Tilt-meter from pad telemetry | Efficiency + what-if simulator
   - **Answer:** Playbook + rule adherence, Trade replay, Tilt-meter from pad telemetry
   - **Rationale:** The what-if simulator is cut. MFE/MAE and efficiency survive anyway as a byproduct
     of the tape the replay needs, so they land in `trade_closed` without the simulator's scope.

5. **[Scope]** How should ~17h of amendments plus ~56h of new work be sequenced?
   - Options: Amend now, build game first (Recommended) | Pull playbook forward | Straight through 1->11 | Amendments only for now
   - **Answer:** Amend now, build game first
   - **Rationale:** Protocol v1 freezes in phase 1 and the journal schema lands in phase 2, so capture
     must exist from day one or phases 7-11 become migrations. Building 1->6 first puts real evenings
     on the board by roughly day 9 while the data for the journal is already being recorded.

6. **[Risks]** VPS specs, which decide the whisper tier and the two-service question?
   - Options: 4+ vCPU / 4GB+ | 2-3 vCPU | 1 vCPU | Not sure, probe it
   - **Answer:** 4+ vCPU, 4GB+ RAM
   - **Rationale:** `small.en` as a gateway subprocess with `taskset` pinning off core 0, concurrency 1,
     and a 60 s kill. Compose stays at two services. On 1 vCPU this would have needed a third service
     with a hard `cpus` quota, since `nice` alone cannot protect the order path on a single core.

#### Confirmed Decisions

- Journal layer: playbook + grading, voice memos, trade replay, tilt-meter, process score
- Voice is memos + ask-the-coach only; never navigation, never execution
- Local whisper.cpp as a gateway child; compose stays two services; no cloud STT path exists
- One rule registry, two consequences: `risk` rules enforced, `playbook` rules graded and never blocking
- Tilt is a safety mechanism, excluded from the score, and can only add friction to `intent.open`
- R is defined **once** in phase 2 — phase 6 required `r_multiple` but no phase had ever defined it
- Five new phases (7-11); effort 8d -> 18d

#### Impact on Phases

> Historical state after Session 4. Session 5 supersedes the day-one full-schema assumption,
> Menu shortcuts, phase-local acceptance dependencies, efforts, and the 11-phase total below.

- **Phase 1 (8h -> 11h):** `voice` channel added to the frozen catalog; six client and six server
  message types; HTTP surfaces declared; `voice`/`tape`/`tilt`/`score`/`playbook` config blocks plus
  `risk.r_unit_usd` and `risk.default_stop`; four new boot-fails; `ffmpeg` + `whisper-cli` + baked
  `tiny.en` in the gateway image; `deploy/fetch-models.sh`.
- **Phase 2 (12h -> 17h):** the single R definition; full journal schema on day one; 1 Hz bid+ask tape
  ring tapped pre-conflation; per-trade freeze with MFE/MAE on the correct side of the book;
  `cooldown` reject reason reserved with close/panic asserted exempt.
- **Phase 3 (12h -> 16h):** FSM telemetry fields at 1 Hz; `LB + RB` chord PTT with bumpers moving to
  fire-on-release; `Menu + D-pad U/D` playbook cycle; `[Memo]` desk tab routing by active tab; live
  grade in the confirm overlay; `confirmHoldMs` as a fire-predicate parameter; tilt pip.
- **Phase 4 (16h -> 18h):** opportunity quality becomes a number, not only a label; four new read-only
  tools; `ai.ask kind=coach`; `speak` field for TTS; transcripts are untrusted user content.
- **Phase 6 (14h -> 17h):** Process Score radar, per-playbook stats, and the tilt retrospective land on
  the process panel.
- **Phases 7-11 (new):** playbook and grading (12h), voice (14h), tilt (10h), replay (12h), score (8h).

#### Whole-Plan Consistency Sweep

Re-read `plan.md` and all eleven phase files after propagation.

- Channel list missing `voice`: **0 remaining**
- Compose described as three services or with an `ev-stt` / `ev-voice` service: **0 remaining**
- A second definition of R: **0 remaining** (phase 2 owns it; every consumer imports)
- Streak / leaderboard / level as a mechanic: **0 remaining** (only in non-goals and risk mitigations)
- Every phase 7-11 dependency resolves to an existing phase: **yes**
- Effort reconciled: 11+17+16+18+7+17 (amended 1-6) + 12+14+10+12+8 (new 7-11) = 142h ≈ 18d

**Unresolved contradictions: none.**

### Session 5 — 2026-08-26 (complete game + journal coverage validation)

**Trigger:** Validate the current plan against a complete end-to-end game experience and the
user-supplied trading-journal research based on Pham Duy Dinh's web app walkthrough.
**Questions asked:** 7

#### Verification Results

- **Initial tier:** Full (11 phases); validated target after scope decisions: 14 phases
- **Claims checked:** 165 (15 per phase across facts, contracts, flow, scope, dependencies, and
  success criteria)
- **Verified:** 142 | **Failed:** 13 | **Unverified:** 10
- `ak plan validate plans/260824-1506-evening-forex-gold-gamepad --json --no-interactive` ->
  `valid: true`; this confirms file shape only, not product completeness or contract correctness.
- The repository contains plans and research but no implementation code, so planned file paths were
  checked for ownership and consistency; runtime symbol/caller verification is not yet possible.

#### Verified external contracts

- cTrader still exposes demo Protobuf on `demo.ctraderapi.com:5035`; non-historical requests are
  capped at 50/s and historical requests at 5/s per connection.
- `ProtoOASymbol` owns `minVolume`, `stepVolume`, `maxVolume`, `digits`, `pipPosition`, and
  `lotSize`; the prior `SymbolsList` -> `SymbolById` correction remains valid.
- xAI `web_search.allowed_domains` remains capped at five domains.
- whisper.cpp currently ships `whisper-cli`; `tiny.en`, `base.en`, and `small.en` are approximately
  75 MiB, 142 MiB, and 466 MiB respectively.
- The Ultimate 2 Wireless Apple Bluetooth path requires macOS 26; keeping the 2.4G dongle as the
  primary path remains consistent with this Mac's recorded macOS 15.6 constraint.

#### Failed checks requiring correction or a product decision

1. **Stale architecture:** `plan.md` still draws `8BitDo --BT--> Mac` despite the locked 2.4G
   decision and the earlier log claiming zero Bluetooth references remained.
2. **Controller conflict:** phase 3 assigns `Menu` to Settings while phase 4 assigns `Menu tap` to
   tab cycling; `Menu + D-pad` is also the playbook picker. One deterministic navigation contract is
   required.
3. **Desk count conflict:** phase 3/8 require five tabs including `[Memo]`; phase 4 still specifies
   and implements four tabs.
4. **Phase 3 cannot close as written:** its success criteria require a live phase 7 playbook grade
   before phase 7 exists.
5. **Phase 5 cannot close as written:** it requires whisper tier selection and working fallback
   voice before phase 8 implements the benchmark and STT path.
6. **Phase 6 cannot close as written:** its todo/success criteria require phase 7 playbook stats,
   phase 9 tilt retrospective, and phase 11 radar before those phases exist.
7. **Phase 7 dependency is incomplete:** it seeds from phase 4 Volman detectors but declares only
   `[2, 3]`.
8. **Phase 11 dependencies are incomplete:** Review requires memos and a replay opened but omits
   phases 8 and 10.
9. **Schema ownership conflicts:** phase 2 claims the full journal schema is created on day one;
   phase 6 later creates the same three core tables in `deck/schema.sql`. One migration owner is
   required.
10. **MARKET SL/TP contract is incomplete:** cTrader does not support absolute `stopLoss` /
    `takeProfit` on `ProtoOANewOrderReq` MARKET orders; phase 2 must map the HUD plan to
    `relativeStopLoss` / `relativeTakeProfit`, then use `ProtoOAAmendPositionSLTPReq` for changes.
11. **`R_usd` is dimensionally wrong for USDJPY:**
    `lots * contract_size * abs(entry - stop)` produces quote-currency risk. It needs the cTrader
    quote-to-deposit conversion chain at entry before it can be named USD.
12. **Journal research coverage is partial:** no day heatmap/drill-down, recent-trades/history
    surface, multi-dimensional analysis, planned-vs-actual result, four trade-quality groups,
    mistake taxonomy/trend, daily analysis entry, position-size calculator, PDF export, or data
    backup/restore/delete flow.
13. **No whole-product completion gate:** the plan lacks an explicit first-run -> preflight -> live
    session -> close -> daily review -> history/data recovery journey and a hardware+broker+journal
    end-to-end test that proves it.

#### Questions & Answers

1. **Product breadth:** one focused account or a general multi-account/multi-market journal?
   - **Answer: 1A — one focused IC Markets cTrader demo account.**
2. **Daily journal:** lightweight review or full daily cockpit?
   - **Answer: 2A — full cockpit** with readiness, analysis, clocks, calculator, heatmap/history,
     execution-quality analysis, mistakes, and personal principles.
3. **Order lifecycle:** how much execution behaviour belongs in the complete game?
   - **Answer: 3A — MARKET orders with relative SL/TP, absolute position SL/TP amendment, full
     close and panic.** No pending orders or partial close.
4. **Controller navigation:** keep overlapping shortcuts or introduce one navigation surface?
   - **Answer: 4A — Menu opens a safe GameOverlay** that locks new opens; navigation/apply cannot
     emit open/modify, while dedicated close/panic exits remain available.
5. **Data ownership:** basic export or full lifecycle?
   - **Answer: 5A — CSV/JSON, browser PDF, backup, restore, and delete-all.** No trade-history import.
6. **Presentation:** responsive/light+dark or focused target?
   - **Answer: 6B — desktop Chrome, dark-only.**
7. **Plan structure:** rewrite existing phases or preserve them and extend?
   - **Answer: 7A — keep phases 1–11, correct them, and add phases 12–14.**

#### Confirmed Decisions

- Product boundary is one cTrader demo account, four configured FX/gold symbols, desktop dark-only.
- Execution supports MARKET open with relative protection, absolute position protection amendment,
  full close, and panic; pending/partial order flows are non-goals.
- Menu owns one safe overlay for desk/playbook/journal/system/reports/settings navigation.
- Journal coverage includes the complete focused daily cockpit and deterministic review analytics.
- Data ownership includes PDF/CSV/JSON plus manifested backup/restore/delete, but no import.
- Existing phases stay in place; additive migrations and phases 12–14 complete the experience.

#### Initial research coverage matrix

| Research area | Initial coverage | Gap found in the 11-phase plan |
|---|---|---|
| Dashboard and performance | Partial | Day heatmap/drill-down, recent trades, daily report, avg win/loss, consistency measure, explicit period filters |
| Trade quality and execution | Partial | Symbol/timeframe/side/session cuts, planned-vs-actual, before/during/after review, four quality groups, mistake trend |
| History and capture | Partial | Dedicated history/trade-detail UX and optional chart attachment; MT5 import conflicts with the cTrader-only boundary |
| Market preparation | Partial | Five-item readiness checklist, position-size calculator, durable daily analysis entry |
| Trading system | Strong partial | Playbook exists; personal philosophy/core-principles surface is missing |
| Reports and settings | Weak | PDF, backup/restore/delete, light theme, and UI-managed catalog settings are absent |
| Game loop | Strong live core | First-run/preflight/session-close navigation and one end-to-end completion gate are absent |

#### Unverified empirical claims

- IC Markets demo symbol names and actual `lotSize`/min/step values until the phase 2 fixture exists.
- 2.4G browser mapping and L4/R4 indices until the target controller probe runs.
- Home-to-VPS and broker-ack latency budgets until measured from the actual locations.
- whisper model RTF, 7-11 second memo latency, and <10 ms order-ack p99 impact until the VPS probe.
- Tape size estimates until real XAUUSD/FX tick density is captured.
- Defensible numeric opportunity-quality normalisation until calibrated on real sessions.
- Forex Factory weekly-feed reliability and terms in the deployed environment.

#### Propagation status

- All seven answers were propagated through `plan.md`, `README.md`, and phases 1–14.
- Phase-owned migrations now run `001` through `010`; duplicate day-one schema ownership is gone.
- cTrader MARKET protection, post-fill amendment, quote-to-USD R conversion, overlay safety, phase
  dependencies, and self-contained acceptance criteria were corrected.
- Phases 12–14 now own the daily journal cockpit, reports/settings/data portability, and full
  first-run-to-recovery release gate.
- Final whole-plan consistency sweep follows after mechanical validation below.

#### Impact on Phases

- **Phase 1 (11h -> 12h):** relative protection/position-amend contracts, expanded HTTP families,
  dark-only config, protected refreshed-token storage, and the migration runner/ledger.
- **Phase 2 (17h -> 22h):** `ProtoOASymbol.lotSize` + assets, relative MARKET SL/TP, absolute
  position amendment, full-close-only lifecycle, trade-plan/events, quote-to-USD R conversion, and
  `001-core-trading.sql`.
- **Phase 3 (16h -> 18h):** one safe GameOverlay, self-contained grade/voice placeholders,
  relative SL/TP/R preview, staged modify confirmation, check-in ownership, and
  `002-client-session.sql`.
- **Phase 4:** five-tab shell with four AI tabs + disabled Memo, overlay navigation, future tool
  stubs, and `003-copilot-signals.sql`.
- **Phase 5:** deployment acceptance stops at CPU/model evidence; phase 8 owns STT selection and
  runtime voice behaviour.
- **Phase 6 (17h -> 14h):** consumes phase 2/3 facts, owns only `004-deck.sql`, and closes without
  phase 7/9/11 surfaces.
- **Phases 7–11:** dependency fixes plus uniquely owned migrations `005`–`008`; phase 10 consumes
  the phase 2 tape without a redundant migration.
- **Phase 12 (new, 24h):** complete daily journal cockpit and deterministic learning surfaces.
- **Phase 13 (new, 18h):** safe settings, reports, export, backup/restore, and delete-all.
- **Phase 14 (new, 14h):** target-hardware and real-demo first-run-to-recovery release gate.
- **README:** controller/navigation, product boundaries, 14-phase index, efforts, and full journal
  journey now match the plan of record.

#### Whole-Plan Consistency Sweep

Re-read `plan.md`, `README.md`, and all 14 phase files after propagation.

- `ak plan validate ... --json --no-interactive`: **`valid: true`**.
- AgentKit file index: reindexed successfully with **14 phases**.
- Phase arithmetic: **14 phases, 203h ≈ 26 days**; no missing, forward, or cyclic dependency.
- Relative Markdown links checked across 16 authoritative Markdown files: **0 broken**.
- Versioned schema ownership: runner bootstraps its ledger; `001`–`010` each have one owner; phase
  10 intentionally reuses phase 2's tape tables.
- Canonical stale-contract scan: **0** BT architecture, competing Menu shortcuts, four-tab desk,
  day-one full schema, duplicate `deck/schema.sql`, old R formula, or phase-5 voice acceptance.
- All **13 initial failed checks are resolved in the plan**. The ten empirical claims remain
  honestly unverified and are explicit phase 2/5/8/14 evidence gates, not accepted assumptions.
- Intentional exclusions match the confirmed answers: multi-account/multi-market, mobile/light,
  pending/partial orders, history import, and a server PDF engine are outside this focused product.
- `git diff --check`: clean.

**Unresolved plan contradictions: none. Runtime validation remains future implementation work.**

<!-- slug: evening-forex-gold-gamepad -->
