"""Session-scoped tilt state: turns the evening's events into scoreable inputs.

The socket feeds this; it holds no connection and makes no network call. Everything it knows
comes from things that already happen — the 1 Hz pad telemetry, the fires the gateway approved,
and the grades phase 7 already writes. Phase 9 adds **no new capture**.

Nothing here is persisted as a trait. The samples are a record of an evening.
"""

from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from .baseline import Baseline, SessionBaseline, effective
from .score import Bands, TiltInputs, TiltScore, cooldown_expires_at, score_tilt

# Hesitation and flip are means over the last few arms, not over the whole evening.
RECENT_ARMS = 3


@dataclass
class TiltTracker:
    """One evening's tilt state."""

    bands: Bands = field(default_factory=Bands)
    baseline: Baseline = field(default_factory=lambda: Baseline(0, None, None))
    cooldown_s: int = 300
    enabled: bool = True

    session: SessionBaseline = field(default_factory=SessionBaseline)
    clutch_cycles: deque[float] = field(default_factory=lambda: deque(maxlen=RECENT_ARMS))
    arm_flips: deque[float] = field(default_factory=lambda: deque(maxlen=RECENT_ARMS))
    recent_grades: deque[bool] = field(default_factory=lambda: deque(maxlen=RECENT_ARMS))

    last_btn_rate: float | None = None
    last_loss_ms: int | None = None
    losses_tonight: int = 0
    pending_lots: float | None = None
    last_memo_ms: int | None = None
    acknowledged: bool = False
    cooldown_until: int | None = None

    # -- feeding ---------------------------------------------------------------------

    def observe_telemetry(self, sample: dict[str, Any]) -> None:
        """One 1 Hz `pad.telemetry` batch. The only high-frequency input, and it is already batched."""
        cycles = sample.get("clutchCycles")
        flips = sample.get("armFlips")
        rate = sample.get("btnRateHz")
        lots = sample.get("lots")

        if cycles is not None:
            self.clutch_cycles.append(float(cycles))
        if flips is not None:
            self.arm_flips.append(float(flips))
        if rate is not None:
            self.last_btn_rate = float(rate)
            self.session.observe_telemetry(float(rate))
        if lots:
            self.pending_lots = float(lots)

    def observe_fire(self, *, lots: float, clean: bool | None) -> None:
        """A fire the gateway accepted, and whether phase 7 graded it clean."""
        self.session.observe_fire(lots)
        self.pending_lots = lots
        if clean is not None:
            self.recent_grades.append(clean)

    def observe_close(self, *, pnl_usd: float | None, ts_ms: int) -> None:
        """A closed position. Only a *losing* close starts the re-entry clock."""
        if pnl_usd is not None and pnl_usd < 0:
            self.losses_tonight += 1
            self.last_loss_ms = ts_ms

    def observe_memo(self, ts_ms: int) -> None:
        """A memo narrated during a cooldown halves the recency terms.

        Fed by phase 8: both ways out of a cooldown are memo-shaped, and the memo pipeline is
        deferred, so nothing calls this yet. The halving it drives is covered in `test_score.py`.
        """
        self.last_memo_ms = ts_ms

    def acknowledge(self) -> None:
        """The non-voice way out, and phase 8's to wire for the same reason as `observe_memo`."""
        self.acknowledged = True

    # -- scoring ---------------------------------------------------------------------

    def inputs(self, now_ms: int) -> TiltInputs:
        """Assemble what the pure scorer reads. Anything unmeasured stays `None`."""
        merged = effective(self.baseline, self.session)
        lot_ratio = None
        if self.pending_lots and merged.lot_median:
            lot_ratio = self.pending_lots / merged.lot_median

        seconds_since_loss = (
            (now_ms - self.last_loss_ms) / 1000 if self.last_loss_ms is not None else None
        )
        rule_breaks = (
            sum(1 for clean in self.recent_grades if not clean) if self.recent_grades else None
        )
        in_cooldown = self.cooldown_until is not None and now_ms < self.cooldown_until
        memo_recent = (
            self.last_memo_ms is not None and (now_ms - self.last_memo_ms) <= self.cooldown_s * 1000
        )

        return TiltInputs(
            lot_ratio=lot_ratio,
            seconds_since_loss=seconds_since_loss,
            losses_tonight=self.losses_tonight,
            rule_breaks_last_3=rule_breaks,
            clutch_cycles_mean=(
                sum(self.clutch_cycles) / len(self.clutch_cycles) if self.clutch_cycles else None
            ),
            arm_flips_mean=(
                sum(self.arm_flips) / len(self.arm_flips) if self.arm_flips else None
            ),
            btn_rate_hz=self.last_btn_rate,
            btn_rate_base=merged.btn_rate_median,
            # Voice lands with phase 8; until then the component is simply absent and its weight
            # redistributes, which is the same path a memo-less evening already takes.
            speech_rate_z=None,
            loudness_z=None,
            seconds_since_memo=None,
            memo_during_cooldown=in_cooldown and memo_recent,
            acknowledged=self.acknowledged,
        )

    def score(self, now_ms: int) -> TiltScore:
        """Score now, and start a cooldown if the band calls for one."""
        if not self.enabled:
            return TiltScore(score=0.0, band="calm", components=(), missing=())

        result = score_tilt(self.inputs(now_ms), bands=self.bands,
                            cooldown_until=self.cooldown_until)

        started = cooldown_expires_at(result.band, now_ms, cooldown_s=self.cooldown_s)
        if started is not None and (self.cooldown_until is None or self.cooldown_until < now_ms):
            self.cooldown_until = started
            result = TiltScore(score=result.score, band=result.band, components=result.components,
                               missing=result.missing, cooldown_until=started)
        elif self.cooldown_until is not None and now_ms >= self.cooldown_until:
            # Expired. Clear it so the next scorched read starts a fresh one.
            self.cooldown_until = None

        return result

    def sample_row(self, result: TiltScore, session_id: str | None, now_ms: int) -> dict[str, Any]:
        """The `tilt_sample` row — a record of an evening, never a trait."""
        return {
            "session_id": session_id,
            "ts": now_ms,
            "score": result.score,
            "band": result.band,
            "components": json.dumps(
                [{"name": c.name, "value": round(c.value, 4), "weight": c.weight}
                 for c in result.components],
                sort_keys=True,
            ),
            "missing": json.dumps(list(result.missing)),
            "top_driver": result.top[0] if result.top else None,
        }
