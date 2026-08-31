"""Gateway boot: healthz, and the generated web types staying in step with the catalog."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import WebSocketDisconnect
from fastapi.testclient import TestClient

from config import load_config
from main import create_app
from protocol.export_ts import SCHEMA_PATH, TYPES_PATH, current_files
from test_config import DEFAULT, VALID_ENV


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    cfg = load_config(DEFAULT, env=dict(VALID_ENV))
    # Keep the test off the real /data volume.
    cfg.paths.data_dir = str(tmp_path)
    with TestClient(create_app(cfg)) as c:
        yield c


def test_healthz_reports_a_demo_gateway_with_an_unwired_broker(client: TestClient) -> None:
    body = client.get("/healthz").json()
    assert body["ok"] is True
    assert body["mode"] == "demo"
    assert body["protocol"] == 1
    # Phase 1 ships a stub: it must never claim a broker connection it does not have.
    assert body["broker"] == {"connected": False, "reason": "not_wired"}


def test_boot_runs_migrations_against_the_configured_volume(client: TestClient, tmp_path: Path) -> None:
    client.get("/healthz")
    assert (tmp_path / "journal.db").exists()


def test_generated_web_types_match_the_catalog() -> None:
    """A catalog change that is not regenerated fails here and in the web build."""
    schema_text, types_text = current_files()
    assert SCHEMA_PATH.read_text(encoding="utf-8") == schema_text, "run: uv run python -m protocol.export_ts"
    assert TYPES_PATH.read_text(encoding="utf-8") == types_text, "run: uv run python -m protocol.export_ts"


def test_the_socket_refuses_a_foreign_origin(client: TestClient) -> None:
    """One origin: the HUD and the socket are served from the same place."""
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws", headers={"origin": "https://evil.example"}):
            pass


def test_the_socket_refuses_a_missing_token(client: TestClient, monkeypatch) -> None:
    cfg = client.app.state.config
    monkeypatch.setenv(cfg.gateway.token_env, "the-real-token")
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(
            "/ws", headers={"origin": cfg.gateway.public_origin}
        ):
            pass


def test_a_full_socket_round_trip_over_the_real_route(client: TestClient, monkeypatch) -> None:
    """hello -> welcome, and an intent reaches the stub broker's refusal, through the ASGI app."""
    import json

    cfg = client.app.state.config
    monkeypatch.setenv(cfg.gateway.token_env, "the-real-token")

    with client.websocket_connect(
        "/ws?token=the-real-token", headers={"origin": cfg.gateway.public_origin}
    ) as ws:
        ws.send_text(json.dumps({"v": 1, "t": "hello", "seq": 1, "ts": 1, "ch": "session",
                                 "p": {"token": "the-real-token"}}))
        welcome = json.loads(ws.receive_text())
        assert welcome["t"] == "welcome"
        assert welcome["p"]["mode"] == "demo"

        ws.send_text(json.dumps({"v": 1, "t": "ping", "seq": 2, "ts": 1, "ch": "session",
                                 "p": {"visible": True, "pad": True, "clutch": False}}))
        assert json.loads(ws.receive_text())["t"] == "pong"


def test_the_session_row_is_opened_and_closed_around_the_socket(client: TestClient, monkeypatch,
                                                                tmp_path: Path) -> None:
    """Session equity brackets the evening, even when the stub broker has no figures to give."""
    import json
    import sqlite3

    cfg = client.app.state.config
    monkeypatch.setenv(cfg.gateway.token_env, "tok")
    with client.websocket_connect(
        "/ws?token=tok", headers={"origin": cfg.gateway.public_origin}
    ) as ws:
        ws.send_text(json.dumps({"v": 1, "t": "hello", "seq": 1, "ts": 1, "ch": "session",
                                 "p": {"token": "tok"}}))
        ws.receive_text()

    conn = sqlite3.connect(cfg.paths.db)
    row = conn.execute("SELECT session_id, opened_at, closed_at FROM session_equity").fetchone()
    conn.close()
    assert row is not None
    assert row[1] > 0, "opened_at is wall-clock milliseconds, not a monotonic reading"
    assert row[2] is not None, "the session is closed when the socket goes away"


