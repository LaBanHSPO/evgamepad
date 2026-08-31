"""Tilt composition, and the safety properties that make it a mechanism rather than a gimmick.

The two tests that matter most are at the bottom: with tilt forced to 1.0, a close and a panic
still execute.
"""

from __future__ import annotations

import pytest

from method.rules import RuleContext
from risk.rules import evaluate_exit, evaluate_open
from tilt.baseline import MIN_SESSIONS_FOR_VOICE, Baseline, SessionBaseline, effective
from tilt.score import (
    RECENCY_COMPONENTS,
    WEIGHTS,
    Bands,
    TiltInputs,
    confirm_hold_ms,
    cooldown_active,
    cooldown_expires_at,
    score_tilt,
)

NOW = 1_788_000_000_000


def gate_ctx(**over) -> RuleContext:
    base = dict(
        now_ms=NOW, symbol="XAUUSD", lots=0.01, clutch=True, session_open=True,
        session_label="tue 20:00", allowed_symbols=frozenset({"XAUUSD"}),
        positions_open=0, max_positions=1, max_lots=0.10,
        day_loss_usd=0.0, max_day_loss_usd=200.0,
        seconds_since_last_order=10.0, min_seconds_between_orders=2.0,
        heartbeat_age_s=0.5, heartbeat_dead_s=3.0,
    )
    base.update(over)
    return RuleContext(**base)  # type: ignore[arg-type]


# -- composition ----------------------------------------------------------------------


def test_the_weights_sum_to_one() -> None:
    assert sum(WEIGHTS.values()) == pytest.approx(1.0)


def test_nothing_measured_is_calm_rather_than_unknown() -> None:
    """An unread pad is not a tilted one."""
    result = score_tilt(TiltInputs())
    assert result.score == 0.0
    assert result.band == "calm"
    assert result.components == ()
    assert len(result.missing) == len(WEIGHTS)


def test_a_missing_component_renormalises_the_rest() -> None:
    """No voice memo means the behavioural components carry the whole score, not 95% of it."""
    behaviour_only = score_tilt(TiltInputs(lot_ratio=3.0, rule_breaks_last_3=3))
    assert "voice_arousal" in behaviour_only.missing
    # Both present components are maxed, so a correctly renormalised score is 1.0.
    assert behaviour_only.score == pytest.approx(1.0)


def test_one_maxed_component_does_not_max_the_score_when_others_are_present() -> None:
    result = score_tilt(TiltInputs(lot_ratio=3.0, rule_breaks_last_3=0))
    assert 0.0 < result.score < 1.0


def test_every_component_is_a_nameable_behaviour() -> None:
    """The HUD renders a sentence, never a bare number — that is what makes it actionable."""
    result = score_tilt(TiltInputs(
        lot_ratio=2.0, seconds_since_loss=40, losses_tonight=1, rule_breaks_last_3=2,
        clutch_cycles_mean=4.0, arm_flips_mean=2.0, btn_rate_hz=6.0, btn_rate_base=3.0,
        speech_rate_z=2.0, loudness_z=1.5, seconds_since_memo=30,
    ))
    assert len(result.components) == len(WEIGHTS)
    assert result.missing == ()
    for component in result.components:
        assert component.sentence and not component.sentence.isdigit()
    assert result.top, "a scoring evening always has a top driver"


def test_revenge_sizing_is_named_when_it_leads() -> None:
    """Two losses then a double-size re-entry inside 60 s: hot, and it says why."""
    result = score_tilt(TiltInputs(
        lot_ratio=2.0, seconds_since_loss=40, losses_tonight=2, rule_breaks_last_3=2,
        clutch_cycles_mean=3.0, arm_flips_mean=1.0,
    ))
    assert result.band in ("hot", "scorched")
    assert "2.0x your session median" in result.top[0]


def test_re_entry_decays_across_ten_minutes() -> None:
    def at(seconds: float) -> float:
        return score_tilt(TiltInputs(seconds_since_loss=seconds, losses_tonight=1)).score

    assert at(30) == pytest.approx(1.0)
    assert at(60) == pytest.approx(1.0)
    assert at(330) == pytest.approx(0.5, abs=0.01)
    assert at(600) == pytest.approx(0.0)
    assert at(900) == pytest.approx(0.0)


