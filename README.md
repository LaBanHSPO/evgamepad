# Evening Forex Gold Gamepad

![Trading Game — discipline, process, improvement](./visual01.png)

A desktop Chrome **web game** where an **8BitDo Ultimate 2 Wireless** trades forex and gold on a
**cTrader demo account**. The pad talks WebSocket to a gateway on an Ubuntu VPS (Docker); the only
broker adapter is the **cTrader Open API**. A near-realtime **AI desk** coaches from the sidelines and
never touches the order path.

On top of the game sits a **trading journal** that takes the best of Edgewonk and TradeZella and
rebuilds them for a gamepad: a **playbook** grades every fire against its own rules *before* you
commit, a **voice memo** captures why you took it because you cannot type while trading, a **replay**
scrubs the trade back through the tape with the sticks, a **tilt-meter** reads your state from the pad
itself, and a **process-weighted score** rates the evening on decisions rather than money.
The same app now covers the full daily loop: readiness and analysis before the session, position
sizing and planned protection, heatmap/history and mistake review afterward, then reports, exports,
backup, restore, and deliberate deletion.

> **The end goal is confidence and enjoyment — improving decision quality, not the money.**
> Demo only. Not advice. Entertainment, not alpha.

**Status:** planning complete, implementation not started. The authority for everything below is
[`plans/260824-1506-evening-forex-gold-gamepad/plan.md`](./plans/260824-1506-evening-forex-gold-gamepad/plan.md).

---

## Controller map

| Input | Action |
|-------|--------|
| `LT` (hold) | Clutch — nothing fires without it |
| `A` / `B` | Arm buy / arm sell |
| `RT` | Confirm to fire |
| D-pad | Symbol / lot size |
| `LB` / `RB` | Timeframe |
| `LB + RB` (hold) | Push-to-talk voice memo |
| `X` | Close |
| `Y` | Flatten (panic) |
| `View` | Lock / unlock |
| `Menu` | Open / close the safe GameOverlay; opening cancels ARM and locks new opens |

Inside GameOverlay, D-pad selects a destination, `LB/RB` changes desk tabs, `A` enters/applies a
safe preference, `B` goes back, and `Menu` exits. Playbook, Journal, System, Reports, and Settings
all use this one navigation contract. Navigation/apply cannot emit open/modify. An SL/TP edit only
stages a modify preview; `LT+RT` is still required before it reaches cTrader. Dedicated close and
panic controls remain available as safety exits.

Pad link is the **2.4G dongle** (wired USB is the fallback). Bluetooth on the Ultimate 2 needs
macOS 26+, so it is out on this machine.

## Architecture

```text
  8BitDo Ultimate 2 --2.4G--> Mac Chrome (focused)
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
    demo.ctraderapi.com     cTrader demo account (IC Markets)
```

- **Hot path:** pad → intent `{clutch, armedAt, relativeSl?, relativeTp?}` → WSS → cid reserve → risk
  → MARKET `ProtoOANewOrderReq` → execution event → ack → rumble. Existing-position protection is
  changed with `ProtoOAAmendPositionSLTPReq` after another LT+RT confirmation.
- **Cold path:** sentinel 1–5 s, copilot 1–30 s, TradingView webhook → `signal.item` only.
- **Journal path** (colder still, never on the order socket): readiness/analysis + plan snapshot →
  trade facts/events → voice/transcript + tape freeze → settled Process Score → daily
  review/heatmap/history → report/export/backup.

Spotware, not the VPS, is the matching engine. Docker on Ubuntu does not buy Equinix-to-broker
nanoseconds; it buys always-on execution without Windows.

### Latency budget (honest)

| Segment | Target |
|---------|--------|
| Pad poll → intent | < 16 ms |
| Home → VPS WS | 15–80 ms (dominant) |
| Gateway risk | < 5 ms |
| VPS → Spotware demo ack | tens of ms typical |
| AI advice | 1–5 s, never blocks a fire |

## Safety invariants

These are enforced by **boot-fails in config**, not by convention. The process refuses to start
otherwise.

- `mode: live` or a live Open API host → exit non-zero.
- `copilot.on_hot_path: true` → exit. The AI has no order tools, ever.
- `voice.stt.mode` outside `{local, off}` → exit. There is no cloud STT code path to misconfigure.
- `voice.bindings` resolving to `LT/RT/A/B/X/Y` → exit. Voice is memos and ask-the-coach only —
  never navigation, never execution.
- `tilt.gate_close: true` → exit. Tilt may add friction to **opens** only; close and panic always
  execute.
- `score.weights` not summing to 1.0 → exit.
- `tradingview.auto_trade: true` → exit.

Risk rules and playbook rules live in **one registry, with two consequences**: `risk` rules are
enforced by the gateway; `playbook` rules are graded and can never block a fire.

## Feature layers

