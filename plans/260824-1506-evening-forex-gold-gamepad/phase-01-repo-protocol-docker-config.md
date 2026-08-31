---
title: "Phase 1: Repo, protocol, Docker config"
status: in-progress
phase: 1
priority: P1
effort: 12h
dependencies: []
---

# Phase 1: Repo, protocol, Docker config

## Overview

Scaffold the repo and freeze contracts: JSON WebSocket envelope, Pydantic catalog, cTrader-only
config, Docker Compose skeleton. No paper engine. No MT5 types. The broker module is a stub that
cannot place until phase 2.

The gateway is **one Python process and one container**. There is no execution sidecar, so there is
no local RPC contract to freeze — the broker link is an internal module boundary
(`apps/gateway/broker/`), not a wire protocol.

Protocol v1 is frozen **here**, so the journal layer's channel and messages (phases 7-14) are
declared in this phase even though nothing implements them yet. Adding them later would be a v2
migration; adding them now costs a few Pydantic models.

## Context Links

- [plan.md](./plan.md)
- [cTrader Docker research](./research/researcher-05-ctrader-docker.md)
- https://help.ctrader.com/open-api/proxies-endpoints/
- https://help.ctrader.com/open-api/account-authentication/

## Requirements

- Functional: `uv` project rooted at `apps/gateway` (Python 3.11+) with packages `protocol`, `broker`,
  `risk`, `method`, `copilot`, `journal`, `api`; plus an npm-built `apps/web` React app
<!-- Updated: Validation Session 6 - pnpm workspace and packages/exec removed with the sidecar -->
- Functional: protocol v1 `{v,t,seq,ts,ch,cid,p}`; 64KiB max; ULID `cid`; channels `quotes|orders|session|ai|voice`
<!-- Updated: Validation Session 4 - journal layer adds exactly one channel; telemetry/tilt/grades/score ride `session` -->
- Functional: `hello` + `lastSeq`; `resync` / `snap`; one WS per token
- Functional: `intent.*` carries `clutch: true`; heartbeat clutch is dead-man only
- Functional: config `broker.adapter: ctrader` only; `mode: demo`; IANA timezone required
- Functional: Docker Compose file exists with **exactly one service** (`ev-gateway`), binding only `127.0.0.1:8444`
- Non-functional: boot-fail on `mode: live`, live Open API host, `on_hot_path: true`, `timezone: local`, non-loopback listen in non-dev, `tradingview.auto_trade: true`
- Non-functional: boot-fail on `voice.stt.mode` outside `{local, off}`, `voice.bindings` resolving to LT/RT/A/B/X/Y, `tilt.gate_close: true`, or `score.weights` not summing to 1.0. These are **structural guarantees** that voice and tilt can never reach the order path, and that the score cannot be silently mis-weighted
<!-- Updated: Validation Session 4 - journal layer safety invariants enforced by config, not convention -->
- Non-functional: initial secrets arrive via env only (`CT_CLIENT_ID`, `CT_CLIENT_SECRET`,
  `CT_ACCESS_TOKEN`, `CT_REFRESH_TOKEN`, `CT_ACCOUNT_ID`, `EV_WS_TOKEN`, `XAI_API_KEY`,
  `TV_WEBHOOK_SECRET`). Refreshed cTrader tokens are persisted only in the protected app volume,
  mode `0600`, never in git, logs, the browser, or a backup archive
- Non-functional: migration runner applies every versioned migration exactly once and records each
  applied migration id; later phases own their tables instead of pretending the final schema exists
  on day one

## Architecture

Envelope and message catalog unchanged from the game protocol. The cTrader link is a **module inside
the gateway process** (`apps/gateway/broker/`), reached by direct call, not by TCP. There is no
sidecar address, no local RPC, and no second container to keep alive.

### Client → VPS

`hello`, `ping`, `sub`, `resync`, `snap`, `intent.open|close|modify|panic`, `session.lock|unlock`, `ai.ask`

Journal layer (phases 7-11): `pad.telemetry`, `voice.begin`, `voice.cancel`, `journal.memo.link`, `grade.answer`, `playbook.select`

`ai.ask`: `{cid, kind: 'research'|'plan'|'advise'|'news'|'coach', sym, tf}`  
`intent.open`: `{cid, sym, side, type:'market', lots, relativeSl?, relativeTp?, clutch: true, armedAt}`.
Relative protection is expressed in cTrader's 1/100000 distance units; MARKET orders do not carry
absolute `stopLoss` or `takeProfit`.
`intent.modify`: `{cid, positionId, sl?, tp?, clutch: true, armedAt}` for absolute protection on an
existing position; it is a broker-changing action and uses the same clutch+confirm gate as an open.
`intent.close` closes the full position. Pending orders and partial closes are outside v1.
`pad.telemetry`: 1 Hz **batch**, never per-frame — `{ts, from, to, sym, lots, reason?, clutchMs, armMs, clutchCycles, armFlips, btnRateHz, lotStepsSince, ttfMs}` plus an idle heartbeat

