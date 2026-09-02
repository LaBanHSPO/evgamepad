"""Replay serving, against a tape frozen by the real recorder rather than a hand-built blob.

The fixture drives ticks through the actual ring, fills and closes through the actual recorder, and
freezes through the actual freeze path. That is deliberate: the one thing worth proving here is
that what phase 2 *writes* is what phase 10 can *read*, and a hand-rolled fixture would only prove
this module agrees with itself.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from broker.volume import SymbolSpec
from db.migrate import connect, migrate
from journal.recorder import PRICE_SCALE, TradeRecorder
from journal.tape import TapeRing, normalise
from journal.writer import JournalWriter
from replay import ReplayRepository

SYMBOL = "XAUUSD"
SESSION = "2026-08-31"
# 20:57 local on an evening, in ms. Round numbers keep the bar arithmetic readable.
OPENED_MS = 1_788_000_000_000
CLOSED_MS = OPENED_MS + 120_000
ENTRY = 2458.10
EXIT = 2473.00

SPEC = SymbolSpec(symbol_id=1, name=SYMBOL, digits=2, pip_position=2, lot_size=100,
                  min_volume=1, step_volume=1, max_volume=100_000, base_asset_id=2,
                  quote_asset_id=1)


def scaled(price: float) -> int:
    return int(round(price * PRICE_SCALE))


@pytest.fixture()
def db(tmp_path: Path) -> Path:
    path = tmp_path / "journal.db"
    migrate(path)
    return path


@pytest.fixture()
def journal(db: Path) -> JournalWriter:
    writer = JournalWriter(connect(db))
    writer.open_session(SESSION, timezone="Asia/Ho_Chi_Minh", opened_at=OPENED_MS - 600_000,
                        balance=10_000.0, equity=10_000.0)
    yield writer
    writer.conn.close()


def reserve(journal: JournalWriter, cid: str, ts_ms: int = OPENED_MS) -> None:
    """The socket reserves a cid before it calls the broker; `trade_plan` has the FK to prove it."""
    journal.reserve_cid(cid, intent="open", symbol=SYMBOL, ts_ms=ts_ms)


def recorder_for(journal: JournalWriter, ring: TapeRing) -> TradeRecorder:
    return TradeRecorder(journal=journal, ring=ring, specs={SYMBOL: SPEC}, graph=None,
                         session_id=SESSION, r_unit_usd=20.0, pre_roll_s=300, post_roll_s=300,
                         dt_s=1)


def fill_the_ring(ring: TapeRing, *, from_ms: int, to_ms: int, base: float = ENTRY) -> None:
    """One tick a second, drifting up, with a visible spread so bid and ask differ."""
    step = 0
    for ts in range(from_ms, to_ms, 1000):
        price = base + step * 0.05
        ring.tick(SYMBOL, bid=scaled(price), ask=scaled(price + 0.30), ts_ms=ts)
        step += 1


def a_closed_trade(journal: JournalWriter, *, position_id: int = 7, cid: str = "cid-1") -> None:
    """Fill, close and freeze one trade end to end."""
    ring = TapeRing(ring_minutes=90, dt_s=1)
    fill_the_ring(ring, from_ms=OPENED_MS - 300_000, to_ms=CLOSED_MS + 300_000)
    recorder = recorder_for(journal, ring)
    reserve(journal, cid)
    recorder.on_fill(cid=cid, position_id=position_id, symbol=SYMBOL, side="buy", volume=1,
                     entry=ENTRY, ts_ms=OPENED_MS, prices={}, armed_at=OPENED_MS - 4_000)
    recorder.on_close(position_id=position_id, exit_price=EXIT, ts_ms=CLOSED_MS, gross_pnl=14.90)
    recorder.flush(now_ms=CLOSED_MS + 300_000)


def pad_row(journal: JournalWriter, *, ts: int, to_phase: str, from_phase: str = "CLUTCH",
            reason: str | None = None) -> None:
    journal.write_pad_event(SESSION, {
        "ts": ts, "from": from_phase, "to": to_phase, "reason": reason, "sym": SYMBOL,
        "lots": 0.01, "clutchMs": 900, "armMs": 300, "clutchCycles": 2, "armFlips": 0,
        "btnRateHz": 3.0, "lotStepsSince": 0,
    })


# -- the round trip -------------------------------------------------------------------


def test_a_frozen_tape_reads_back_with_both_sides_of_the_book(journal: JournalWriter,
                                                              db: Path) -> None:
    a_closed_trade(journal)
    body = ReplayRepository(db).trade("cid-1")

    assert body is not None
    tape = body["tape"]
    assert tape["n"] > 0
    assert len(tape["ts"]) == tape["n"]
    # Both sides are stored because a buy's excursion is measured on the bid and a sell's on the
    # ask. Serving one side would put the asymmetry bug back.
    assert tape["askC"][0] > tape["bidC"][0]
    # Integers all the way out: the client divides once, at the point of drawing.
    assert all(isinstance(value, int) for value in tape["bidC"])
    assert body["scale"] == PRICE_SCALE


def test_the_window_covers_the_pre_roll_and_the_post_roll(journal: JournalWriter, db: Path) -> None:
    a_closed_trade(journal)
    tape = ReplayRepository(db).trade("cid-1")["tape"]

    assert tape["fromTs"] <= OPENED_MS // 1000 - 300
    assert tape["toTs"] >= CLOSED_MS // 1000 + 299


def test_entry_and_exit_come_from_the_fill_not_from_the_bars(journal: JournalWriter,
                                                             db: Path) -> None:
    """At 1 Hz the entry bar is context; the fill is truth."""
    a_closed_trade(journal)
    trade = ReplayRepository(db).trade("cid-1")["trade"]

    assert trade["entry"] == ENTRY
    assert trade["exit"] == EXIT
    assert trade["openedAt"] == OPENED_MS
    assert trade["closedAt"] == CLOSED_MS
    assert trade["rMultiple"] is not None


def test_excursions_survive_the_freeze(journal: JournalWriter, db: Path) -> None:
    a_closed_trade(journal)
    body = ReplayRepository(db).trade("cid-1")
    assert body["trade"]["mfe"] is not None and body["trade"]["mfe"] > 0
    assert body["tape"]["mfe"] is not None


# -- events ---------------------------------------------------------------------------


def test_an_arm_cancelled_before_the_fire_is_on_the_rail(journal: JournalWriter, db: Path) -> None:
    """The single most valuable event in a review: the trade you decided not to take."""
    pad_row(journal, ts=OPENED_MS - 40_000, to_phase="ARMED")
    pad_row(journal, ts=OPENED_MS - 38_000, from_phase="ARMED", to_phase="IDLE", reason="spread")
    pad_row(journal, ts=OPENED_MS - 200, from_phase="ARMED", to_phase="FIRE")
    a_closed_trade(journal)

    events = ReplayRepository(db).trade("cid-1")["events"]
    kinds = [e["kind"] for e in events]
    assert "arm" in kinds and "cancel" in kinds and "fire" in kinds

    cancel = next(e for e in events if e["kind"] == "cancel")
    assert cancel["ts"] == OPENED_MS - 38_000, "the cancel keeps its real timestamp"
    assert "spread" in cancel["label"]


def test_the_broker_ack_and_a_stop_move_land_on_the_rail(journal: JournalWriter, db: Path) -> None:
    ring = TapeRing(ring_minutes=90, dt_s=1)
    fill_the_ring(ring, from_ms=OPENED_MS - 300_000, to_ms=CLOSED_MS + 300_000)
    recorder = recorder_for(journal, ring)
    reserve(journal, "cid-1")
    recorder.on_fill(cid="cid-1", position_id=7, symbol=SYMBOL, side="buy", volume=1,
                     entry=ENTRY, ts_ms=OPENED_MS, prices={})
    recorder.on_amend(position_id=7, ts_ms=OPENED_MS + 30_000, sl=2460.0, tp=None)
    recorder.on_close(position_id=7, exit_price=EXIT, ts_ms=CLOSED_MS, gross_pnl=14.90)
    recorder.flush(now_ms=CLOSED_MS + 300_000)

    events = ReplayRepository(db).trade("cid-1")["events"]
    kinds = [e["kind"] for e in events]
    assert "ack" in kinds and "sl_move" in kinds
    assert "2460.0" in next(e for e in events if e["kind"] == "sl_move")["label"]


def test_tilt_contributes_crossings_not_every_sample(journal: JournalWriter, db: Path) -> None:
    """A band held for ten minutes is one event, not six hundred."""
    for offset, band in enumerate(["calm", "calm", "warm", "warm", "warm", "hot"]):
        journal.write_tilt_sample({
            "session_id": SESSION, "ts": OPENED_MS - 60_000 + offset * 1000, "score": 0.5,
            "band": band, "components": "[]", "missing": "[]", "top_driver": "size at 2.0x",
        })
    a_closed_trade(journal)

    bands = [e for e in ReplayRepository(db).trade("cid-1")["events"]
             if e["kind"] == "tilt_band_change"]
    assert [e["band"] for e in bands] == ["calm", "warm", "hot"]


def test_signals_are_labelled_by_their_source(journal: JournalWriter, db: Path) -> None:
    journal.conn.execute(
        "INSERT INTO signal_item (id, session_id, kind, symbol, side, text, url, ts) "
        "VALUES (?,?,?,?,?,?,?,?)",
        ("s1", SESSION, "volman", SYMBOL, "buy", "M5 range break", None, OPENED_MS - 10_000),
    )
    journal.conn.execute(
        "INSERT INTO signal_item (id, session_id, kind, symbol, side, text, url, ts) "
        "VALUES (?,?,?,?,?,?,?,?)",
        ("s2", SESSION, "tv", SYMBOL, "buy", "VIP alert", None, OPENED_MS - 5_000),
    )
    a_closed_trade(journal)

    kinds = {e["kind"] for e in ReplayRepository(db).trade("cid-1")["events"]}
    assert "volman_tag" in kinds and "tv_signal" in kinds


def test_events_are_ordered_by_time_across_every_source(journal: JournalWriter, db: Path) -> None:
    pad_row(journal, ts=OPENED_MS - 40_000, to_phase="ARMED")
    journal.write_tilt_sample({
        "session_id": SESSION, "ts": OPENED_MS - 20_000, "score": 0.7, "band": "hot",
        "components": "[]", "missing": "[]", "top_driver": None,
    })
    a_closed_trade(journal)

    stamps = [e["ts"] for e in ReplayRepository(db).trade("cid-1")["events"]]
    assert stamps == sorted(stamps)


def test_a_pre_phase_10_tape_still_replays(journal: JournalWriter, db: Path) -> None:
    """Phase 2 froze `{kind, payload, ts}`. A thinner rail beats a 500 on last month's trade."""
    legacy = [{"kind": "fill", "ts": OPENED_MS, "payload": {"entry": ENTRY}},
              {"kind": "close", "ts": CLOSED_MS, "payload": {"exit": EXIT}}]
    assert [e["kind"] for e in normalise(legacy)] == ["fill", "close"]
    assert all("label" in e for e in normalise(legacy))