| Layer | What it does |
|-------|--------------|
| **AI desk** | Sentinel (spread/news/session), news, Volman M5 setups, research / plan / advise / monitor. Read-only tools. |
| **Playbook & grading** | Every fire graded against its own rules, with the rule count named in the ARM overlay *before* it fires. |
| **Voice memo** | Hold `LB + RB`; audio uploads over HTTP and is transcribed locally by whisper.cpp on the VPS. Audio never leaves the box. |
| **Tilt detection** | Pad telemetry at 1 Hz (clutch cycles, arm flips, button rate, lot steps) → tilt band → adaptive friction on opens. Never a score input. |
| **Trade replay** | Scrub the frozen tape with the sticks; entry, exit, MFE/MAE, and the memo audio. Cannot place an order. |
| **Process Score** | Five process-only axes (adherence, selectivity, risk discipline, preparation, review). Standing down scores *well*. |
| **Daily journal cockpit** | DST-aware session clocks, five-item readiness, analysis, position sizing, process heatmap, day drill-down, latest ten, filterable history, and trade detail. |
| **Execution learning** | Actual vs Plan, planned/impulsive quality groups, before/during/after scores, mistake taxonomy/trends, and personal principles. |
| **Reports & data** | Process-first browser PDF, streamed CSV/JSON, manifested backup/restore, and explicit delete-all. |

No streaks, no levels, no badges, no leaderboards, and nothing that accumulates across sessions —
every mechanic that would create pressure to trade a dead tape is deliberately absent.

## Locked decisions

| Decision | Choice |
|----------|--------|
| Execution | cTrader Open API, `demo.ctraderapi.com:5035` (Protobuf) |
| Broker | IC Markets cTrader demo (plain, unsuffixed symbols) |
| Host | Ubuntu VPS, Docker Compose, two services |
| Live money | Refused — boot-fail on live host or `isLive` |
| Symbols | XAUUSD, EURUSD, GBPUSD, USDJPY; max 0.10 lot gold |
| Session | `Asia/Ho_Chi_Minh`, 18:00–23:30 |
| Transport | WSS JSON `{v,t,seq,ts,ch,cid,p}` on `/ws`, same origin as the HUD |
| Bind | Gateway `127.0.0.1:8444` behind existing VPS TLS on :443 |
| Copilot | Node child forked by `ev-gateway`, not a third container |
| Speech-to-text | Browser capture → whisper.cpp child on the VPS |
| Coach TTS | Browser `speechSynthesis`, default off |
| Deck priority | Process first; money sits behind a deliberate tab click |
| TradingView VIP | Second-screen cockpit + Pine webhook signals; never auto-trade |
| Product scope | One focused IC Markets cTrader demo account |
| Orders | MARKET with relative SL/TP; absolute SL/TP amend; full close/panic; no pending/partial |
| Navigation | Menu opens one safe GameOverlay; broker-changing applies still require LT+RT |
| Journal | Full daily cockpit and deterministic execution-quality analysis |
| Data ownership | Browser PDF, CSV/JSON, backup/restore/delete; no history import |
| UI boundary | Desktop Chrome, dark-only; no mobile/light mode |
| Database | Phase-owned migrations `001`–`010` |

## Phases

Recommended delivery order is sequential. Phase files declare minimum direct dependencies, but the
acceptance gates follow migration, navigation, and evidence contracts from `1` through `14`.

```text
1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13 → 14
```

| # | Phase | Effort | Status |
|---|-------|--------|--------|
| 1 | [Repo, protocol, Docker config](./plans/260824-1506-evening-forex-gold-gamepad/phase-01-repo-protocol-docker-config.md) | 12h | Pending |
| 2 | [cTrader exec and socket gateway](./plans/260824-1506-evening-forex-gold-gamepad/phase-02-ctrader-exec-and-socket-gateway.md) | 22h | Pending |
| 3 | [Web game and 8BitDo client agent](./plans/260824-1506-evening-forex-gold-gamepad/phase-03-web-game-and-8bitdo-client-agent.md) | 18h | Pending |
| 4 | [AI desk: sentinel, news, Volman, advise](./plans/260824-1506-evening-forex-gold-gamepad/phase-04-ai-desk-sentinel-news-volman.md) | 18h | Pending |
| 5 | [Ubuntu Docker deploy](./plans/260824-1506-evening-forex-gold-gamepad/phase-05-ubuntu-docker-deploy.md) | 7h | Pending |
| 6 | [Performance and psychology deck](./plans/260824-1506-evening-forex-gold-gamepad/phase-06-performance-and-psychology-deck.md) | 14h | Pending |
| 7 | [Playbook, rule registry, trade grading](./plans/260824-1506-evening-forex-gold-gamepad/phase-07-playbook-and-trade-grading.md) | 12h | Pending |
| 8 | [Voice: capture, whisper.cpp, coach](./plans/260824-1506-evening-forex-gold-gamepad/phase-08-voice-capture-whisper-and-coach.md) | 14h | Pending |
| 9 | [Tilt telemetry and adaptive friction](./plans/260824-1506-evening-forex-gold-gamepad/phase-09-tilt-telemetry-and-adaptive-friction.md) | 10h | Pending |
| 10 | [Trade replay](./plans/260824-1506-evening-forex-gold-gamepad/phase-10-trade-replay.md) | 12h | Pending |
| 11 | [Process Score and radar deck](./plans/260824-1506-evening-forex-gold-gamepad/phase-11-process-score-and-radar-deck.md) | 8h | Pending |
| 12 | [Daily journal cockpit and preparation](./plans/260824-1506-evening-forex-gold-gamepad/phase-12-daily-journal-cockpit-and-preparation.md) | 24h | Pending |
| 13 | [Reports, settings, and data portability](./plans/260824-1506-evening-forex-gold-gamepad/phase-13-reports-settings-and-data-portability.md) | 18h | Pending |
| 14 | [End-to-end session journey and release gate](./plans/260824-1506-evening-forex-gold-gamepad/phase-14-end-to-end-session-journey-and-release-gate.md) | 14h | Pending |

