"""The score assembled from real journal rows, not from a hand-built `SessionInputs`.

`test_session.py` proves the arithmetic. This proves the *inputs* — that phase 7's grades, phase 2's
frozen risk context, phase 3's stand-down counter and phase 11's own review events all arrive where
the axes expect them, and that a weight change really does recompute history.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from db.migrate import connect, migrate
from journal.writer import JournalWriter
from score.repository import ScoreRepository

SESSION = "2026-08-31"
T0 = 1_788_000_000_000


@pytest.fixture()
def db(tmp_path: Path) -> Path:
    path = tmp_path / "journal.db"
    migrate(path)
    return path


@pytest.fixture()
def journal(db: Path) -> JournalWriter:
    writer = JournalWriter(connect(db))
    writer.open_session(SESSION, timezone="Asia/Ho_Chi_Minh", opened_at=T0, balance=10_000.0,
                        equity=10_000.0)
    yield writer
    writer.conn.close()


def a_fire(journal: JournalWriter, cid: str, *, at: int, lots: float = 0.01,
           planned_sl: float | None = 2456.0, r_usd: float = 20.0,
           playbook_id: str | None = None, max_lots: float = 0.10,
           positions: int = 0, max_positions: int = 1) -> None:
    """A plan row as phase 2 froze it, with the caps that were in force at the fire."""
    journal.reserve_cid(cid, intent="open", symbol="XAUUSD", ts_ms=at)
    journal.write_plan({
        "cid": cid, "session_id": SESSION, "symbol": "XAUUSD", "side": "buy",
        "timeframe": "M5", "market_session": "london", "playbook_id": playbook_id,
        "lots": lots, "volume": 1, "planned_entry": 2458.0, "planned_sl": planned_sl,
        "planned_tp": None, "planned_rr": None, "r_usd": r_usd, "r_method": "stop",
        "r_units": 1.0, "created_at": at, "max_lots_at_fire": max_lots,
        "positions_at_fire": positions, "max_positions_at_fire": max_positions,
    })


def a_grade(journal: JournalWriter, cid: str, *, required_pass: int, required_total: int,
            manual_unknown: bool = False) -> None:
    journal.write_grade({
        "cid": cid, "playbook_id": "pb-range", "stage": "fire", "evaluated_at": T0,
        "results": json.dumps([
            {"code": "auto1", "kind": "auto", "ok": True, "unknown": False},
            {"code": "man1", "kind": "manual", "ok": not manual_unknown,
             "unknown": manual_unknown},
        ]),
        "required_pass": required_pass, "required_total": required_total,
        "clean": int(required_pass == required_total),
    })


def prepared(journal: JournalWriter) -> None:
    """The evening set up the way the Preparation axis asks for."""
    journal.conn.execute(
        "INSERT INTO session_plan (session_id, created_at, text) VALUES (?, ?, ?)",
        (SESSION, T0 - 60_000, "range into the open"),
    )
    journal.write_checkin(SESSION, phase="pre", rating=4, ts_ms=T0 - 30_000)
    journal.write_opportunity_quality(SESSION, 0.5)
    journal.conn.commit()


# -- the inputs arrive where the axes expect them --------------------------------------


def test_grades_supply_adherence(journal: JournalWriter, db: Path) -> None:
    prepared(journal)
    a_fire(journal, "c1", at=T0)
    a_grade(journal, "c1", required_pass=4, required_total=5)
    journal.conn.commit()

    result = ScoreRepository(db).score(SESSION)
    assert result.axis("adherence").value == pytest.approx(80.0)
    assert result.axis("adherence").detail == {"passed": 4, "evaluated": 5}


def test_an_ungraded_fire_evaluates_no_required_rule(journal: JournalWriter, db: Path) -> None:
    """A fire with no playbook is unplanned, not failed."""
    prepared(journal)
    a_fire(journal, "c1", at=T0)
    journal.conn.commit()

    result = ScoreRepository(db).score(SESSION)
    assert result.axis("adherence").value is None
    # It still happened, so risk discipline keeps its denominator.
    assert result.axis("risk_discipline").value is not None


def test_the_risk_context_is_the_one_frozen_at_the_fire(journal: JournalWriter, db: Path) -> None:
    """Scoring a trade against tonight's config would score it against rules it never had."""
    prepared(journal)
    # A cap of 0.02 was in force then, even though today's config allows 0.10.
    a_fire(journal, "c1", at=T0, lots=0.05, max_lots=0.02)
    journal.conn.commit()

    checks = ScoreRepository(db).score(SESSION).axis("risk_discipline").detail["byCheck"]
    assert checks["within_lot_cap"] == 0


