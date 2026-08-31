"""The journal cockpit against real rows, and the boundary that keeps it honest.

The test that matters most is at the bottom: no statement this service runs can write to a table
that holds a broker fact. A journal that can edit a fill is not a journal.
"""

from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

import pytest

from db.migrate import connect, migrate
from journal.attachments import AttachmentError, dimensions, sniff, store
from journal.query_service import READINESS_ITEMS, JournalService

SESSION = "2026-08-31"
T0 = 1_788_000_000_000

# The smallest valid PNG: an 8x8 signature plus an IHDR the dimension reader can parse.
PNG = (b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR"
       + (8).to_bytes(4, "big") + (6).to_bytes(4, "big") + b"\x08\x06\x00\x00\x00" + b"\x00" * 20)


@pytest.fixture()
def db(tmp_path: Path) -> Path:
    path = tmp_path / "journal.db"
    migrate(path)
    conn = connect(path)
    conn.execute(
        "INSERT INTO session_equity (session_id, timezone, opened_at, equity_open) "
        "VALUES (?,?,?,?)", (SESSION, "Asia/Ho_Chi_Minh", T0, 10_000.0),
    )
    conn.commit()
    conn.close()
    return path


@pytest.fixture()
def service(db: Path) -> JournalService:
    svc = JournalService(db)
    svc.seed_mistakes(T0)
    return svc


def a_trade(db: Path, cid: str = "c1", *, lots: float = 0.01, planned_sl: float | None = 2456.0,
            playbook: str | None = None, r_multiple: float = 1.2, side: str = "buy",
            max_lots: float = 0.10, amend_sl: float | None = None,
            timeframe: str = "M5") -> None:
    """A fired-and-closed trade, written the way phases 2 and 7 write one."""
    conn = connect(db)
    conn.execute("INSERT INTO cid_reservation (cid, intent, symbol, state, created_at, updated_at) "
                 "VALUES (?,?,?,?,?,?)", (cid, "open", "XAUUSD", "acked", T0, T0))
    conn.execute(
        "INSERT INTO trade_plan (cid, session_id, symbol, side, timeframe, market_session, "
        "playbook_id, lots, volume, planned_entry, planned_sl, planned_tp, planned_rr, r_usd, "
        "r_method, r_units, created_at, max_lots_at_fire, inside_window, positions_at_fire, "
        "max_positions_at_fire, seconds_to_high_impact) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (cid, SESSION, "XAUUSD", side, timeframe, "london", playbook, lots, 100, 2458.0,
         planned_sl, 2462.0, 2.0, 20.0, "stop", 100.0, T0, max_lots, 1, 0, 1, 3600.0),
    )
    conn.execute(
        "INSERT INTO trade_closed (cid, session_id, position_id, symbol, side, lots, volume, "
        "entry_price, exit_price, opened_at, closed_at, net_pnl_usd, r_usd, r_multiple, mfe, mae) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (cid, SESSION, 7, "XAUUSD", side, lots, 100, 2458.0, 2461.0, T0, T0 + 60_000,
         r_multiple * 20, 20.0, r_multiple, 3.0, 1.0),
    )
    conn.execute("INSERT INTO position_event (cid, position_id, kind, payload, ts) "
                 "VALUES (?,?,?,?,?)", (cid, 7, "fill", json.dumps({"entry": 2458.0}), T0))
    if amend_sl is not None:
        conn.execute("INSERT INTO position_event (cid, position_id, kind, payload, ts) "
                     "VALUES (?,?,?,?,?)",
                     (cid, 7, "amend", json.dumps({"sl": amend_sl}), T0 + 30_000))
    conn.commit()
    conn.close()


def a_grade(db: Path, cid: str, *, clean: bool, manual_unknown: bool = False) -> None:
    conn = connect(db)
    conn.execute(
        "INSERT INTO trade_grade (cid, playbook_id, stage, evaluated_at, results, required_pass, "
        "required_total, clean) VALUES (?,?,?,?,?,?,?,?)",
        (cid, "pb-range", "fire", T0, json.dumps([
            {"code": "m1", "kind": "manual", "ok": not manual_unknown, "unknown": manual_unknown},
        ]), 5 if clean else 3, 5, int(clean)),
    )
    conn.commit()
    conn.close()


