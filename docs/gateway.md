# ev-gateway

The backend. One Python process and one container: it owns the WebSocket, the
REST surfaces, the risk checks, the journal, the static HUD, and the cTrader
link. There is no execution sidecar and no second service, so an approved intent
reaches the broker by direct call rather than by a local socket hop.

## Layout

```
apps/gateway/
  protocol/     Frozen v1 envelope + Pydantic message catalog + JSON Schema export
  broker/       cTrader Open API link, volume/price scaling, asset conversion
  risk/         Rule registry, session window, the single R definition
  journal/      SQLite writes, 1 Hz tape ring, per-trade freeze
  api/          Gateway state, /ws session
  db/           Migration runner + phase-owned migrations
  method/       (phase 7) rule registry moves here; risk/rules.py will import it
  copilot/      (phase 4) AI desk worker task
  tests/
config/default.yaml
compose.yaml         one service, 127.0.0.1:8444 only
deploy/fetch-models.sh
```

## Run it

```bash
uv sync --all-extras
uv run pytest                                  # 210 tests, no credentials needed
uv run python -m apps.gateway.db.migrate       # applies 001-core-trading
uv run python -m apps.gateway.protocol.export_schema
node app/scripts/gen-protocol-types.mjs        # regenerate the web's TS types

cp .env.example .env && $EDITOR .env           # see README for the manual flow
uv run python -m apps.gateway.main             # 127.0.0.1:8444
curl -s localhost:8444/healthz
```

`docker compose build && docker compose up -d` builds the same thing as one
image, with the web bundle baked in.

## Running without credentials

`broker.transport` picks how ProtoOA messages are delivered:

| value | what it does |
|-------|--------------|
| `real` | TLS socket to `demo.ctraderapi.com:5035`. Needs the full `.env`. |
| `mock` | Answered in process by `broker/mock.py`. Needs only `EV_WS_TOKEN`. |
| `none` | The phase 1 stub. Refuses every broker-changing call with `not_wired`. |

```bash
EV_WS_TOKEN=dev EV_CONFIG=config/mock.yaml uv run python -m apps.gateway.main
```

`config/mock.yaml` is that setup ready to run: mock transport, a 24/7 session
window so opens are not refused during the working day, and the copilot off.

Anything but `real` is a **boot-fail unless `dev: true`**, reports
`"simulated": true` in `/healthz`, and logs a banner at startup. A mock broker
must never be something you are running by accident.

What the mock replaces is the *socket*, not the protocol. The gateway still
builds genuine `ProtoOANewOrderReq` messages and the mock answers with genuine
`ProtoOAExecutionEvent` messages, so symbol mapping, the lots/volume scale,
execution translation, the `isLive` guard, and error-code mapping are all
exercised for real. It reproduces the orderings that matter: `ORDER_ACCEPTED`
first and `ORDER_FILLED` on a later tick, one-sided spot ticks, stop-outs with
no request, and rejections on a bad volume grid.

What it cannot tell you is whether the *numbers* match IC Markets. Its symbol
specs are invented. Phase 2 is not done until a real `SymbolsList` +
`SymbolById` dump lands in `broker/fixtures/` and a 0.01-lot gold round trip has
been eyeballed in cTrader web.

## The parts worth knowing

**The protocol is frozen.** `protocol/catalog.py` holds every message type,
including the journal layer that phases 7-14 implement. Adding a type later
would be a v2 migration; declaring them now cost a few Pydantic models. The web
app's TypeScript types are generated from the exported JSON Schema, so a catalog
change that skips regeneration fails the web build.

**Safety invariants are boot-fails, not conventions.** `config.check_invariants`
refuses to start on `mode: live`, a live Open API host, `copilot.on_hot_path`,
`tradingview.auto_trade`, an STT mode outside `{local, off}`, a voice binding
that resolves to LT/RT/A/B/X/Y, `tilt.gate_close`, score weights that do not sum
to 1.0, a non-IANA timezone, or a non-loopback bind outside dev. Each exits
non-zero with a named invariant.

**A close and a panic are never gated.** Every open-only rule in
`risk/rules.py` declares `applies_to = OPEN_ONLY`, and both the test suite and a
boot assertion check that no such rule can reach `intent.close` or
`intent.panic`. Tilt friction (phase 9) lands in this registry as
`risk.cooldown`, already open-only, so it cannot stand between the player and an
exit. They still need the clutch — exempt from risk gates is not exempt from the
confirm contract.

