"""TradingView webhook intake.

A VIP alert is a *hint*, not an order. It becomes a `signal.item kind=tv` on the desk and reaches
the player's eyes; it never reaches `place`. Two things enforce that rather than describing it:
`tradingview.auto_trade: true` is a phase 1 boot-fail, and nothing in this module imports the
broker at all.

The endpoint is public by necessity — TradingView posts to it — so the secret is checked in
constant time and the route is rate limited before anything is parsed.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# TradingView's alert body is small; anything larger is not from TradingView.
MAX_BODY_BYTES = 4096

# A public endpoint gets a hard ceiling, independent of whether the secret is right.
RATE_LIMIT_PER_MINUTE = 30


class TvAlert(BaseModel):
    """The alert shape we accept. Unknown fields are refused, not ignored."""

    model_config = ConfigDict(extra="forbid")

    secret: str = Field(max_length=256)
    setup: str = Field(max_length=64)
    sym: str = Field(max_length=16)
    side: Literal["buy", "sell", "none"] = "none"
    tf: str = Field(default="M5", max_length=8)
    price: float | None = None
    note: str | None = Field(default=None, max_length=280)


@dataclass
class WebhookGuard:
    """Rate limit plus constant-time secret check for a publicly reachable route."""

    secret: str
    per_minute: int = RATE_LIMIT_PER_MINUTE
    _hits: deque[float] = field(default_factory=deque)

    def allow(self, now: float | None = None) -> bool:
        """Rate limit first: an attacker should not get to spend our CPU on comparisons."""
        now = time.monotonic() if now is None else now
        while self._hits and now - self._hits[0] > 60:
            self._hits.popleft()
        if len(self._hits) >= self.per_minute:
            return False
        self._hits.append(now)
        return True

    def verify(self, presented: str) -> bool:
        """Constant-time compare, so a wrong secret leaks nothing through timing."""
        if not self.secret:
            return False
        return hmac.compare_digest(presented, self.secret)

    def verify_signature(self, body: bytes, signature: str) -> bool:
        """Optional HMAC form, for alerts that sign the body rather than embedding the secret."""
        if not self.secret:
            return False
        expected = hmac.new(self.secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature.strip().lower())


def to_signal(alert: TvAlert, ts_ms: int) -> dict[str, object]:
    """The `signal.item` payload. Note what is absent: no lots, no order, no broker field."""
    text = f"{alert.setup} {alert.sym} {alert.tf}"
    if alert.side != "none":
        text += f" ({alert.side})"
    if alert.note:
        text += f" — {alert.note}"
    return {
        "id": f"tv-{ts_ms}",
        "kind": "tv",
        "sym": alert.sym.upper(),
        "text": text,
        "ts": ts_ms,
    }
