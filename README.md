# Evening Forex Gold Gamepad

<p align="center">
  <img src="./visual01.png" alt="Trading Game — discipline, process, improvement" width="100%">
</p>

<p align="center">
  <a href="#test-suite"><img src="https://img.shields.io/badge/tests-756%20passed-22c55e?style=flat-square&logo=pytest&logoColor=white" alt="Tests"></a>
  <a href="#architecture"><img src="https://img.shields.io/badge/architecture-single--process%20gateway-3b82f6?style=flat-square" alt="Architecture"></a>
  <a href="#locked-decisions"><img src="https://img.shields.io/badge/backend-Python%203.11+%20%7C%20FastAPI-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="#locked-decisions"><img src="https://img.shields.io/badge/frontend-React%2018%20%7C%20Vite%20PWA-61DAFB?style=flat-square&logo=react&logoColor=black" alt="React"></a>
  <a href="#controller-map"><img src="https://img.shields.io/badge/controller-8BitDo%20Ultimate%202%20Wireless-8b5cf6?style=flat-square" alt="8BitDo"></a>
  <a href="#locked-decisions"><img src="https://img.shields.io/badge/broker-cTrader%20Open%20API%20(Demo)-f97316?style=flat-square" alt="cTrader"></a>
  <a href="#safety-invariants"><img src="https://img.shields.io/badge/mode-demo%20only-ef4444?style=flat-square" alt="Demo Only"></a>
</p>

---

## Overview

A desktop Chrome **web game** — an installable, client-side **React PWA** — where an **8BitDo Ultimate 2 Wireless** controller trades forex and gold on a **cTrader demo account**. The pad communicates over WebSocket to a **Python gateway** on an Ubuntu VPS (Docker Compose behind nginx). Production splits the origins: the HUD is a static site, the gateway is `https://gw.bobvolman.com`. There is no execution sidecar and no secondary microservice. A near-realtime **AI desk** coaches from the sidelines without touching the order path.

On top of the game sits a **trading journal** that takes the best of Edgewonk and TradeZella and rebuilds them for gamepad interaction:
- **Playbook:** grades every fire against its own rules *before* you commit.
- **Voice memo:** captures trade rationale hands-free when you cannot type while trading.
- **Trade replay:** scrubs closed trades back through the 1 Hz tape using gamepad analog sticks.
- **Tilt-meter:** derives emotional arousal directly from pad telemetry and interaction pace.
- **Process-weighted score:** rates the evening on decision quality rather than financial outcome.
- **Daily cockpit:** covers the entire daily trading loop — readiness checklists, multi-market clocks, position sizing, execution review (Actual vs Plan), reports, encrypted backup, restore, and audit wipe.

> [!IMPORTANT]
> **The end goal is confidence and enjoyment — improving decision quality, not the money.**  
> Demo only. Not financial advice. Entertainment and discipline, not alpha.

---

## Project Status

**Current State:** Phases **1–4, 6, 7, 9, 10, 11, 12, and 13** are **built and fully covered by 756 tests** (542 Python pytest + 214 TypeScript vitest).

- **Backend Gateway:** Single-process FastAPI + WebSocket gateway with frozen v1 envelope, SQLite migrations `001`–`010`, risk engine with atomic CID reservations, position limits, dead-man switch, and native `ctrader-open-api` integration with request timeout resilience and fire-and-forget execution.
- **Web Arcade Frontend:** React 18 PWA (`evgamepad-arcade`) with 20+ responsive screens, collapsible navigation rail, lightweight-charts candlestick integration, interactive HUD, GameOverlay modal, and full offline service worker caching.
- **Terminology Refactored:** Clean, consistent **BUY / SELL** terminology unified across the entire stack (protocol catalog, database schema, risk engine, frontend components).
- **Discipline & Journaling:** Complete implementation of pre-commit playbook grading, 5-axis Process Score radar (where standing down in a dead tape scores 100), measured behavioral tilt telemetry with open-friction gates, 1 Hz dual-book tape replay, printable browser PDF reports, streamed CSV/JSON exports, and encrypted SQLite snapshot backup/restore lifecycle.

**Remaining Roadmap:**
- **Phase 5 (Ubuntu Docker Deploy):** Documented below — nginx + Docker Compose on an Ubuntu VPS, gateway at `gw.bobvolman.com`.
- **Phase 8 (Voice Memo Local STT):** Local `whisper.cpp` container speech-to-text pipeline (deferred).
- **Phase 14 (Release Gate):** End-to-end integration and smoke verification on physical 8BitDo hardware and live IC Markets demo accounts.

Detailed authority: [`plans/260824-1506-evening-forex-gold-gamepad/plan.md`](./plans/260824-1506-evening-forex-gold-gamepad/plan.md).

---

## Table of Contents