**R is defined once**, in `risk/r.py`. Protocol volume is cents of a unit, so
`units = volume / 100`; raw stop risk is `units * distance` in the symbol's
*quote* asset, converted to USD through `broker/conversion.py` at the entry-time
rate, with the rate, chain, and timestamp stored alongside the plan. It is
computed from the stop **distance**, because that is what a MARKET order
carries — so R is known at FIRE without waiting for a fill price.
XAUUSD is identity; USDJPY is JPY and must be converted before it may be called
USD. Phase 12's position-size calculator is the tested inverse of the same
function, so the HUD and the journal cannot disagree about the same trade.

**The tape is tapped before conflation.** The HUD sees quotes at 10-20 Hz; the
ring sees every tick and stores 1 Hz bid+ask OHLC with `n_ticks`. MFE/MAE read
the side the trade would actually exit on — bid for a long, ask for a short —
because measuring both from one side would flatter every short by a full spread.

**One process is one blast radius.** That is the cost of removing the sidecar,
and `broker/base.py`'s `Containment` is where it is paid: a raised exception in
a broker callback becomes an `order.reject` or a `maint` frame and never reaches
the reactor. Tested.

**Migrations are phase-owned.** The runner records every applied id, refuses a
migration edited after the fact, and rolls a failure back without marking it
applied. `001-core-trading.sql` holds the phase 2 core and nothing a later phase
owns.

**Two calls per symbol, on purpose.** `SymbolsListReq` returns
`ProtoOALightSymbol` — ids, names, and base/quote assets, and no volume spec at
all. `SymbolByIdReq` returns `ProtoOASymbol` — digits, lotSize, min/step/max
volume, and no name and no assets. `SymbolSpec` is the join, and the broker
refuses a symbol it has not resolved through both. Reading min/step/max off the
light record is the bug that sends a thousand times the intended ounces of gold.

**`isLive` is checked before account auth.** It lives on
`ProtoOACtidTraderAccount`, reached through `GetAccountListByAccessToken`, so a
live account is refused before the gateway has even authenticated — let alone
placed anything.

## What is not implemented

The broker link itself is written and tested against the mock, but it has never
spoken to Spotware. Phase 2 is done when its prerequisites are met — a cTrader
ID, an IC Markets demo account, an approved Open API application, the manual
consent flow, and a real symbol dump in `broker/fixtures/` — and the acceptance
criteria pass against the real endpoint.

Phase 2's code is complete. The tape freezes at `closed_at + post_roll_s` and
flushes on shutdown, MFE/MAE land on the closed trade, equity is snapshotted at
open, once a minute, and at close, M5 history seeds the chart, and a watchdog
re-authenticates and reconciles when the broker link comes back. What it has
never done is speak to Spotware.

Phase 7 is in: the rule registry moved to `method/rules.py` with two
consequences — `risk` rules are enforced by `risk/rules.py`, `playbook` rules
are graded and structurally cannot reject (no `applies_to`, no `reason`, and a
test asserts it). Five Volman M5 playbooks seed on first boot; grading is a pure
function over context, keyed on the cid so a declined fire is gradeable too, and
an unanswered manual rule is *unknown* rather than failed, so skipping the
post-trade checklist costs nothing.

Phase 9 is in: tilt is composed only from behaviours you can name, each
measured against the player's own rolling baseline. A missing component
redistributes its weight rather than scoring zero — absent evidence is not calm.
Friction is exactly two things: a 750 ms confirm hold from `hot` upward, and a
soft block on **opens** at `scorched`. A close and a panic are exempt in both
directions — the cooldown reaches the order path only as the registry's
OPEN_ONLY `risk.cooldown` rule, and the client's fire predicate zeroes the hold
for a safety exit itself. Starting a memo halves the recency terms, because
narrating it is the intervention. No keyword scoring, no affect classification,
no LLM in the score, and tilt is never stored against the player.

Phases 4, 6, 8, and 10-14 are untouched: `ai.ask` answers `{disabled: true}`, and
the voice, replay, and score messages are accepted and dropped.