def test_a_missing_stop_at_entry_is_the_only_failing_check(journal: JournalWriter,
                                                           db: Path) -> None:
    prepared(journal)
    a_fire(journal, "c1", at=T0, planned_sl=None)
    journal.conn.commit()

    axis = ScoreRepository(db).score(SESSION).axis("risk_discipline")
    assert axis.detail["byCheck"]["stop_at_entry"] == 0
    assert axis.value == pytest.approx(80.0)  # 4 of 5 checks


def test_order_spacing_is_measured_between_consecutive_fires(journal: JournalWriter,
                                                             db: Path) -> None:
    prepared(journal)
    a_fire(journal, "c1", at=T0)
    a_fire(journal, "c2", at=T0 + 500)          # half a second later
    a_fire(journal, "c3", at=T0 + 60_000)
    journal.conn.commit()

    checks = ScoreRepository(db, min_seconds_between_orders=2.0).score(SESSION)
    # The first fire has nothing to be spaced from; only the 0.5 s gap fails.
    assert checks.axis("risk_discipline").detail["byCheck"]["respected_order_spacing"] == 2


def test_an_unrecorded_cap_is_not_invented_into_a_failure(journal: JournalWriter,
                                                          db: Path) -> None:
    """A missing column is missing evidence, not evidence of a breach."""
    prepared(journal)
    journal.reserve_cid("c1", intent="open", symbol="XAUUSD", ts_ms=T0)
    journal.write_plan({
        "cid": "c1", "session_id": SESSION, "symbol": "XAUUSD", "side": "buy",
        "lots": 5.0, "volume": 1, "r_usd": 20.0, "r_method": "stop", "r_units": 1.0,
        "planned_sl": 2456.0, "created_at": T0,
    })
    journal.conn.commit()

    checks = ScoreRepository(db).score(SESSION).axis("risk_discipline").detail["byCheck"]
    assert checks["within_lot_cap"] == 1
    assert checks["within_max_positions"] == 1


def test_the_stand_down_counter_feeds_selectivity(journal: JournalWriter, db: Path) -> None:
    """One counter, phase 3's — not a second one invented for the score."""
    prepared(journal)
    journal.conn.execute(
        "UPDATE session_process SET stood_down_count = 2 WHERE session_id = ?", (SESSION,)
    )
    journal.conn.commit()

    axis = ScoreRepository(db).score(SESSION).axis("selectivity")
    assert axis.detail["declineCredit"] == pytest.approx(10.0)


def test_a_plan_written_after_the_first_fire_is_a_note_not_preparation(journal: JournalWriter,
                                                                      db: Path) -> None:
    a_fire(journal, "c1", at=T0)
    journal.conn.execute(
        "INSERT INTO session_plan (session_id, created_at, text) VALUES (?, ?, ?)",
        (SESSION, T0 + 60_000, "written afterwards"),
    )
    journal.write_opportunity_quality(SESSION, 0.5)
    journal.conn.commit()

    items = ScoreRepository(db).score(SESSION).axis("preparation").detail["items"]
    assert items["planAcknowledged"] is False


def test_a_playbook_on_any_fire_counts_as_selected(journal: JournalWriter, db: Path) -> None:
    prepared(journal)
    a_fire(journal, "c1", at=T0, playbook_id="pb-range")
    journal.conn.commit()
    items = ScoreRepository(db).score(SESSION).axis("preparation").detail["items"]
    assert items["playbookSelected"] is True


def test_an_unanswered_checklist_costs_the_review_axis_only(journal: JournalWriter,
                                                            db: Path) -> None:
    """Skipping the checklist leaves a rule unknown — which is neither a pass nor a fail."""
    prepared(journal)
    a_fire(journal, "c1", at=T0)
    a_grade(journal, "c1", required_pass=5, required_total=5, manual_unknown=True)
    journal.conn.commit()

    result = ScoreRepository(db).score(SESSION)
    assert result.axis("review").detail["items"]["checklists"] is False
    assert result.axis("adherence").value == pytest.approx(100.0)


# -- review evidence ------------------------------------------------------------------


def test_opening_a_replay_is_credited(journal: JournalWriter, db: Path) -> None:
    prepared(journal)
    a_fire(journal, "c1", at=T0)
    a_grade(journal, "c1", required_pass=5, required_total=5)
    journal.write_checkin(SESSION, phase="post", rating=4, ts_ms=T0 + 90_000)
    journal.conn.commit()

    repository = ScoreRepository(db)
    assert repository.score(SESSION).axis("review").detail["items"]["replayOpened"] is False

    repository.record_replay_open(SESSION, "c1", now_ms=T0 + 100_000)
    assert repository.score(SESSION).axis("review").detail["items"]["replayOpened"] is True


def test_reopening_the_same_trade_is_not_two_reviews(journal: JournalWriter, db: Path) -> None:
    prepared(journal)
    repository = ScoreRepository(db)
    for _ in range(3):
        repository.record_replay_open(SESSION, "c1", now_ms=T0)
    assert repository.inputs_for(SESSION).replays_opened == 1


