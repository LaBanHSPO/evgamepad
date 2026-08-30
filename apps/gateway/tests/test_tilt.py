"""Tilt: composition, bands, friction, and the lines this feature must not cross."""

from __future__ import annotations

import pytest

from apps.gateway.method import tilt as T
from apps.gateway.method.rules import OPEN_ONLY
from apps.gateway.risk import rules as risk_rules

NOW = 1_700_000_000_000


def inputs(**over) -> T.TiltInputs:
    base = dict(now_ms=NOW)
    base.update(over)
    return T.TiltInputs(**base)


def arms(n=3, cycles=1, flips=0, rate=3.0):
    return [T.ArmSample(ts=NOW, clutch_cycles=cycles, arm_flips=flips, btn_rate_hz=rate)
            for _ in range(n)]


# -- the lines ---------------------------------------------------------------


def test_weights_sum_to_one():
    assert round(sum(T.WEIGHTS.values()), 6) == 1.0


def test_every_component_has_a_sentence():
    """The HUD always renders a nameable behaviour, never a bare number."""
    assert set(T.SENTENCES) == set(T.WEIGHTS)


def test_voice_is_the_weakest_component_by_design():
    assert T.WEIGHTS["voice_arousal"] == min(T.WEIGHTS.values())


def test_friction_can_only_ever_reach_an_open():
    """The cooldown reaches the order path as one OPEN_ONLY registry rule."""
    rule = risk_rules.RULES_BY_ID["risk.cooldown"]
    assert rule.applies_to == OPEN_ONLY
    assert "intent.close" not in rule.applies_to
    assert "intent.panic" not in rule.applies_to


def test_a_cooldown_is_only_produced_by_the_scorched_band():
    for band in ("cool", "warm", "hot"):
        assert T.cooldown_for(band, NOW, 300) is None
    assert T.cooldown_for("scorched", NOW, 300) == NOW + 300_000


def test_confirm_hold_only_applies_from_hot_upward():
    assert T.confirm_hold_ms("cool", 750) == 0
    assert T.confirm_hold_ms("warm", 750) == 0     # a warning that costs nothing
    assert T.confirm_hold_ms("hot", 750) == 750
    assert T.confirm_hold_ms("scorched", 750) == 750


# -- composition -------------------------------------------------------------


def test_nothing_measured_is_not_tilt():
    result = T.compute(inputs())
    assert result.score == 0.0
    assert result.band == "cool"
    assert result.top == ()


def test_a_missing_component_redistributes_rather_than_scoring_zero():
    """Absent evidence is not calm: the score means 'of what we can see'."""
    only_reentry = T.compute(inputs(last_loss_ms=NOW - 10_000))
    assert only_reentry.score == pytest.approx(1.0)
    assert only_reentry.band == "scorched"
    # Its single component was scaled up to carry the whole weight.
    assert only_reentry.components[0].weight == pytest.approx(1.0)


def test_revenge_size_reads_the_players_own_median():
    calm = T.compute(inputs(pending_lots=0.01, session_lots=[0.01, 0.01, 0.02]))
    assert calm.score == pytest.approx(0.0)

    revenge = T.compute(inputs(pending_lots=0.03, session_lots=[0.01, 0.01, 0.01]))
    assert revenge.score == pytest.approx(1.0)
    assert "2.0×" in revenge.top[0] or "3.0×" in revenge.top[0]


def test_reentry_speed_decays_linearly():
    at_once = T.compute(inputs(last_loss_ms=NOW - 30_000)).score
    at_five = T.compute(inputs(last_loss_ms=NOW - 330_000)).score
    at_ten = T.compute(inputs(last_loss_ms=NOW - 700_000)).score
    assert at_once == pytest.approx(1.0)
    assert 0.3 < at_five < 0.7
    assert at_ten == pytest.approx(0.0)


def test_rule_breaks_count_only_the_last_three_fires():
    old = [True] * 10
    result = T.compute(inputs(recent_rule_breaks=old))
    assert result.score == pytest.approx(1.0)
    mixed = T.compute(inputs(recent_rule_breaks=[True, True, True, False, False, False]))
    assert mixed.score == pytest.approx(0.0)