### VPS → client

`welcome`, `pong`, `quote`, `candle`, `order.ack|reject|upd`, `pos.snap`, `pnl`, `session`, `risk`, `sentinel.tick`, `news.item`, `signal.item`, `ai.advice`, `error`, `maint`

Journal layer (phases 7-11): `voice.transcript {voiceId, cid?, ok, text?, reason?, durMs, sttMs}`, `voice.state {busy, queued}`, `tilt {score, band, top[], cooldownUntil?}`, `grade {cid, playbookId, required_pass, required_total, clean, results[]}`, `playbook.list`, `score.session {axes, total, na[], weightsVersion}`

### HTTP surfaces (declared here, implemented in phases 6-13)

`POST /api/voice/memo` (multipart, returns `202 {voiceId}`), `GET /api/voice/:id/audio`,
`GET /api/replay/:cid`, `GET /api/replay/index`, `GET|POST /api/playbooks*`,
`GET /api/score/session/:id`, `/api/deck/*`, `/api/journal/*`, `/api/settings/*`,
`/api/reports/*`, `/api/export/*`, and `/api/data/*`.

Audio and tape ride **HTTP, never the WS**. Base64 in a 64 KiB envelope is ~16 s of audio per frame
plus chunking and reordering, on the socket whose entire job is prioritising order acks. This follows
the same reasoning as phase 6's `GET /api/deck/*`.

Quotes come from **cTrader spots**, not a random walk.

### Config sketch

```yaml
mode: demo                    # demo only; live = exit
timezone: "Asia/Ho_Chi_Minh"
broker:
  adapter: ctrader            # only value
  host: "demo.ctraderapi.com"
  port: 5035
  proto: protobuf
  account_id_env: CT_ACCOUNT_ID
  token_env: CT_ACCESS_TOKEN
  refresh_env: CT_REFRESH_TOKEN
  client_id_env: CT_CLIENT_ID
  client_secret_env: CT_CLIENT_SECRET
symbols:
  - name: XAUUSD
    max_spread: 0.80
    max_lots: 0.10
    default_lots: 0.01
    lot_step: 0.01
  - name: EURUSD
    max_lots: 0.50
    default_lots: 0.10
    lot_step: 0.01
  - name: GBPUSD
    max_lots: 0.50
    default_lots: 0.10
    lot_step: 0.01
  - name: USDJPY
    max_lots: 0.50
    default_lots: 0.10
    lot_step: 0.01
session:
  days: [sun, mon, tue, wed, thu, fri]
  start: "18:00"
  end: "23:30"
risk:
  max_positions: 1
  max_daily_loss_usd: 200
  min_seconds_between_orders: 2
  panic_flatten_on_disconnect: false
  r_unit_usd: 20              # R when no SL at entry; see phase 2 for the single R definition
  default_stop:               # per-symbol, price units
    XAUUSD: 2.00
    EURUSD: 0.0010
    GBPUSD: 0.0012
    USDJPY: 0.15
gateway:
  listen: "127.0.0.1:8444"
  static_dir: "apps/web/dist"   # gateway serves the HUD itself
  ws_path: "/ws"                # same origin as the HUD
  public_origin: "https://YOUR_DOMAIN"
  token_env: EV_WS_TOKEN
  heartbeat_s: 1
  heartbeat_dead_s: 3
  max_frame_bytes: 65536
ui:
  theme: dark                 # the only supported theme in v1
  desktop_only: true
voice:                         # phase 8
  enabled: true
  stt:
    mode: local                # local | off  — anything else exits; there is no cloud path
    model: small.en            # boot benchmark may downgrade: small -> base -> tiny -> disabled
    lang: en
  bindings: [LB+RB, "key:V"]   # exits if this resolves to LT/RT/A/B/X/Y
  hold_stream: true            # keeps the tab recording indicator lit; false costs 200-400ms/press
  max_seconds: 60
  max_bytes: 262144
  max_uploads_per_hour: 60
  stt_timeout_s: 60
  audio_retention_days: 365    # transcripts kept indefinitely
  tts: off                     # off | browser
tape:                          # phase 2 records, phase 10 replays
  dt_s: 1                      # 1 Hz bid+ask OHLC
  ring_minutes: 90
  pre_roll_s: 300
  post_roll_s: 300
  retention_days: 730
tilt:                          # phase 9
  enabled: true
  gate_close: false            # true exits: tilt may never gate a close or a panic
  warm: 0.35
  hot: 0.60
  scorched: 0.80
  confirm_hold_ms: 750         # friction 1, applied to opens only
  cooldown_s: 300              # friction 2, opens only, fails open on reconnect
score:                         # phase 11
  trades_max: 6
  band_width: 1
  decline_credit_max: 15
  weights:                     # must sum to 1.0 or the process exits
    adherence: 0.30
    selectivity: 0.25
    risk_discipline: 0.20
    preparation: 0.15
    review: 0.10
playbook:                      # phase 7
  seed_volman: true
  allow_custom: true
# copilot / method / signals / gamepad: same as previous plan (SpaceXAI, Volman M5, FF calendar, TV webhook)
```

