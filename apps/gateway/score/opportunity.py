"""The evening's opportunity quality, accumulated one sample at a time.

Selectivity asks how well the trade count matched what the tape actually offered, which needs a
number for the tape. Phase 4's sentinel computes one per tick; nothing was persisting it, so the
mean is accumulated here and written once, at session close.

A running mean rather than stored samples: the score wants the evening's average, and keeping ~9,000
rows a night to re-average later would be storage bought for a number already known.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class OpportunitySampler:
    """One evening's mean sentinel quality. Never a trait, never carried between sessions."""

    n: int = 0
    total: float = 0.0

    def observe(self, quality: float | None) -> None:
        if quality is None:
            return
        self.n += 1
        self.total += quality

    @property
    def mean(self) -> float | None:
        """`None` when the tape was never sampled — which is not the same as a dead tape."""
        return None if self.n == 0 else self.total / self.n