# -- today ------------------------------------------------------------------------------


def test_today_lists_every_readiness_item_even_unanswered(service: JournalService) -> None:
    """An unanswered item is a question, not a gap."""
    body = service.today(SESSION)
    assert [r["item"] for r in body["readiness"]] == list(READINESS_ITEMS)
    assert all(r["ok"] is None for r in body["readiness"])


def test_readiness_keeps_declined_distinct_from_no(service: JournalService) -> None:
    service.put_readiness(SESSION, [
        {"item": "sleep", "ok": True}, {"item": "calm", "ok": False},
        {"item": "focus", "ok": None, "note": "did not answer"},
    ], T0)
    by_item = {r["item"]: r for r in service.today(SESSION)["readiness"]}

    assert by_item["sleep"]["ok"] is True
    assert by_item["calm"]["ok"] is False
    assert by_item["focus"]["ok"] is None


def test_an_unknown_readiness_item_is_ignored_rather_than_stored(service: JournalService) -> None:
    service.put_readiness(SESSION, [{"item": "vibes", "ok": True}], T0)
    assert all(r["ok"] is None for r in service.today(SESSION)["readiness"])


def test_the_daily_analysis_is_the_players_own_and_sits_beside_the_desks(service: JournalService,
                                                                        db: Path) -> None:
    conn = connect(db)
    conn.execute("INSERT INTO session_plan (session_id, created_at, text) VALUES (?,?,?)",
                 (SESSION, T0, "the desk's view"))
    conn.commit()
    conn.close()

    service.put_analysis(SESSION, {
        "thesis": "range into the London open", "instruments": ["XAUUSD"],
        "keyLevels": [{"price": 2460, "label": "range high"}], "invalidation": "close above 2462",
        "eventRisks": "NFP", "tags": ["range"], "notes": "wait for the break",
    }, T0)

    body = service.today(SESSION)
    assert body["analysis"]["thesis"] == "range into the London open"
    assert body["analysis"]["keyLevels"][0]["label"] == "range high"
    # Two separate fields: the model never edits what the player wrote.
    assert body["deskPlan"]["text"] == "the desk's view"


def test_player_text_is_length_capped(service: JournalService) -> None:
    service.put_analysis(SESSION, {"thesis": "x" * 50_000}, T0)
    assert len(service.today(SESSION)["analysis"]["thesis"]) <= 8_000


# -- history ----------------------------------------------------------------------------


def test_history_filters_combine_without_leaking_a_trade(service: JournalService,
                                                         db: Path) -> None:
    a_trade(db, "c1", playbook="pb-range", r_multiple=1.2, side="buy", timeframe="M5")
    a_trade(db, "c2", playbook="pb-break", r_multiple=-0.9, side="sell", timeframe="M15")
    a_grade(db, "c1", clean=True)
    a_grade(db, "c2", clean=False)

    only = service.history({"playbook": "pb-range", "side": "buy", "timeframe": "M5",
                            "result": "win"})
    assert [t["cid"] for t in only["trades"]] == ["c1"]
    assert only["total"] == 1

    # A combination nothing satisfies returns nothing rather than relaxing a clause.
    assert service.history({"playbook": "pb-range", "side": "sell"})["total"] == 0


def test_history_filters_by_result_and_by_mistake(service: JournalService, db: Path) -> None:
    a_trade(db, "c1", planned_sl=None, r_multiple=-1.0)
    service.sync_mistakes("c1", T0)

    assert service.history({"result": "loss"})["total"] == 1
    assert service.history({"result": "win"})["total"] == 0
    assert service.history({"mistake": "no_initial_sl"})["total"] == 1
    assert service.history({"mistake": "oversize"})["total"] == 0


def test_an_unrecognised_filter_cannot_reach_the_sql(service: JournalService, db: Path) -> None:
    a_trade(db, "c1")
    # The clause table is fixed, so an unknown key is dropped rather than interpolated.
    assert service.history({"cid": "'; DROP TABLE trade_closed; --"})["total"] == 1


