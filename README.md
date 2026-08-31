# Evening Forex Gold Gamepad

![Trading Game — discipline, process, improvement](./visual01.png)

A desktop Chrome **web game** — an installable, client-side **React PWA** — where an **8BitDo
Ultimate 2 Wireless** trades forex and gold on a **cTrader demo account**. The pad talks WebSocket to
a single **Python gateway** on an Ubuntu VPS (Docker) that speaks the **cTrader Open API** in-process
through `ctrader-open-api`. There is no execution sidecar and no second service. A near-realtime
**AI desk** coaches from the sidelines and never touches the order path.

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

**Status:** phases 1–4, 6 and 7 landed in code — frozen protocol, config boot-fails, migrations, risk gates,
the cid ledger, the journal and tape pipeline, the game socket, the cTrader client, and the 8BitDo
client agent, the AI desk and sentinel, the performance deck, and the playbook with
trade grading. Three things are still
**unverified**: the broker link needs an IC Markets demo account and an approved Open API app, the
pad has never been held (no 8BitDo hardware here), and the desk stays offline until
`copilot.model` and `XAI_API_KEY` are set. Phase 5 (VPS deploy) is the remaining gap. The
authority for everything below is
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

**Pairing the 8BitDo Ultimate 2 Wireless**

1. Put the switch on the back to **X** (XInput). Chrome then reports `mapping: "standard"` and the
   table above holds with no calibration.
2. Plug the **2.4G dongle** into the Mac and press **Start**. The dongle is the supported path.
3. Wired USB-C is the fallback and behaves identically; use it if the dongle drops.
4. Open the HUD, focus the tab, and **press any button** — the Gamepad API stays silent until the
   page has seen one (a spec privacy gesture), so the HUD reports "pad: absent" until you do.
5. Paddles (L4/R4) are adopted only if a first-run probe sees one move. If it never does, the game
   stays on LT/RT forever — nothing degrades.

**The tab must stay focused.** Hiding it or unplugging the pad cancels any arm on the spot and
locks new opens at both ends: the client stops sending, and the gateway's dead-man rejects. Close,
panic, and the HUD's own **FLATTEN** button keep working regardless — a dead pad must never trap an
open position.

## Architecture

![How the Evening Forex Gold Gamepad works](./docs/how-the-app-works.svg)

[Open the standalone diagram](./docs/how-the-app-works.html).

For a new member, the system has one important boundary: the **gateway is the only component that
can approve a demo order**. The controller and the PWA prepare intent; the Python gateway itself
translates an approved command into cTrader Open API messages over its own `ctrader-open-api`
connection, and Spotware remains the actual matching engine.

Read the diagram as three paths:

1. **Order hot path:** controller → focused Chrome tab → gateway risk checks → the gateway's own
   cTrader Open API connection → cTrader demo.
2. **Broker return path:** market data, fills, positions, and acknowledgements travel back through
   the same trusted services to update the HUD and rumble the controller.
3. **Learning path:** AI coaching, voice transcription, journal writes, replay, and scoring run
   beside the order path. They can enrich or record a session, but cannot place an order.

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
| Execution | cTrader Open API in-process via `ctrader-open-api` (OpenApiPy), `demo.ctraderapi.com:5035` (Protobuf) |
| Broker | IC Markets cTrader demo (plain, unsuffixed symbols) |
| Host | Ubuntu VPS, Docker Compose, **one service** (`ev-gateway`) |
| Live money | Refused — boot-fail on live host or `isLive` |
| Symbols | XAUUSD, EURUSD, GBPUSD, USDJPY; max 0.10 lot gold |
| Session | `Asia/Ho_Chi_Minh`, 18:00–23:30 |
| Transport | WSS JSON `{v,t,seq,ts,ch,cid,p}` on `/ws`, same origin as the HUD |
| Bind | Gateway `127.0.0.1:8444` behind existing VPS TLS on :443 |
| Copilot | Python worker task inside `ev-gateway`, not a second container |
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
| Web stack | Client-side **React PWA** (Vite + TanStack Router/Query). No SSR, no Node at runtime |
| Backend stack | **Python** — one process owns WS, REST, risk, journal, static HUD, and the broker link |
| Database | Phase-owned migrations `001`–`010` |

