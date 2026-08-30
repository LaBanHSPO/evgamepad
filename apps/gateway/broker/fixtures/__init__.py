"""Symbol specs for tests.

These are **placeholders shaped like** ``ProtoOASymbol``, not a capture from a
real IC Markets demo. Phase 2's prerequisite is a real ``SymbolsList`` +
``SymbolById`` dump landing here, and its success criterion is asserting volume
conversion against *that*, not against these. Until then a 0.01-lot gold order
is verified by hand in cTrader web before anything larger is sent.
"""

from ..types import Asset, SymbolSpec

# lotSize is in cents of a unit. One gold lot is 100 ounces, so 100 units ->
# 10_000 cents; one FX lot is 100_000 units -> 10_000_000 cents. Gold's lotSize
# being three orders of magnitude smaller than FX's is exactly the trap that
# makes a hardcoded 10_000_000 send 1000x the intended ounces.
XAUUSD = SymbolSpec(
    symbol_id=41, name="XAUUSD", digits=2, pip_position=2,
    lot_size=10_000, min_volume=100, step_volume=100,
    max_volume=1_000_000, base_asset_id=41, quote_asset_id=840,
)
# 100_000 units of base = 10_000_000 cents of a unit.
EURUSD = SymbolSpec(
    symbol_id=1, name="EURUSD", digits=5, pip_position=4,
    lot_size=10_000_000, min_volume=100_000, step_volume=100_000,
    max_volume=10_000_000_000, base_asset_id=978, quote_asset_id=840,
)
GBPUSD = SymbolSpec(
    symbol_id=2, name="GBPUSD", digits=5, pip_position=4,
    lot_size=10_000_000, min_volume=100_000, step_volume=100_000,
    max_volume=10_000_000_000, base_asset_id=826, quote_asset_id=840,
)
USDJPY = SymbolSpec(
    symbol_id=4, name="USDJPY", digits=3, pip_position=2,
    lot_size=10_000_000, min_volume=100_000, step_volume=100_000,
    max_volume=10_000_000_000, base_asset_id=840, quote_asset_id=392,
)

SPECS = {s.name: s for s in (XAUUSD, EURUSD, GBPUSD, USDJPY)}

ASSETS = [
    Asset(840, "USD"),
    Asset(978, "EUR"),
    Asset(826, "GBP"),
    Asset(392, "JPY"),
    Asset(41, "XAU"),
]