`risk` rules are **enforced**; `playbook` rules are **graded** and never block a fire. Both come from
one registry at `apps/gateway/method/rules.py` (phase 7) so they cannot drift apart.

Volume in cTrader is **not lots**. The broker module converts HUD lots → protocol volume from
`ProtoOASymbol` at connect. If `name` is missing on the demo, refuse that symbol.

## Related Code Files

- Create: `pyproject.toml` + `uv.lock` (gateway), `.gitignore`, `.env.example`
- Create: `compose.yaml` (**one service** `ev-gateway`, volumes; no host bind except 127.0.0.1:8444)
- Create: `apps/gateway/Dockerfile` — multi-stage: a Node stage builds `apps/web/dist`, the final
  python-slim stage copies it in and adds `tini` (Twisted SIGTERM path, phase 2), `ffmpeg`,
  `whisper-cli`, and a baked `ggml-tiny.en` floor for phase 8
<!-- Updated: Validation Session 6 - three images collapse to one; tini moves to the gateway -->
- Create: `apps/gateway/protocol/__init__.py` (Pydantic v2 envelope + message catalog)
- Create: `apps/gateway/protocol/export_schema.py` (dumps JSON Schema; the web's TS types are
  generated from it so the catalog has one source of truth)
- Create: `apps/gateway/db/migrate.py` (ordered, transactional runner; bootstraps the
  `schema_migration` ledger and records every id)
- Create: `deploy/fetch-models.sh` (checksum-verified `small.en` download into the journal volume)
- Create: `apps/gateway/broker/__init__.py` (stub: `place` → `not_wired`; phase 2 wires OpenApiPy)
- Create: `apps/gateway/main.py` (healthz `{ok:true}` on the loopback bind)
- Create: `apps/web` React + Vite stub (TanStack Router, PWA manifest + service worker)
- Create: `config/default.yaml`
- Create: `README.md`

## Implementation Steps

1. `uv` project + `pytest` + protocol Pydantic round-trips.
2. Broker module interface (`health`, `snapshot`, `account`, `positions`, `place`, `close`,
   `amend_position_sl_tp`, fill callback). This is a **Python interface, not a wire protocol** —
   phase 2 implements it against OpenApiPy. There is no pending-order cancel or partial-close method.
3. Config loader: refuse live host (`live.ctraderapi.com`), `mode: live`, bad timezone, public bind, `auto_trade`.
4. One `apps/gateway/Dockerfile`: Node build stage for the web bundle, python-slim runtime with `tini`.
5. `compose.yaml` with a real `build:` context and exactly one service.
6. Gateway healthz. React PWA stub pad-connect.
7. Add the migration runner and prove ordered, transactional, idempotent application on a fresh DB.
8. Journal-layer schemas in the Pydantic catalog (`voice` channel + the message types above) and the
   new config blocks with their boot-fails. Nothing implements them yet — this is the protocol freeze,
   and it is why they land in phase 1 rather than phase 7.
9. Export the catalog's JSON Schema and generate the web's TS types from it in the build.

## Todo

- [x] `uv` project + protocol tests
- [x] Broker module interface (in-process, no wire protocol)
- [x] JSON Schema export + generated TS types for the web
- [x] Versioned migration runner with per-id tracking
- [x] Config boot-fails (live, local TZ, auto_trade, 0.0.0.0)
- [ ] Single gateway Dockerfile with the web build stage
- [ ] compose.yaml skeleton, one service, real build context
- [x] Journal-layer messages + `voice` channel in the frozen catalog for phases 7–14
- [x] Journal-layer config blocks (`voice`, `tape`, `tilt`, `score`, `playbook`, `risk.r_unit_usd`)
- [x] Boot-fails: stt mode, voice bindings, `tilt.gate_close`, score weights
- [ ] `ffmpeg` + `whisper-cli` + baked tiny.en in the gateway image; `deploy/fetch-models.sh`
- [x] README: cTrader ID -> IC Markets demo -> Open API app -> manual token paste

## Success Criteria