def test_re_entry_needs_a_loss_to_re_enter_on() -> None:
    result = score_tilt(TiltInputs(seconds_since_loss=10, losses_tonight=0))
    assert "reentry_speed" in result.missing


def test_voice_only_counts_while_the_memo_is_fresh() -> None:
    fresh = score_tilt(TiltInputs(speech_rate_z=3.0, loudness_z=3.0, seconds_since_memo=60))
    assert "voice_arousal" not in fresh.missing

    stale = score_tilt(TiltInputs(speech_rate_z=3.0, loudness_z=3.0, seconds_since_memo=1200))
    assert "voice_arousal" in stale.missing

    never = score_tilt(TiltInputs(speech_rate_z=3.0, loudness_z=3.0))
    assert "voice_arousal" in never.missing


def test_a_memo_halves_the_recency_terms() -> None:
    """Narrating the state is the intervention, so it is rewarded rather than just locking a door."""
    inputs = TiltInputs(seconds_since_loss=30, losses_tonight=2, rule_breaks_last_3=3)
    before = score_tilt(inputs)
    after = score_tilt(TiltInputs(**{**inputs.__dict__, "memo_during_cooldown": True}))

    assert after.score == pytest.approx(before.score * 0.5, abs=1e-9)
    assert set(RECENCY_COMPONENTS) == {"reentry_speed", "rule_break_recency"}


def test_an_acknowledgement_halves_them_too() -> None:
    inputs = TiltInputs(seconds_since_loss=30, losses_tonight=1, rule_breaks_last_3=3)
    assert score_tilt(TiltInputs(**{**inputs.__dict__, "acknowledged": True})).score < score_tilt(
        inputs
    ).score


def test_a_memo_does_not_touch_the_behavioural_components() -> None:
    """Talking about it does not un-double your size."""
    inputs = TiltInputs(lot_ratio=3.0)
    assert score_tilt(TiltInputs(**{**inputs.__dict__, "acknowledged": True})).score == pytest.approx(
        score_tilt(inputs).score
    )


# -- bands and friction ---------------------------------------------------------------


def test_the_bands_come_from_config() -> None:
    bands = Bands(warm=0.35, hot=0.60, scorched=0.80)
    assert bands.band_for(0.10) == "calm"
    assert bands.band_for(0.40) == "warm"
    assert bands.band_for(0.65) == "hot"
    assert bands.band_for(0.95) == "scorched"


def test_a_warning_that_costs_nothing_is_one_you_keep_listening_to() -> None:
    """The warm band adds no friction at all — by design, not by omission."""
    assert confirm_hold_ms("calm", hot_hold_ms=750) == 0
    assert confirm_hold_ms("warm", hot_hold_ms=750) == 0
    assert confirm_hold_ms("hot", hot_hold_ms=750) == 750
    assert confirm_hold_ms("scorched", hot_hold_ms=750) == 750


def test_only_the_scorched_band_starts_a_cooldown() -> None:
    for band in ("calm", "warm", "hot"):
        assert cooldown_expires_at(band, NOW, cooldown_s=300) is None
    assert cooldown_expires_at("scorched", NOW, cooldown_s=300) == NOW + 300_000


def test_the_cooldown_fails_open() -> None:
    """The opposite of the dead-man, on purpose: this one is a judgement call."""
    assert cooldown_active(NOW + 60_000, NOW) is True
    assert cooldown_active(NOW - 1, NOW) is False
    assert cooldown_active(None, NOW) is False
    # An unusable clock allows trading rather than trapping the player.
    assert cooldown_active(NOW + 60_000, None) is False


# -- the safety invariants ------------------------------------------------------------


