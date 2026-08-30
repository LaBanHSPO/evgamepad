"""Quote-asset -> USD conversion, with the audit trail attached.

Risk on ``USDJPY`` is naturally in JPY. Naming a JPY number ``R_usd`` without
converting it is how the HUD's R and the deck's R end up disagreeing about the
same trade, so every conversion returns the rate, the chain, and the timestamp
that produced it, and those are stored with the plan.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .types import Asset, SymbolSpec

USD = "USD"


class ConversionError(ValueError):
    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


@dataclass(frozen=True)
class Conversion:
    """One conversion, auditable after the fact."""

    rate: float
    chain: str
    ts: int
    source: str = "spot"

    def apply(self, amount: float) -> float:
        return float(Decimal(str(amount)) * Decimal(str(self.rate)))


class AssetGraph:
    """Resolves ``quote asset -> USD`` through the symbols the account can see.

    Direct pairs only, in either direction, plus the identity case. That covers
    the four configured symbols; anything needing a second hop raises rather
    than guessing, because a wrong rate here is a silently wrong R forever.
    """

    def __init__(self) -> None:
        self._assets: dict[int, Asset] = {}
        self._by_pair: dict[tuple[str, str], str] = {}
        self._mid: dict[str, tuple[float, int]] = {}

    def set_assets(self, assets: list[Asset]) -> None:
        self._assets = {a.asset_id: a for a in assets}

    def add_symbol(self, spec: SymbolSpec) -> None:
        base = self.asset_name(spec.base_asset_id)
        quote = self.asset_name(spec.quote_asset_id)
        if base and quote:
            self._by_pair[(base, quote)] = spec.name

    def asset_name(self, asset_id: int) -> str | None:
        asset = self._assets.get(asset_id)
        return asset.name if asset else None

    def observe(self, sym: str, bid: float, ask: float, ts: int) -> None:
        """Feed the raw spot stream. Mid, not bid or ask -- a conversion rate is
        not a tradeable price and should not carry half the spread."""
        self._mid[sym] = ((bid + ask) / 2.0, ts)

    def to_usd(self, quote_asset: str, ts: int) -> Conversion:
        quote_asset = quote_asset.upper()
        if quote_asset == USD:
            return Conversion(rate=1.0, chain="USD", ts=ts, source="identity")

        direct = self._by_pair.get((quote_asset, USD))
        if direct and direct in self._mid:
            rate, rate_ts = self._mid[direct]
            return Conversion(rate=rate, chain=f"{quote_asset}/USD via {direct}", ts=rate_ts)

        inverse = self._by_pair.get((USD, quote_asset))
        if inverse and inverse in self._mid:
            rate, rate_ts = self._mid[inverse]
            if rate <= 0:
                raise ConversionError(f"{inverse} mid is {rate}")
            return Conversion(
                rate=1.0 / rate,
                chain=f"{quote_asset}/USD via 1/{inverse}",
                ts=rate_ts,
            )

        raise ConversionError(
            f"no direct {quote_asset}->USD pair with a live quote; "
            "refusing to guess a rate"
        )