## Phases

Recommended delivery order is sequential. Phase files declare minimum direct dependencies, but the
acceptance gates follow migration, navigation, and evidence contracts from `1` through `14`.

```text
1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13 → 14
```

| # | Phase | Effort | Status |
|---|-------|--------|--------|
| 1 | [Repo, protocol, Docker config](./plans/260824-1506-evening-forex-gold-gamepad/phase-01-repo-protocol-docker-config.md) | 12h | Built |
| 2 | [cTrader exec and socket gateway](./plans/260824-1506-evening-forex-gold-gamepad/phase-02-ctrader-exec-and-socket-gateway.md) | 22h | Built |
| 3 | [Web game and 8BitDo client agent](./plans/260824-1506-evening-forex-gold-gamepad/phase-03-web-game-and-8bitdo-client-agent.md) | 18h | Built |
| 4 | [AI desk: sentinel, news, Volman, advise](./plans/260824-1506-evening-forex-gold-gamepad/phase-04-ai-desk-sentinel-news-volman.md) | 18h | Built |
| 5 | [Ubuntu Docker deploy](./plans/260824-1506-evening-forex-gold-gamepad/phase-05-ubuntu-docker-deploy.md) | 7h | Pending — needs the VPS |
| 6 | [Performance and psychology deck](./plans/260824-1506-evening-forex-gold-gamepad/phase-06-performance-and-psychology-deck.md) | 14h | Built |
| 7 | [Playbook, rule registry, trade grading](./plans/260824-1506-evening-forex-gold-gamepad/phase-07-playbook-and-trade-grading.md) | 12h | Built |
| 8 | [Voice: capture, whisper.cpp, coach](./plans/260824-1506-evening-forex-gold-gamepad/phase-08-voice-capture-whisper-and-coach.md) | 14h | Deferred |
| 9 | [Tilt telemetry and adaptive friction](./plans/260824-1506-evening-forex-gold-gamepad/phase-09-tilt-telemetry-and-adaptive-friction.md) | 10h | Built |
| 10 | [Trade replay](./plans/260824-1506-evening-forex-gold-gamepad/phase-10-trade-replay.md) | 12h | Built |
| 11 | [Process Score and radar deck](./plans/260824-1506-evening-forex-gold-gamepad/phase-11-process-score-and-radar-deck.md) | 8h | Built |
| 12 | [Daily journal cockpit and preparation](./plans/260824-1506-evening-forex-gold-gamepad/phase-12-daily-journal-cockpit-and-preparation.md) | 24h | Built |
| 13 | [Reports, settings, and data portability](./plans/260824-1506-evening-forex-gold-gamepad/phase-13-reports-settings-and-data-portability.md) | 18h | Pending |
| 14 | [End-to-end session journey and release gate](./plans/260824-1506-evening-forex-gold-gamepad/phase-14-end-to-end-session-journey-and-release-gate.md) | 14h | Pending |

Total: 203h ≈ 26 working days.

## Repo layout

```text
app/              React PWA (Vite), built and served by the gateway. Node is
                  build-time only.
  src/protocol/   GENERATED from the gateway catalog — schema.json + types.ts
  scripts/        check-protocol-types.mjs — fails the build on type drift
apps/
  gateway/        Python — one process, one container:
    protocol/     Frozen v1 envelope + Pydantic message catalog (phase 1)
    broker/       cTrader Open API via ctrader-open-api — stub until phase 2
    risk/         cid reserve, limits, dead-man, session lock (phase 2)
    method/       Rule registry (risk + playbook), Volman method profile (phase 4/7)
    copilot/      AI desk worker task (read-only tools, never on the hot path)
    journal/      SQLite writes, tape, replay, score
    api/          WS /ws, REST /api/*, static HUD
    db/           migrate.py + versioned migrations/
config/           default.yaml
deploy/           fetch-models.sh, reverse-proxy notes
docs/             release checklist and verified operating decisions
plans/            Plan of record, phase files, research, journals
```