def test_the_checkin_rides_http_because_the_catalog_was_frozen_without_it(
    client: TestClient,
) -> None:
    """A journal write has no business on the socket that prioritises order acks."""
    body = client.post("/api/journal/checkin", json={"phase": "pre", "rating": 4}).json()
    assert body["ok"] is True
    assert body["skipped"] is False

    import sqlite3

    conn = sqlite3.connect(client.app.state.config.paths.db)
    row = conn.execute("SELECT pre_rating, post_rating FROM session_process").fetchone()
    conn.close()
    assert row == (4, None)


def test_a_skipped_checkin_is_recorded_as_a_skip_not_as_a_one(client: TestClient) -> None:
    """Declining to rate is different from rating yourself badly, and must stay distinguishable."""
    import sqlite3

    assert client.post("/api/journal/checkin", json={"phase": "post"}).json()["skipped"] is True
    conn = sqlite3.connect(client.app.state.config.paths.db)
    row = conn.execute("SELECT post_rating, post_at FROM session_process").fetchone()
    conn.close()
    assert row[0] is None
    assert row[1] is not None, "the skip itself is timestamped"


def test_a_rating_outside_one_to_five_is_refused(client: TestClient) -> None:
    assert client.post("/api/journal/checkin", json={"phase": "pre", "rating": 9}).status_code == 422
    assert client.post("/api/journal/checkin", json={"phase": "mid"}).status_code == 422


def test_standing_down_increments_a_counter_that_reads_as_a_win(client: TestClient) -> None:
    first = client.post("/api/journal/stand-down", json={"conditions": ["outside_window"]}).json()
    second = client.post("/api/journal/stand-down", json={"conditions": ["spread_wide"]}).json()
    assert first["stoodDown"] == 1
    assert second["stoodDown"] == 2


def test_the_desk_answers_ai_ask_offline_without_blocking_the_socket(client: TestClient,
                                                                     monkeypatch) -> None:
    """No key and no model: the desk still answers, and the socket keeps taking frames."""
    import json

    cfg = client.app.state.config
    monkeypatch.setenv(cfg.gateway.token_env, "tok")
    with client.websocket_connect(
        "/ws?token=tok", headers={"origin": cfg.gateway.public_origin}
    ) as ws:
        ws.send_text(json.dumps({"v": 1, "t": "hello", "seq": 1, "ts": 1, "ch": "session",
                                 "p": {"token": "tok"}}))
        ws.receive_text()

        ws.send_text(json.dumps({"v": 1, "t": "ai.ask", "seq": 2, "ts": 1, "ch": "ai",
                                 "cid": "01JKQ8ZC9N7Y2WX4T6VB3MHRAE",
                                 "p": {"kind": "advise", "sym": "XAUUSD"}}))
        advice = json.loads(ws.receive_text())
        assert advice["t"] == "ai.advice"
        assert "coach offline" in advice["p"]["text"]

        ws.send_text(json.dumps({"v": 1, "t": "ping", "seq": 3, "ts": 1, "ch": "session",
                                 "p": {"visible": True, "pad": True, "clutch": False}}))
        assert json.loads(ws.receive_text())["t"] == "pong"


def test_the_tv_webhook_is_off_until_it_is_switched_on(client: TestClient, monkeypatch) -> None:
    cfg = client.app.state.config
    monkeypatch.setenv(cfg.tradingview.webhook_secret_env, "shh")
    client.app.state.tv_guard.secret = "shh"

    body = {"secret": "shh", "setup": "range break", "sym": "XAUUSD", "side": "buy"}
    assert client.post("/hooks/tv", json=body).status_code == 404, "intake is disabled by default"


