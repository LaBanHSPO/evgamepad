"""Boot-fails.

Each test here is a shape the gateway must refuse to run in. They are asserted against the real
`config/default.yaml`, so a change that quietly loosens the shipped config fails the suite too.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from config import ConfigError, load_config

ROOT = Path(__file__).resolve().parents[2]
DEFAULT = ROOT / "config" / "default.yaml"

VALID_ENV = {
    "CT_CLIENT_ID": "id",
    "CT_CLIENT_SECRET": "secret",
    "CT_ACCESS_TOKEN": "access",
    "CT_REFRESH_TOKEN": "refresh",
    "CT_ACCOUNT_ID": "123",
    "EV_WS_TOKEN": "ws",
}


def write_config(tmp_path: Path, mutate: Any = None) -> Path:
    raw = yaml.safe_load(DEFAULT.read_text(encoding="utf-8"))
    if mutate is not None:
        mutate(raw)
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    return path


def test_shipped_default_config_boots() -> None:
    cfg = load_config(DEFAULT, env=dict(VALID_ENV))
    assert cfg.mode == "demo"
    assert cfg.broker.adapter == "ctrader"
    assert cfg.paths.db.as_posix() == "/data/journal.db"


@pytest.mark.parametrize(
    ("name", "mutate", "match"),
    [
        ("live mode", lambda c: c.__setitem__("mode", "live"), "mode"),
        ("live host", lambda c: c["broker"].__setitem__("host", "live.ctraderapi.com"), "live"),
        ("local timezone", lambda c: c.__setitem__("timezone", "local"), "timezone"),
        ("unknown timezone", lambda c: c.__setitem__("timezone", "Mars/Olympus"), "IANA"),
        ("copilot on hot path", lambda c: c["copilot"].__setitem__("on_hot_path", True), "on_hot_path"),
        ("tv auto trade", lambda c: c["tradingview"].__setitem__("auto_trade", True), "auto_trade"),
        ("cloud stt", lambda c: c["voice"]["stt"].__setitem__("mode", "cloud"), "mode"),
        ("voice on a trading button", lambda c: c["voice"].__setitem__("bindings", ["RT"]), "bindings"),
        ("tilt gates a close", lambda c: c["tilt"].__setitem__("gate_close", True), "gate_close"),
        ("frame cap drift", lambda c: c["gateway"].__setitem__("max_frame_bytes", 32768), "max_frame_bytes"),
        ("wrong adapter", lambda c: c["broker"].__setitem__("adapter", "mt5"), "adapter"),
    ],
)
def test_unsafe_shapes_are_refused(tmp_path: Path, name: str, mutate: Any, match: str) -> None:
    path = write_config(tmp_path, mutate)
    with pytest.raises(ConfigError, match=match):
        load_config(path, env=dict(VALID_ENV))


def test_more_than_five_search_domains_is_a_boot_fail(tmp_path: Path) -> None:
    """The provider caps its search filter at five; a sixth would fail mid-session, not at boot."""
    def mutate(c: dict) -> None:
        c["copilot"]["allowed_domains"] = [f"d{i}.example" for i in range(6)]

    path = write_config(tmp_path, mutate)
    with pytest.raises(ConfigError, match="caps the search"):
        load_config(path, env=dict(VALID_ENV))


def test_the_calendar_source_has_exactly_two_values(tmp_path: Path) -> None:
    path = write_config(tmp_path, lambda c: c["signals"]["calendar"].__setitem__("source", "scrape"))
    with pytest.raises(ConfigError, match="source"):
        load_config(path, env=dict(VALID_ENV))


def test_score_weights_must_sum_to_one(tmp_path: Path) -> None:
    """0.95 is the failure the plan names: a silently mis-weighted score."""
    def mutate(c: dict) -> None:
        c["score"]["weights"]["review"] = 0.05

    path = write_config(tmp_path, mutate)
    with pytest.raises(ConfigError, match="0.95"):
        load_config(path, env=dict(VALID_ENV))


def test_public_bind_is_refused_outside_dev_and_container(tmp_path: Path) -> None:
    path = write_config(tmp_path, lambda c: c["gateway"].__setitem__("listen", "0.0.0.0:8444"))
    with pytest.raises(ConfigError, match="loopback"):
        load_config(path, env=dict(VALID_ENV))

    for flag in ("EV_DEV", "EV_CONTAINER_BIND"):
        cfg = load_config(path, env={**VALID_ENV, flag: "1"})
        assert cfg.gateway.host == "0.0.0.0"


def test_listen_override_still_faces_the_bind_check(tmp_path: Path) -> None:
    """The deploy override cannot be used to sneak a public bind past the guard."""
    path = write_config(tmp_path)
    with pytest.raises(ConfigError, match="loopback"):
        load_config(path, env={**VALID_ENV, "EV_LISTEN": "0.0.0.0:8444"})

    cfg = load_config(path, env={**VALID_ENV, "EV_LISTEN": "0.0.0.0:8444", "EV_CONTAINER_BIND": "1"})
    assert cfg.gateway.port == 8444


def test_missing_credentials_boot_fail_with_a_pointer(tmp_path: Path) -> None:
    """No half-start on an empty CT_REFRESH_TOKEN: exit and name the README section."""
    env = dict(VALID_ENV)
    env["CT_REFRESH_TOKEN"] = ""
    with pytest.raises(ConfigError, match="CT_REFRESH_TOKEN.*README"):
        load_config(DEFAULT, env=env)


def test_tradingview_needs_its_secret_when_enabled(tmp_path: Path) -> None:
    path = write_config(tmp_path, lambda c: c["tradingview"].__setitem__("enabled", True))
    with pytest.raises(ConfigError, match="TV_WEBHOOK_SECRET"):
        load_config(path, env=dict(VALID_ENV))


def test_default_stop_must_cover_every_symbol(tmp_path: Path) -> None:
    """R has one definition; a symbol without a default stop would leave it undefined."""
    path = write_config(tmp_path, lambda c: c["risk"]["default_stop"].pop("XAUUSD"))
    with pytest.raises(ConfigError, match="XAUUSD"):
        load_config(path, env=dict(VALID_ENV))


def test_missing_config_file_is_a_boot_fail(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="config not found"):
        load_config(tmp_path / "nope.yaml", env=dict(VALID_ENV))


def test_data_dir_override_moves_the_whole_volume(tmp_path: Path) -> None:
    """One override moves journal.db, voice, models, and the token dir together."""
    cfg = load_config(DEFAULT, env={**VALID_ENV, "EV_DATA_DIR": str(tmp_path)})
    assert cfg.paths.db == tmp_path / "journal.db"
    assert cfg.paths.voice_dir == tmp_path / "voice"
    assert cfg.paths.secure_dir == tmp_path / "secure"