**Where the journal lives.** One Docker volume, `ev-journal`, mounted at `/data`:
`/data/journal.db` (SQLite — trades, plans, grades, tilt samples, scores), `/data/voice/` (memo
audio), `/data/models/` (whisper `small.en`), `/data/secure/` (refreshed cTrader tokens, `0600`).
One volume means one backup root; nothing durable lives in the image, the repo, or the browser.

## Getting started

Phase 1 has landed: the protocol is frozen, the config boot-fails, the migration runner works, and
the gateway answers `/healthz`. The broker is a stub that refuses every order until phase 2, so
nothing can be traded yet.

**Prerequisites**

- Ubuntu VPS, 4+ vCPU / 4 GB+ RAM, Docker + Compose, existing TLS on :443
- Python 3.11+ with `uv`; Node 22 for the web build only
- Chrome on the desktop, 8BitDo Ultimate 2 with its 2.4G dongle
- A cTrader ID with an **IC Markets demo** account

**cTrader credentials (one-time, manual — no auth helper ships in v1)**

1. Create a cTrader ID.
2. Open an IC Markets cTrader **demo** account under it.
3. Register an Open API application at `connect.spotware.com`; wait for approval.
4. Run the consent flow in a browser with the `trading` scope against the app's redirect URI.
5. Paste `CT_CLIENT_ID`, `CT_CLIENT_SECRET`, `CT_ACCESS_TOKEN`, `CT_REFRESH_TOKEN`, `CT_ACCOUNT_ID`
   into `.env`. The gateway only refreshes what you provided here, and boot-fails if it is missing.

Other secrets: `EV_WS_TOKEN`, `XAI_API_KEY`, `TV_WEBHOOK_SECRET`. Initial secrets go through env;
refreshed cTrader tokens use the protected app volume with mode `0600`. Neither is committed, baked
into an image, exported, or included in backups.

**Run**

```bash
cd apps/gateway
uv sync                   # gateway deps, including ctrader-open-api
uv run pytest             # protocol, boot-fails, migrations, risk gates, R, tape, socket
uv run ruff check .
cd ../..

npm --prefix app ci
npm --prefix app run build   # checks generated protocol types, then builds the HUD bundle

cp .env.example .env      # then fill in the cTrader credentials above
docker compose build
docker compose up -d      # ev-gateway on 127.0.0.1:8444 — the only service
curl -s http://127.0.0.1:8444/healthz
```

Then open `https://YOUR_DOMAIN` in a focused Chrome tab, connect the pad, and the HUD and socket come
from the same origin.

**Protocol types are generated, never hand-written.** The Pydantic catalog in
`apps/gateway/protocol/` is the single source of truth; `app/src/protocol/schema.json` and
`types.ts` are built from it:

```bash
cd apps/gateway && uv run python -m protocol.export_ts          # regenerate
cd apps/gateway && uv run python -m protocol.export_ts --check  # fail if stale
```

Three gates catch drift: `uv run pytest`, `npm --prefix app run build`, and the image build itself.

**Local dev without Docker.** The gateway refuses a non-loopback bind unless `EV_DEV=1` (your own
machine) or `EV_CONTAINER_BIND=1` (inside the container, where Docker publishes the port to host
loopback only). `EV_DATA_DIR` moves the whole volume — DB, voice, models, tokens — somewhere
writable:

```bash
cd apps/gateway
EV_CONFIG=../../config/default.yaml EV_DATA_DIR=../../data uv run python main.py
```

## Playbooks: enforced vs graded

A **playbook** is a named setup with explicit rules — one of five seeded from the detectors, or one
you write. Every fire is graded against the playbook that was active when it fired, and the grade
appears in the confirm overlay **before** you commit:

```
BUY 0.10 XAUUSD @ 2345.12
[M5 range break]  4/5 rules OK  ·  ✗ Not chasing (3.00 ATR)
```

The distinction the whole feature rests on:

| | Risk rules | Playbook rules |
|---|---|---|
| Where they live | one registry, `method/rules.py` | the same registry |
| What a failure does | **rejects the intent** server-side | **is recorded and shown** |
| Who decides them | config, and only config | you |

A playbook rule can never block a trade. That is asserted by a test, not by convention — the
failure mode it guards against is the journal quietly turning into a gate nobody agreed to.

Three more things it deliberately does:

- **Grading is keyed on the fire, not the position.** A cancelled arm and a rejected intent are
  both graded, which is what lets the deck count trades you declined.
- **Skipping the post-trade checklist costs nothing.** An unanswered rule is `unknown` — neither
  pass nor fail — and leaves the denominator entirely.
- **No playbook selected is a valid state.** The fire grades as `unplanned`, which reads honestly
  on the deck rather than as a failure.

Retiring a playbook hides it from selection and keeps it resolvable, so last month's deck numbers
survive a change of mind.

## The deck, and what it refuses to show

`/deck` answers one question: **am I improving?** It opens on the **process** panel and there is
not a single dollar figure on it — not a balance, not a P/L, not a return. Watching the money
mid-trade is what pulls attention off the process, so the outcome tab is a deliberate click, and
its figures are not even fetched until you make it.

What the process panel measures:

| Figure | Why it is there |
|---|---|
| **Adherence** | Fraction of fires that satisfied every rule. Scored with the gateway's *own* rule set, imported rather than re-listed, so the deck cannot claim a rule the gate never had |
| **Trades declined** | Arms cancelled while a stand-down condition was live. Counts **upward** — not trading is a position |
| **Opportunity quality** | What the tape actually offered that evening. A flat night on a dead tape reads as discipline, not as a missing result |
| **Check-in** | Two pad taps, skippable, plotted against adherence — never against money |
| **This month vs last** | The primary "am I improving?" answer |

What it deliberately refuses:

- **No streaks, levels, badges, or leaderboards.** Every one of them creates pressure to trade a
  dead tape.
- **No Sharpe below 30 sessions.** ~20 evenings a month means the first two months are noise, so
  the deck prints "not enough sessions yet" and the sample size instead of a confident number.
- **No zero standing in for "not measured".** An evening with no fires has *no* adherence score
  rather than a score of zero; scoring a stand-down at zero would punish the exact behaviour the
  deck exists to reward.
- **No money in a notification, ever.**

The desk can read these process figures through its one read-only `get_progress` tool and coach
the process with them. It cannot see a balance, and it still has no order tool.

Process framing after Brett Steenbarger (*The Daily Trading Coach*, *Trading Psychology 2.0*,
*Enhancing Trader Performance*) — cited, not reproduced.

## The daily journal

`/journal` is the loop the rest of the product feeds: **prepare, trade, close, review**, without
leaving the shell.

**Today** carries four IANA market clocks (Sydney, Tokyo, London, New York — real tzdata, so
London and New York move across DST and Tokyo never does), a five-item readiness check, the
evening's written analysis, and a position-size calculator. The desk's own plan sits *beside* your
analysis rather than merged into it; no model writes a word of what you wrote.

**Sizing** runs on the gateway, through phase 2's own quote-to-USD conversion and the broker's real
volume step. It answers with three numbers kept deliberately apart: the lots your risk implies, the
lots the broker will actually accept, and the risk you will therefore **carry** — recomputed from
the rounded volume, because reporting the risk you asked for rather than the one you will hold is
lying by omission. It rounds down, never up. Applying a result changes the HUD's preview; LT+RT is
still the only thing that trades.

**The dashboard** leads with Process Consistency over the last 20 sessions —
`0.5 × mean + 0.5 × (100 − mean absolute deviation from the median)`. Two halves doing different
jobs: the mean says how well you played, the deviation says how reliably. It always prints `n` and
refuses a confident number below five sessions, because four evenings is a week, not a process. The
day heatmap is coloured by **Process Score** and activity; a day with no score is an outline, not a
bad day, and there is no dollar figure on the surface at all.

**History** filters on period, playbook, setup, symbol, timeframe, side, market session, intent,
mistake, and win/loss/breakeven. The clauses are built from a fixed table on the server, so an
unknown filter is dropped rather than interpolated and a combination can never return a trade
outside what was asked for. Paging is capped at 200.

