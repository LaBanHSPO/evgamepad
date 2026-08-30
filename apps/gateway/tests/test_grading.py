"""Playbooks and grading.

The property this whole feature rests on: grading scores, it never rejects.
"""

from __future__ import annotations

import json

import pytest

from apps.gateway.journal.writer import JournalWriter
from apps.gateway.method import rules as registry
from apps.gateway.method.grading import GradeContext, grade, unanswered_manual_codes
from apps.gateway.method.playbook import SEEDS, UNPLANNED, PlaybookStore
from apps.gateway.risk import rules as risk_rules

MS = 1_700_000_000_000


def ctx(**over) -> GradeContext:
    base = dict(
        now_ms=MS, side="buy", sym="XAUUSD", lots=0.01, price=2345.0, ema=2340.0,
        atr=5.0, spread=0.2, open_positions=0, has_stop=True, session_open=True,
    )
    base.update(over)
    return GradeContext(**base)


def book(slug: str):
    return next(b for b in SEEDS if b.slug == slug)


# -- the separation ---------------------------------------------------------


def test_a_playbook_rule_can_never_reject_an_intent():
    """The failure mode this separation exists to prevent: the journal
    quietly becoming a trade blocker."""
    assert registry.playbook_rules_never_reject()
    for rule in registry.rules_for_scope("playbook"):
        assert rule.applies_to == frozenset(), rule.code
        assert rule.reason is None, rule.code


def test_enforcement_sees_only_risk_rules():
    assert {r.scope for r in risk_rules.RULES} == {"risk"}
    codes = {r.code for r in risk_rules.RULES}
    assert not codes & {r.code for r in registry.rules_for_scope("playbook")}


def test_the_registry_is_the_one_definition():
    """risk/rules.py imports; it does not redefine."""
    for rule in risk_rules.RULES:
        assert registry.BY_CODE[rule.code] is rule


def test_every_registry_code_is_unique():
    codes = [r.code for r in registry.REGISTRY]
    assert len(codes) == len(set(codes))


def test_safety_exits_stay_ungated_after_the_move():
    assert registry.safety_exits_are_ungated()
    assert risk_rules.safety_exits_are_ungated()


# -- grading ----------------------------------------------------------------


def test_a_clean_setup_grades_clean():
    result = grade(book("volman-break"), ctx())
    assert result.clean is True
    assert result.required_pass == result.required_total
    assert result.headline.endswith("rules OK")


def test_a_counter_trend_entry_fails_the_trend_rule():
    result = grade(book("volman-break"), ctx(price=2330.0))  # below the EMA
    assert result.clean is False
    failed = [r for r in result.results if r.ok is False]
    assert "pb.with_trend" in [r.code for r in failed]
    assert "EMA20" in failed[0].actual


def test_an_extended_entry_fails_the_distance_rule():
    # 3 ATR above the EMA against a 1.5 ATR limit.
    result = grade(book("volman-break"), ctx(price=2355.0))
    codes = [r.code for r in result.results if r.ok is False]
    assert "pb.near_ema" in codes


def test_each_playbook_carries_its_own_parameters():
    """The block break allows 0.8 ATR where the break allows 1.5."""
    extended = ctx(price=2345.0)  # exactly 1.0 ATR out
    assert grade(book("volman-break"), extended).clean is True
    block = grade(book("volman-block-break"), extended)
    assert "pb.near_ema" in [r.code for r in block.results if r.ok is False]


def test_a_missing_input_grades_unknown_not_passed():
    """A rule that silently passes when its input is missing is worse than no
    rule."""
    result = grade(book("volman-break"), ctx(ema=None, atr=None))
    by_code = {r.code: r for r in result.results}
    assert by_code["pb.with_trend"].ok is None
    assert by_code["pb.near_ema"].ok is None


def test_the_news_rule_is_unknown_until_phase_four_supplies_a_calendar():
    result = grade(book("volman-break"), ctx(minutes_to_news=None))
    by_code = {r.code: r for r in result.results}
    assert by_code["pb.outside_news"].ok is None


def test_the_news_rule_fails_inside_the_blackout():
    result = grade(book("volman-break"), ctx(minutes_to_news=4))
    by_code = {r.code: r for r in result.results}
    assert by_code["pb.outside_news"].ok is False
    # Symmetric around the release.
    assert grade(book("volman-break"), ctx(minutes_to_news=-4)).results[4].ok is False


# -- manual rules -----------------------------------------------------------


def test_an_unanswered_manual_rule_costs_nothing():
    """Skipping the checklist is neither pass nor fail: the rule drops out of
    the denominator entirely."""
    without = grade(book("volman-pullback-test"), ctx())
    with_answer = grade(
        book("volman-pullback-test"),
        ctx(answers={"pb.waited_for_test": True}),
    )
    assert with_answer.required_total == without.required_total + 1
    assert with_answer.required_pass == without.required_pass + 1
    # And skipping never drags the ratio down.
    assert without.clean is True


def test_a_manual_rule_answered_no_does_fail():
    result = grade(
        book("volman-pullback-test"), ctx(answers={"pb.waited_for_test": False})
    )
    assert result.clean is False
    assert [r for r in result.results if r.code == "pb.waited_for_test"][0].ok is False