def test_hesitation_and_flips_average_the_recent_arms():
    steady = T.compute(inputs(recent_arms=arms(cycles=1, flips=0)))
    assert steady.score == pytest.approx(0.0)
    frantic = T.compute(inputs(recent_arms=arms(cycles=4, flips=2)))
    assert frantic.score == pytest.approx(1.0)


def test_input_aggression_needs_a_baseline_before_it_says_anything():
    """Without the player's own median there is nothing to be faster than."""
    thin = T.compute(inputs(recent_arms=arms(rate=20.0), session_btn_rates=[3.0]))
    assert all(c.key != "input_aggression" for c in thin.components)

    withbase = T.compute(
        inputs(recent_arms=arms(rate=9.0), session_btn_rates=[3.0, 3.0, 3.0])
    )
    assert any(c.key == "input_aggression" for c in withbase.components)


def test_voice_contributes_only_when_a_memo_exists():
    quiet = T.compute(inputs(recent_arms=arms()))
    assert all(c.key != "voice_arousal" for c in quiet.components)
    loud = T.compute(inputs(recent_arms=arms(), speech_rate_z=3.0))
    assert any(c.key == "voice_arousal" for c in loud.components)


def test_the_score_is_clamped():
    everything = T.compute(inputs(
        pending_lots=1.0, session_lots=[0.01, 0.01],
        last_loss_ms=NOW - 1000, recent_rule_breaks=[True, True, True],
        recent_arms=arms(cycles=9, flips=9, rate=99.0),
        session_btn_rates=[1.0, 1.0, 1.0], speech_rate_z=9.0,
    ))
    assert everything.score == pytest.approx(1.0)
    assert everything.band == "scorched"


# -- bands -------------------------------------------------------------------


@pytest.mark.parametrize("score,band", [
    (0.0, "cool"), (0.34, "cool"), (0.35, "warm"), (0.59, "warm"),
    (0.60, "hot"), (0.79, "hot"), (0.80, "scorched"), (1.0, "scorched"),
])
def test_band_boundaries(score, band):
    assert T.band_for(score, T.Bands()) == band


# -- the driver sentence -----------------------------------------------------


def test_the_top_driver_is_a_sentence_about_a_behaviour():
    result = T.compute(inputs(
        pending_lots=0.05, session_lots=[0.01, 0.01, 0.01],
        last_loss_ms=NOW - 40_000,
    ))
    assert result.top
    assert "usual lot" in result.top[0] or "after a loss" in result.top[0]
    # No bare numbers, and nothing that reads as a streak.
    assert not any("streak" in s for s in result.top)


def test_zero_components_are_not_listed_as_drivers():
    result = T.compute(inputs(
        last_loss_ms=NOW - 40_000, recent_arms=arms(cycles=1, flips=0),
    ))
    assert all("clutching" not in s for s in result.top)


def test_at_most_three_drivers():
    result = T.compute(inputs(
        pending_lots=1.0, session_lots=[0.01, 0.01], last_loss_ms=NOW - 1000,
        recent_rule_breaks=[True, True, True], recent_arms=arms(cycles=9, flips=9),
    ))
    assert len(result.top) <= 3


# -- the acknowledgement -----------------------------------------------------


def test_narrating_it_halves_the_recency_terms():
    """The productive alternative is rewarded, rather than the door merely
    being locked."""
    before = T.compute(inputs(
        last_loss_ms=NOW - 30_000, recent_rule_breaks=[True, True, True],
    ))
    after = T.compute(inputs(
        last_loss_ms=NOW - 30_000, recent_rule_breaks=[True, True, True],
        recency_halved=True,
    ))
    assert after.score == pytest.approx(before.score / 2, rel=1e-6)


def test_halving_does_not_touch_the_non_recency_terms():
    plain = T.compute(inputs(pending_lots=0.03, session_lots=[0.01, 0.01, 0.01]))
    halved = T.compute(inputs(
        pending_lots=0.03, session_lots=[0.01, 0.01, 0.01], recency_halved=True
    ))
    assert halved.score == pytest.approx(plain.score)


def test_the_message_shape():
    result = T.compute(inputs(last_loss_ms=NOW - 30_000), cooldown_until_ms=NOW + 1000)
    msg = result.as_message()
    assert set(msg) == {"score", "band", "top", "cooldownUntil"}
    assert isinstance(msg["top"], list)