Total: 203h ≈ 26 working days.

## Planned repo layout

```text
apps/
  web/         Vite + Svelte HUD (built to dist, served by the gateway)
  gateway/     Node — risk, cid, journal, WS, REST; forks copilot + whisper children
  exec/        Python — cTrader Open API (OpenApiPy) over Protobuf TCP
packages/
  protocol/    Frozen v1 envelope + Zod message catalog
  exec/        Sidecar protocol types
  method/      Rule registry (risk + playbook), Volman method profile
config/        default.yaml
deploy/        fetch-models.sh, compose glue
docs/          release checklist and verified operating decisions
plans/         Plan of record, phase files, research, journals
```

## Getting started

Nothing is implemented yet — phase 1 scaffolds the workspace. Once it lands the setup is:

**Prerequisites**

- Ubuntu VPS, 4+ vCPU / 4 GB+ RAM, Docker + Compose, existing TLS on :443
- Node + pnpm, Chrome on the desktop, 8BitDo Ultimate 2 with its 2.4G dongle
- A cTrader ID with an **IC Markets demo** account

**cTrader credentials (one-time, manual — no auth helper ships in v1)**

1. Create a cTrader ID.
2. Open an IC Markets cTrader **demo** account under it.
3. Register an Open API application at `connect.spotware.com`; wait for approval.
4. Run the consent flow in a browser with the `trading` scope against the app's redirect URI.
5. Paste `CT_CLIENT_ID`, `CT_CLIENT_SECRET`, `CT_ACCESS_TOKEN`, `CT_REFRESH_TOKEN`, `CT_ACCOUNT_ID`
   into `.env`. `ev-exec` only refreshes what you provided here, and boot-fails if it is missing.

Other secrets: `EV_WS_TOKEN`, `XAI_API_KEY`, `TV_WEBHOOK_SECRET`. Initial secrets go through env;
refreshed cTrader tokens use the protected app volume with mode `0600`. Neither is committed, baked
into an image, exported, or included in backups.

**Run**

```bash
pnpm install
pnpm test                 # protocol round-trips
docker compose build
docker compose up -d      # gateway on 127.0.0.1:8444, exec unpublished
```

Then open `https://YOUR_DOMAIN` in a focused Chrome tab, connect the pad, and the HUD and socket come
from the same origin.

## Non-goals

Paper simulator. MT5/broker-history import. Pending orders or partial closes. Multiple accounts or
markets. Mobile delivery or light mode. Wine. Live money. Multiplayer / SaaS / copy-trading. Native HID helper.
Auto-trading AI, including TradingView `auto_trade`. Scraping Supercharts. Guaranteed profit.
Leaderboards, streaks, levels, badges, or any deck mechanic that punishes standing down. Edgewonk's
what-if trade simulator. Cloud speech-to-text. Voice or AI on the order path. Voice as navigation.
A third compose service.

## Open questions

- Exact public origin hostname (resolved in phase 5).
- `score.trades_max: 6` and the ±1 Selectivity band are uncalibrated for this player; the first month
  is provisional and recalibrates retroactively.
- Voice arousal (5% of tilt) is the weakest component — if a month of data does not support it,
  delete it rather than defend it.
- `voice.hold_stream: true` keeps the tab's recording indicator lit all evening in exchange for
  200–400 ms lower PTT latency. Decide before phase 8 ships.

## Documentation

- [Plan of record](./plans/260824-1506-evening-forex-gold-gamepad/plan.md) — decisions, goals,
  success criteria, validation log
- [Research](./plans/260824-1506-evening-forex-gold-gamepad/research/) — client/gamepad/socket,
  VPS/broker/AI, copilot desk, TradingView VIP, cTrader Docker
- [Journals](./plans/journals/) — chronological session records

---

Demo only · Not advice · Process over outcome
