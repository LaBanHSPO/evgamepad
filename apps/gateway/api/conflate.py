"""Quote conflation for the browser.

The tape sees every tick; the HUD does not need to. Text at 60 Hz would spend the socket's
budget on numbers a human cannot read, on the same socket whose entire job is prioritising order
acks. The conflator keeps only the latest book per symbol and hands it over on a fixed tick.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# 10-20 Hz to the browser. 50 ms is the slow end of that band and is plenty for a price readout.
DEFAULT_INTERVAL_S = 0.05


@dataclass
class Conflator:
    """Latest-wins buffer. Nothing queues, so a burst never becomes a backlog."""

    interval_s: float = DEFAULT_INTERVAL_S
    _pending: dict[str, dict[str, object]] = field(default_factory=dict, init=False)

    def offer(self, symbol: str, payload: dict[str, object]) -> None:
        """Replace this symbol's pending quote. Called at full spot rate."""
        self._pending[symbol] = payload

    def drain(self) -> list[dict[str, object]]:
        """Take everything buffered since the last drain, at most one frame per symbol."""
        drained = list(self._pending.values())
        self._pending.clear()
        return drained

    @property
    def pending(self) -> int:
        return len(self._pending)
