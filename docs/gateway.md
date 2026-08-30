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
uv run pytest                                  # 160 tests, no broker needed
uv run python -m apps.gateway.db.migrate       # applies 001-core-trading
uv run python -m apps.gateway.protocol.export_schema
node app/scripts/gen-protocol-types.mjs        # regenerate the web's TS types

cp .env.example .env && $EDITOR .env           # see README for the manual flow
uv run python -m apps.gateway.main             # 127.0.0.1:8444
curl -s localhost:8444/healthz
```

`docker compose build && docker compose up -d` builds the same thing as one
image, with the web bundle baked in.

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
`units = volume / 100`; raw stop risk is `units * abs(entry - sl)` in the
symbol's *quote* asset, converted to USD through `broker/conversion.py` at the
entry-time rate, with the rate, chain, and timestamp stored alongside the plan.
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

## What is not implemented

`broker/ctrader.py` does not exist. `NotWiredBroker` answers every
broker-changing call with `not_wired`, which is what lets the whole intent path
— protocol, risk, cid reservation, journal, reject frame — be exercised end to
end before there are credentials to exercise it with.

Wiring OpenApiPy needs the phase 2 prerequisites: a cTrader ID, an IC Markets
demo account, an approved Open API application, a completed manual consent flow,
and a real `SymbolsList` + `SymbolById` dump captured to
`apps/gateway/broker/fixtures/`. The specs currently in that module are
placeholders shaped like `ProtoOASymbol`, not a capture — phase 2's success
criterion is asserting volume conversion against the real dump.