def test_with_tilt_forced_to_one_a_close_and_a_panic_still_execute() -> None:
    """The single most important test in this phase."""
    scorched = score_tilt(TiltInputs(
        lot_ratio=5.0, seconds_since_loss=1, losses_tonight=5, rule_breaks_last_3=3,
        clutch_cycles_mean=10.0, arm_flips_mean=5.0, btn_rate_hz=20.0, btn_rate_base=2.0,
        speech_rate_z=5.0, loudness_z=5.0, seconds_since_memo=1,
    ))
    assert scorched.score == pytest.approx(1.0)
    assert scorched.band == "scorched"

    # Exits run no gates at all, whatever the score is.
    assert evaluate_exit().allowed is True
    assert evaluate_exit().outcomes == ()


def test_the_cooldown_blocks_an_open_and_names_the_reason(monkeypatch) -> None:
    blocked = evaluate_open(gate_ctx(cooldown_until_ms=NOW + 120_000))
    assert blocked.allowed is False
    assert blocked.reason == "cooldown"

    clear = evaluate_open(gate_ctx(cooldown_until_ms=NOW - 1))
    assert clear.allowed is True


def test_a_reconnect_with_no_cooldown_recorded_allows_trading() -> None:
    assert evaluate_open(gate_ctx(cooldown_until_ms=None)).allowed is True


def test_the_cooldown_is_a_risk_rule_so_it_is_open_only_by_construction() -> None:
    from method.rules import get, rules_for

    rule = get("cooldown")
    assert rule.scope == "risk"
    assert rule.reason == "cooldown"
    assert rule.code in {r.code for r in rules_for("risk")}
    # `evaluate_exit` runs no rules, so there is no path by which a close could see this one.
    assert evaluate_exit().outcomes == ()


# -- baselines ------------------------------------------------------------------------


def test_a_cold_start_withholds_the_voice_component() -> None:
    """Below the floor, a z-score against "your baseline" is arithmetic on noise."""
    assert Baseline(sessions=2, lot_median=0.01, btn_rate_median=3.0).voice_ready is False
    assert Baseline(sessions=2, lot_median=None, btn_rate_median=None).cold_start is True
    assert Baseline(sessions=MIN_SESSIONS_FOR_VOICE, lot_median=0.01,
                    btn_rate_median=3.0).voice_ready is True


def test_a_first_session_falls_back_to_its_own_medians() -> None:
    """A player with no history still gets a comparison — against themselves."""
    session = SessionBaseline()
    for lots in (0.01, 0.02, 0.01):
        session.observe_fire(lots)
    for rate in (2.0, 4.0, 3.0):
        session.observe_telemetry(rate)

    merged = effective(Baseline(sessions=0, lot_median=None, btn_rate_median=None), session)
    assert merged.lot_median == pytest.approx(0.01)
    assert merged.btn_rate_median == pytest.approx(3.0)


def test_the_rolling_baseline_wins_when_it_exists() -> None:
    session = SessionBaseline()
    session.observe_fire(0.10)
    merged = effective(Baseline(sessions=30, lot_median=0.01, btn_rate_median=3.0), session)
    assert merged.lot_median == pytest.approx(0.01)


def test_tilt_never_reaches_the_process_score() -> None:
    """Taxing an evening for a bad ten minutes is the punishment this design exists to avoid.

    Phase 11 renders tilt on the deck as a **retrospective**, which is why this checks the score
    itself rather than banning the word from every deck module. The invariant was always about what
    the score consumes, not about what the deck is allowed to show.
    """
    from score import session as score_module
    from score.session import FireInputs, SessionInputs

    with open(score_module.__file__, encoding="utf-8") as handle:
        text = handle.read().lower()
    assert "tilt" not in text, "tilt leaked into the Process Score"
    for fields in (FireInputs.__dataclass_fields__, SessionInputs.__dataclass_fields__):
        assert not any("tilt" in name.lower() for name in fields)


def test_the_deck_s_tilt_retrospective_is_scored_against_adherence_not_money() -> None:
    """It is a record of an evening, so what it is placed beside matters."""
    from deck.metrics import tilt_against_adherence

    retro = tilt_against_adherence(
        [{"ts": NOW, "score": 0.7, "band": "hot", "topDriver": "size at 2.0x"}], []
    )
    assert set(retro) == {"samples", "bands", "topDrivers", "adherence", "peak"}
    for money in ("pnl", "usd", "equity", "balance", "profit"):
        assert money not in str(retro).lower()