# -- degrading rather than blanking ---------------------------------------------------


def test_a_trade_with_no_tape_still_returns_its_markers(journal: JournalWriter, db: Path) -> None:
    """A pre-phase-2 trade has no window. It is still worth reviewing."""
    ring = TapeRing(ring_minutes=90, dt_s=1)
    recorder = recorder_for(journal, ring)
    reserve(journal, "cid-bare")
    recorder.on_fill(cid="cid-bare", position_id=9, symbol=SYMBOL, side="buy", volume=1,
                     entry=ENTRY, ts_ms=OPENED_MS, prices={})
    recorder.on_close(position_id=9, exit_price=EXIT, ts_ms=CLOSED_MS, gross_pnl=14.90)
    # No freeze at all.

    body = ReplayRepository(db).trade("cid-bare")
    assert body is not None
    assert body["tape"] is None
    assert body["trade"]["entry"] == ENTRY
    assert body["events"] == []


def test_an_unreadable_blob_degrades_to_the_marker_view(journal: JournalWriter, db: Path) -> None:
    a_closed_trade(journal)
    journal.conn.execute("UPDATE trade_tape SET bars = ? WHERE cid = ?", (b"not gzip", "cid-1"))
    journal.conn.commit()

    body = ReplayRepository(db).trade("cid-1")
    assert body["tape"] is None
    assert body["trade"]["entry"] == ENTRY