**A trade** shows the immutable plan and execution, then everything you reviewed on top: Actual vs
Plan, the three execution scores, the grade, mistakes, attachments, and a link to the tape.

Things the journal deliberately will not do:

- **It cannot rewrite a fact.** Every write targets a review table; a test parses the service's
  statements and fails if any of them names `trade_plan`, `trade_closed`, `position_event`,
  `trade_tape`, `trade_grade`, `cid_reservation` or `session_equity`. A journal that can edit a
  fill is not a journal.
- **It never claims a counterfactual.** The panel is called *Actual vs Plan*, not "theoretical
  profit". Where price went after your exit is not evidence about a position you had closed.
- **It never infers that you were on tilt.** A clean fire under a real playbook derives as
  `planned`; anything else stays `unknown` until you say otherwise. `impulsive` and `revenge`
  describe a state of mind, and the four-group chart **excludes** the unclassified rather than
  guessing — the cost of libelling one clean discretionary trade is that you stop trusting the
  whole record.
- **Unknown is never zero.** The before/during/after scores drop what was not captured and
  renormalise, and each names the inputs it could not measure, so a high score over a small
  denominator looks like one.
- **A mistake costs nothing.** The taxonomy separates what the rows *prove* (oversize, no initial
  stop, a stop moved further away, an event-window fire) from what only you can assert (early
  discretionary exit, chased entry, revenge re-entry). You can withdraw your own judgement; a
  derived one comes back on the next sync, because it is a fact. There is no streak, badge, or
  penalty, and none of it reaches the Process Score.
- **Readiness never blocks anything.** A checklist that can lock you out is one you click through,
  and then it measures nothing. It has three answers, not two: skipping is a real answer and
  different from "no".
- **Attachments cannot name a path.** The server reads the magic bytes, decides what the file
  actually is, generates a ULID, and writes that; your filename is stored as a label. PNG, JPEG and
  WebP only — no SVG and no HTML, because an image that can run script is a stored XSS with a
  `.png` on the end.
- **The desk sees counts, never your words.** `get_journal` returns session counts, consistency and
  the top mistake codes. Your analysis, review notes and memos never leave the box — a journal you
  cannot write privately is one you stop writing honestly.

## The Process Score

TradeZella's Zella Score gives you one number to chase. That is the right game mechanic pointed at
the wrong inputs — win rate and profit factor are *outcome*, and chasing an outcome number is the
anxiety this whole design exists to treat. So the mechanic stays and the inputs change.

Five axes, all process:

| Axis | What it measures | w |
|---|---|---|
| **Adherence** | Required playbook rules passed / required rules evaluated, over the evening | 0.30 |
| **Selectivity** | How well the trade count matched what the tape actually offered | 0.25 |
| **Risk discipline** | Per fire: lot cap, stop at entry, R within tolerance, position cap, order spacing | 0.20 |
| **Preparation** | Plan acknowledged before the first fire, pre check-in, a playbook selected | 0.15 |
| **Review** | Post check-in, checklists answered, a replay opened | 0.10 |

The property the whole thing is built around: **a correctly-declined evening scores at least as well
as a well-traded one.**

| Evening | Score |
|---|---|
| Dead tape, zero trades, three genuine stand-downs | **100** |
| Busy tape, four fires, executed well | **98** |
| Rich tape, froze, took nothing | **70** |
| Dead tape, overtraded it | **65** |

Timidity costs less than recklessness, and both cost something. Those four numbers are the unit
tests, not an illustration — if they drift, the score has changed meaning.

