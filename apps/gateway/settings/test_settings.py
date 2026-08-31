"""Settings, reports, and the boundary that keeps a preference from becoming a safety decision.

The test that matters most asserts a negative: there is no editable key that could put the gateway
into live mode, move its bind address, name a credential, or turn off one of the three boot-fails.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from db.migrate import migrate
from reports.builder import PROCESS_ONLY_KEYS, ReportBuilder, resolve_window
from settings.repository import SettingsRepository
from settings.schema import (
    FORBIDDEN_PHRASES,
    FORBIDDEN_SEGMENTS,
    Setting,
    SettingsError,
    a_bool,
    build,
    segments,
)

T0 = 1_788_000_000_000
SYMBOLS = {"XAUUSD", "EURUSD", "GBPUSD", "USDJPY"}


@pytest.fixture()
def repo(tmp_path: Path) -> SettingsRepository:
    migrate(tmp_path / "journal.db")
    return SettingsRepository(tmp_path / "journal.db", server_symbols=lambda: SYMBOLS)


# -- the boundary ------------------------------------------------------------------------


def test_no_editable_setting_can_reach_a_safety_property(repo: SettingsRepository) -> None:
    """Demo mode, the bind address, the credentials and the boot-fails are not database rows."""
    for key in repo.defined:
        assert not (segments(key) & FORBIDDEN_SEGMENTS), key
        for phrase in FORBIDDEN_PHRASES:
            assert phrase not in key


def test_defining_a_dangerous_setting_fails_at_construction() -> None:
    """A second, independent net: the allowlist is edited by people."""
    for key in ("broker.mode", "gateway.bind", "broker.client_secret", "copilot.on_hot_path",
                "tilt.gate_close", "tradingview.auto_trade", "account.id", "paths.data_dir",
                "copilot.tools"):
        with pytest.raises(SettingsError, match="boot-fails|config"):
            Setting(key, "should never exist", False, a_bool)


def test_a_legitimate_key_that_merely_contains_a_forbidden_word_is_fine() -> None:
    """`report` contains `port`. A guard that rejects the report defaults is one nobody keeps."""
    assert Setting("report.default_period", "fine", "month", a_bool).key == "report.default_period"
    assert "report.default_period" in build(server_symbols=lambda: SYMBOLS)


def test_an_unknown_key_is_refused_rather_than_ignored(repo: SettingsRepository) -> None:
    """A silently dropped write is a setting the player thinks they changed."""
    with pytest.raises(SettingsError, match="not an editable setting"):
        repo.put({"broker.mode": "live"}, T0)
    with pytest.raises(SettingsError, match="not an editable setting"):
        repo.put({"pad.rumble": False, "gateway.bind": "0.0.0.0"}, T0)

    # And the valid half of that batch was not applied either.
    assert repo.values()["pad.rumble"] is True


def test_the_account_is_a_chip_with_nothing_that_could_authenticate(repo: SettingsRepository) -> None:
    payload = repo.payload(identity={"broker": "IC Markets", "platform": "cTrader",
                                     "mode": "demo", "readOnly": True})
    flat = str(payload).lower()
    for secret in ("client_secret", "access_token", "refresh_token", "password", "bearer"):
        assert secret not in flat
    assert payload["account"]["readOnly"] is True


def test_the_symbol_list_can_be_narrowed_but_never_widened(repo: SettingsRepository) -> None:
    """The UI chooses among what the risk config already approved."""
    repo.put({"symbols.enabled": ["XAUUSD"]}, T0)
    assert repo.values()["symbols.enabled"] == ["XAUUSD"]

    with pytest.raises(SettingsError, match="not available on this server"):
        repo.put({"symbols.enabled": ["XAUUSD", "BTCUSD"]}, T0)


def test_the_editors_that_already_exist_are_linked_not_duplicated(repo: SettingsRepository) -> None:
    where = {row["where"] for row in repo.payload(identity={})["elsewhere"]}
    assert where == {"/api/playbooks", "/api/journal/system"}


# -- validation ----------------------------------------------------------------------------


def test_values_are_range_checked(repo: SettingsRepository) -> None:
    with pytest.raises(SettingsError, match="between"):
        repo.put({"pad.deadzone": 0.9}, T0)
    with pytest.raises(SettingsError, match="between"):
        repo.put({"journal.retention_days": 5}, T0)
    with pytest.raises(SettingsError, match="expected"):
        repo.put({"pad.rumble": "yes"}, T0)


def test_the_clutch_hysteresis_cannot_be_inverted(repo: SettingsRepository) -> None:
    """Inverted, one stick position reads as both engaged and released and the FSM chatters."""
    with pytest.raises(SettingsError, match="below"):
        repo.put({"pad.clutch_engage": 0.4, "pad.clutch_release": 0.6}, T0)

    # Judged against the merged result, so sending one half still gets checked.
    repo.put({"pad.clutch_engage": 0.8, "pad.clutch_release": 0.5}, T0)
    with pytest.raises(SettingsError, match="below"):
        repo.put({"pad.clutch_release": 0.95}, T0)


def test_a_timezone_the_machine_cannot_resolve_is_refused(repo: SettingsRepository) -> None:
    repo.put({"evening.timezone": "Europe/London"}, T0)
    with pytest.raises(SettingsError, match="not a timezone"):
        repo.put({"evening.timezone": "Middle/Earth"}, T0)


def test_times_and_weekdays_are_normalised(repo: SettingsRepository) -> None:
    repo.put({"evening.start": "9:05", "evening.days": [3, 1, 1, 0]}, T0)
    values = repo.values()
    assert values["evening.start"] == "09:05"
    assert values["evening.days"] == [0, 1, 3]

    with pytest.raises(SettingsError, match="valid time"):
        repo.put({"evening.start": "25:00"}, T0)


def test_a_boolean_setting_will_not_take_a_number(repo: SettingsRepository) -> None:
    with pytest.raises(SettingsError):
        repo.put({"pad.rumble": 1}, T0)


# -- storage -------------------------------------------------------------------------------


def test_unset_settings_read_as_their_shipped_defaults(repo: SettingsRepository) -> None:
    values = repo.values()
    assert values["pad.clutch_engage"] == 0.80
    assert values["report.include_outcome"] is False
    assert set(values) == set(repo.defined)


def test_a_write_survives_a_reopen(repo: SettingsRepository) -> None:
    repo.put({"coach.speak": True}, T0)
    again = SettingsRepository(repo.db_path, server_symbols=lambda: SYMBOLS)
    assert again.values()["coach.speak"] is True


def test_reset_returns_a_setting_to_its_default(repo: SettingsRepository) -> None:
    repo.put({"pad.deadzone": 0.4}, T0)
    assert repo.reset(["pad.deadzone"], T0)["pad.deadzone"] == 0.15

    with pytest.raises(SettingsError, match="not an editable setting"):
        repo.reset(["broker.mode"], T0)


def test_a_stored_key_the_schema_forgot_is_ignored(repo: SettingsRepository) -> None:
    """A row left behind by an older build must not resurrect a removed setting."""
    import sqlite3

    conn = sqlite3.connect(repo.db_path)
    conn.execute("INSERT INTO user_setting (key, value, updated_at) VALUES ('legacy.thing','1',1)")
    conn.commit()
    conn.close()

    assert "legacy.thing" not in repo.values()


# -- reports --------------------------------------------------------------------------------


class FakeDeck:
    def process(self) -> dict:
        return {"panel": "process", "adherence": 0.9}

    def outcome(self) -> dict:
        return {"panel": "outcome", "returnPct": 0.031, "netPnlUsd": 412.0}

    def playbooks(self, *, outcome: bool = False) -> dict:
        row = {"playbookId": "pb-range", "n": 3, "adherence": 0.9}
        if outcome:
            row = {**row, "expectancyR": 0.4}
        return {"playbooks": [row]}

    def tilt_retro(self, session_id: str) -> dict:
        return {"samples": [], "bands": {}, "topDrivers": [], "adherence": None}


class FakeJournal:
    def overview(self, *, from_ms=None, to_ms=None) -> dict:
        return {"sessions": 4, "consistency": {"value": 82.0, "n": 6},
                "processScoreMean": 88.0,
                "groups": {"groups": {}, "unclassified": 0, "note": ""},
                "mistakes": {"mistakes": [], "focus": None, "note": ""}}

    def days(self, *, from_ms=None, to_ms=None) -> dict:
        return {"days": [{"sessionId": "2026-08-31", "openedAt": T0, "score": 92.0, "trades": 2,
                          "declined": 1, "mistakes": 0, "hasAnalysis": True,
                          "checkinPre": 4, "checkinPost": 4}]}

    def day(self, session_id: str) -> dict:
        return {"readiness": [], "analysis": {"thesis": "range"}, "trades": [],
                "mistakes": [], "score": {"total": 92.0}, "checkin": {"declined": 1}}


class FakeScore:
    def session_payload(self, session_id: str) -> dict:
        return {"total": 92, "axes": []}


def builder(tmp_path: Path) -> ReportBuilder:
    return ReportBuilder(tmp_path / "journal.db", deck=FakeDeck(), score=FakeScore(),
                         journal=FakeJournal())


def test_a_report_without_the_appendix_never_held_a_money_figure(tmp_path: Path) -> None:
    """Assembled only on request, so a report saved without it never contained the numbers."""
    report = builder(tmp_path).build(period="month", now_ms=T0)

    assert set(report) == set(PROCESS_ONLY_KEYS)
    assert "outcome" not in report
    flat = str(report).lower()
    for money in ("returnpct", "netpnlusd", "expectancyr", "profit"):
        assert money not in flat


def test_the_outcome_appendix_arrives_only_when_asked_for(tmp_path: Path) -> None:
    report = builder(tmp_path).build(period="month", include_outcome=True, now_ms=T0)
    assert "outcome" in report
    assert report["outcome"]["summary"]["returnPct"] == 0.031
    # Still after the process pages: the cover has no money on it in either configuration.
    assert "netPnlUsd" not in str(report["cover"])


def test_the_cover_is_process_only_in_every_configuration(tmp_path: Path) -> None:
    for include in (False, True):
        cover = builder(tmp_path).build(period="month", include_outcome=include,
                                        now_ms=T0)["cover"]
        assert set(cover) >= {"sessions", "trades", "declined", "consistency"}
        for money in ("pnl", "usd", "return", "equity"):
            assert money not in str(cover).lower()


def test_a_session_report_is_one_evening_in_full(tmp_path: Path) -> None:
    report = builder(tmp_path).build(period="session", session_id="2026-08-31", now_ms=T0)
    assert report["kind"] == "session"
    assert report["analysis"]["thesis"] == "range"
    assert "tilt" in report


def test_the_period_windows_are_derived_from_now(tmp_path: Path) -> None:
    week = resolve_window("week", from_ms=None, to_ms=None, now_ms=T0)
    month = resolve_window("month", from_ms=None, to_ms=None, now_ms=T0)
    assert T0 - week[0] == 7 * 86_400_000
    assert T0 - month[0] == 31 * 86_400_000

    # `custom` passes the caller's own bounds through untouched.
    assert resolve_window("custom", from_ms=1, to_ms=2, now_ms=T0) == (1, 2)


def test_the_report_recomputes_nothing(tmp_path: Path) -> None:
    """Every figure comes from the phase that owns it; a second implementation would drift."""
    source = Path(__file__).parent.parent / "reports" / "builder.py"
    body = source.read_text(encoding="utf-8")
    body = body[body.index('"""', body.index('"""') + 3):]
    for arithmetic in ("mean(", "median(", "statistics.", "/ len("):
        assert arithmetic not in body


# -- the HTTP surface -------------------------------------------------------------------------


def http_client(tmp_path: Path):
    from fastapi.testclient import TestClient

    from config import load_config
    from main import create_app
    from test_config import DEFAULT, VALID_ENV

    cfg = load_config(DEFAULT, env=dict(VALID_ENV))
    cfg.paths.data_dir = str(tmp_path)
    return TestClient(create_app(cfg))


def test_the_settings_route_refuses_a_safety_key(tmp_path: Path) -> None:
    with http_client(tmp_path) as client:
        assert client.put("/api/settings", json={"broker.mode": "live"}).status_code == 422
        assert client.put("/api/settings", json={"gateway.bind": "0.0.0.0"}).status_code == 422
        assert client.put("/api/settings", json={"pad.rumble": False}).status_code == 200

        body = client.get("/api/settings").json()
        assert body["settings"]["pad.rumble"] is False
        assert body["account"]["readOnly"] is True


def test_the_report_route_defaults_to_process_only(tmp_path: Path) -> None:
    with http_client(tmp_path) as client:
        plain = client.get("/api/reports?period=month").json()
        assert "outcome" not in plain

        with_money = client.get("/api/reports?period=month&include_outcome=true").json()
        assert "outcome" in with_money

        assert client.get("/api/reports?period=decade").status_code == 422


def test_the_exports_stream_and_carry_no_secret(tmp_path: Path) -> None:
    with http_client(tmp_path) as client:
        csv_body = client.get("/api/export/trades.csv")
        assert csv_body.status_code == 200
        assert csv_body.headers["content-type"].startswith("text/csv")
        assert "cid" in csv_body.text

        journal = client.get("/api/export/journal.json")
        assert journal.json()["format"] == "evgamepad-journal"
        for secret in ("client_secret", "refresh_token", str(tmp_path)):
            assert secret not in journal.text


def test_backup_restore_and_delete_ride_http_with_their_gates(tmp_path: Path) -> None:
    with http_client(tmp_path) as client:
        made = client.post("/api/data/backup")
        assert made.status_code == 200
        name = made.json()["name"]
        assert name in [row["name"] for row in client.get("/api/data/backups").json()["backups"]]

        inspected = client.post("/api/data/restore/inspect", json={"name": name}).json()
        assert inspected["files"] >= 1

        # A path outside the backups directory is not a backup.
        assert client.post("/api/data/restore/inspect",
                           json={"name": "../../etc/passwd"}).status_code == 404

        # Restore refuses an unlocked session before touching anything.
        refused = client.post("/api/data/restore", json={"name": name, "locked": False})
        assert refused.status_code == 409
        assert "lock" in refused.json()["detail"]

        assert client.post("/api/data/restore", json={"name": name, "locked": True}).status_code == 200

        # Delete needs all four conditions.
        wrong = client.request("DELETE", "/api/data/all",
                               json={"phrase": "delete everything", "heldMs": 3000,
                                     "locked": True, "positionsOpen": 0})
        assert wrong.status_code == 409

        done = client.request("DELETE", "/api/data/all",
                              json={"phrase": "DELETE EVERYTHING", "heldMs": 3000,
                                    "locked": True, "positionsOpen": 0})
        assert done.status_code == 200 and done.json()["ok"] is True
