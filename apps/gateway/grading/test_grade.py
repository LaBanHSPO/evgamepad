"""Grading fixtures: the unplanned fallback, unknown answers, and the never-blocks guarantee."""

from __future__ import annotations

import json

from grading.grade import UNPLANNED, UNPLANNED_ID, Playbook, PlaybookRule, grade_fire, regrade_with_answers
from grading.seed import starter_playbooks
from method.rules import RuleContext
from risk.rules import evaluate_open

NOW = 1_788_000_000_000


def ctx(**over) -> RuleContext:
    base = dict(
        now_ms=NOW, symbol="XAUUSD", lots=0.01, clutch=True, session_open=True,
        session_label="tue 20:00", allowed_symbols=frozenset({"XAUUSD"}),
        positions_open=0, max_positions=1, max_lots=0.10,
        day_loss_usd=0.0, max_day_loss_usd=200.0,
        seconds_since_last_order=10.0, min_seconds_between_orders=2.0,
        heartbeat_age_s=0.5, heartbeat_dead_s=3.0,
        # A clean chart: the range broke upward and we are buying it, close to the average.
        setup_tag="range_break", setup_side="buy", side="buy",
        price=2000.5, ema20=2000.0, atr=1.0, spread=0.3, spread_cap=0.8,
        seconds_to_high_impact=None,
    )
    base.update(over)
    return RuleContext(**base)  # type: ignore[arg-type]


def book() -> Playbook:
    return next(p for p in starter_playbooks() if p.detector_tag == "range_break")


def test_a_clean_fire_grades_clean() -> None:
    grade = grade_fire(cid="01ABC", playbook=book(), ctx=ctx(manual_answers={"no_chase": True}))
    assert grade.clean is True
    assert grade.required_pass == grade.required_total
    assert grade.summary.endswith("rules OK")
    assert grade.first_failure() is None


def test_the_overlay_gets_a_count_and_the_one_line_that_explains_it() -> None:
    """`4/5 rules OK · ✗ price 3.00 ATR from EMA20` — the whole reason this feature exists."""
    grade = grade_fire(cid="01ABC", playbook=book(),
                       ctx=ctx(price=2003.0, manual_answers={"no_chase": True}))
    assert grade.clean is False
    assert grade.summary == f"{grade.required_pass}/{grade.required_total} rules OK"
    failure = grade.first_failure()
    assert failure is not None
    assert failure.code == "ema_distance"
    assert failure.actual == "3.00 ATR"


def test_a_failing_playbook_rule_never_stops_the_trade() -> None:
    hostile = ctx(setup_tag="buildup", price=2010.0)
    grade = grade_fire(cid="01ABC", playbook=book(), ctx=hostile)
    assert grade.clean is False
    # Same context through the gate: still allowed.
    assert evaluate_open(hostile).allowed is True


def test_no_playbook_selected_grades_as_unplanned_rather_than_crashing() -> None:
    grade = grade_fire(cid="01ABC", playbook=None, ctx=ctx())
    assert grade.playbook_id == UNPLANNED_ID
    assert grade.playbook_name == "Unplanned"
    assert grade.results == ()
    assert grade.required_total == 0
    assert grade.clean is False
    assert grade.summary == "no rules to check"


def test_the_unplanned_book_holds_no_rules_at_all() -> None:
    assert UNPLANNED.rules == ()
    assert UNPLANNED.applies_to("XAUUSD") is True


def test_an_unanswered_manual_rule_leaves_the_denominator() -> None:
    """Skipping the checklist is neither pass nor fail, and costs the player nothing."""
    answered = grade_fire(cid="01ABC", playbook=book(),
                          ctx=ctx(manual_answers={"no_chase": True}))
    skipped = grade_fire(cid="01ABC", playbook=book(), ctx=ctx())

    assert skipped.required_total == answered.required_total - 1
    assert skipped.clean is True, "a skip must not cost the clean flag"
    unknown = [r for r in skipped.results if r.unknown]
    assert [r.code for r in unknown] == ["no_chase"]


def test_answering_the_checklist_no_does_cost_the_clean_flag() -> None:
    graded = grade_fire(cid="01ABC", playbook=book(),
                        ctx=ctx(manual_answers={"no_chase": False}))
    assert graded.clean is False
    assert graded.first_failure() is not None


def test_a_rule_with_no_chart_data_is_unknown_not_failed() -> None:
    blind = grade_fire(cid="01ABC", playbook=book(),
                       ctx=ctx(price=None, ema20=None, atr=None, spread=None,
                               manual_answers={"no_chase": True}))
    unknown_codes = {r.code for r in blind.results if r.unknown}
    assert {"ema_distance", "spread_under_cap"} <= unknown_codes
    assert blind.required_total < len(blind.results)


def test_regrading_after_the_checklist_folds_the_answers_in() -> None:
    at_arm = grade_fire(cid="01ABC", playbook=book(), ctx=ctx())
    assert at_arm.stage == "arm"

    at_close = regrade_with_answers(at_arm, book(), ctx(), {"no_chase": False})
    assert at_close.stage == "fire"
    assert at_close.required_total == at_arm.required_total + 1
    assert at_close.clean is False


def test_a_declined_arm_is_gradeable_because_grading_is_keyed_on_the_cid() -> None:
    """Phase 6's declined count depends on a cancelled arm still producing a row."""
    grade = grade_fire(cid="01DECLINED", playbook=book(),
                       ctx=ctx(spread=5.0, manual_answers={"no_chase": True}))
    row = grade.as_db_row()
    assert row["cid"] == "01DECLINED"
    assert row["clean"] == 0
    assert json.loads(row["results"])


def test_the_unplanned_book_is_stored_as_a_null_playbook_id() -> None:
    """It is not a row in `playbook`, so a foreign key to it would never resolve."""
    row = grade_fire(cid="01ABC", playbook=None, ctx=ctx()).as_db_row()
    assert row["playbook_id"] is None


def test_the_wire_payload_matches_the_frozen_grade_message() -> None:
    payload = grade_fire(cid="01ABC", playbook=book(), ctx=ctx()).payload()
    assert set(payload) == {"cid", "playbookId", "required_pass", "required_total", "clean",
                            "results"}


def test_every_starter_playbook_is_gradeable_out_of_the_box() -> None:
    """A player starts with a real book, and every rule in it resolves to a registry entry."""
    books = starter_playbooks()
    assert len(books) >= 5
    for playbook in books:
        assert playbook.detector_tag
        assert playbook.narrative
        grade = grade_fire(cid="01ABC", playbook=playbook,
                           ctx=ctx(setup_tag=playbook.detector_tag))
        assert grade.results, f"{playbook.slug} graded nothing"


def test_a_symbol_specific_playbook_only_applies_to_its_symbols() -> None:
    gold_only = Playbook(id="pb", name="Gold", slug="gold", symbols=("XAUUSD",),
                         rules=(PlaybookRule(code="named_setup"),))
    assert gold_only.applies_to("XAUUSD") is True
    assert gold_only.applies_to("EURUSD") is False