- [Controller Map & Safety](#controller-map)
- [Architecture](#architecture)
- [Safety Invariants](#safety-invariants)
- [Feature Layers](#feature-layers)
- [Locked Technical Decisions](#locked-decisions)
- [Phases & Roadmap](#phases)
- [Repo Layout](#repo-layout)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [cTrader Credentials](#ctrader-credentials-one-time-manual-setup)
  - [Local Development](#local-development)
  - [Testing & Quality Assurance](#test-suite)
  - [Docker (local smoke)](#docker-local-smoke)
  - [Production deploy (Ubuntu VPS)](#production-deploy-ubuntu-vps)
  - [Protocol & Type Synchronization](#protocol-types-are-generated-never-hand-written)
- [Playbooks: Enforced vs Graded](#playbooks-enforced-vs-graded)
- [The Performance Deck](#the-deck-and-what-it-refuses-to-show)
- [The Daily Journal Cockpit](#the-daily-journal)
- [Process Score & Radar](#the-process-score)
- [Trade Replay](#trade-replay)
- [Tilt Detection & Telemetry](#tilt-what-it-measures-and-what-it-cannot-do)
- [Settings, Reports & Data Ownership](#settings-reports-and-your-data)
- [Non-Goals](#non-goals)
- [Documentation](#documentation)

---

## Controller Map

| Input | Action |
|---|---|
| `LT` (hold) | Clutch — nothing fires without it |
| `A` | Arm **BUY** |
| `B` | Arm **SELL** |
| `RT` | Confirm to fire |
| D-pad | Symbol / lot size |
| `LB` / `RB` | Timeframe |
| `LB + RB` (hold) | Push-to-talk voice memo |
| `X` | Close active position |
| `Y` | Flatten (panic) |
| `View` | Lock / unlock session |
| `Menu` | Open / close the safe GameOverlay; opening cancels ARM and locks new opens |

Inside **GameOverlay**, D-pad selects a destination, `LB/RB` changes desk tabs, `A` enters/applies a safe preference, `B` goes back, and `Menu` exits. Playbook, Journal, System, Reports, and Settings all adhere to this single navigation contract. Navigation cannot emit open/modify orders. An SL/TP edit only stages a modify preview; `LT+RT` is still required before it reaches cTrader. Dedicated close and panic controls remain available as safety exits.

### Pairing the 8BitDo Ultimate 2 Wireless

1. Set the switch on the back to **X** (XInput). Chrome reports `mapping: "standard"`, ensuring direct button mapping without custom calibration.
2. Plug the **2.4G dongle** into the Mac and press **Start** (the primary supported link).
3. Wired USB-C is the verified fallback; use it if the wireless dongle encounters interference.
4. Open the HUD, focus the tab, and **press any button** — the Gamepad API stays silent until an initial user gesture occurs (browser privacy spec). The HUD reports `pad: absent` until pressed.
5. Back paddles (`L4`/`R4`) are activated only if an initial probe detects movement; otherwise, the game operates on `LT`/`RT` without degradation.

> [!CAUTION]
> **The browser tab must stay focused.** Hiding the tab or unplugging the controller immediately cancels any active ARM and locks new open orders at both ends: the client stops transmitting, and the gateway dead-man rejects execution. Close, panic, and the HUD's **FLATTEN** button continue to function regardless.

---

## Architecture

![How the Evening Forex Gold Gamepad works](./docs/how-the-app-works.svg)

[Open the standalone interactive diagram](./docs/how-the-app-works.html).

The **gateway is the sole component authorized to approve and route demo orders**. The controller and the React PWA prepare user intent; the Python gateway validates risk and translates approved intents into cTrader Open API Protobuf messages over its internal `ctrader-open-api` connection. Spotware operates as the matching engine.

```
Order Hot Path:
  [8BitDo Controller] ──> [Focused Chrome PWA] ──(WSS to gw.bobvolman.com)──> [Gateway Risk Gates] ──(Protobuf)──> [cTrader Demo API]

Broker Return Path:
  [cTrader Demo API] ──(Execution Events / Quotes)──> [Python Gateway] ──(WSS)──> [React HUD & Controller Rumble]

Sidecar Learning Path:
  [TradingView / Sentinel] ──> [AI Copilot Worker] ──> [Advisory / Voice / Tape / Journal SQLite] (Read-Only)
```

1. **Order hot path:** controller → focused Chrome tab → gateway risk checks → in-process cTrader Open API connection → cTrader demo.
2. **Broker return path:** market data, fills, positions, and execution events flow back through the gateway to update the HUD and trigger controller vibration.
3. **Learning path:** AI coaching, voice transcription, journal persistence, tape replay, and Process Score calculation run alongside the order path without blocking execution.

### Latency Budget (Honest)

| Segment | Target | Notes |
|---|---|---|
| Pad poll → intent | < 16 ms | 60 Hz Gamepad API polling loop |
| Home → VPS WS | 15–80 ms | Dominant segment (network transport) |
| Gateway risk gates | < 5 ms | In-memory CID check, position caps, R limits |
| VPS → Spotware demo ack | 20–80 ms | Protobuf TCP/SSL session to `demo.ctraderapi.com:5035` |
| AI advisory | 1–5 s | Cold path; never blocks order execution |

---

## Safety Invariants

Enforced through **hard boot-fails in configuration**, not conventions. The gateway process exits immediately if any invariant is violated:

- `mode: live` or connection to a live Open API host → **Refuse to start (exit non-zero)**.
- `copilot.on_hot_path: true` → **Refuse to start**. AI tools are read-only and strictly isolated from the order path.
- `voice.stt.mode` outside `{local, off}` → **Refuse to start**. No external cloud speech transcription.
- `voice.bindings` resolving to `LT/RT/A/B/X/Y` → **Refuse to start**. Voice is restricted to memos and advisory questions.
- `tilt.gate_close: true` → **Refuse to start**. Tilt may add friction to *opens* only; close and panic always execute.
- `score.weights` not summing to 1.0 → **Refuse to start**.
- `tradingview.auto_trade: true` → **Refuse to start**. External signals are informational only.

---

## Feature Layers

| Layer | What It Does |
|---|---|
| **AI Desk** | Sentinel (spread, news events, market session clocks), Volman M5 price action setups, research, plan, and real-time coaching. Restricted to read-only tools. |
| **Playbook & Grading** | Every trade is graded against its specific setup rules, with the rule validation count displayed in the ARM overlay *before* commit. |
| **Voice Memo** | Hold `LB + RB` push-to-talk; records trade rationale and persists locally with audio playback in replay. |
| **Tilt Detection** | 1 Hz controller telemetry (clutch cycles, arm flips, button rates, lot scaling) drives adaptive friction on opens. Never affects exits. |
| **Trade Replay** | Scrub frozen 1 Hz dual-book tapes with analog sticks; inspect entry, exit, MAE/MFE excursions, and associated voice memos. |
| **Process Score** | 5 process-only dimensions (adherence, selectivity, risk discipline, preparation, review). Correctly standing down scores a perfect 100. |
| **Daily Journal Cockpit** | Multi-timezone IANA market clocks, 5-item readiness check, pre-session analysis, lot sizing calculator, Process Score heatmap, and filterable trade history. |
| **Execution Learning** | Actual vs Plan review, planned vs impulsive classification, mistake taxonomy, and trader principles linkage. |
| **Data Portability** | Print-friendly CSS reports (browser PDF), streamed CSV/JSON exports, and SHA-256 validated SQLite backup, restore, and nuclear wipe. |

---

## Locked Decisions

| Area | Decision | Details |
|---|---|---|
| **Execution** | cTrader Open API | In-process Protobuf via `ctrader-open-api`, `demo.ctraderapi.com:5035` |
| **Broker** | IC Markets cTrader Demo | Standard symbols (`XAUUSD`, `EURUSD`, `GBPUSD`, `USDJPY`), max 0.10 lot gold |
| **Host** | Ubuntu VPS (Docker Compose + nginx) | One container (`ev-gateway`) on loopback `:8444`; nginx terminates TLS at `gw.bobvolman.com` |
| **Account Mode** | Demo Only | Hard boot-fail on live endpoints or production accounts |
| **Session Window** | `Asia/Ho_Chi_Minh` | 18:00–23:30 evening trading session |
| **Transport** | WebSocket (`/ws`) + REST (`/api/*`) | Envelope: `{v, t, seq, ts, ch, cid, p}`. HUD may be a separate origin; gateway CORS + Origin allowlist |
| **Frontend Stack** | React 18 PWA | TypeScript, Vite, Lightweight Charts, dark arcade theme. Production build sets `VITE_GATEWAY_ORIGIN=https://gw.bobvolman.com` |
| **Backend Stack** | Python 3.11+ | FastAPI, Uvicorn, Pydantic v2, Twisted/OpenApiPy, SQLite |
| **Database** | SQLite + Migrations | Phase migrations `001`–`010` stored in `/data/journal.db` |

---

## Phases

```text
1 → 2 → 3 → 4 → [5] → 6 → 7 → [8] → 9 → 10 → 11 → 12 → 13 → [14]
```

| # | Phase | Scope | Status |
|---|---|---|---|
| 1 | [Repo, protocol, Docker config](./plans/260824-1506-evening-forex-gold-gamepad/phase-01-repo-protocol-docker-config.md) | Protocol v1, config boot-fails, migrations runner | **Built & Verified** |
| 2 | [cTrader exec and socket gateway](./plans/260824-1506-evening-forex-gold-gamepad/phase-02-ctrader-exec-and-socket-gateway.md) | cTrader client, risk gates, cid ledger, tape pipeline | **Built & Verified** |
| 3 | [Web game and 8BitDo client agent](./plans/260824-1506-evening-forex-gold-gamepad/phase-03-web-game-and-8bitdo-client-agent.md) | Gamepad FSM agent, chord detection, PWA shell | **Built & Verified** |
| 4 | [AI desk: sentinel, news, Volman](./plans/260824-1506-evening-forex-gold-gamepad/phase-04-ai-desk-sentinel-news-volman.md) | Opportunity quality, Volman detectors, advisory tools | **Built & Verified** |
| 5 | [Ubuntu Docker deploy](./plans/260824-1506-evening-forex-gold-gamepad/phase-05-ubuntu-docker-deploy.md) | Single-service compose, nginx TLS reverse-proxy to `gw.bobvolman.com` | **Documented** (see [Production deploy](#production-deploy-ubuntu-vps)) |
| 6 | [Performance and psychology deck](./plans/260824-1506-evening-forex-gold-gamepad/phase-06-performance-and-psychology-deck.md) | Process deck, adherence, month-over-month trends | **Built & Verified** |
| 7 | [Playbook and trade grading](./plans/260824-1506-evening-forex-gold-gamepad/phase-07-playbook-and-trade-grading.md) | Rule registry, setups, pre-commit rule grading | **Built & Verified** |
| 8 | [Voice: capture, whisper.cpp, coach](./plans/260824-1506-evening-forex-gold-gamepad/phase-08-voice-capture-whisper-and-coach.md) | Audio upload, local whisper.cpp STT, coach TTS | *Deferred* |
| 9 | [Tilt telemetry and adaptive friction](./plans/260824-1506-evening-forex-gold-gamepad/phase-09-tilt-telemetry-and-adaptive-friction.md) | Behavioral pad telemetry, open friction, cooldown | **Built & Verified** |
| 10 | [Trade replay](./plans/260824-1506-evening-forex-gold-gamepad/phase-10-trade-replay.md) | 1 Hz dual-book tape freeze, gamepad stick scrubbing | **Built & Verified** |
| 11 | [Process Score and radar deck](./plans/260824-1506-evening-forex-gold-gamepad/phase-11-process-score-and-radar-deck.md) | 5 process axes, vacuous axes normalization, radar | **Built & Verified** |
| 12 | [Daily journal cockpit](./plans/260824-1506-evening-forex-gold-gamepad/phase-12-daily-journal-cockpit-and-preparation.md) | Market clocks, readiness, sizing, Actual vs Plan | **Built & Verified** |
| 13 | [Reports, settings, and data portability](./plans/260824-1506-evening-forex-gold-gamepad/phase-13-reports-settings-and-data-portability.md) | Printable PDF reports, exports, backup, restore, wipe | **Built & Verified** |
| 14 | [End-to-end release gate](./plans/260824-1506-evening-forex-gold-gamepad/phase-14-end-to-end-session-journey-and-release-gate.md) | Full demo session on physical pad and VPS broker | *Pending* |

---

## Repo Layout

```text
evgamepad/
├── app/                        # React 18 Arcade PWA (Vite, TypeScript, Tailwind)
│   ├── src/
│   │   ├── components/         # Reusable arcade UI widgets & layout primitives
│   │   ├── screens/            # 20+ specialized screens (Live HUD, Journal, Replay, etc.)
│   │   ├── pad/                # 8BitDo gamepad driver, chord detection, FSM, telemetry
│   │   ├── net/                # WebSocket client, reconnection, message routing
│   │   ├── journal/            # Journal cockpit, readiness checklists, trade review
│   │   ├── replay/             # 1 Hz dual-book tape scrubber and chart components
│   │   ├── deck/               # Process performance metrics, Process Score radar
│   │   ├── protocol/           # Auto-generated schema.json and types.ts
│   │   └── sw.ts               # Offline PWA service worker implementation
│   └── scripts/                # check-protocol-types.mjs (catches contract drift)
│
├── apps/
│   └── gateway/                # Single-process Python 3.11 gateway (FastAPI)
│       ├── api/                # WebSocket `/ws`, REST endpoints, static HUD serving
│       ├── broker/             # cTrader Open API client (Protobuf TCP/SSL, events, timeouts)
│       ├── copilot/            # AI desk background worker (read-only advisory tools)
│       ├── data/               # SQLite backup snapshots, restore verification, wipe
│       ├── db/                 # SQLite migrations runner and migrations 001–010
│       ├── deck/               # Process adherence and performance metric calculators
│       ├── grading/            # Playbook pre-commit trade grading engine
│       ├── journal/            # Journal queries, review attachments, tape freezing
│       ├── method/             # Unified rule registry (risk rules + playbook setups)
│       ├── protocol/           # Frozen v1 envelope & Pydantic catalog (single source of truth)
│       ├── replay/             # 1 Hz dual-book tape aggregations & scrub endpoints
│       ├── reports/            # Printable PDF report queries and data formatting
│       ├── risk/               # Risk engine: CID reservations, limits, dead-man switch
│       ├── score/              # 5-axis Process Score radar engine
│       ├── sentinel/           # Market sentinel: spread, session clocks, opportunity quality
│       ├── settings/           # Safe user preferences schema & reflection
│       ├── signals/            # Economic calendar and external signal intake
│       └── tilt/               # Measured behavioral tilt telemetry & friction gates
│
├── config/
│   └── default.yaml            # Single configuration source of truth
├── deploy/                     # nginx vhosts for gw.bobvolman.com, VPS runbook, model fetch
├── docs/                       # Architecture diagrams, specifications, BA artifacts
└── plans/                      # Phase implementation specifications, journals, research
```

---

## Getting Started

### Prerequisites

- **Python:** 3.11+ with [`uv`](https://github.com/astral-sh/uv) package manager.
- **Node.js:** v20+ (v22 recommended) for building the web bundle.
- **Hardware:** Desktop Chrome browser and an **8BitDo Ultimate 2 Wireless** controller with 2.4G USB dongle.
- **Broker Account:** A free **cTrader ID** with an **IC Markets cTrader Demo** account.
- **Container Runtime (optional):** Docker & Docker Compose for deployment.

### cTrader Credentials (One-time Manual Setup)

1. Register or log in to your **cTrader ID**.
2. Open an **IC Markets cTrader Demo** account under that cTrader ID.
3. Create an Open API application at [connect.spotware.com](https://connect.spotware.com).
4. Run the OAuth consent flow in your browser with the `trading` scope against your redirect URI.
5. Copy your credentials into `.env`:
   ```bash
   cp .env.example .env
   ```
   Fill in:
   ```dotenv
   CT_CLIENT_ID=your_client_id
   CT_CLIENT_SECRET=your_client_secret
   CT_ACCESS_TOKEN=your_access_token
   CT_REFRESH_TOKEN=your_refresh_token
   CT_ACCOUNT_ID=your_demo_account_id
   EV_WS_TOKEN=generate_a_secure_token
   ```

### Local Development

#### 1. Backend Gateway

```bash
cd apps/gateway
uv sync --group dev
EV_DEV=1 EV_CONFIG=../../config/default.yaml EV_DATA_DIR=../../data uv run python main.py
```
The gateway binds to `127.0.0.1:8444`. Health check:
```bash
curl -s http://127.0.0.1:8444/healthz
```

#### 2. Frontend Web App

In a separate terminal:
```bash
cd app
npm install
npm run dev
```
Open `http://localhost:5173` in Google Chrome, connect your 8BitDo controller, and press any button to begin.

---

### Test Suite

The project enforces high test reliability across both backend and frontend layers:

```bash
# Run backend tests (542 tests covering risk, broker, protocol, journal, replay, score)
cd apps/gateway
uv run python -m pytest

# Run frontend tests (214 tests covering gamepad FSM, chords, WebSocket, HUD, replay, gateway URL)
cd ../../app
npm test

# Run frontend type checking & protocol drift validation
npm run build
```

---

### Docker (local smoke)

The production stack is still **one container**. This is a loopback smoke test, not the public hostname:

```bash
docker compose build
docker compose up -d
docker compose ps
curl -s http://127.0.0.1:8444/healthz
```

Compose publishes `127.0.0.1:8444` only. Put nginx in front of that port for TLS — see the next section.

---

### Production deploy (Ubuntu VPS)

This is the path for a new operator. The Python gateway listens on the VPS loopback. nginx on the host terminates HTTPS for **`gw.bobvolman.com`**. The React HUD is a separate static site whose production build points at that gateway.

```text
Chrome (HUD, e.g. https://bobvolman.com)
        │  fetch /api/*  and  wss://gw.bobvolman.com/ws
        ▼
Internet ──TLS:443──► nginx (host) ──► 127.0.0.1:8444  ev-gateway (Docker)
                                              │
                                              ▼
                                   demo.ctraderapi.com:5035
```

Two origins, one process that talks to the broker:

| Piece | Public hostname | What it serves |
|---|---|---|
| **HUD** | your site (example: `bobvolman.com`) | Vite `app/dist` (nginx, Pages, or any static host) |
| **Gateway** | `gw.bobvolman.com` | FastAPI `/healthz`, `/api/*`, `/ws`, `/hooks/tv` |

The session token is still pasted into the HUD at connect time. It is never written into the frontend bundle.

#### 0. What you need

- An Ubuntu 22.04 or 24.04 VPS with a public IPv4 address and SSH.
- DNS you can edit.
- A domain whose **A record** for `gw.bobvolman.com` points at the VPS. The HUD hostname is separate; it only has to be a real `https://` origin you control.
- A cTrader demo application and the values in `.env.example`.
- Ports **22**, **80**, and **443** open. Port **8444** must not be reachable from the WAN.

#### 1. DNS

Create an A (and AAAA if you have IPv6) record:

```text
gw.bobvolman.com    A    YOUR_VPS_IPV4
```

Wait until `dig +short gw.bobvolman.com` returns the VPS address from your laptop.

If the HUD is also on this VPS, add its hostname the same way (see step 8).

#### 2. Ubuntu packages

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl git ufw nginx
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
. /etc/os-release
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $VERSION_CODENAME stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker "$USER"
# log out and back in so `docker` works without sudo
```

Firewall — SSH + HTTP/HTTPS only. Compose already binds 8444 to loopback; the firewall is the second belt:

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
sudo ufw status
```

#### 3. Clone and secrets

```bash
sudo mkdir -p /opt/evgamepad /var/www/certbot
sudo chown "$USER":"$USER" /opt/evgamepad
cd /opt/evgamepad
git clone https://github.com/YOUR_ORG/YOUR_REPO.git .
cp .env.example .env
chmod 600 .env
```

Edit `.env`. Required:

```dotenv
CT_CLIENT_ID=...
CT_CLIENT_SECRET=...
CT_ACCESS_TOKEN=...
CT_REFRESH_TOKEN=...
CT_ACCOUNT_ID=...
EV_WS_TOKEN=generate_a_long_random_string

# Browser Origin of the HUD — the page Chrome loads, not the gateway host.
EV_PUBLIC_ORIGIN=https://YOUR_HUD_ORIGIN
# Optional extras (www, a staging HUD):
# EV_CORS_ORIGINS=https://www.YOUR_HUD_ORIGIN
```

Generate the socket token with `openssl rand -hex 32`. Never commit `.env`.

`EV_PUBLIC_ORIGIN` must match the HUD origin **exactly** (scheme + host, no trailing slash). If Chrome loads `https://bobvolman.com`, that is the value — not `https://gw.bobvolman.com`. A mismatch closes the WebSocket with code `4403`.

#### 4. Docker Compose on the VPS

From `/opt/evgamepad`:

```bash
docker compose build
docker compose up -d
docker compose ps
curl -sS http://127.0.0.1:8444/healthz
ss -lntp | grep 8444
```

`healthz` must return `"ok": true`. `ss` must show `127.0.0.1:8444`, not `0.0.0.0:8444` on the host.

Useful commands:

```bash
docker compose logs -f --tail=200 ev-gateway
docker compose restart ev-gateway
# after pulling a new git revision:
git pull
docker compose build
docker compose up -d
```

The journal, voice files, and models live in the named volume `ev-journal` (`/data` in the container). Back that volume up; do not delete it casually.

Optional, once, for the later whisper.cpp path:

```bash
./deploy/fetch-models.sh
```

#### 5. nginx → `gw.bobvolman.com`

The repo ships the vhost at [`deploy/nginx/gw.bobvolman.com.conf`](./deploy/nginx/gw.bobvolman.com.conf). It proxies everything — including WebSocket `/ws` — to `127.0.0.1:8444`.

```bash
sudo mkdir -p /var/www/certbot
sudo cp /opt/evgamepad/deploy/nginx/gw.bobvolman.com.conf /etc/nginx/sites-available/gw.bobvolman.com
sudo ln -sf /etc/nginx/sites-available/gw.bobvolman.com /etc/nginx/sites-enabled/gw.bobvolman.com
# disable the default site if it is still grabbing :80
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

Issue the certificate (installs and rewrites the vhost for 443):

```bash
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d gw.bobvolman.com --agree-tos -m YOU@YOUR_DOMAIN --redirect
```

After certbot, open `/etc/nginx/sites-available/gw.bobvolman.com` and confirm the **443** `location /` block still has:

- `proxy_http_version 1.1;`
- `proxy_set_header Upgrade $http_upgrade;`
- `proxy_set_header Connection $connection_upgrade;` (or `"upgrade"`)
- `proxy_read_timeout 86400s;`
- `proxy_set_header Origin $http_origin;`

`sudo nginx -t && sudo systemctl reload nginx`.

Check from your laptop:

```bash
curl -sS https://gw.bobvolman.com/healthz
```

You want JSON with `"ok": true` and a valid certificate, not a browser warning.

#### 6. Frontend production build

The HUD is **not** the gateway hostname. Production builds bake the gateway URL:

```bash
cd app
cp .env.example .env.local   # optional; production defaults live in .env.production
npm ci
npm run build
```

`app/.env.production` is:

```dotenv
VITE_GATEWAY_ORIGIN=https://gw.bobvolman.com
```

That is a hostname, not a secret. The session token is still pasted in the HUD and kept in memory.

`dist/` is static files. Publish them however you already host the site:

- **Same VPS, second nginx vhost** — copy [`deploy/nginx/hud.example.conf`](./deploy/nginx/hud.example.conf), set `server_name` to the HUD host, `sudo certbot --nginx -d YOUR_HUD_ORIGIN`, then:

  ```bash
  sudo mkdir -p /var/www/evgamepad-arcade
  sudo rsync -a --delete /opt/evgamepad/app/dist/ /var/www/evgamepad-arcade/
  ```

- **Cloudflare Pages / any static host** — upload `app/dist`. Set the HUD URL as `EV_PUBLIC_ORIGIN` on the VPS and recreate the container (`docker compose up -d`) so CORS and the WebSocket allowlist match.

Local development is unchanged: `npm run dev` leaves `VITE_GATEWAY_ORIGIN` empty and Vite proxies `/api` and `/ws` to `127.0.0.1:8444`.

#### 7. First-evening checklist

1. Chrome, desktop, tab focused. Open the HUD origin (not necessarily `gw.bobvolman.com`).
2. Paste `EV_WS_TOKEN`. Connect. The socket URL should be `wss://gw.bobvolman.com/ws`.
3. DevTools → Network: `/api/arcade/hud` is `200` from `gw.bobvolman.com`, CORS origin is your HUD, no mixed-content errors.
4. Pair the 8BitDo (XInput, 2.4G dongle). Press a button. The HUD should leave `pad: absent`.
5. `docker compose logs ev-gateway` should show the broker link coming up against **demo** (`demo.ctraderapi.com:5035`), never live.

If the socket closes immediately: `EV_PUBLIC_ORIGIN` does not match the HUD origin (including `https` vs `http`, or a missing `www`). If REST works and WS does not: nginx is not forwarding `Upgrade` / `Connection`. If the HUD still calls `localhost` or its own origin for `/api`: you served a build without `VITE_GATEWAY_ORIGIN` — rebuild step 6.

#### 8. Operations

| Task | Command / note |
|---|---|
| Status | `docker compose ps` and `curl -sS https://gw.bobvolman.com/healthz` |
| Logs | `docker compose logs -f --tail=200 ev-gateway` |
| Restart after reboot | `restart: unless-stopped` brings the container back; nginx is a systemd service |
| Renew TLS | `certbot.timer` renews; `sudo certbot renew --dry-run` once to verify |
| Rotate the HUD token | new `EV_WS_TOKEN` in `.env`, then `docker compose up -d` |
| Data | Docker volume `ev-journal` — include it in VPS backups |

Do not put a CDN in front of `/ws`. Do not publish `8444` on `0.0.0.0`. Live cTrader hosts still fail boot.

---

### Protocol Types Are Generated, Never Hand-Written

The Pydantic message catalog in `apps/gateway/protocol/` is the single source of truth. TypeScript definitions and JSON schemas are generated automatically:

```bash
# Regenerate TypeScript types from backend Pydantic models
cd apps/gateway
uv run python -m protocol.export_ts

# Verify types are up to date (fails build if drift occurs)
uv run python -m protocol.export_ts --check
```

---

## Playbooks: Enforced vs Graded

A **playbook** represents a structured trading setup with explicit verification rules. Every trade is graded against the active playbook before execution:

```text
BUY 0.10 XAUUSD @ 2345.12
[M5 Range Break]  4/5 rules OK  ·  ✗ Not chasing (3.00 ATR)
```

The fundamental distinction between rule types:

| Property | Risk Rules | Playbook Rules |
|---|---|---|
| **Defined In** | Unified registry (`method/rules.py`) | Same registry |
| **Violation Outcome** | **Rejects the intent server-side** | **Recorded and displayed in HUD** |
| **Configured By** | Server configuration only | Trader / Strategy profile |

> [!NOTE]
> **A playbook rule can never block a trade.** This invariant is verified by automated tests to ensure the journal never silently becomes an unauthorized gatekeeper.

---

## The Deck, and What It Refuses to Show

The `/deck` view answers one question: **Am I improving?**

It opens on the **process panel**, deliberately free of dollar amounts, balances, or financial P/L. Monitoring monetary fluctuations mid-session distracts from execution quality; the outcome panel requires an explicit user click.

| Metric | Purpose |
|---|---|
| **Adherence** | Ratio of executed trades that satisfied every setup rule. Evaluated using the gateway's server-enforced rule set. |
| **Trades Declined** | Controller arms cancelled while a stand-down condition was active. Not trading is treated as an active, positive decision. |
| **Opportunity Quality** | Evaluates market conditions offered by the tape. A flat session during a dead market represents high discipline. |
| **Check-In** | Two-tap physical controller check-in plotted against adherence rather than monetary gain. |
| **Month vs Month** | Comparative trajectory tracking disciplined execution over time. |

### Deliberately Refused Dark Patterns
- **No streaks, levels, or badges:** Gamification mechanics that incentivize trading dead markets are excluded.
- **No Sharpe ratios under 30 sessions:** Statistically insignificant sample sizes are marked as "insufficient data".
- **No zeros for unmeasured sessions:** Standing down during a zero-trade session does not score zero.

---

## The Daily Journal

The `/journal` cockpit powers the full daily cycle: **prepare, trade, close, and review** without leaving the application.

- **Pre-Session Readiness:** IANA market clocks (Sydney, Tokyo, London, New York), 5-item emotional/physical readiness check, and pre-session trade planning.
- **Dynamic Lot Sizing:** Calculated directly by the gateway using live quote-to-USD conversion and broker volume stepping. Sizing rounds down conservatively to ensure risk boundaries are respected.
- **Actual vs Plan Review:** Trade analysis comparing planned vs executed entry/stop parameters.
- **Immutable Records:** Trade fills, execution events, and tape data cannot be altered or overwritten.

---

## The Process Score

Five process-driven axes evaluate overall trading discipline:

| Axis | Metric | Weight |
|---|---|---|
| **Adherence** | Playbook rules passed / rules evaluated | 0.30 |
| **Selectivity** | Alignment between trade count and market opportunity | 0.25 |
| **Risk Discipline** | Compliance with lot size, entry stops, R-multiple limits | 0.20 |
| **Preparation** | Pre-session check-in, readiness checklist, and plan setup | 0.15 |
| **Review** | Post-session review, replay inspection, and trade tagging | 0.10 |

> [!TIP]
> **A correctly declined evening scores at least as well as a well-traded session:**  
> - Dead tape, 0 trades, genuine stand-downs: **100 / 100**  
> - Active tape, 4 fires, executed cleanly: **98 / 100**  
> - Active tape, hesitation/freeze: **70 / 100**  
> - Dead tape, over-trading: **65 / 100**

---

## Trade Replay

Replay closed trades through the exact 1 Hz tape they unfolded on:

| Gamepad Input | Replay Function |
|---|---|
| **LS ← / →** | Velocity-based tape scrubbing |
| **RS ← / →** | Zoom timeframe window (1s, 5s, 15s, 1m, 5m) |
| **A** | Play / Pause |
| **D-pad ↑ / ↓** | Playback speed (0.5x, 1x, 2x, 4x) |
| **LB / RB** | Navigate previous / next trade of the session |
| **B** | Exit replay |

The replay tape is frozen at 1 Hz resolution for **both sides of the book (Bid and Ask)**, ensuring buy and sell excursions (MAE/MFE) are rendered with precision. Orders cannot be emitted from the replay route.

---

## Tilt: What It Measures, and What It Cannot Do

The system derives emotional state directly from measured physical controller interactions:

| Component | Telemetry Measurement | Weight |
|---|---|---|
| **Revenge Size** | Order volume relative to session median | 0.25 |
| **Re-Entry Speed** | Seconds elapsed since a losing close | 0.20 |
| **Rule-Break Recency** | Adherence failures in recent fires | 0.20 |
| **Hesitation** | Clutch cycles before arming | 0.10 |
| **Arm Flip** | Rapid switching between BUY and SELL while armed | 0.10 |
| **Input Aggression** | Button pressing frequency against baseline | 0.10 |
| **Voice Arousal** | Speech pacing and volume deviations | 0.05 |

### Adaptive Friction Bands

- **Calm (`< 0.35`):** Standard operation.
- **Warm (`0.35 - 0.60`):** Informational amber indicator.
- **Hot (`0.60 - 0.80`):** Requires holding confirmation for 750 ms instead of a tap.
- **Scorched (`> 0.80`):** Imposes a 300 s cooldown on new open orders.

> [!IMPORTANT]
> **Tilt safeguards never block exits:** Close (`X`), panic flatten (`Y`), and emergency locks always execute without friction regardless of tilt band.

---

## Settings, Reports, and Your Data

- **Printable Reports:** Generate clean, print-optimized PDF reports directly through the browser.
- **Data Export:** Streamed `trades.csv` and complete `journal.json` exports based on strict column allowlists.
- **Backup & Restore:** Atomic SQLite online backups packaged with screenshots and tape logs. Archives are validated against SHA-256 manifests before any restore swap occurs.
- **Audit Wipe:** Irreversible data wipe requiring explicit confirmation (`DELETE EVERYTHING`), session lock, and zero active positions.

---

## Non-Goals

- Real-money live execution (strictly rejected at runtime).
- MT5 or proprietary broker history imports.
- Pending orders or partial position scaling.
- Multi-user SaaS, copy-trading, or social leaderboards.
- Automated AI order placement.
- Cloud speech-to-text data transmission.
- Secondary microservices or execution sidecars.

---

## Documentation

- [User Guide](./docs/userguide/README.md) — play an evening, controller map, every screen
- [Master Implementation Plan](./plans/260824-1506-evening-forex-gold-gamepad/plan.md) — Architectural decisions, phase milestones, validation logs
- [Research Compendium](./plans/260824-1506-evening-forex-gold-gamepad/research/) — Gamepad APIs, cTrader Protobuf protocols, AI integration
- [Session Development Journals](./plans/journals/) — Chronological development logs

---

<p align="center">
  <sub>Demo only · Not financial advice · Process over outcome</sub>
</p>
