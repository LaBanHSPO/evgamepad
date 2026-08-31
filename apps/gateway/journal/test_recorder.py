"""Fill -> plan, close -> trade + excursions, post-roll -> tape."""

from __future__ import annotations

from pathlib import Path

import pytest

from broker.conversion import AssetGraph
from broker.volume import SymbolSpec
from db.migrate import connect, migrate
from journal.recorder import PRICE_SCALE, TradeRecorder
from journal.tape import TapeRing, unpack_bars
from journal.writer import JournalWriter

USD, JPY, XAU = 1, 3, 4
ASSETS = {USD: "USD", JPY: "JPY", XAU: "XAU"}
GOLD = SymbolSpec(symbol_id=41, name="XAUUSD", digits=2, pip_position=1, lot_size=10_000,
                  min_volume=100, step_volume=100, max_volume=1_000_000,
                  base_asset_id=XAU, quote_asset_id=USD)
GRAPH = AssetGraph(assets=ASSETS, symbols={GOLD.symbol_id: GOLD})

OPENED_MS = 1_700_000_000_000


def price(value: float) -> int:
    return int(round(value * PRICE_SCALE))


@pytest.fixture()
def recorder(tmp_path: Path) -> TradeRecorder:
    db = tmp_path / "journal.db"
    migrate(db)
    journal = JournalWriter(connect(db))
    journal.open_session("S-1", timezone="UTC", opened_at=OPENED_MS, balance=10_000.0,
                         equity=10_000.0)
    ring = TapeRing(ring_minutes=90)
    return TradeRecorder(journal=journal, ring=ring, specs={"XAUUSD": GOLD}, graph=GRAPH,
                         session_id="S-1", r_unit_usd=20.0, pre_roll_s=300, post_roll_s=300)


def tape(recorder: TradeRecorder, *, seconds: int, start_ms: int, bid: float, drift: float) -> None:
    for i in range(seconds):
        recorder.ring.tick("XAUUSD", bid=price(bid + i * drift), ask=price(bid + 0.3 + i * drift),
                           ts_ms=start_ms + i * 1000)


def fill(recorder: TradeRecorder, **over: object) -> object:
    kwargs = dict(cid="01ABC", position_id=9, symbol="XAUUSD", side="buy", volume=100,
                  entry=2000.0, ts_ms=OPENED_MS, prices={}, planned_sl=1998.0, planned_tp=2006.0,
                  timeframe="M5", armed_at=OPENED_MS - 900)
    kwargs.update(over)
    recorder.journal.reserve_cid(str(kwargs["cid"]), intent="open", symbol="XAUUSD", ts_ms=1)
    return recorder.on_fill(**kwargs)  # type: ignore[arg-type]


def test_a_fill_writes_the_plan_with_r_and_its_conversion(recorder: TradeRecorder) -> None:
    fill(recorder)
    row = recorder.journal.conn.execute(
        "SELECT r_usd, r_method, r_rate_source, planned_rr, market_session, lots FROM trade_plan"
    ).fetchone()
    assert row[0] == pytest.approx(2.0), "1 ounce with a $2 stop"
    assert row[1] == "stop"
    assert row[2] == "identity"
    assert row[3] == pytest.approx(3.0), "6 up over 2 down is 3R planned"
    assert row[4] in {"asia", "london", "ny", "late"}
    assert row[5] == pytest.approx(0.01)


def test_a_fill_without_a_stop_records_the_policy_r(recorder: TradeRecorder) -> None:
    fill(recorder, planned_sl=None, planned_tp=None)
    row = recorder.journal.conn.execute("SELECT r_usd, r_method FROM trade_plan").fetchone()
    assert row == (20.0, "fallback")


def test_a_close_writes_an_r_multiple_from_the_brokers_own_figures(recorder: TradeRecorder) -> None:
    fill(recorder)
    closed = recorder.on_close(position_id=9, exit_price=2004.0, ts_ms=OPENED_MS + 60_000,
                               gross_pnl=4.0, commission=-0.1, swap=0.0)
    assert closed is not None
    assert closed.net_pnl_usd == pytest.approx(3.9)
    assert closed.r_multiple == pytest.approx(1.95)


def test_r_multiple_is_non_null_with_and_without_a_stop(recorder: TradeRecorder) -> None:
    """The success criterion: every closed trade is measurable in R."""
    fill(recorder)
    recorder.on_close(position_id=9, exit_price=2004.0, ts_ms=OPENED_MS + 1000, gross_pnl=4.0)
    fill(recorder, cid="01DEF", position_id=10, planned_sl=None, planned_tp=None)
    recorder.on_close(position_id=10, exit_price=1999.0, ts_ms=OPENED_MS + 2000, gross_pnl=-1.0)

    rows = recorder.journal.conn.execute(
        "SELECT cid, r_multiple FROM trade_closed ORDER BY cid"
    ).fetchall()
    assert len(rows) == 2
    assert all(r[1] is not None for r in rows)
    assert rows[1][1] == pytest.approx(-0.05), "the no-stop trade measures against the policy R"


