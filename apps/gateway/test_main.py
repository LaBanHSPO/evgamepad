"""Gateway boot: healthz, and the generated web types staying in step with the catalog."""

from __future__ import annotations

from pathlib import Path

import pytest
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
