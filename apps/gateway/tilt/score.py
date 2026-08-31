"""Tilt: measured behaviour, composed into one number.

Edgewonk asks you to rate your own state after the fact. The gamepad is already telling us: a
re-entry forty seconds after a loss, size at double the session median, six clutch cycles before
an arm. Every component here is a **nameable behaviour**, never an inferred feeling, which is why
the HUD can always say *why* rather than just showing a colour.

Two rules make this a safety mechanism rather than a gimmick, and both are enforced elsewhere so
they cannot be argued with here:

1. **Tilt is never an input to the Process Score.** Taxing an evening for a bad ten minutes would
   reintroduce the punishment this whole design exists to avoid.
2. **Tilt can only slow down an open.** Never a close, never a panic, never the HUD Flatten button,
   never a session lock. `tilt.gate_close: true` is a phase 1 boot-fail.

Where the line is: no keyword scoring, no profanity detection, no affect classification, and no
model anywhere in the number. Voice contributes exactly two measures, each a deviation from the
player's own rolling baseline.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Band = Literal["calm", "warm", "hot", "scorched"]

# Weights sum to 1.00. A missing component drops out and the rest renormalise, so an evening with
# no voice memo is scored on behaviour alone rather than on a guess.
WEIGHTS: dict[str, float] = {
    "revenge_size": 0.25,
    "reentry_speed": 0.20,
    "rule_break_recency": 0.20,
    "hesitation": 0.10,
    "arm_flip": 0.10,
    "input_aggression": 0.10,
    "voice_arousal": 0.05,
}

# Re-entry is scored 1 immediately after a losing close and decays to 0 across ten minutes.
REENTRY_FLOOR_S = 60.0
REENTRY_CEILING_S = 600.0

# The two recency terms a memo or an acknowledgement halves. Narrating it is the intervention.
RECENCY_COMPONENTS = ("reentry_speed", "rule_break_recency")

# How many recent arms the hesitation and flip means are taken over.
RECENT_ARMS = 3

# A memo counts toward the voice component only if it is this fresh.
VOICE_WINDOW_S = 600


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


@dataclass(frozen=True)
class TiltInputs:
    """Everything the score can read. `None` means *not measured*, which is not zero."""

    # Behaviour, from the journal and the 1 Hz pad telemetry.
    lot_ratio: float | None = None            # pending lots / session median
    seconds_since_loss: float | None = None   # since the last *losing* close
    losses_tonight: int = 0
    rule_breaks_last_3: int | None = None     # phase 7 grades
    clutch_cycles_mean: float | None = None   # mean over the last few arms
    arm_flips_mean: float | None = None
    btn_rate_hz: float | None = None
    btn_rate_base: float | None = None        # the player's own session median

    # Voice, from phase 8. Both are z-scores against the player's own 30-session baseline.
    speech_rate_z: float | None = None
    loudness_z: float | None = None
    seconds_since_memo: float | None = None

    # Interventions that halve the recency terms.
    memo_during_cooldown: bool = False
    acknowledged: bool = False


@dataclass(frozen=True)
class Component:
    """One scored behaviour, with the sentence the HUD shows if it is the top driver."""

    name: str
    value: float
    weight: float
    sentence: str


@dataclass(frozen=True)
class TiltScore:
    """The score, its band, and what is driving it."""

    score: float
    band: Band
    components: tuple[Component, ...]
    missing: tuple[str, ...] = ()
    cooldown_until: int | None = None

    @property
    def top(self) -> list[str]:
        """Drivers, loudest first. The HUD renders the first one as a sentence."""
        ranked = sorted(self.components, key=lambda c: c.value * c.weight, reverse=True)
        return [c.sentence for c in ranked if c.value > 0]

    def payload(self) -> dict[str, object]:
        """The frozen `tilt` message shape."""
        body: dict[str, object] = {
            "score": round(self.score, 3),
            "band": self.band,
            "top": self.top[:3],
        }
        if self.cooldown_until is not None:
            body["cooldownUntil"] = self.cooldown_until
        return body


@dataclass(frozen=True)
class Bands:
    """Thresholds from config, so an evening can be tuned without a code change."""

    warm: float = 0.35
    hot: float = 0.60
    scorched: float = 0.80

    def band_for(self, score: float) -> Band:
        if score >= self.scorched:
            return "scorched"
        if score >= self.hot:
            return "hot"
        if score >= self.warm:
            return "warm"
        return "calm"


# -- components -----------------------------------------------------------------------


def _revenge_size(inputs: TiltInputs) -> tuple[float, str] | None:
    if inputs.lot_ratio is None:
        return None
    value = clamp01(inputs.lot_ratio - 1)
    return value, f"size at {inputs.lot_ratio:.1f}x your session median"


def _reentry_speed(inputs: TiltInputs) -> tuple[float, str] | None:
    """Only meaningful after a loss. With no losing close tonight there is nothing to re-enter on."""
    if inputs.seconds_since_loss is None or inputs.losses_tonight == 0:
        return None
    seconds = inputs.seconds_since_loss
    if seconds <= REENTRY_FLOOR_S:
        value = 1.0
    elif seconds >= REENTRY_CEILING_S:
        value = 0.0
    else:
        value = (REENTRY_CEILING_S - seconds) / (REENTRY_CEILING_S - REENTRY_FLOOR_S)
    return value, f"re-entered {seconds:.0f} s after a loss"


def _rule_break_recency(inputs: TiltInputs) -> tuple[float, str] | None:
    if inputs.rule_breaks_last_3 is None:
        return None
    value = clamp01(inputs.rule_breaks_last_3 / 3)
    return value, f"{inputs.rule_breaks_last_3} of your last 3 fires broke a rule"


def _hesitation(inputs: TiltInputs) -> tuple[float, str] | None:
    if inputs.clutch_cycles_mean is None:
        return None
    value = clamp01((inputs.clutch_cycles_mean - 1) / 3)
    return value, f"{inputs.clutch_cycles_mean:.1f} clutch cycles before each arm"


def _arm_flip(inputs: TiltInputs) -> tuple[float, str] | None:
    if inputs.arm_flips_mean is None:
        return None
    value = clamp01(inputs.arm_flips_mean / 2)
    return value, f"{inputs.arm_flips_mean:.1f} side changes while armed"


def _input_aggression(inputs: TiltInputs) -> tuple[float, str] | None:
    if inputs.btn_rate_hz is None or not inputs.btn_rate_base:
        return None
    value = clamp01((inputs.btn_rate_hz - inputs.btn_rate_base) / inputs.btn_rate_base)
    return value, f"pressing at {inputs.btn_rate_hz:.1f} Hz against your usual {inputs.btn_rate_base:.1f}"


def _voice_arousal(inputs: TiltInputs) -> tuple[float, str] | None:
    """Two measures, both deviations from the player's own baseline. Nothing is classified."""
    if inputs.seconds_since_memo is None or inputs.seconds_since_memo > VOICE_WINDOW_S:
        return None
    scores = [z for z in (inputs.speech_rate_z, inputs.loudness_z) if z is not None]
    if not scores:
        return None
    value = clamp01((max(scores) - 1) / 2)
    return value, "speaking faster and louder than your own baseline"