- [x] `uv run pytest` protocol round-trips
- [x] `mode: live` or `host: live.ctraderapi.com` exits non-zero
- [ ] `docker compose build` succeeds for the single gateway image
- [ ] `docker compose config` validates with a real `build:` context, not a placeholder, and lists
      **one** service
- [x] Generated TS types match the exported JSON Schema; a deliberate catalog change fails the web
      build until the types are regenerated
- [x] Fresh DB applies an ordered migration fixture once; a second run is a no-op and a failed
      migration rolls back without being marked applied
- [x] `voice.stt.mode: cloud`, `voice.bindings: [RT]`, `tilt.gate_close: true`, and score weights
      summing to 0.95 each exit non-zero
- [ ] `whisper-cli --help` and `ffmpeg -version` succeed inside the built gateway image

## Verification Status

Verified on this machine (`uv run pytest`: 40 passed; `ruff check`: clean; `npm --prefix app run
build`: passes through the protocol gate; gateway boots, serves `/healthz` and the HUD, and creates
`journal.db` at the configured data dir). Each of the nine boot-fails was also run as a real
process and exits `2`.

Not verifiable here — no Docker daemon in this environment. Run on the VPS before closing the phase:

- `docker compose config` lists exactly one service with a real build context
- `docker compose build` succeeds for the single gateway image
- `whisper-cli --help` and `ffmpeg -version` succeed inside the built image
- the `WHISPER_REF` build arg pins a tag that still exists upstream (default `v1.7.4` is unverified
  from here; GitHub was unreachable in this session)

### Deviations from this phase as written

- **No `apps/web` stub.** `app/` already holds 21 built screens; a second React scaffold would have
  duplicated it. `gateway.static_dir` points at the existing app's build output instead. TanStack
  Router and the PWA manifest are therefore still unstarted — they belong to phase 3, which owns
  the client agent anyway.
- **`EV_CONTAINER_BIND` and `EV_LISTEN`.** The phase requires both a loopback bind and a Docker
  port publish, which cannot both hold: Docker only forwards a published port to a process bound
  on the container's `0.0.0.0`. The bind guard now accepts a non-loopback listen only when
  `EV_DEV=1` or `EV_CONTAINER_BIND=1` is set, so the loopback guarantee moves to the publish
  (`127.0.0.1:8444:8444`) plus the host firewall. A test asserts the override cannot bypass it.
- **`paths.data_dir`.** The phase never named the journal's path. One volume root at `/data`
  (`journal.db`, `voice/`, `models/`, `secure/`), overridable with `EV_DATA_DIR`.
- **ASGI stack, ULID, and YAML libraries** were unnamed in the plan: FastAPI + uvicorn,
  `python-ulid`, `PyYAML`.

## Risk Assessment

- **Wrong volume scale on gold** — signal: 0.01 lot sends a huge ounce count. Response: convert only after `SymbolById` (light symbols carry no volume spec); fixture test.
- **OAuth token expired overnight** — signal: account auth fail. Response: refresh token on volume (phase 2).
- **Journal-layer protocol added late becomes a v2 migration** — signal: a later phase needs a message the
  frozen catalog lacks. Response: the channel, the new message types, and the HTTP surfaces are
  declared in this phase; only their implementations are deferred.
- **Gateway image bloats with models** — signal: a multi-hundred-MB image. Response: bake only the
  ~75 MB `tiny.en` floor; `small.en` lands in the journal volume via `deploy/fetch-models.sh`.
- **No token to refresh** — signal: `CT_REFRESH_TOKEN` empty. Response: initial consent is manual and documented in the README; the gateway boot-fails with a pointer to it rather than half-starting.
- **One process now means one blast radius** — signal: an unhandled broker-callback exception takes
  the whole gateway down, where it used to kill `ev-exec` alone. Response: the broker module owns a
  containment boundary from phase 1; callbacks may not raise past it. Phase 2 tests it.

## Security Considerations

- No secrets in yaml or images. `.env` gitignored.
- The single container publishes nothing beyond the `127.0.0.1:8444` loopback bind.

### README: cTrader credentials (one-time, manual)

1. Create a cTrader ID.
2. Open an **IC Markets** cTrader **demo** account under it.
3. Register an Open API application at connect.spotware.com; wait for approval.
4. Run the consent flow in a browser with the `trading` scope against the app's redirect URI.
5. Paste `CT_CLIENT_ID`, `CT_CLIENT_SECRET`, `CT_ACCESS_TOKEN`, `CT_REFRESH_TOKEN`, `CT_ACCOUNT_ID` into `.env`.

No auth helper ships in v1 — the gateway only refreshes what step 5 provided.

## Next Steps

Phase 2 implements Open API spots/orders against these types.
