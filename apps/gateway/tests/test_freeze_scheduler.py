"""The tape freeze job: when it runs, what it writes, and what happens if the
process stops inside a post-roll window."""

from __future__ import annotations

import asyncio

import pytest

from apps.gateway.journal.tape.freeze import unpack_bars
from apps.gateway.journal.tape.ring import TapeRing
from apps.gateway.journal.tape.scheduler import FreezeScheduler, PendingFreeze, r_per_price
from apps.gateway.journal.writer import JournalWriter

T0 = 1_700_000_000
MS = T0 * 1000


def px(v: float) -> int:
    return int(round(v * 100_000))


@pytest.fixture
def writer(tmp_path):
    w = JournalWriter(str(tmp_path / "ev.sqlite3"))
    w.reserve_cid("01JBXQ4T7ZK9M2N5P8R3V6W1YZ", "open", MS, "XAUUSD")
    w.write_closed({
        "position_id": 7001, "cid": None, "session_id": None, "sym": "XAUUSD",
        "side": "buy", "lots": 0.01, "opened_at": MS, "closed_at": MS + 60_000,
        "entry": 2340.0, "exit": 2342.0, "gross_pnl": 2.0, "net_pnl": 2.0,
        "r_usd": 2.0, "r_multiple": 1.0,
    })
    yield w
    w.close()


def ring_with_walk(low: float = 2338.0, high: float = 2344.0) -> TapeRing:
    """Two minutes of gold: dips to `low` at t+20s, spikes to `high` at t+40s."""
    ring = TapeRing(ring_minutes=90, dt_s=1)
    for i in range(120):
        if i == 20:
            bid = low
        elif i == 40:
            bid = high
        else:
            bid = 2340.0
        ring.on_tick("XAUUSD", px(bid), px(bid + 0.20), MS + i * 1000, digits=2)
    ring.seal_all()
    return ring


def pending(**over) -> PendingFreeze:
    base = dict(
        position_id=7001, cid=None, sym="XAUUSD", side="buy", entry=2340.0,
        digits=2, opened_at=MS, closed_at=MS + 60_000,
        r_usd=2.0, protocol_volume=100, r_rate=1.0,
    )
    base.update(over)
    return PendingFreeze(**base)


def scheduler(writer, ring, post_roll_s=300) -> FreezeScheduler:
    return FreezeScheduler(ring, writer, pre_roll_s=300, post_roll_s=post_roll_s, dt_s=1)


def test_a_freeze_writes_one_tape_row(writer):
    sched = scheduler(writer, ring_with_walk())
    sched.flush_one(pending())

    row = writer.conn.execute("SELECT * FROM trade_tape WHERE position_id = 7001").fetchone()
    assert row is not None
    assert row["sym"] == "XAUUSD"
    assert row["n"] > 0
    assert row["dt_s"] == 1
    assert len(unpack_bars(row["bars_gz"])) == row["n"]


def test_the_window_spans_pre_roll_to_post_roll(writer):
    sched = scheduler(writer, ring_with_walk())
    sched.flush_one(pending())
    row = writer.conn.execute("SELECT * FROM trade_tape WHERE position_id = 7001").fetchone()
    assert row["from_ts"] == T0 - 300
    assert row["to_ts"] == T0 + 60 + 300


def test_excursion_lands_on_the_closed_trade(writer):
    sched = scheduler(writer, ring_with_walk())
    sched.flush_one(pending())

    row = writer.conn.execute("SELECT * FROM trade_closed WHERE position_id = 7001").fetchone()
    # Long, entry 2340: best bid 2344 (+4.00), worst bid 2338 (-2.00).
    assert row["mfe"] == pytest.approx(4.0)
    assert row["mae"] == pytest.approx(-2.0)
    # R is $2.00 on one ounce, so one R is 2.00 of price.
    assert row["mfe_r"] == pytest.approx(2.0)
    assert row["mae_r"] == pytest.approx(-1.0)


def test_a_short_measures_the_other_side_of_the_book(writer):
    sched = scheduler(writer, ring_with_walk())
    sched.flush_one(pending(side="sell"))
    row = writer.conn.execute("SELECT * FROM trade_closed WHERE position_id = 7001").fetchone()
    # Short exits at the ask, 0.20 higher: best 2340 - 2338.20, worst 2340 - 2344.20.
    assert row["mfe"] == pytest.approx(1.8)
    assert row["mae"] == pytest.approx(-4.2)