def test_the_checklist_asks_only_what_is_unanswered():
    b = book("volman-break")
    assert unanswered_manual_codes(b, {}) == ["pb.setup_was_named", "pb.exit_as_planned"]
    assert unanswered_manual_codes(b, {"pb.setup_was_named": True}) == ["pb.exit_as_planned"]


def test_the_checklist_fits_three_taps():
    """The plan allows a three-tap post-trade checklist; no seeded playbook
    asks for more."""
    for b in SEEDS:
        assert len(unanswered_manual_codes(b, {})) <= 3, b.slug


# -- unplanned --------------------------------------------------------------


def test_no_playbook_grades_as_unplanned():
    result = grade(None, ctx())
    assert result.playbook_slug == "__unplanned__"
    assert result.results == ()
    # Not clean: an unplanned fire must never read as a clean one.
    assert result.clean is False
    assert result.required_total == 0


def test_optional_rules_do_not_gate_clean():
    result = grade(book("volman-range-box"), ctx())
    optional = [r for r in result.results if not r.required]
    assert optional  # the seed has one
    assert result.clean is True


def test_rules_are_immutable():
    """A rule that could be mutated at runtime is a rule whose historical
    grades cannot be trusted."""
    with pytest.raises(Exception):
        registry.BY_CODE["pb.with_trend"].label = "changed"  # type: ignore[misc]


def test_a_broken_rule_does_not_lose_the_whole_grade(monkeypatch):
    def explode(_ctx):
        raise RuntimeError("rule is broken")

    from dataclasses import replace

    broken = replace(registry.BY_CODE["pb.with_trend"], evaluate=explode)
    monkeypatch.setitem(registry.BY_CODE, "pb.with_trend", broken)
    result = grade(book("volman-break"), ctx())
    by_code = {r.code: r for r in result.results}
    assert by_code["pb.with_trend"].ok is None
    assert "error" in by_code["pb.with_trend"].actual
    assert len(result.results) == len(book("volman-break").rules)


def test_a_code_the_registry_lost_grades_unknown():
    from apps.gateway.method.playbook import Playbook, PlaybookRule

    ghost = Playbook(
        slug="ghost", name="Ghost", method="custom", narrative="",
        rules=(PlaybookRule(code="pb.gone", label="Gone", kind="auto"),),
    )
    result = grade(ghost, ctx())
    assert result.results[0].ok is None
    assert "no longer defined" in result.results[0].expected


# -- the store --------------------------------------------------------------


@pytest.fixture
def store(tmp_path):
    writer = JournalWriter(str(tmp_path / "ev.sqlite3"))
    yield PlaybookStore(writer.conn), writer
    writer.close()


def test_seeding_installs_a_real_book(store):
    s, _ = store
    assert s.seed(MS) == len(SEEDS)
    books = s.list()
    assert len(books) == len(SEEDS)
    assert all(b.rules for b in books)


def test_seeding_is_idempotent_and_keeps_player_edits(store):
    s, writer = store
    s.seed(MS)
    writer.conn.execute("UPDATE playbook SET narrative = 'mine' WHERE slug = 'volman-break'")
    assert s.seed(MS) == 0
    assert s.get("volman-break").narrative == "mine"


def test_a_retired_playbook_leaves_selection_but_still_resolves(store):
    s, _ = store
    s.seed(MS)
    book_id = s.get("volman-break").id
    assert s.retire("volman-break", MS) is True

    assert "volman-break" not in [b.slug for b in s.list()]
    # Historical grades must keep naming the book they were graded against.
    assert s.by_id(book_id).name == "Range break"
    assert "volman-break" in [b.slug for b in s.list(include_retired=True)]


def test_rules_round_trip_with_their_parameters(store):
    s, _ = store
    s.seed(MS)
    block = s.get("volman-block-break")
    near = [r for r in block.rules if r.code == "pb.near_ema"][0]
    assert near.params == {"max_atr_from_ema": 0.8}
    assert near.required is True


def test_a_grade_is_stored_against_its_cid(store):
    s, writer = store
    s.seed(MS)
    result = grade(book("volman-break"), ctx())
    cid = "01JBXQ4T7ZK9M2N5P8R3V6W1YZ"
    writer.write_grade(cid, s.get("volman-break").id, None, "fire", result, MS)

    row = writer.grade_row(cid)
    assert row["clean"] == 1
    assert row["phase"] == "fire"
    assert len(json.loads(row["results_json"])) == len(book("volman-break").rules)


def test_re_grading_a_cid_replaces_rather_than_duplicates(store):
    s, writer = store
    s.seed(MS)
    cid = "01JBXQ4T7ZK9M2N5P8R3V6W1YZ"
    writer.write_grade(cid, None, None, "arm", grade(book("volman-break"), ctx()), MS)
    writer.write_grade(cid, None, None, "fire", grade(book("volman-break"), ctx()), MS + 1)
    assert writer.conn.execute("SELECT COUNT(*) c FROM trade_grade").fetchone()["c"] == 1
    assert writer.grade_row(cid)["phase"] == "fire"
