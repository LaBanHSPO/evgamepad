"""The player's own baselines.

Every comparison tilt makes is against *this player's* rolling medians — never a population claim.
"Pressing faster than usual" means faster than your usual, and the only way to know that is to
have watched you.

Which forces a cold-start guard. With too few sessions there is no baseline worth deviating from,
so the voice component is withheld entirely (its weight redistributes) and the behavioural
components fall back to the current session's own median.
"""

from __future__ import annotations

import sqlite3
import statistics
from dataclasses import dataclass
from pathlib import Path

# The window the plan specifies. Long enough to be a habit, short enough to follow a change in one.
ROLLING_SESSIONS = 30

# Below this, a z-score against "your baseline" is arithmetic on noise.
MIN_SESSIONS_FOR_VOICE = 5


@dataclass(frozen=True)
class Baseline:
    """What "usual" means for this player right now."""

    sessions: int
    lot_median: float | None
    btn_rate_median: float | None

    @property
    def voice_ready(self) -> bool:
        """Whether a voice z-score means anything yet. Below the floor it does not."""
        return self.sessions >= MIN_SESSIONS_FOR_VOICE

    @property
    def cold_start(self) -> bool:
        return not self.voice_ready


def _median(values: list[float]) -> float | None:
    usable = [v for v in values if v is not None and v > 0]
    return statistics.median(usable) if usable else None


def load_baseline(db_path: Path, *, sessions: int = ROLLING_SESSIONS) -> Baseline:
    """Rolling medians over the player's most recent sessions.

    Reads only; the baseline is derived on demand rather than cached, because a cached baseline
    that disagrees with the rows is worse than recomputing a few hundred of them.
    """
    conn = sqlite3.connect(db_path)
    try:
        recent = [
            row[0]
            for row in conn.execute(
                "SELECT session_id FROM session_equity ORDER BY opened_at DESC LIMIT ?",
                (sessions,),
            )
        ]
        if not recent:
            return Baseline(sessions=0, lot_median=None, btn_rate_median=None)

        placeholders = ",".join("?" for _ in recent)
        lots = [
            row[0]
            for row in conn.execute(
                f"SELECT lots FROM trade_plan WHERE session_id IN ({placeholders})", recent
            )
        ]
        rates = [
            row[0]
            for row in conn.execute(
                f"SELECT btn_rate_hz FROM pad_event WHERE session_id IN ({placeholders})", recent
            )
        ]
        return Baseline(
            sessions=len(recent),
            lot_median=_median(lots),
            btn_rate_median=_median(rates),
        )
    finally:
        conn.close()


@dataclass
class SessionBaseline:
    """This evening's own medians, used until the rolling ones exist."""

    lots: list[float]
    btn_rates: list[float]

    def __init__(self) -> None:
        self.lots = []
        self.btn_rates = []

    def observe_fire(self, lots: float) -> None:
        if lots > 0:
            self.lots.append(lots)

    def observe_telemetry(self, btn_rate_hz: float) -> None:
        if btn_rate_hz > 0:
            self.btn_rates.append(btn_rate_hz)

    @property
    def lot_median(self) -> float | None:
        return _median(self.lots)

    @property
    def btn_rate_median(self) -> float | None:
        return _median(self.btn_rates)


def effective(baseline: Baseline, session: SessionBaseline) -> Baseline:
    """The rolling baseline where it exists, this evening's where it does not.

    A first-ever session still gets a usable comparison — against itself — rather than no tilt
    signal at all.
    """
    return Baseline(
        sessions=baseline.sessions,
        lot_median=baseline.lot_median if baseline.lot_median else session.lot_median,
        btn_rate_median=(
            baseline.btn_rate_median if baseline.btn_rate_median else session.btn_rate_median
        ),
    )
