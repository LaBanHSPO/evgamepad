"""Quote-asset to USD conversion, with an auditable record of how it was reached.

Risk is computed in the symbol's quote asset (`units * |entry - sl|`), but R is spoken in USD.
XAUUSD is already quoted in USD; USDJPY is not. The conversion therefore has to be looked up in
the asset graph the broker itself gave us, at the moment of entry, and stored with the trade —
otherwise last week's R is measured with today's rate and every historical number quietly drifts.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from dataclasses import dataclass, field

from .volume import SymbolSpec

USD = "USD"

# One hop covers XAU/USD-style pairs; two covers a cross that reaches USD through one bridge.
MAX_HOPS = 3


class ConversionError(ValueError):
    """No auditable path from the quote asset to USD. R cannot be named, so the trade is not sized."""


@dataclass(frozen=True)
class ConversionAudit:
    """Everything needed to re-derive this number a year later."""

    rate: float
    chain: tuple[str, ...]
    source: str
    ts_ms: int

    def as_row(self) -> dict[str, object]:
        return {
            "rate": self.rate,
            "chain": " -> ".join(self.chain),
            "source": self.source,
            "ts_ms": self.ts_ms,
        }


@dataclass
class AssetGraph:
    """Assets and the symbols that connect them, as reported by the broker at connect time."""

    assets: Mapping[int, str]
    symbols: Mapping[int, SymbolSpec]
    _edges: dict[int, list[tuple[int, int, bool]]] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        # (neighbour asset, symbol id, invert) — invert=False means 1 base = price quote.
        for spec in sorted(self.symbols.values(), key=lambda s: s.symbol_id):
            self._edges.setdefault(spec.base_asset_id, []).append(
                (spec.quote_asset_id, spec.symbol_id, False)
            )
            self._edges.setdefault(spec.quote_asset_id, []).append(
                (spec.base_asset_id, spec.symbol_id, True)
            )

    def _usd_asset_id(self) -> int | None:
        for asset_id, name in sorted(self.assets.items()):
            if name.upper() == USD:
                return asset_id
        return None

    def quote_to_usd(
        self, quote_asset_id: int, prices: Mapping[int, float], ts_ms: int
    ) -> ConversionAudit:
        """Rate that turns one unit of `quote_asset_id` into USD, plus how it was derived.

        Prices are mid prices keyed by symbol id, taken from the same spot stream the trade was
        entered on, so the rate is contemporaneous with the fill rather than looked up later.
        """
        name = self.assets.get(quote_asset_id)
        if name is None:
            raise ConversionError(f"unknown quote asset id {quote_asset_id}")
        if name.upper() == USD:
            return ConversionAudit(rate=1.0, chain=(USD,), source="identity", ts_ms=ts_ms)

        usd_id = self._usd_asset_id()
        if usd_id is None:
            raise ConversionError("no USD asset in the broker's asset list")

        # Breadth-first so the shortest auditable chain wins; edges are visited in symbol-id order
        # so the same market state always produces the same chain.
        queue: deque[tuple[int, float, tuple[str, ...], tuple[str, ...]]] = deque(
            [(quote_asset_id, 1.0, (name,), ())]
        )
        seen = {quote_asset_id}
        while queue:
            asset_id, rate, chain, via = queue.popleft()
            if len(chain) > MAX_HOPS:
                continue
            for neighbour, symbol_id, invert in self._edges.get(asset_id, []):
                if neighbour in seen:
                    continue
                price = prices.get(symbol_id)
                if price is None or price <= 0:
                    continue
                step = rate / price if invert else rate * price
                spec = self.symbols[symbol_id]
                next_chain = (*chain, self.assets.get(neighbour, str(neighbour)))
                next_via = (*via, spec.name)
                if neighbour == usd_id:
                    return ConversionAudit(
                        rate=step, chain=next_chain, source=" via ".join(next_via), ts_ms=ts_ms
                    )
                seen.add(neighbour)
                queue.append((neighbour, step, next_chain, next_via))

        raise ConversionError(
            f"no path from {name} to USD within {MAX_HOPS} hops using the subscribed symbols"
        )