def test_history_paginates_with_a_hard_maximum(service: JournalService, db: Path) -> None:
    for index in range(5):
        a_trade(db, f"c{index}")

    first = service.history({}, page=0, size=2)
    second = service.history({}, page=1, size=2)
    assert len(first["trades"]) == 2 and len(second["trades"]) == 2
    assert first["trades"][0]["cid"] != second["trades"][0]["cid"]
    assert first["total"] == 5

    assert service.history({}, size=10_000)["size"] == 200


# -- trade detail -----------------------------------------------------------------------


def test_the_trade_record_carries_plan_execution_and_review(service: JournalService,
                                                            db: Path) -> None:
    a_trade(db, "c1", playbook="pb-range")
    a_grade(db, "c1", clean=True)

    body = service.trade("c1")
    assert body["plan"]["plannedSl"] == 2456.0
    assert body["execution"]["entry"] == 2458.0
    assert body["grade"]["clean"] is True
    assert body["actualVsPlan"]["label"] == "Actual vs Plan"
    assert set(body["scores"]) == {"before", "during", "after"}
    # Phase 8 is deferred, so this is every trade today — and it must read as normal.
    assert body["memos"] == []


def test_a_worsened_stop_shows_in_actual_vs_plan_and_in_the_mistakes(service: JournalService,
                                                                     db: Path) -> None:
    a_trade(db, "c1", playbook="pb-range", amend_sl=2454.0)
    a_grade(db, "c1", clean=True)
    service.sync_mistakes("c1", T0)

    body = service.trade("c1")
    assert len(body["actualVsPlan"]["worsenedStops"]) == 1
    assert body["actualVsPlan"]["worsenedStops"][0]["to"] == 2454.0
    assert "worsened_sl" in [m["code"] for m in body["mistakes"]]
    assert body["scores"]["during"]["items"]["stopNeverWorsened"] is False


def test_an_early_discretionary_exit_is_the_players_to_record(service: JournalService,
                                                              db: Path) -> None:
    """The tape cannot prove intent, so this arrives from the player and is stored as theirs."""
    a_trade(db, "c1", playbook="pb-range")
    service.put_review("c1", {"intent": "impulsive", "earlyExit": True, "note": "bailed"}, T0)
    service.add_mistake("c1", "early_exit", T0)

    body = service.trade("c1")
    assert body["review"]["earlyExit"] is True
    assert body["intent"] == {"value": "impulsive", "by": "player"}
    assert [m["source"] for m in body["mistakes"] if m["code"] == "early_exit"] == ["player"]


def test_an_unknown_intent_is_refused_rather_than_stored(service: JournalService,
                                                         db: Path) -> None:
    a_trade(db, "c1")
    with pytest.raises(ValueError):
        service.put_review("c1", {"intent": "self-sabotage"}, T0)


def test_a_missing_trade_is_absent_rather_than_empty(service: JournalService) -> None:
    assert service.trade("never-existed") is None


def test_a_trade_with_no_tape_still_has_a_full_record(service: JournalService, db: Path) -> None:
    """Missing tape degrades the replay link, never the detail page."""
    a_trade(db, "c1")
    body = service.trade("c1")
    assert body["hasTape"] is False
    assert body["execution"]["entry"] == 2458.0


# -- mistakes ---------------------------------------------------------------------------


def test_syncing_replaces_derived_mistakes_but_never_player_judgements(service: JournalService,
                                                                      db: Path) -> None:
    a_trade(db, "c1", planned_sl=None)
    service.add_mistake("c1", "revenge_entry", T0)
    service.sync_mistakes("c1", T0)
    service.sync_mistakes("c1", T0 + 1000)

    codes = [(m["code"], m["source"]) for m in service.trade("c1")["mistakes"]]
    assert ("revenge_entry", "player") in codes
    assert codes.count(("no_initial_sl", "auto")) == 1


