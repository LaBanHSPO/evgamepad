"""Tilt: a score built only from behaviours you can name.

Every component is something the player did, measured against **their own**
rolling baseline -- never a population claim, and never an inference about how
they feel. The HUD always renders the top contributor as a sentence, because a
bare number invites arguing with the number instead of noticing the behaviour.

Three lines this module does not cross:

* **No keyword scoring, no profanity detection, no affect classification, and
  no LLM anywhere in the score.** That is the pseudo-science line.
* **Tilt is never persisted as a trait.** It is per-session state plus
  ``tilt_sample`` rows for the deck's retrospective. Nobody is "a tilty trader".
* **Friction only ever applies to opening.** A close and a panic are safety
  exits; ``tilt.gate_close: true`` is a boot-fail, and the cooldown rule is
  ``OPEN_ONLY`` in the registry.

Consecutive losses are an input signal only and are never rendered as a streak.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import Literal

Band = Literal["cool", "warm", "hot", "scorched"]

#: Weights sum to 1.00. A missing component's weight is redistributed across
#: the rest rather than scored as zero -- absent evidence is not calm.
WEIGHTS: dict[str, float] = {
    "revenge_size": 0.25,
    "reentry_speed": 0.20,
    "rule_break_recency": 0.20,
    "hesitation": 0.10,
    "arm_flip": 0.10,
    "input_aggression": 0.10,
    "voice_arousal": 0.05,
}

#: How each component reads as a sentence. The HUD shows one of these, filled.
SENTENCES: dict[str, str] = {
    "revenge_size": "sizing {ratio:.1f}× your usual lot",
    "reentry_speed": "re-entered {seconds:.0f}s after a loss",
    "rule_break_recency": "{breaks} of the last 3 fires broke a rule",
    "hesitation": "clutching {cycles:.0f}× before each arm",
    "arm_flip": "flipping side {flips:.0f}× per arm",
    "input_aggression": "pressing {rate:.0f}× your usual rate",
    "voice_arousal": "speaking faster and louder than usual",
}

REENTRY_FLOOR_S = 60.0
REENTRY_CEILING_S = 600.0
RECENT_ARMS = 3
RECENT_FIRES = 3


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


@dataclass
class ArmSample:
    """One ARM, from a `pad.telemetry` batch."""

    ts: int
    clutch_cycles: int = 0
    arm_flips: int = 0
    btn_rate_hz: float = 0.0
    lots: float | None = None


@dataclass
class TiltInputs:
    """Everything the score reads. Anything absent redistributes its weight."""

    now_ms: int
    pending_lots: float | None = None
    session_lots: list[float] = field(default_factory=list)
    #: Unix ms of the last *losing* close, or None.
    last_loss_ms: int | None = None
    #: Grades of the last few fires: True when a required rule failed.
    recent_rule_breaks: list[bool] = field(default_factory=list)
    recent_arms: list[ArmSample] = field(default_factory=list)
    session_btn_rates: list[float] = field(default_factory=list)
    #: Phase 8. Both are deviations from the player's own 30-session baseline.
    speech_rate_z: float | None = None
    loudness_z: float | None = None
    #: Set by a memo or an explicit acknowledge; halves the recency terms.
    recency_halved: bool = False


@dataclass(frozen=True)
class Component:
    key: str
    score: float
    weight: float
    sentence: str

    @property
    def contribution(self) -> float:
        return self.score * self.weight


@dataclass(frozen=True)
class Tilt:
    score: float
    band: Band
    components: tuple[Component, ...]
    cooldown_until_ms: int | None = None

    @property
    def top(self) -> tuple[str, ...]:
        """Driver sentences, strongest first. Only contributors that actually
        moved the score -- a list padded with zeroes reads as noise."""
        ranked = sorted(
            (c for c in self.components if c.contribution > 0.01),
            key=lambda c: c.contribution,
            reverse=True,
        )
        return tuple(c.sentence for c in ranked[:3])

    def as_message(self) -> dict:
        return {
            "score": round(self.score, 3),
            "band": self.band,
            "top": list(self.top),
            "cooldownUntil": self.cooldown_until_ms,
        }


def _revenge_size(inputs: TiltInputs) -> Component | None:
    if inputs.pending_lots is None or len(inputs.session_lots) < 2:
        return None
    median = statistics.median(inputs.session_lots)
    if median <= 0:
        return None
    ratio = inputs.pending_lots / median
    return Component(
        "revenge_size", clamp01(ratio - 1), WEIGHTS["revenge_size"],
        SENTENCES["revenge_size"].format(ratio=ratio),
    )


def _reentry_speed(inputs: TiltInputs) -> Component | None:
    if inputs.last_loss_ms is None:
        return None
    seconds = (inputs.now_ms - inputs.last_loss_ms) / 1000.0
    if seconds < 0:
        return None
    if seconds <= REENTRY_FLOOR_S:
        score = 1.0
    elif seconds >= REENTRY_CEILING_S:
        score = 0.0
    else:
        span = REENTRY_CEILING_S - REENTRY_FLOOR_S
        score = 1.0 - (seconds - REENTRY_FLOOR_S) / span
    if inputs.recency_halved:
        # Narrating it is the intervention, so the productive alternative is
        # rewarded rather than the door merely being locked.
        score /= 2
    return Component(
        "reentry_speed", clamp01(score), WEIGHTS["reentry_speed"],
        SENTENCES["reentry_speed"].format(seconds=seconds),
    )


def _rule_break_recency(inputs: TiltInputs) -> Component | None:
    if not inputs.recent_rule_breaks:
        return None
    recent = inputs.recent_rule_breaks[-RECENT_FIRES:]
    breaks = sum(1 for broke in recent if broke)
    score = breaks / RECENT_FIRES
    if inputs.recency_halved:
        score /= 2
    return Component(
        "rule_break_recency", clamp01(score), WEIGHTS["rule_break_recency"],
        SENTENCES["rule_break_recency"].format(breaks=breaks),
    )


def _hesitation(inputs: TiltInputs) -> Component | None:
    arms = inputs.recent_arms[-RECENT_ARMS:]
    if not arms:
        return None
    mean_cycles = statistics.fmean(a.clutch_cycles for a in arms)
    return Component(
        "hesitation", clamp01((mean_cycles - 1) / 3), WEIGHTS["hesitation"],
        SENTENCES["hesitation"].format(cycles=mean_cycles),
    )


def _arm_flip(inputs: TiltInputs) -> Component | None:
    arms = inputs.recent_arms[-RECENT_ARMS:]
    if not arms:
        return None
    mean_flips = statistics.fmean(a.arm_flips for a in arms)
    return Component(
        "arm_flip", clamp01(mean_flips / 2), WEIGHTS["arm_flip"],
        SENTENCES["arm_flip"].format(flips=mean_flips),
    )


def _input_aggression(inputs: TiltInputs) -> Component | None:
    arms = inputs.recent_arms[-RECENT_ARMS:]
    if not arms or len(inputs.session_btn_rates) < 3:
        return None
    base = statistics.median(inputs.session_btn_rates)
    if base <= 0:
        return None
    current = statistics.fmean(a.btn_rate_hz for a in arms)
    return Component(
        "input_aggression", clamp01((current - base) / base),
        WEIGHTS["input_aggression"],
        SENTENCES["input_aggression"].format(rate=current / base),
    )


def _voice_arousal(inputs: TiltInputs) -> Component | None:
    """Phase 8, and the weakest component in the set by design.

    Two measures only, each a deviation from the player's own rolling baseline.
    If a month of data does not support it, delete it rather than defend it.
    """
    values = [z for z in (inputs.speech_rate_z, inputs.loudness_z) if z is not None]
    if not values:
        return None
    return Component(
        "voice_arousal", clamp01((max(values) - 1) / 2), WEIGHTS["voice_arousal"],
        SENTENCES["voice_arousal"],
    )


_COMPONENTS = (
    _revenge_size,
    _reentry_speed,
    _rule_break_recency,
    _hesitation,
    _arm_flip,
    _input_aggression,
    _voice_arousal,
)


@dataclass(frozen=True)
class Bands:
    warm: float = 0.35
    hot: float = 0.60
    scorched: float = 0.80


def band_for(score: float, bands: Bands) -> Band:
    if score >= bands.scorched:
        return "scorched"
    if score >= bands.hot:
        return "hot"
    if score >= bands.warm:
        return "warm"
    return "cool"


def compute(
    inputs: TiltInputs,
    bands: Bands | None = None,
    cooldown_until_ms: int | None = None,
) -> Tilt:
    """Weighted sum over whatever components have evidence.

    A missing component redistributes its weight across the rest, so the score
    always means "of what we can see" rather than being diluted toward calm by
    absent inputs.
    """
    bands = bands or Bands()
    present = [c for c in (fn(inputs) for fn in _COMPONENTS) if c is not None]
    if not present:
        return Tilt(score=0.0, band="cool", components=(), cooldown_until_ms=cooldown_until_ms)

    total_weight = sum(c.weight for c in present)
    scaled = tuple(
        Component(c.key, c.score, c.weight / total_weight, c.sentence) for c in present
    )
    score = clamp01(sum(c.contribution for c in scaled))
    return Tilt(
        score=score,
        band=band_for(score, bands),
        components=scaled,
        cooldown_until_ms=cooldown_until_ms,
    )


def confirm_hold_ms(band: Band, configured: int) -> int:
    """Friction 1. Hot makes the confirm a **hold** rather than a press.

    Returned as a number the client threads into its fire predicate, which is
    why phase 3 made ``confirmHoldMs`` a parameter: the FSM gains no states.
    """
    return configured if band in {"hot", "scorched"} else 0


def cooldown_for(band: Band, now_ms: int, cooldown_s: int) -> int | None:
    """Friction 2. Scorched soft-blocks **opens** for the cooldown.

    Never a close, never a panic: the cooldown reaches the order path only as
    the registry's `risk.cooldown` rule, which is OPEN_ONLY.
    """
    if band != "scorched":
        return None
    return now_ms + cooldown_s * 1000