def test_net_pnl_falls_back_to_price_difference_when_the_broker_gave_none(
    recorder: TradeRecorder,
) -> None:
    fill(recorder)
    closed = recorder.on_close(position_id=9, exit_price=2004.0, ts_ms=OPENED_MS + 1000)
    assert closed is not None
    assert closed.net_pnl_usd == pytest.approx(4.0), "1 ounce moved $4"


def test_a_long_and_a_short_take_excursions_from_opposite_sides(recorder: TradeRecorder) -> None:
    tape(recorder, seconds=120, start_ms=OPENED_MS, bid=2000.0, drift=0.05)
    fill(recorder)
    long_closed = recorder.on_close(position_id=9, exit_price=2005.0,
                                    ts_ms=OPENED_MS + 119_000, gross_pnl=5.0)

    fill(recorder, cid="01DEF", position_id=10, side="sell")
    short_closed = recorder.on_close(position_id=10, exit_price=2005.0,
                                     ts_ms=OPENED_MS + 119_000, gross_pnl=-5.0)

    assert long_closed is not None and short_closed is not None
    assert long_closed.mfe > 0, "a rising bid is the long's gain"
    assert short_closed.mae > 0, "the same rise is the short's pain"
    assert short_closed.mae > long_closed.mae


def test_the_tape_is_frozen_only_after_the_post_roll(recorder: TradeRecorder) -> None:
    tape(recorder, seconds=60, start_ms=OPENED_MS, bid=2000.0, drift=0.01)
    fill(recorder)
    closed_at = OPENED_MS + 60_000
    recorder.on_close(position_id=9, exit_price=2000.5, ts_ms=closed_at, gross_pnl=0.5)

    assert recorder.due_freezes(now_ms=closed_at + 1000) == 0, "the post-roll has not settled"
    assert recorder.journal.conn.execute("SELECT COUNT(*) FROM trade_tape").fetchone()[0] == 0

    assert recorder.due_freezes(now_ms=closed_at + 300_000) == 1
    row = recorder.journal.conn.execute(
        "SELECT cid, from_ts, to_ts, bars, mfe FROM trade_tape"
    ).fetchone()
    assert row[0] == "01ABC"
    assert row[1] == OPENED_MS // 1000 - 300, "pre-roll reaches back before the fill"
    header, bars = unpack_bars(row[3])
    assert header["n"] == len(bars) > 0


def test_shutdown_freezes_with_whatever_post_roll_exists(recorder: TradeRecorder) -> None:
    tape(recorder, seconds=30, start_ms=OPENED_MS, bid=2000.0, drift=0.01)
    fill(recorder)
    recorder.on_close(position_id=9, exit_price=2000.2, ts_ms=OPENED_MS + 30_000, gross_pnl=0.2)

    assert recorder.flush(now_ms=OPENED_MS + 35_000) == 1, "a short post-roll still gets frozen"
    assert recorder.journal.conn.execute("SELECT COUNT(*) FROM trade_tape").fetchone()[0] == 1


def test_a_zero_trade_evening_writes_no_tape(recorder: TradeRecorder) -> None:
    tape(recorder, seconds=120, start_ms=OPENED_MS, bid=2000.0, drift=0.01)
    assert recorder.flush(now_ms=OPENED_MS + 200_000) == 0
    assert recorder.journal.conn.execute("SELECT COUNT(*) FROM trade_tape").fetchone()[0] == 0


def test_an_amendment_is_appended_not_overwritten(recorder: TradeRecorder) -> None:
    fill(recorder)
    recorder.on_amend(position_id=9, ts_ms=OPENED_MS + 1000, sl=1999.0, tp=None)
    recorder.on_amend(position_id=9, ts_ms=OPENED_MS + 2000, sl=2000.5, tp=None)
    kinds = [e["kind"] for e in recorder.journal.events_for(9)]
    assert kinds == ["fill", "amend", "amend"]


def test_a_close_for_an_unknown_position_is_recorded_not_dropped(recorder: TradeRecorder) -> None:
    """Reconcile can surface a position this process never saw open."""
    assert recorder.on_close(position_id=404, exit_price=1.0, ts_ms=OPENED_MS) is None
    assert [e["kind"] for e in recorder.journal.events_for(404)] == ["close"]