def test_a_player_can_withdraw_only_their_own_judgement(service: JournalService,
                                                        db: Path) -> None:
    a_trade(db, "c1", planned_sl=None)
    service.sync_mistakes("c1", T0)
    service.add_mistake("c1", "chased_entry", T0)

    service.remove_mistake("c1", "chased_entry")
    service.remove_mistake("c1", "no_initial_sl")

    codes = [m["code"] for m in service.trade("c1")["mistakes"]]
    assert "chased_entry" not in codes
    # A derived mistake is a fact; withdrawing it is not the player's to do.
    assert "no_initial_sl" in codes


def test_a_custom_mistake_is_counted_by_the_same_code_as_a_built_in(service: JournalService,
                                                                    db: Path) -> None:
    a_trade(db, "c1")
    service.define_mistake("traded_tired", "Traded while tired", T0)
    service.add_mistake("c1", "traded_tired", T0)

    taxonomy = {m["code"]: m for m in service.taxonomy()["mistakes"]}
    assert taxonomy["traded_tired"]["builtin"] is False
    assert taxonomy["no_initial_sl"]["builtin"] is True

    trend = service.overview()["mistakes"]["mistakes"]
    assert "traded_tired" in [m["code"] for m in trend]


def test_the_taxonomy_is_seeded_once(service: JournalService) -> None:
    assert service.seed_mistakes(T0) == 0
    assert len(service.taxonomy()["mistakes"]) == 10


# -- overview and days --------------------------------------------------------------------


def test_the_account_appears_as_a_read_only_chip(service: JournalService) -> None:
    """One configured cTrader demo account, not a selector."""
    assert service.overview()["account"]["readOnly"] is True


def test_consistency_states_its_n_and_refuses_a_confident_score_early(service: JournalService,
                                                                      db: Path) -> None:
    conn = connect(db)
    conn.execute("INSERT INTO session_score (session_id, computed_at, weights_version, total, "
                 "inputs) VALUES (?,?,?,?,?)", (SESSION, T0, 1, 92.0, "{}"))
    conn.commit()
    conn.close()

    consistency = service.overview()["consistency"]
    assert consistency["n"] == 1
    assert consistency["value"] is None
    assert consistency["reason"] == "not enough sessions yet"


def test_the_heatmap_carries_process_and_activity_and_no_money(service: JournalService,
                                                               db: Path) -> None:
    a_trade(db, "c1")
    day = service.days()["days"][0]

    assert set(day) == {"sessionId", "openedAt", "score", "trades", "declined", "mistakes",
                        "hasAnalysis", "checkinPre", "checkinPost"}
    flat = str(day).lower()
    for money in ("pnl", "usd", "equity", "balance"):
        assert money not in flat


def test_a_day_drills_into_its_analysis_readiness_score_mistakes_and_trades(
    service: JournalService, db: Path,
) -> None:
    a_trade(db, "c1", planned_sl=None)
    service.put_analysis(SESSION, {"thesis": "range"}, T0)
    service.put_readiness(SESSION, [{"item": "sleep", "ok": True}], T0)
    service.sync_mistakes("c1", T0)

    day = service.day(SESSION)
    assert day["analysis"]["thesis"] == "range"
    assert any(r["item"] == "sleep" and r["ok"] for r in day["readiness"])
    assert [t["cid"] for t in day["trades"]] == ["c1"]
    assert "no_initial_sl" in [m["code"] for m in day["mistakes"]]


def test_the_latest_trades_carry_what_the_list_promises(service: JournalService, db: Path) -> None:
    a_trade(db, "c1", playbook="pb-range", timeframe="M15")
    a_grade(db, "c1", clean=True)

    trade = service.overview()["latestTrades"][0]
    for key in ("symbol", "side", "timeframe", "playbookId", "intent", "rMultiple", "scores",
                "hasTape"):
        assert key in trade
    assert trade["intent"] == "planned"


def test_the_copilot_aggregate_carries_counts_and_no_player_prose(service: JournalService,
                                                                  db: Path) -> None:
    a_trade(db, "c1")
    service.put_analysis(SESSION, {"thesis": "a private thought"}, T0)
    service.put_review("c1", {"note": "another private thought"}, T0)

    flat = json.dumps(service.aggregates()).lower()
    assert "private thought" not in flat
    for money in ("pnl", "usd", "equity", "balance"):
        assert money not in flat