def test_only_the_bars_the_position_was_open_for_count(writer):
    """The spike happens during the trade; a later one outside it must not."""
    ring = TapeRing(ring_minutes=90, dt_s=1)
    for i in range(200):
        bid = 9999.0 if i == 150 else 2340.0  # long after the close
        ring.on_tick("XAUUSD", px(bid), px(bid + 0.2), MS + i * 1000, digits=2)
    ring.seal_all()

    scheduler(writer, ring).flush_one(pending())
    row = writer.conn.execute("SELECT mfe FROM trade_closed WHERE position_id = 7001").fetchone()
    assert row["mfe"] == pytest.approx(0.0)


def test_r_per_price_inverts_the_r_definition():
    # r_usd = units * distance * rate, so distance = r_usd / (units * rate).
    assert r_per_price(pending()) == pytest.approx(2.0)          # 1 oz, $2 R
    assert r_per_price(pending(protocol_volume=200)) == pytest.approx(1.0)
    assert r_per_price(pending(r_rate=0.5)) == pytest.approx(4.0)


def test_a_zero_volume_plan_reports_no_r_excursion(writer):
    """Better a null than an R computed by dividing by zero."""
    scheduler(writer, ring_with_walk()).flush_one(pending(protocol_volume=0))
    row = writer.conn.execute("SELECT * FROM trade_closed WHERE position_id = 7001").fetchone()
    assert row["mfe"] == pytest.approx(4.0)
    assert row["mfe_r"] is None


async def test_the_freeze_waits_for_the_post_roll(writer):
    sched = scheduler(writer, ring_with_walk(), post_roll_s=300)
    sched.schedule(pending(), now_ms=MS + 60_000)
    assert sched.pending_count == 1

    await asyncio.sleep(0)
    # Still waiting: the post-roll is five minutes out.
    assert writer.conn.execute("SELECT COUNT(*) c FROM trade_tape").fetchone()["c"] == 0
    await sched.flush_all()


async def test_a_post_roll_already_elapsed_freezes_immediately(writer):
    sched = scheduler(writer, ring_with_walk(), post_roll_s=1)
    sched.schedule(pending(), now_ms=MS + 600_000)
    await asyncio.sleep(0.05)
    assert writer.conn.execute("SELECT COUNT(*) c FROM trade_tape").fetchone()["c"] == 1


async def test_shutdown_inside_the_post_roll_still_freezes(writer):
    """The failure this exists to prevent: a trade with no tape because the
    process stopped while its post-roll was still running."""
    sched = scheduler(writer, ring_with_walk(), post_roll_s=3600)
    sched.schedule(pending(), now_ms=MS + 60_000)

    flushed = await sched.flush_all()
    assert flushed == 1
    row = writer.conn.execute("SELECT * FROM trade_tape WHERE position_id = 7001").fetchone()
    assert row is not None
    # A short window, stored as a short window rather than as missing data.
    assert row["n"] < row["to_ts"] - row["from_ts"]


async def test_flush_all_is_safe_with_nothing_pending(writer):
    assert await scheduler(writer, ring_with_walk()).flush_all() == 0


async def test_re_closing_a_position_replaces_its_pending_freeze(writer):
    sched = scheduler(writer, ring_with_walk(), post_roll_s=3600)
    sched.schedule(pending(), now_ms=MS)
    sched.schedule(pending(closed_at=MS + 90_000), now_ms=MS)
    assert sched.pending_count == 1
    await sched.flush_all()
    row = writer.conn.execute("SELECT to_ts FROM trade_tape WHERE position_id = 7001").fetchone()
    # The later close won: 3600s post-roll off the replaced closed_at.
    assert row["to_ts"] == T0 + 90 + 3600


def test_a_symbol_with_no_ring_does_not_raise(writer):
    sched = scheduler(writer, TapeRing())
    assert sched.flush_one(pending()) is None


def test_a_zero_trade_evening_writes_no_tape(writer):
    """The ring runs all evening; nothing is persisted without a close."""
    ring = ring_with_walk()
    scheduler(writer, ring)  # constructed, never scheduled
    assert writer.conn.execute("SELECT COUNT(*) c FROM trade_tape").fetchone()["c"] == 0
