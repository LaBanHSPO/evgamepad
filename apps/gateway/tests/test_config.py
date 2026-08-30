"""Every safety invariant, proved to exit non-zero."""

from __future__ import annotations

import copy

import pytest
import yaml

from apps.gateway.config import BootFail, check_secrets, load

BASE = "config/default.yaml"


def write(tmp_path, mutate=None):
    data = yaml.safe_load(open(BASE))
    data = copy.deepcopy(data)
    if mutate:
        mutate(data)
    p = tmp_path / "cfg.yaml"
    p.write_text(yaml.safe_dump(data))
    return p


def test_shipped_config_boots(tmp_path):
    cfg = load(write(tmp_path))
    assert cfg.mode == "demo"
    assert cfg.timezone == "Asia/Ho_Chi_Minh"
    assert cfg.symbol_names == ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY"]
    assert cfg.symbol("XAUUSD").max_lots == 0.10


@pytest.mark.parametrize(
    "invariant,mutate",
    [
        ("live_mode", lambda d: d.update(mode="live")),
        ("live_host", lambda d: d["broker"].update(host="live.ctraderapi.com")),
        ("timezone", lambda d: d.update(timezone="local")),
        ("timezone", lambda d: d.update(timezone="Mars/Olympus")),
        ("public_bind", lambda d: d["gateway"].update(listen="0.0.0.0:8444")),
        ("copilot_hot_path", lambda d: d["copilot"].update(on_hot_path=True)),
        ("tv_auto_trade", lambda d: d["tradingview"].update(auto_trade=True)),
        ("stt_mode", lambda d: d["voice"]["stt"].update(mode="cloud")),
        ("voice_binding", lambda d: d["voice"].update(bindings=["RT"])),
        ("voice_binding", lambda d: d["voice"].update(bindings=["LT+RT"])),
        ("tilt_gate_close", lambda d: d["tilt"].update(gate_close=True)),
        ("symbols", lambda d: d.update(symbols=[])),
    ],
)
def test_boot_fails(tmp_path, invariant, mutate):
    with pytest.raises(BootFail) as exc:
        load(write(tmp_path, mutate))
    assert exc.value.invariant == invariant
    assert exc.value.code != 0


def test_score_weights_must_sum_to_one(tmp_path):
    def mutate(d):
        d["score"]["weights"]["review"] = 0.05  # sums to 0.95

    with pytest.raises(BootFail) as exc:
        load(write(tmp_path, mutate))
    assert exc.value.invariant == "score_weights"
    assert "0.95" in exc.value.detail


def test_dev_may_bind_non_loopback(tmp_path):
    """The loopback rule exists because TLS on :443 fronts the gateway. In dev
    there is no TLS to front it, so the escape hatch is explicit rather than
    someone quietly deleting the check."""
    def mutate(d):
        d["dev"] = True
        d["gateway"]["listen"] = "0.0.0.0:8444"

    assert load(write(tmp_path, mutate)).dev is True


def test_unknown_key_is_refused(tmp_path):
    with pytest.raises(BootFail) as exc:
        load(write(tmp_path, lambda d: d.update(paper_engine=True)))
    assert exc.value.invariant == "config_invalid"


def test_missing_secrets_point_at_the_manual_flow(tmp_path):
    cfg = load(write(tmp_path))
    with pytest.raises(BootFail) as exc:
        check_secrets(cfg, env={})
    assert exc.value.invariant == "missing_secrets"
    assert "CT_REFRESH_TOKEN" in exc.value.detail
    assert "README" in exc.value.detail


def test_secrets_pass_when_present(tmp_path):
    cfg = load(write(tmp_path))
    env = {
        "CT_CLIENT_ID": "a", "CT_CLIENT_SECRET": "b", "CT_ACCESS_TOKEN": "c",
        "CT_REFRESH_TOKEN": "d", "CT_ACCOUNT_ID": "1", "EV_WS_TOKEN": "e",
        "XAI_API_KEY": "f",
    }
    check_secrets(cfg, env=env)


def test_yaml_bare_off_is_read_as_off_not_false(tmp_path):
    p = tmp_path / "cfg.yaml"
    text = open(BASE).read().replace('tts: "off"', "tts: off")
    p.write_text(text)
    assert load(p).voice.tts == "off"