**Selectivity** is the mechanism. The sentinel scores each evening's opportunity quality; `expected =
round(OQ x 6)` sets a band of ±1 trade, and each trade outside it costs 25. A genuine stand-down —
an ARM cancelled while a stand-down condition was live — earns 5 back, capped at 15, using phase 3's
existing counter rather than a second one. The credit cannot push the axis past 100, so declining is
never a way to farm a perfect evening.

**Vacuous axes** are the subtle part. With zero fires, Adherence and Risk Discipline have no
denominator. Scoring them 0 punishes standing down; scoring them 100 is free points for doing
nothing. Both are wrong, so the axis is **dropped** and its weight renormalises across the axes that
have evidence — and the radar draws it as a dashed *n/a* ring that names why, never as a zero spoke.
Axes are vacuous at zero fires only: one bad fire gives both a real denominator, so nothing hides
behind renormalisation.

What the score deliberately will not do:

- **No outcome input, anywhere.** Not P/L, not R, not win rate. A test reads the module and fails if
  a money word appears in it.
- **No live score.** It is computed at session close and lives on the deck. A number you can refresh
  mid-trade becomes the anxiety the P/L replaced.
- **Tilt is not an input.** Taxing an evening for a bad ten minutes reintroduces the punishment this
  design avoids. It renders on the deck as a *retrospective*, set against adherence — never against
  P/L.
- **Nothing accumulates across sessions.** No streak, no level, no badge, no "days since". A test
  walks the whole schema and fails if such a column ever exists. The month view is a **distribution
  with n**, because a distribution says "this is the shape of your evenings" and a streak says "do
  not break it", which is pressure to trade a dead tape.
- **No memo penalty for a feature that is not built.** Voice evidence counts only when capture was
  actually available; a supported degradation drops the sub-item instead of failing it. Skipping a
  memo you *could* have recorded is a genuine miss.

Every axis stores its **inputs**, not just its total, so changing `score.weights` recomputes every
past evening from what was actually measured rather than leaving last month scored under a weighting
nobody can reconstruct. Weights that do not sum to 1.0 refuse to boot.

Process framing after Brett Steenbarger — markets do not offer equal opportunity every night.
Cited, not reproduced.

## Trade replay

TradeZella's trade replay, on the hardware you traded with. Open a closed trade and scrub it back
through the tape it actually happened on: the ARM you cancelled forty seconds before you fired, the
stop you moved, the band you crossed, where MFE and MAE really sat.

| Input | Action |
|---|---|
| **LS ←→** | scrub, velocity-based (deadzone 0.2) |
| **RS ←→** | zoom the window — 1s, 5s, 15s, 1m, 5m |
| **A** | play / pause |
| **D-pad ↑↓** | speed 0.5x · 1x · 2x · 4x |
| **LB / RB** | previous / next trade of the evening |
| **B** | exit |

The tape is one row per trade, frozen after the post-roll settles: 1 Hz OHLC for **both sides of
the book** (a long's excursions are measured on the bid, a short's on the ask), plus the events,
denormalised at freeze time from the pad telemetry, the broker, the signals and the tilt samples.
About 12-20 KB a trade. A zero-trade evening writes nothing at all.

Every displayed timeframe is folded out of that one stored series, so a 5-minute view and the
second-by-second tape can never disagree. The aggregation stays on the scaled integers and the
divide happens once, when drawing.

Things it deliberately will not do:

- **No order can be placed from a replay.** Not because a flag says so: the route mounts no agent
  and no socket. Selecting a screen unmounts the previous one, so arriving here destroys the live
  HUD's order path rather than merely locking it, and the pad on this route drives an action type
  that has no order case to construct. Tests assert both halves.
- **Nothing on the replay path writes.** A test reads the repository and fails if any statement it
  runs is not a `SELECT`.
- **Entry and exit are never inferred from the bars.** At 1 Hz the entry candle is context; the
  fill is truth, so the markers come from `trade_closed`.
- **MFE and MAE are drawn as price lines, not dots.** The freeze stores the extremes, not when they
  happened, so a timestamped dot would be a fabrication. They print in R only when a recorded stop
  makes R knowable — otherwise the price distance prints as itself.
- **A trade with no tape still opens**, as a marker-only view, and so does one whose blob will not
  decompress. A pre-phase-2 trade is still worth reviewing.
- **Memo audio takes its length from the stored `durMs`**, never `audio.duration` — Chrome's
  MediaRecorder WebM reports `Infinity`. Above 2x the memo mutes rather than pitch-shifting. Until
  phase 8 lands there are no memos, and replay works identically without them.

## Tilt: what it measures, and what it cannot do

Edgewonk asks you to rate your emotional state after the fact. The pad is already telling us. Every
component of the tilt score is a **measured behaviour** with a name, never an inferred feeling,
which is why the HUD can always say *why* instead of just showing a colour:

| Component | What it measures | Weight |
|---|---|---|
| **Revenge size** | Pending lots against your own session median | 0.25 |
| **Re-entry speed** | Seconds since a *losing* close — 1 under a minute, 0 by ten | 0.20 |
| **Rule-break recency** | Adherence failures in your last three fires | 0.20 |
| **Hesitation** | Clutch cycles before each arm, over the last three | 0.10 |
| **Arm flip** | Side changes while armed | 0.10 |
| **Input aggression** | Button rate against your own session median | 0.10 |
| **Voice arousal** | Speech rate and loudness against your own 30-session baseline | 0.05 |

Everything compares you to **you**. There is no population claim anywhere in the number, and a
component that was not measured drops out and the rest renormalise — an evening without a voice
memo is scored on behaviour alone, not on a guess.

What the bands do:

| Band | HUD | What changes about firing |
|---|---|---|
| `< 0.35` calm | green pip | nothing |
| `0.35` warm | amber pip, top driver named | **nothing** — a warning that costs nothing is one you keep listening to |
| `0.60` hot | red pip, driver + the evening's R in the confirm overlay, one desk advice | ARM → FIRE needs the confirm **held 750 ms** instead of a tap |
| `0.80` scorched | countdown and a prompt to log a memo | opens paused for 300 s |

Narrating the state is the intervention, so a memo recorded during a cooldown — or an explicit
acknowledgement — **halves the recency terms**. The productive way out is rewarded; the door is not
merely locked.

What tilt cannot do, structurally rather than by convention:

- **It cannot slow or block an exit.** `intent.close`, `intent.panic`, the HUD Flatten button and
  `session.lock` run no gates at all. `tilt.gate_close: true` refuses to boot, and a test forces the
  score to 1.0 and asserts a close and a panic both still execute.
- **It cannot reach the Process Score.** Taxing an evening for a bad ten minutes would reintroduce
  the punishment this whole design exists to avoid. A test greps the deck's metrics module for the
  word.
- **It cannot move the FSM.** It changes exactly two things: the `confirmHoldMs` parameter of the
  existing fire predicate, and whether the server accepts an open. The pad's state machine is
  byte-identical with tilt on or off.
- **It cannot classify you.** No keyword scoring, no profanity detection, no affect model, no LLM
  anywhere in the score. Voice contributes two arithmetic deviations from your own baseline, capped
  at 5%, and is designed to be deleted rather than defended if a month of data does not support it.
- **It cannot trap you.** The cooldown **fails open** — deliberately the opposite of the dead-man.
  An unusable clock or a lost cooldown allows trading, because the dead-man is about unattended
  input and this is a judgement call.
- **It cannot become a trait.** Tilt is per-session state plus `tilt_sample` rows for the deck's
  retrospective. Nothing is persisted about you, only about an evening.
- **`tilt.enabled: false` removes it entirely** — the gate, the friction, the pip, and the desk's
  `get_tilt` tool with it.

The desk sees the band, the score, and the driver sentences already on your screen. It never sees a
component value or a pad frame.

## Non-goals

Paper simulator. MT5/broker-history import. Pending orders or partial closes. Multiple accounts or
markets. Mobile delivery or light mode. Wine. Live money. Multiplayer / SaaS / copy-trading. Native HID helper.
Auto-trading AI, including TradingView `auto_trade`. Scraping Supercharts. Guaranteed profit.
Leaderboards, streaks, levels, badges, or any deck mechanic that punishes standing down. Edgewonk's
what-if trade simulator. Cloud speech-to-text. Voice or AI on the order path. Voice as navigation.
A second compose service. An execution sidecar or any cross-process broker hop. Server-side
rendering, server functions, or Node at runtime.

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
