"""The desk cannot trade, cannot write, and cannot stop the evening by being unreachable.

The first test here is the important one: it fails the suite if a trading or writing verb ever
appears in the copilot's tool surface. That is the structural guarantee, and it is checked rather
than reviewed.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

import pytest

from copilot.client import MAX_ALLOWED_DOMAINS, SpaceXaiClient
from copilot.loops import DeskLoops
from copilot.prompt import CITATION, system_prompt
from copilot.tools import FORBIDDEN_VERBS, ToolRegistry, build_registry
from signals.tv_webhook import TvAlert, WebhookGuard, to_signal


def registry() -> ToolRegistry:
    return build_registry(
        get_sentinel=lambda: {"spread": 0.3, "state": "tight"},
        get_positions=lambda: [],
        get_account=lambda: {"balance": 10_000.0},
        get_calendar=lambda: [],
        get_setup=lambda: {"kind": "range"},
        get_progress=lambda: {"stoodDown": 2},
    )


# -- the structural guarantee ---------------------------------------------------------


def test_no_copilot_tool_names_a_trading_or_writing_verb() -> None:
    """The test the plan asks for: it fails if an action ever reaches this surface."""
    names = registry().names()
    assert names, "the desk has tools; it just cannot act with them"
    for name in names:
        for verb in FORBIDDEN_VERBS:
            assert verb not in name.lower(), f"tool `{name}` contains the action verb `{verb}`"


def test_registering_an_action_is_refused_at_the_registry() -> None:
    tools = ToolRegistry()
    for name in ("place_order", "close_position", "write_journal", "update_plan", "send_intent"):
        with pytest.raises(ValueError, match="read-only"):
            tools.register(name, "should never exist", lambda: None)


def test_calling_something_outside_the_allowlist_is_refused() -> None:
    with pytest.raises(PermissionError, match="read-only"):
        registry().call("place")


def test_the_schema_handed_to_the_model_contains_only_reads() -> None:
    """Nothing outside this list exists to the model at all."""
    schema = registry().schema()
    assert {entry["name"] for entry in schema} == set(registry().names())
    assert all(entry["name"].startswith("get_") for entry in schema)


def test_the_journal_tool_is_a_read() -> None:
    """Phase 6 and 11 read progress through the desk; that stays a read."""
    assert registry().call("get_progress") == {"stoodDown": 2}


# -- offline behaviour ----------------------------------------------------------------


def test_no_api_key_is_a_state_not_an_error() -> None:
    client = SpaceXaiClient(api_key=None, model="pinned-in-config")
    assert client.available is False
    answer = client.ask(kind="advise", system="s", user="u")
    assert answer.offline is True
    assert "coach offline" in answer.text


def test_an_unreachable_provider_degrades_instead_of_raising() -> None:
    client = SpaceXaiClient(api_key="k", model="m", base_url="http://127.0.0.1:9")
    answer = client.ask(kind="advise", system="s", user="u")
    assert answer.offline is True
    assert "coach offline" in answer.text


def test_more_than_five_allowed_domains_is_refused_at_construction() -> None:
    with pytest.raises(ValueError, match="caps it at"):
        SpaceXaiClient(api_key="k", model="m",
                       allowed_domains=[f"d{i}.example" for i in range(MAX_ALLOWED_DOMAINS + 1)])


def test_only_research_news_and_plan_may_reach_the_web() -> None:
    sent: dict[str, Any] = {}

    class Recording(SpaceXaiClient):
        def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
            sent.update(body)
            return {"choices": [{"message": {"content": "ok"}}]}

    client = Recording(api_key="k", model="m", allowed_domains=["reuters.com"])
    client.ask(kind="research", system="s", user="u")
    assert "search_parameters" in sent

    sent.clear()
    client.ask(kind="coach", system="s", user="u")
    assert "search_parameters" not in sent, "the coach does not browse"


def test_the_desk_answers_an_ask_without_a_key_and_without_blocking() -> None:
    loops = DeskLoops(
        client=SpaceXaiClient(api_key=None, model="m"),
        tools=registry(),
        publish=lambda *_args: asyncio.sleep(0),
        symbols=["XAUUSD"],
    )
    answer = asyncio.run(loops.ask("advise", question="what now?"))
    assert answer.offline is True
    assert loops.session_plan is None


def test_a_failing_tool_leaves_the_desk_seeing_less_not_nothing() -> None:
    tools = ToolRegistry()
    tools.register("get_sentinel", "fine", lambda: {"ok": True})

    def explode() -> dict[str, Any]:
        raise RuntimeError("journal unavailable")

    tools.register("get_progress", "broken", explode)
    loops = DeskLoops(client=SpaceXaiClient(api_key=None, model="m"), tools=tools,
                      publish=lambda *_args: asyncio.sleep(0))
    context = loops.context()
    assert context["get_sentinel"] == {"ok": True}
    assert context["get_progress"] is None


def test_the_prompt_cites_the_books_rather_than_reproducing_them() -> None:
    prompt = system_prompt("plan")
    assert "Volman" in CITATION
    assert "no order tool" in prompt.lower()
    assert "demo" in prompt.lower()
    # A profile, not a reprint: the prompt is short enough that it cannot be book text.
    assert len(prompt) < 3000


# -- TradingView webhook --------------------------------------------------------------


def test_a_tv_alert_becomes_a_signal_and_carries_no_order_fields() -> None:
    alert = TvAlert(secret="s", setup="range break", sym="xauusd", side="buy", tf="M5")
    signal = to_signal(alert, ts_ms=1)
    assert signal["kind"] == "tv"
    assert signal["sym"] == "XAUUSD"
    body = json.dumps(signal).lower()
    for field in ("lots", "volume", "order", "place"):
        assert field not in body, "a webhook hint must not look like an order"


def test_an_unknown_field_in_an_alert_is_refused() -> None:
    """`lots` is exactly the field an attacker would add. Extra fields are refused, not ignored."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="lots"):
        TvAlert(secret="s", setup="x", sym="XAUUSD", lots=0.5)  # type: ignore[call-arg]


def test_the_webhook_secret_is_compared_in_constant_time() -> None:
    guard = WebhookGuard(secret="correct-horse")
    assert guard.verify("correct-horse") is True
    assert guard.verify("wrong") is False
    assert WebhookGuard(secret="").verify("") is False, "an unset secret authorises nothing"


def test_the_hmac_form_verifies_a_signed_body() -> None:
    import hashlib
    import hmac as hmac_mod

    guard = WebhookGuard(secret="shh")
    body = b'{"setup":"range break"}'
    signature = hmac_mod.new(b"shh", body, hashlib.sha256).hexdigest()
    assert guard.verify_signature(body, signature) is True
    assert guard.verify_signature(body, "0" * 64) is False


def test_the_public_route_is_rate_limited_before_anything_is_parsed() -> None:
    guard = WebhookGuard(secret="s", per_minute=3)
    assert [guard.allow(now=100.0) for _ in range(4)] == [True, True, True, False]
    # A minute later the window has rolled.
    assert guard.allow(now=200.0) is True