def test_a_tv_alert_with_the_wrong_secret_is_refused(client: TestClient) -> None:
    client.app.state.tv_guard.secret = "shh"
    body = {"secret": "wrong", "setup": "range break", "sym": "XAUUSD"}
    assert client.post("/hooks/tv", json=body).status_code == 401


def test_an_accepted_tv_alert_becomes_a_hint_and_not_an_order(client: TestClient) -> None:
    client.app.state.config.tradingview.enabled = True
    client.app.state.tv_guard.secret = "shh"

    body = {"secret": "shh", "setup": "range break", "sym": "xauusd", "side": "buy", "tf": "M5"}
    signal = client.post("/hooks/tv", json=body).json()["signal"]
    assert signal["kind"] == "tv"
    assert signal["sym"] == "XAUUSD"
    assert "lots" not in signal and "volume" not in signal
    client.app.state.config.tradingview.enabled = False


def test_an_alert_carrying_an_order_field_is_refused_outright(client: TestClient) -> None:
    client.app.state.config.tradingview.enabled = True
    client.app.state.tv_guard.secret = "shh"
    body = {"secret": "shh", "setup": "x", "sym": "XAUUSD", "lots": 0.5}
    assert client.post("/hooks/tv", json=body).status_code == 422
    client.app.state.config.tradingview.enabled = False


def seed_deck(db_path, sessions: int = 3, *, with_fires: bool = True) -> None:
    """A few evenings of journal rows, written the way the gateway would write them."""
    import sqlite3

    conn = sqlite3.connect(db_path)
    for i in range(sessions):
        sid = f"2026-09-{i + 1:02d}"
        opened = 1_788_000_000_000 + i * 86_400_000
        conn.execute(
            "INSERT OR REPLACE INTO session_equity (session_id, timezone, opened_at, closed_at, "
            "balance_open, equity_open, balance_close, equity_close) VALUES (?,?,?,?,?,?,?,?)",
            (sid, "UTC", opened, opened + 3600, 10_000.0, 10_000.0, 10_050.0, 10_050.0),
        )
        conn.execute(
            "INSERT OR REPLACE INTO session_process (session_id, pre_rating, post_rating, "
            "stood_down_count, opportunity_quality, note) VALUES (?,?,?,?,?,?)",
            (sid, 4, 3, 2, 0.2, "<b>quiet</b>"),
        )
        if not with_fires:
            continue
        cid = f"01CID{i:021d}"
        conn.execute("INSERT INTO cid_reservation (cid, intent, state, created_at, updated_at) "
                     "VALUES (?,?,?,?,?)", (cid, "open", "acked", opened, opened))
        conn.execute(
            "INSERT INTO trade_plan (cid, session_id, symbol, side, lots, volume, r_usd, "
            "r_method, r_units, created_at, setup_tag, inside_window, positions_at_fire, "
            "max_lots_at_fire, max_positions_at_fire) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (cid, sid, "XAUUSD", "buy", 0.01, 100, 2.0, "stop", 1.0, opened,
             "range_break", 1, 0, 0.10, 1),
        )
        conn.execute(
            "INSERT INTO trade_closed (cid, session_id, position_id, symbol, side, lots, volume, "
            "closed_at, net_pnl_usd, r_usd, r_multiple) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (cid, sid, 100 + i, "XAUUSD", "buy", 0.01, 100, opened + 60_000, 20.0, 2.0, 1.0),
        )
    conn.commit()
    conn.close()


def test_the_process_panel_shows_no_dollar_figure_at_all(client: TestClient) -> None:
    """The default view must not let you check the money. That is the whole design."""
    import json

    seed_deck(client.app.state.config.paths.db)
    body = client.get("/api/deck/process").json()
    assert body["panel"] == "process"
    assert body["allTime"]["sessions"] == 3

    text = json.dumps(body).lower()
    for banned in ("pnl", "equity", "balance", "usd", "return", "profit", "drawdown", "sharpe"):
        assert banned not in text, f"`{banned}` reached the process panel"


