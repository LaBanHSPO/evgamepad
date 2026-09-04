"""Arcade catalog, asset serving, and the token-free HUD snapshot."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

from arcade.catalog import ASSET_FILES, asset_path, get_skin, list_skins
from arcade.hud import _positions, duration_s, format_clock, remaining_s, snapshot
from broker.ctrader import Quote
from config import load_config
from main import create_app
from risk.session import SessionWindow
from test_config import DEFAULT, VALID_ENV


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    cfg = load_config(DEFAULT, env=dict(VALID_ENV))
    cfg.paths.data_dir = str(tmp_path)
    with TestClient(create_app(cfg)) as c:
        yield c


def test_shipped_artwork_files_are_on_disk() -> None:
    missing = [name for name, path in ASSET_FILES.items() if not path.is_file()]
    assert missing == []


def test_skins_catalog_marks_matrix_and_city_ready() -> None:
    skins = {row["id"]: row for row in list_skins()}
    assert set(skins) == {"matrix", "city"}
    assert skins["matrix"]["screen"] == "artmatrix"
    assert skins["city"]["screen"] == "artcontra"
    assert skins["matrix"]["ready"] is True
    assert skins["city"]["ready"] is True
    assert skins["matrix"]["background"] == "/api/arcade/assets/matrix"
    assert skins["matrix"]["fallback"] == "/uploads/matrix-like-bg-fullhd.png"
    assert skins["city"]["sprites"]["heroFire"] == "/api/arcade/assets/hero-fire"
    assert skins["city"]["spriteFallbacks"]["heroFire"] == "/sprites/hero-fire.png"
    assert get_skin("missing") is None
    assert asset_path("nope") is None


def test_skins_route_lists_both_cabinets(client: TestClient) -> None:
    body = client.get("/api/arcade/skins").json()
    ids = [row["id"] for row in body["skins"]]
    assert ids == ["matrix", "city"]
    one = client.get("/api/arcade/skins/city")
    assert one.status_code == 200
    assert one.json()["label"] == "Fire on city art"
    assert client.get("/api/arcade/skins/neon").status_code == 404


def test_assets_are_pngs_with_a_cache_header(client: TestClient) -> None:
    response = client.get("/api/arcade/assets/matrix")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/png")
    assert "max-age=86400" in response.headers["cache-control"]
    assert client.get("/api/arcade/assets/hero-fire").status_code == 200
    assert client.get("/api/arcade/assets/not-a-skin").status_code == 404


def test_clock_formats_hours_only_when_needed() -> None:
    assert format_clock(0) == "0:00"
    assert format_clock(72) == "1:12"
    assert format_clock(4324) == "1:12:04"


def test_remaining_matches_the_artboard_clock() -> None:
    """22:17:56 in the session zone is 1:12:04 before a 23:30 close — the mock's number."""
    window = SessionWindow.from_config("Asia/Ho_Chi_Minh", ["fri"], "18:00", "23:30")
    now = datetime(2026, 9, 4, 22, 17, 56, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))
    remaining = remaining_s(window, int(now.timestamp() * 1000))
    assert remaining == 4324
    assert format_clock(remaining) == "1:12:04"
    assert duration_s(window) == 5 * 3600 + 30 * 60


def test_hud_is_always_200_and_never_invents_a_price(client: TestClient) -> None:
    response = client.get("/api/arcade/hud")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    body = response.json()
    assert body["mode"] == "demo"
    assert body["broker"]["connected"] is False
    assert body["positions"] == []
    assert body["pnl"] == {"openPnl": None, "dayPnl": None}
    gold = next(row for row in body["symbols"] if row["name"] == "XAUUSD")
    assert gold["bid"] is None
    assert gold["ask"] is None
    assert gold["mid"] is None
    assert gold["stop"] == 2.0
    assert body["sentinel"] is None
    assert body["session"]["clock"] == format_clock(body["session"]["remainingS"])
    assert body["risk"]["maxPositions"] == 1
    assert body["risk"]["rUsd"] == 20


class _FakeBroker:
    def __init__(self, *, connected: bool, quotes: dict[str, Any] | None = None,
                 positions: list[dict[str, Any]] | None = None) -> None:
        self.quotes = quotes or {}
        self._connected = connected
        self._positions = positions or []

    def snapshot(self) -> dict[str, Any]:
        return {"connected": self._connected, "reason": None if self._connected else "not_wired"}

    async def positions(self) -> list[dict[str, Any]]:
        return self._positions


class _HungBroker(_FakeBroker):
    async def positions(self) -> list[dict[str, Any]]:
        import asyncio
        await asyncio.sleep(5)
        return [{"symbol": "XAUUSD", "side": "buy"}]


async def test_snapshot_scales_cached_quotes_and_skips_a_dead_broker(tmp_path: Path) -> None:
    cfg = load_config(DEFAULT, env=dict(VALID_ENV))
    cfg.paths.data_dir = str(tmp_path)
    quote = Quote(symbol="XAUUSD", bid=246_138_000, ask=246_162_000, ts_ms=1)
    live = await snapshot(
        config=cfg,
        broker=_FakeBroker(connected=True, quotes={"XAUUSD": quote}, positions=[
            {"positionId": 9, "symbol": "XAUUSD", "side": "buy", "lots": 0.2,
             "entry": 2458.10, "sl": 2455.60, "tp": 2473.00},
        ]),
        sentinel=None,
        journal=None,
        now_ms=1,
    )
    gold = next(row for row in live["symbols"] if row["name"] == "XAUUSD")
    assert gold["bid"] == pytest.approx(2461.38)
    assert gold["ask"] == pytest.approx(2461.62)
    assert gold["spread"] == pytest.approx(0.24)
    assert live["positions"][0]["lots"] == pytest.approx(0.2)
    assert live["risk"]["positions"] == 1

    dead = await snapshot(
        config=cfg,
        broker=_FakeBroker(connected=False, quotes={"XAUUSD": quote}),
        sentinel=None,
        journal=None,
        now_ms=1,
    )
    # Cached quotes still paint; a disconnected link must not hang on positions().
    gold = next(row for row in dead["symbols"] if row["name"] == "XAUUSD")
    assert gold["bid"] == pytest.approx(2461.38)
    assert dead["positions"] == []


async def test_positions_time_out_instead_of_hanging_the_hud() -> None:
    rows = await _positions(_HungBroker(connected=True), timeout_s=0.05)
    assert rows == []