# -- attachments -------------------------------------------------------------------------


def test_the_bytes_decide_the_type_not_the_clients_claim(tmp_path: Path) -> None:
    assert sniff(PNG) == ("image/png", "png")
    with pytest.raises(AttachmentError):
        sniff(b"<svg xmlns='http://www.w3.org/2000/svg'><script/></svg>")
    with pytest.raises(AttachmentError):
        sniff(b"<!doctype html><script>alert(1)</script>")


def test_a_stored_attachment_is_named_by_the_server(tmp_path: Path) -> None:
    stored = store(PNG, directory=tmp_path)
    assert re.fullmatch(r"[0-9A-Z]{26}", stored.id)
    assert (tmp_path / stored.filename()).exists()
    # Dimensions come from the header, so the cap can be enforced without decoding.
    assert (stored.width, stored.height) == (8, 6)


def test_an_empty_or_oversized_upload_is_refused(tmp_path: Path) -> None:
    with pytest.raises(AttachmentError):
        store(b"", directory=tmp_path)
    with pytest.raises(AttachmentError):
        store(PNG + b"\x00" * (9 * 1024 * 1024), directory=tmp_path)


def test_unknown_dimensions_are_absent_rather_than_zero(tmp_path: Path) -> None:
    assert dimensions(b"\xff\xd8\xff" + b"\x00" * 4, "image/jpeg") == (None, None)


def test_an_attachment_row_never_shadows_a_trade(service: JournalService, db: Path,
                                                 tmp_path: Path) -> None:
    a_trade(db, "c1")
    stored = store(PNG, directory=tmp_path)
    service.record_attachment(attachment_id=stored.id, mime=stored.mime, size=stored.bytes,
                              width=stored.width, height=stored.height, session_id=None,
                              cid="c1", label="../../etc/passwd", ts_ms=T0)

    body = service.trade("c1")
    assert body["attachments"][0]["id"] == stored.id
    # The client's name is a label. It is never a path.
    assert body["attachments"][0]["label"] == "../../etc/passwd"
    assert body["execution"]["entry"] == 2458.0


# -- the boundary ---------------------------------------------------------------------------

# Tables holding a broker fact. Nothing in the journal service may write to any of them.
IMMUTABLE = ("trade_plan", "trade_closed", "position_event", "trade_tape", "cid_reservation",
             "session_equity", "trade_grade")


def test_no_journal_write_can_touch_a_broker_fact() -> None:
    """A journal that can edit a fill is not a journal."""
    source = Path(__file__).with_name("query_service.py").read_text(encoding="utf-8")
    statements = re.findall(r"(INSERT|UPDATE|DELETE)\s+(?:OR\s+\w+\s+)?(?:INTO\s+|FROM\s+)?(\w+)",
                            source)
    assert statements, "the guard found no write statements to check"
    for verb, table in statements:
        assert table not in IMMUTABLE, f"{verb} reaches the immutable table `{table}`"


def test_player_review_survives_beside_the_fill_without_changing_it(service: JournalService,
                                                                    db: Path) -> None:
    a_trade(db, "c1")
    before = service.trade("c1")["execution"]

    service.put_review("c1", {"intent": "impulsive", "note": "should not have"}, T0)
    service.add_mistake("c1", "chased_entry", T0)
    service.put_analysis(SESSION, {"thesis": "rewritten"}, T0)

    after = service.trade("c1")["execution"]
    assert after == before


def test_the_service_holds_no_connection_between_calls(service: JournalService) -> None:
    """One connection per call, closed in a finally — a long-lived handle would lock the file."""
    source = Path(__file__).with_name("query_service.py").read_text(encoding="utf-8")
    assert source.count("conn.close()") >= source.count("self._connect()") - 1


def test_every_parameter_reaches_sqlite_as_a_parameter(service: JournalService, db: Path) -> None:
    """No filter value is ever interpolated into a statement."""
    a_trade(db, "c1")
    hostile = "' OR 1=1 --"
    assert service.history({"symbol": hostile})["total"] == 0
    assert service.history({"playbook": hostile})["total"] == 0
    assert service.trade(hostile) is None
    # The table is intact.
    assert sqlite3.connect(db).execute("SELECT COUNT(*) FROM trade_closed").fetchone()[0] == 1