def test_the_outcome_panel_is_a_separate_request(client: TestClient) -> None:
    seed_deck(client.app.state.config.paths.db)
    body = client.get("/api/deck/outcome").json()
    assert body["panel"] == "outcome"
    assert "returnPct" in body["months"]["current"]
    assert body["bySetup"]["range_break"]["trades"] == 3


def test_a_short_history_refuses_to_print_a_sharpe(client: TestClient) -> None:
    seed_deck(client.app.state.config.paths.db, sessions=3)
    sharpe = client.get("/api/deck/outcome").json()["sharpe"]
    assert sharpe["enough"] is False
    assert sharpe["value"] is None
    assert sharpe["display"] == "not enough sessions yet"
    assert "3 of 30" in sharpe["note"]


def test_a_dead_tape_evening_with_no_trades_reads_as_disciplined(client: TestClient) -> None:
    seed_deck(client.app.state.config.paths.db, sessions=2, with_fires=False)
    latest = client.get("/api/deck/process").json()["latestSession"]
    assert "standing down was the read" in latest["verdict"]
    assert latest["declined"] == 2


def test_month_deltas_render_for_the_process_figures(client: TestClient) -> None:
    seed_deck(client.app.state.config.paths.db)
    months = client.get("/api/deck/process").json()["months"]
    assert set(months["delta"]) == {"adherence", "declinedRate", "checkinAverage",
                                    "opportunityQuality"}


def test_every_panel_carries_the_demo_and_not_advice_line(client: TestClient) -> None:
    seed_deck(client.app.state.config.paths.db)
    for path in ("/api/deck/summary", "/api/deck/process", "/api/deck/outcome"):
        assert "not advice" in client.get(path).json()["disclaimer"]


def test_the_desk_reads_process_figures_and_never_a_money_figure(client: TestClient) -> None:
    """`get_progress` is a read, and what it returns has no money field to leak."""
    import json

    seed_deck(client.app.state.config.paths.db)
    progress = client.app.state.deck.summary()
    text = json.dumps(progress).lower()
    for banned in ("pnl", "equity", "balance", "usd", "return", "profit"):
        assert banned not in text

    tools = client.app.state.desk.tools
    assert "get_progress" in tools.names()
    assert not any(verb in name for name in tools.names()
                   for verb in ("place", "close", "write", "update"))


def test_the_session_note_is_returned_as_text_for_the_client_to_escape(client: TestClient) -> None:
    """Player text. The API hands it back verbatim; the panel renders it as text, never markup."""
    seed_deck(client.app.state.config.paths.db)
    assert client.get("/api/deck/process").json()["latestSession"]["note"] == "<b>quiet</b>"


def test_a_new_player_starts_with_a_real_book(client: TestClient) -> None:
    """Seeded from the phase 4 detectors, so the overlay says something on night one."""
    body = client.get("/api/playbooks").json()
    slugs = {p["slug"] for p in body["playbooks"]}
    assert len(slugs) >= 5
    assert "m5-false-break" in slugs
    assert all(p["rules"] for p in body["playbooks"])


def test_the_editor_is_only_offered_rules_the_registry_has(client: TestClient) -> None:
    registry = client.get("/api/playbooks").json()["registry"]
    assert {r["code"] for r in registry["playbook"]}
    assert "manual" in registry
    # The enforced rules are listed so the editor can explain them, not so they can be authored.
    assert {r["code"] for r in registry["riskEnforced"]} & {"max_lots", "daily_loss"}


def test_a_playbook_naming_an_unknown_rule_is_refused(client: TestClient) -> None:
    body = {"name": "Invented", "slug": "invented",
            "rules": [{"code": "always_win", "params": {}}]}
    response = client.post("/api/playbooks", json=body)
    assert response.status_code == 422
    assert "always_win" in response.json()["detail"]