def test_an_unknown_cid_is_absent_rather_than_empty(journal: JournalWriter, db: Path) -> None:
    assert ReplayRepository(db).trade("never-existed") is None


def test_a_trade_with_no_memo_replays_with_an_empty_index(journal: JournalWriter, db: Path) -> None:
    """Phase 8 is deferred, so this is every trade today — and it must read as normal, not broken."""
    a_closed_trade(journal)
    assert ReplayRepository(db).trade("cid-1")["memos"] == []


# -- the index ------------------------------------------------------------------------


def test_the_index_lists_trades_in_the_order_they_were_taken(journal: JournalWriter,
                                                             db: Path) -> None:
    """Stepping order has to match the evening, or "previous trade" means nothing."""
    ring = TapeRing(ring_minutes=90, dt_s=1)
    fill_the_ring(ring, from_ms=OPENED_MS - 300_000, to_ms=CLOSED_MS + 900_000)
    recorder = recorder_for(journal, ring)
    for index, (cid, position_id) in enumerate([("cid-a", 1), ("cid-b", 2), ("cid-c", 3)]):
        opened = OPENED_MS + index * 200_000
        reserve(journal, cid, opened)
        recorder.on_fill(cid=cid, position_id=position_id, symbol=SYMBOL, side="buy", volume=1,
                         entry=ENTRY, ts_ms=opened, prices={})
        recorder.on_close(position_id=position_id, exit_price=EXIT, ts_ms=opened + 60_000,
                          gross_pnl=1.0)

    trades = ReplayRepository(db).index()["trades"]
    assert [t["cid"] for t in trades] == ["cid-a", "cid-b", "cid-c"]
    assert [t["closedAt"] for t in trades] == sorted(t["closedAt"] for t in trades)