# -- the HTTP surface ----------------------------------------------------------------------


def test_the_journal_routes_serve_what_the_service_reads(tmp_path: Path) -> None:
    from fastapi.testclient import TestClient

    from config import load_config
    from main import create_app
    from test_config import DEFAULT, VALID_ENV

    cfg = load_config(DEFAULT, env=dict(VALID_ENV))
    cfg.paths.data_dir = str(tmp_path)
    with TestClient(create_app(cfg)) as client:
        db_path = Path(cfg.paths.db)
        conn = connect(db_path)
        conn.execute(
            "INSERT INTO session_equity (session_id, timezone, opened_at, equity_open) "
            "VALUES (?,?,?,?)", (SESSION, "Asia/Ho_Chi_Minh", T0, 10_000.0),
        )
        conn.commit()
        conn.close()
        a_trade(db_path, "c1", playbook="pb-range")

        # The taxonomy is seeded at boot, not on first use.
        assert len(client.get("/api/journal/mistakes").json()["mistakes"]) == 10

        today = client.put("/api/journal/today", json={
            "sessionId": SESSION,
            "readiness": [{"item": "sleep", "ok": True}],
            "analysis": {"thesis": "range into the open"},
        })
        assert today.status_code == 200
        assert today.json()["analysis"]["thesis"] == "range into the open"

        assert client.get("/api/journal/overview").json()["account"]["readOnly"] is True
        assert client.get("/api/journal/days").json()["days"][0]["sessionId"] == SESSION
        assert client.get("/api/journal/history").json()["total"] == 1
        assert client.get("/api/journal/trade/c1").json()["plan"]["cid"] == "c1"
        assert client.get("/api/journal/trade/nope").status_code == 404

        # An intent the schema does not know is refused rather than stored.
        assert client.put("/api/journal/trade/c1", json={"intent": "vibes"}).status_code == 422

        system = client.put("/api/journal/system", json={
            "philosophy": "process over outcome", "principles": ["one trade at a time"],
        })
        assert system.json()["principles"] == ["one trade at a time"]


def test_an_attachment_round_trips_and_a_script_is_refused(tmp_path: Path) -> None:
    from fastapi.testclient import TestClient

    from config import load_config
    from main import create_app
    from test_config import DEFAULT, VALID_ENV

    cfg = load_config(DEFAULT, env=dict(VALID_ENV))
    cfg.paths.data_dir = str(tmp_path)
    with TestClient(create_app(cfg)) as client:
        stored = client.post("/api/journal/attachments?label=../../etc/passwd",
                             content=PNG, headers={"content-type": "image/png"})
        assert stored.status_code == 200
        body = stored.json()
        assert body["mime"] == "image/png"

        served = client.get(f"/api/journal/attachments/{body['id']}")
        assert served.status_code == 200
        assert served.headers["content-type"] == "image/png"
        assert served.content == PNG

        # The label never became a path.
        assert not (tmp_path / "etc").exists()

        # An SVG claiming to be a PNG is refused on its bytes, not on its header.
        refused = client.post("/api/journal/attachments", content=b"<svg><script/></svg>",
                              headers={"content-type": "image/png"})
        assert refused.status_code == 415

        assert client.get("/api/journal/attachments/NOTANID").status_code == 404


def test_sizing_rides_http_and_has_no_path_to_an_order(tmp_path: Path) -> None:
    """Phase 1's stub broker has no specs, so the honest answer is a refusal, not a guess."""
    from fastapi.testclient import TestClient

    from config import load_config
    from main import create_app
    from test_config import DEFAULT, VALID_ENV

    cfg = load_config(DEFAULT, env=dict(VALID_ENV))
    cfg.paths.data_dir = str(tmp_path)
    with TestClient(create_app(cfg)) as client:
        response = client.post("/api/journal/size", json={
            "symbol": "XAUUSD", "entry": 2458.0, "stop": 2456.0, "riskUsd": 200.0,
        })
        assert response.status_code == 404
        assert "spec" in response.json()["detail"]