def test_a_playbook_round_trips_with_its_prose_intact(client: TestClient) -> None:
    body = {
        "name": "My break", "slug": "my-break", "detector_tag": "range_break",
        "narrative": "Wait for the <retest> & only then.",
        "rules": [{"code": "named_setup", "ord": 0},
                  {"code": "ema_distance", "params": {"max_atr": 2.0}, "ord": 1}],
    }
    saved = client.post("/api/playbooks", json=body).json()["playbook"]
    assert saved["narrative"] == "Wait for the <retest> & only then."
    assert saved["rules"][1]["params"] == {"max_atr": 2.0}
    # The rule's kind comes from the registry, not from the request.
    assert saved["rules"][0]["kind"] == "auto"


def test_retiring_a_playbook_hides_it_but_keeps_it_resolvable(client: TestClient) -> None:
    """The deck must not lose a month because the book changed."""
    before = {p["id"] for p in client.get("/api/playbooks").json()["playbooks"]}
    target = "pb-range-fade"
    assert target in before

    assert client.post(f"/api/playbooks/{target}/retire").json()["ok"] is True
    after = {p["id"] for p in client.get("/api/playbooks").json()["playbooks"]}
    assert target not in after

    with_retired = client.get("/api/playbooks?include_retired=true").json()["playbooks"]
    retired = next(p for p in with_retired if p["id"] == target)
    assert retired["retired_at"] is not None
    assert client.app.state.playbooks.get(target) is not None

    assert client.post(f"/api/playbooks/{target}/retire").status_code == 404


def test_the_arm_preview_names_the_playbook_and_counts_the_rules(client: TestClient) -> None:
    """`4/5 rules OK · ✗ …` — what the confirm overlay shows before you commit."""
    body = {"cid": "01JKQ8ZC9N7Y2WX4T6VB3MHRAE", "sym": "XAUUSD", "side": "buy", "lots": 0.01,
            "playbookId": "pb-range-break", "price": 2010.0, "ema20": 2000.0, "atr": 1.0,
            "spread": 0.3}
    preview = client.post("/api/playbooks/grade-preview", json=body).json()

    assert preview["playbookName"] == "M5 range break"
    assert "rules OK" in preview["summary"]
    assert preview["firstFailure"]["code"] in {"setup_matches", "ema_distance", "with_trend",
                                               "named_setup"}


def test_the_preview_persists_nothing(client: TestClient) -> None:
    """The socket writes the authoritative grade at FIRE; a preview is only a look."""
    cid = "01JKQ8ZC9N7Y2WX4T6VB3MHRAF"
    client.post("/api/playbooks/grade-preview",
                json={"cid": cid, "sym": "XAUUSD", "side": "buy", "lots": 0.01})
    assert client.app.state.playbooks.grade_for(cid) is None


def test_a_fire_is_graded_and_the_grade_reaches_the_socket(client: TestClient, monkeypatch) -> None:
    import json

    cfg = client.app.state.config
    monkeypatch.setenv(cfg.gateway.token_env, "tok")
    cid = "01JKQ8ZC9N7Y2WX4T6VB3MHRAG"

    with client.websocket_connect(
        "/ws?token=tok", headers={"origin": cfg.gateway.public_origin}
    ) as ws:
        ws.send_text(json.dumps({"v": 1, "t": "hello", "seq": 1, "ts": 1, "ch": "session",
                                 "p": {"token": "tok"}}))
        ws.receive_text()

        ws.send_text(json.dumps({"v": 1, "t": "playbook.select", "seq": 2, "ts": 1,
                                 "ch": "session", "p": {"playbookId": "pb-range-break"}}))
        ws.receive_text()

        ws.send_text(json.dumps({
            "v": 1, "t": "intent.open", "seq": 3, "ts": 1, "ch": "orders", "cid": cid,
            "p": {"sym": "XAUUSD", "side": "buy", "type": "market", "lots": 0.01,
                  "clutch": True, "armedAt": 1},
        }))
        frames = [json.loads(ws.receive_text()) for _ in range(2)]

    grade = next(f for f in frames if f["t"] == "grade")
    assert grade["p"]["playbookId"] == "pb-range-break"
    assert grade["p"]["results"]
    # A grade row exists even though the gate refused the fire — declines are gradeable.
    assert client.app.state.playbooks.grade_for(cid) is not None
    assert any(f["t"] == "order.reject" for f in frames)


