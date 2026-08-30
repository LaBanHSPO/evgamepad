"""Value types shared across the broker boundary.

This is a **module boundary, not a wire protocol**. There is no sidecar, no
local RPC, and nothing here is serialised between processes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Side = Literal["buy", "sell"]

#: cTrader expresses volume in cents of a unit, and relative SL/TP distance in
#: 1/100000 of a price unit. Both live here so no other module invents a scale.
VOLUME_CENTS_PER_UNIT = 100
RELATIVE_UNITS_PER_PRICE = 100_000


@dataclass(frozen=True)
class SymbolSpec:
    """From ``ProtoOASymbolByIdReq``. ``SymbolsListReq`` returns
    ``ProtoOALightSymbol``, which carries **no volume spec** -- reading min/step/
    max off the light record is the wrong-volume-on-gold bug."""

    symbol_id: int
    name: str
    digits: int
    pip_position: int
    lot_size: int
    min_volume: int
    step_volume: int
    max_volume: int
    base_asset_id: int
    quote_asset_id: int


@dataclass(frozen=True)
class Asset:
    asset_id: int
    name: str


@dataclass(frozen=True)
class BrokerQuote:
    sym: str
    bid: float
    ask: float
    ts: int
    digits: int


@dataclass(frozen=True)
class BrokerPosition:
    position_id: int
    sym: str
    side: Side
    volume: int
    entry: float
    opened_at: int
    sl: float | None = None
    tp: float | None = None
    commission: float = 0.0
    swap: float = 0.0
    label: str | None = None


@dataclass(frozen=True)
class AccountSnapshot:
    account_id: int
    is_live: bool
    currency: str
    balance: float
    equity: float
    ts: int


@dataclass(frozen=True)
class OpenRequest:
    cid: str
    sym: str
    side: Side
    volume: int
    relative_sl: int | None = None
    relative_tp: int | None = None

    @property
    def label(self) -> str:
        """cTrader limits label length, so short-cid it."""
        return f"evgp{self.cid[-8:]}"


@dataclass(frozen=True)
class BrokerResult:
    ok: bool
    cid: str
    reason: str | None = None
    detail: str | None = None
    order_id: int | None = None
    position_id: int | None = None


@dataclass
class BrokerHealth:
    connected: bool = False
    authed: bool = False
    account_id: int | None = None
    last_heartbeat_ms: int | None = None
    symbols: list[str] = field(default_factory=list)
    detail: str | None = None