def test_the_index_says_which_trades_have_a_tape(journal: JournalWriter, db: Path) -> None:
    a_closed_trade(journal, position_id=7, cid="cid-1")
    ring = TapeRing(ring_minutes=90, dt_s=1)
    recorder = recorder_for(journal, ring)
    reserve(journal, "cid-bare")
    recorder.on_fill(cid="cid-bare", position_id=9, symbol=SYMBOL, side="buy", volume=1,
                     entry=ENTRY, ts_ms=OPENED_MS + 400_000, prices={})
    recorder.on_close(position_id=9, exit_price=EXIT, ts_ms=OPENED_MS + 460_000, gross_pnl=1.0)

    by_cid = {t["cid"]: t for t in ReplayRepository(db).index()["trades"]}
    assert by_cid["cid-1"]["hasTape"] is True
    assert by_cid["cid-bare"]["hasTape"] is False


def test_the_index_windows_by_close_time(journal: JournalWriter, db: Path) -> None:
    a_closed_trade(journal)
    assert ReplayRepository(db).index(from_ms=CLOSED_MS + 1)["trades"] == []
    assert len(ReplayRepository(db).index(to_ms=CLOSED_MS)["trades"]) == 1


def test_an_empty_journal_lists_nothing_rather_than_failing(db: Path) -> None:
    assert ReplayRepository(db).index()["trades"] == []


# -- size ---------------------------------------------------------------------------


def test_one_evening_of_five_trades_stays_small(journal: JournalWriter, db: Path) -> None:
    """The plan's budget: under ~100 KB of tape for a five-trade evening."""
    ring = TapeRing(ring_minutes=90, dt_s=1)
    fill_the_ring(ring, from_ms=OPENED_MS - 300_000, to_ms=OPENED_MS + 1_800_000)
    recorder = recorder_for(journal, ring)
    for index in range(5):
        opened = OPENED_MS + index * 200_000
        reserve(journal, f"cid-{index}", opened)
        recorder.on_fill(cid=f"cid-{index}", position_id=index + 1, symbol=SYMBOL, side="buy",
                         volume=1, entry=ENTRY, ts_ms=opened, prices={})
        recorder.on_close(position_id=index + 1, exit_price=EXIT, ts_ms=opened + 60_000,
                          gross_pnl=1.0)
    recorder.flush(now_ms=OPENED_MS + 1_800_000)

    conn = sqlite3.connect(db)
    try:
        total: int = conn.execute("SELECT SUM(LENGTH(bars)) FROM trade_tape").fetchone()[0]
        rows: int = conn.execute("SELECT COUNT(*) FROM trade_tape").fetchone()[0]
    finally:
        conn.close()

    assert rows == 5, "one row per trade, never one per sample"
    assert total < 100 * 1024, f"five trades wrote {total} bytes of tape"


# -- the HTTP surface -----------------------------------------------------------------


def test_the_routes_serve_what_the_repository_reads(tmp_path: Path) -> None:
    from fastapi.testclient import TestClient

    from config import load_config
    from main import create_app
    from test_config import DEFAULT, VALID_ENV

    cfg = load_config(DEFAULT, env=dict(VALID_ENV))
    cfg.paths.data_dir = str(tmp_path)
    with TestClient(create_app(cfg)) as client:
        writer = JournalWriter(connect(Path(cfg.paths.db)))
        try:
            writer.open_session(SESSION, timezone="Asia/Ho_Chi_Minh", opened_at=OPENED_MS,
                                balance=10_000.0, equity=10_000.0)
            a_closed_trade(writer)
        finally:
            writer.conn.close()

        listed = client.get("/api/replay/index").json()
        assert [t["cid"] for t in listed["trades"]] == ["cid-1"]

        body = client.get("/api/replay/cid-1").json()
        assert body["trade"]["entry"] == ENTRY
        assert body["tape"]["n"] > 0

        assert client.get("/api/replay/no-such-trade").status_code == 404


def test_every_statement_replay_runs_is_a_select() -> None:
    """Review is a read. Nothing on this path may mutate the journal."""
    source = Path(__file__).with_name("repository.py").read_text(encoding="utf-8")
    fragments = source.split("execute(")[1:]
    assert fragments, "the guard found no statements to check"
    for fragment in fragments:
        first = fragment.lstrip(" \n\"'f").split(None, 1)[0].upper()
        assert first == "SELECT", f"replay runs a `{first}` statement"