def test_the_checklist_answers_only_the_manual_rules(client: TestClient) -> None:
    """The auto verdicts stay as they were at FIRE; re-running them now would use a moved chart."""
    from grading.grade import grade_fire
    from grading.routes import to_domain
    from method.rules import RuleContext

    cid = "01JKQ8ZC9N7Y2WX4T6VB3MHRAH"
    book = client.app.state.playbooks.get("pb-range-break")
    ctx = RuleContext(
        now_ms=1, symbol="XAUUSD", lots=0.01, clutch=True, session_open=True, session_label="",
        allowed_symbols=frozenset({"XAUUSD"}), positions_open=0, max_positions=1, max_lots=0.1,
        day_loss_usd=0.0, max_day_loss_usd=200.0, seconds_since_last_order=10.0,
        min_seconds_between_orders=2.0, heartbeat_age_s=0.0, heartbeat_dead_s=3.0,
        setup_tag="range_break", setup_side="buy", side="buy",
        price=2000.5, ema20=2000.0, atr=1.0, spread=0.3, spread_cap=0.8,
    )
    at_fire = grade_fire(cid=cid, playbook=book, ctx=ctx, stage="fire")
    client.app.state.playbooks.save_grade(at_fire.as_db_row())
    assert to_domain  # the loader the route uses

    answered = client.post("/api/playbooks/checklist",
                           json={"cid": cid, "answers": {"no_chase": True}}).json()
    assert answered["ok"] is True
    codes = {r["code"]: r for r in answered["grade"]["results"]}
    assert codes["no_chase"]["ok"] is True
    assert codes["ema_distance"]["actual"] == "0.50 ATR", "the auto verdict survived unchanged"


def test_skipping_the_checklist_shrinks_the_denominator(client: TestClient) -> None:
    from grading.grade import grade_fire
    from method.rules import RuleContext

    cid = "01JKQ8ZC9N7Y2WX4T6VB3MHRAI"
    book = client.app.state.playbooks.get("pb-range-break")
    ctx = RuleContext(
        now_ms=1, symbol="XAUUSD", lots=0.01, clutch=True, session_open=True, session_label="",
        allowed_symbols=frozenset({"XAUUSD"}), positions_open=0, max_positions=1, max_lots=0.1,
        day_loss_usd=0.0, max_day_loss_usd=200.0, seconds_since_last_order=10.0,
        min_seconds_between_orders=2.0, heartbeat_age_s=0.0, heartbeat_dead_s=3.0,
        setup_tag="range_break", setup_side="buy", side="buy",
        price=2000.5, ema20=2000.0, atr=1.0, spread=0.3, spread_cap=0.8,
    )
    stored = grade_fire(cid=cid, playbook=book, ctx=ctx, stage="fire")
    client.app.state.playbooks.save_grade(stored.as_db_row())

    skipped = client.post("/api/playbooks/checklist", json={"cid": cid, "answers": {}}).json()
    assert skipped["grade"]["required_total"] == stored.required_total
    assert skipped["grade"]["clean"] is True, "a skip costs nothing"


def test_a_checklist_for_an_unknown_fire_is_a_404(client: TestClient) -> None:
    assert client.post("/api/playbooks/checklist",
                       json={"cid": "01NOSUCHFIRE", "answers": {}}).status_code == 404