_BUILDERS = {
    "revenge_size": _revenge_size,
    "reentry_speed": _reentry_speed,
    "rule_break_recency": _rule_break_recency,
    "hesitation": _hesitation,
    "arm_flip": _arm_flip,
    "input_aggression": _input_aggression,
    "voice_arousal": _voice_arousal,
}


def score_tilt(
    inputs: TiltInputs,
    *,
    bands: Bands | None = None,
    cooldown_until: int | None = None,
) -> TiltScore:
    """Compose the score. Missing components renormalise; nothing is imputed."""
    bands = bands or Bands()

    # Narrating the state is the intervention, so it is rewarded rather than the door just locking.
    halve_recency = inputs.memo_during_cooldown or inputs.acknowledged

    present: list[Component] = []
    missing: list[str] = []
    for name, weight in WEIGHTS.items():
        built = _BUILDERS[name](inputs)
        if built is None:
            missing.append(name)
            continue
        value, sentence = built
        if halve_recency and name in RECENCY_COMPONENTS:
            value *= 0.5
        present.append(Component(name=name, value=value, weight=weight, sentence=sentence))

    if not present:
        # Nothing measured yet. That is calm, not zero-confidence — an unread pad is not a tilted one.
        return TiltScore(score=0.0, band="calm", components=(), missing=tuple(missing))

    total_weight = sum(c.weight for c in present)
    score = clamp01(sum(c.value * c.weight for c in present) / total_weight)

    return TiltScore(
        score=score,
        band=bands.band_for(score),
        components=tuple(present),
        missing=tuple(missing),
        cooldown_until=cooldown_until,
    )


def confirm_hold_ms(band: Band, *, hot_hold_ms: int) -> int:
    """The client-side friction for a band.

    This is the *only* thing tilt changes about firing, and it is a parameter of the existing fire
    predicate — the FSM gains no state, so phase 3's suite stays valid.
    """
    return hot_hold_ms if band in ("hot", "scorched") else 0


def cooldown_expires_at(band: Band, now_ms: int, *, cooldown_s: int) -> int | None:
    """When opens may resume. Only the scorched band soft-blocks at all."""
    if band != "scorched":
        return None
    return now_ms + cooldown_s * 1000


def cooldown_active(cooldown_until: int | None, now_ms: int | None) -> bool:
    """Whether opens are blocked right now.

    **Fails open**, deliberately the opposite of the dead-man. An unusable clock or a missing
    cooldown means trading is allowed: the dead-man is about unattended input, this is a judgement
    call, and a judgement call should not be enforced by a broken clock.
    """
    if cooldown_until is None or now_ms is None:
        return False
    return now_ms < cooldown_until
