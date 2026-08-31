"""Journal writes, with the cid ledger as the idempotency guarantee behind every order."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from db.migrate import connect, migrate
from journal.writer import ACKED, REJECTED, ClosedTrade, JournalWriter


@pytest.fixture()
def journal(tmp_path: Path) -> JournalWriter:
    db = tmp_path / "journal.db"
    migrate(db)
    return JournalWriter(connect(db))


def test_a_cid_can_only_be_claimed_once(journal: JournalWriter) -> None:
    """The duplicate-fire guard: a second claim fails, so a retry cannot open a second position."""
    assert journal.reserve_cid("01ABC", intent="open", symbol="XAUUSD", ts_ms=1) is True
    assert journal.reserve_cid("01ABC", intent="open", symbol="XAUUSD", ts_ms=2) is False
    assert journal.cid_state("01ABC")["state"] == "pending"


def test_a_settled_cid_records_how_it_ended(journal: JournalWriter) -> None:
    journal.reserve_cid("01ABC", intent="open", symbol="XAUUSD", ts_ms=1)
    journal.settle_cid("01ABC", state=ACKED, ts_ms=2, order_id=7, position_id=9)
    row = journal.cid_state("01ABC")
    assert row["state"] == ACKED
    assert row["position_id"] == 9

    journal.reserve_cid("01DEF", intent="open", symbol="XAUUSD", ts_ms=3)
    journal.settle_cid("01DEF", state=REJECTED, ts_ms=4, reason="daily_loss")
    assert journal.cid_state("01DEF")["reason"] == "daily_loss"


def test_pending_cids_are_what_a_reboot_reconciles(journal: JournalWriter) -> None:
    journal.reserve_cid("01A", intent="open", symbol="XAUUSD", ts_ms=1)
    journal.reserve_cid("01B", intent="open", symbol="EURUSD", ts_ms=2)
    journal.settle_cid("01A", state=ACKED, ts_ms=3)
    assert journal.pending_cids() == ["01B"]


def test_session_equity_comes_from_the_account_at_both_ends(journal: JournalWriter) -> None:
    """Balance and equity are snapshots from cTrader, never sums of local fills."""
    journal.open_session("S-1", timezone="Asia/Ho_Chi_Minh", opened_at=100,
                         balance=10_000.0, equity=10_000.0)
    journal.close_session("S-1", closed_at=200, balance=10_120.0, equity=10_120.0)
    row = journal.session_row("S-1")
    assert row["balance_open"] == 10_000.0
    assert row["equity_close"] == 10_120.0
    assert row["closed_at"] == 200


def test_opening_the_same_session_twice_keeps_the_first_snapshot(journal: JournalWriter) -> None:
    journal.open_session("S-1", timezone="UTC", opened_at=100, balance=10_000.0, equity=10_000.0)
    journal.open_session("S-1", timezone="UTC", opened_at=150, balance=9_000.0, equity=9_000.0)
    assert journal.session_row("S-1")["balance_open"] == 10_000.0


def test_a_plan_stores_r_and_the_conversion_that_produced_it(journal: JournalWriter) -> None:
    journal.reserve_cid("01ABC", intent="open", symbol="USDJPY", ts_ms=1)
    journal.write_plan({
        "cid": "01ABC", "session_id": None, "symbol": "USDJPY", "side": "buy",
        "timeframe": "M5", "market_session": "london", "playbook_id": None,
        "lots": 0.01, "volume": 100_000, "planned_entry": 150.0, "relative_sl": 15_000,
        "relative_tp": None, "planned_sl": 149.85, "planned_tp": None, "planned_rr": None,
        "r_usd": 1.0, "r_method": "stop", "r_units": 1000.0, "r_stop_distance": 0.15,
        "r_rate": 1 / 150, "r_rate_chain": "JPY -> USD", "r_rate_source": "USDJPY",
        "r_rate_ts": 1_700_000_000_000, "armed_at": 5, "created_at": 6,
    })
    row = journal.conn.execute(
        "SELECT r_usd, r_rate_source, r_rate_ts FROM trade_plan WHERE cid = ?", ("01ABC",)
    ).fetchone()
    assert row == (1.0, "USDJPY", 1_700_000_000_000)


def test_position_events_are_append_only_and_ordered(journal: JournalWriter) -> None:
    journal.append_event(kind="fill", ts_ms=10, position_id=5, payload={"price": 2000.0})
    journal.append_event(kind="amend", ts_ms=20, position_id=5, payload={"sl": 1998.0})
    journal.append_event(kind="close", ts_ms=30, position_id=5, payload={"price": 2004.0})
    events = journal.events_for(5)
    assert [e["kind"] for e in events] == ["fill", "amend", "close"]
    assert events[1]["payload"]["sl"] == 1998.0


def test_every_closed_trade_carries_an_r_multiple(journal: JournalWriter) -> None:
    journal.reserve_cid("01ABC", intent="open", symbol="XAUUSD", ts_ms=1)
    journal.write_plan({"cid": "01ABC", "symbol": "XAUUSD", "side": "buy", "lots": 0.01,
                        "volume": 100, "r_usd": 2.0, "r_method": "stop", "r_units": 1.0,
                        "created_at": 1})
    journal.write_closed(ClosedTrade(
        cid="01ABC", session_id=None, position_id=9, symbol="XAUUSD", side="buy", lots=0.01,
        volume=100, entry_price=2000.0, exit_price=2004.0, opened_at=10, closed_at=20,
        gross_pnl=4.0, commission=-0.1, swap=0.0, net_pnl_usd=3.9, r_usd=2.0, r_multiple=1.95,
        mfe=5.0, mae=1.0,
    ))
    row = journal.conn.execute(
        "SELECT r_multiple, mfe, mae FROM trade_closed WHERE cid = ?", ("01ABC",)
    ).fetchone()
    assert row == (1.95, 5.0, 1.0)


def test_a_closed_trade_must_reference_a_planned_one(journal: JournalWriter) -> None:
    """Foreign keys are on; a close with no plan is a bug, not a row."""
    with pytest.raises(sqlite3.IntegrityError):
        journal.write_closed(ClosedTrade(
            cid="unknown", session_id=None, position_id=1, symbol="XAUUSD", side="buy",
            lots=0.01, volume=100, entry_price=None, exit_price=None, opened_at=None,
            closed_at=1, gross_pnl=None, commission=None, swap=None, net_pnl_usd=None,
            r_usd=1.0, r_multiple=0.0,
        ))


def test_tape_rows_are_written_once_per_trade(journal: JournalWriter) -> None:
    journal.reserve_cid("01ABC", intent="open", symbol="XAUUSD", ts_ms=1)
    journal.write_plan({"cid": "01ABC", "symbol": "XAUUSD", "side": "buy", "lots": 0.01,
                        "volume": 100, "r_usd": 2.0, "r_method": "stop", "r_units": 1.0,
                        "created_at": 1})
    for mfe in (5.0, 6.0):
        journal.write_tape(cid="01ABC", position_id=9, symbol="XAUUSD", from_ts=0, to_ts=900,
                           dt_s=1, bars=b"gzipped", events=[{"kind": "fill"}], mfe=mfe, mae=1.0,
                           created_at=1)
    rows = journal.conn.execute("SELECT COUNT(*), MAX(mfe) FROM trade_tape").fetchone()
    assert rows == (1, 6.0), "a re-freeze replaces the window rather than duplicating it"