def test_a_first_session_is_not_asked_for_a_replay(journal: JournalWriter, db: Path) -> None:
    """No past trade exists, so the item is dropped rather than failed."""
    prepared(journal)
    items = ScoreRepository(db).score(SESSION).axis("review").detail["items"]
    assert "replayOpened" not in items


def test_memo_items_drop_out_while_voice_is_unbuilt(journal: JournalWriter, db: Path) -> None:
    """Phase 8 is deferred. Scoring the install rather than the evening is explicitly forbidden."""
    prepared(journal)
    items = ScoreRepository(db, voice_available=False).score(SESSION).axis("preparation").detail
    assert "memo" not in items["items"]


# -- persistence and auditability ------------------------------------------------------


def test_the_row_stores_the_inputs_not_just_the_total(journal: JournalWriter, db: Path) -> None:
    prepared(journal)
    a_fire(journal, "c1", at=T0)
    a_grade(journal, "c1", required_pass=4, required_total=5)
    journal.conn.commit()

    ScoreRepository(db).write(SESSION, now_ms=T0 + 200_000)
    row = journal.conn.execute(
        "SELECT total, adherence, na_axes, inputs, n_fires, oq_mean FROM session_score "
        "WHERE session_id = ?", (SESSION,)
    ).fetchone()

    assert row[1] == pytest.approx(80.0)
    assert json.loads(row[2]) == []
    stored = json.loads(row[3])
    assert stored["fires"][0]["required_total"] == 5
    assert row[4] == 1
    assert row[5] == pytest.approx(0.5)


def test_changing_the_weights_recomputes_a_stored_evening(journal: JournalWriter,
                                                          db: Path) -> None:
    """The whole reason the inputs are stored rather than only the total."""
    prepared(journal)
    a_fire(journal, "c1", at=T0)
    a_grade(journal, "c1", required_pass=3, required_total=5)
    journal.conn.commit()

    ScoreRepository(db).write(SESSION, now_ms=T0)
    reweighted = ScoreRepository(db, weights={
        "adherence": 1.0, "selectivity": 0.0, "risk_discipline": 0.0,
        "preparation": 0.0, "review": 0.0,
    }).session_payload(SESSION)

    assert reweighted["total"] == 60  # adherence alone, 3/5


def test_a_vacuous_axis_is_stored_as_null_not_as_zero(journal: JournalWriter, db: Path) -> None:
    prepared(journal)
    ScoreRepository(db).write(SESSION, now_ms=T0)
    row = journal.conn.execute(
        "SELECT adherence, risk_discipline, na_axes FROM session_score WHERE session_id = ?",
        (SESSION,),
    ).fetchone()

    assert row[0] is None and row[1] is None
    assert set(json.loads(row[2])) == {"adherence", "risk_discipline"}


def test_the_month_view_is_a_distribution_with_n(journal: JournalWriter, db: Path) -> None:
    prepared(journal)
    ScoreRepository(db).write(SESSION, now_ms=T0)

    months = ScoreRepository(db).month()["months"]
    assert len(months) == 1
    assert months[0]["n"] == 1
    assert "scores" in months[0] and "mean" in months[0]
    # A distribution, never a streak or a "days since".
    for forbidden in ("streak", "daysSince", "consecutive", "level"):
        assert forbidden not in months[0]


def test_the_schema_has_nowhere_to_accumulate_across_sessions(db: Path) -> None:
    """Structural, not a convention: there is no cross-session table to grow a streak in."""
    import sqlite3

    conn = sqlite3.connect(db)
    try:
        names = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()]
        columns: list[str] = []
        for table in names:
            columns += [r[1].lower() for r in conn.execute(f"PRAGMA table_info({table})")]
    finally:
        conn.close()

    # Matched as whole snake_case tokens rather than substrings: phase 12's `key_levels` holds
    # chart price levels, which is not the gamification kind and must not trip this.
    tokens = {token for column in columns for token in column.split("_")}
    for forbidden in ("streak", "streaks", "level", "badge", "badges", "consecutive"):
        assert forbidden not in tokens, f"`{forbidden}` exists in the schema"
    assert not any(c.startswith("days_since") for c in columns)


def test_the_axes_summary_the_copilot_reads_carries_no_money(journal: JournalWriter,
                                                             db: Path) -> None:
    prepared(journal)
    summary = ScoreRepository(db).axes_summary(SESSION)
    assert set(summary["axes"]) == {"adherence", "selectivity", "risk_discipline",
                                    "preparation", "review"}
    flat = json.dumps(summary).lower()
    for word in ("pnl", "usd", "balance", "equity", "profit"):
        assert word not in flat
