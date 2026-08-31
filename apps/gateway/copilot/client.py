"""SpaceXAI client for the desk.

Deliberately thin: one HTTP call, a domain-filtered web search, and a hard timeout. The model id
is **config**, not a constant — the provider docs could not be reached from this environment, and
a guessed model name would fail mid-session rather than at boot.

Missing `XAI_API_KEY` is a supported state, not an error. The sentinel, the detectors, and trading
all keep working; the desk simply says "coach offline".
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any

log = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://api.x.ai/v1"

# The provider caps the domain filter at five, and a longer list is a phase 1 boot-fail.
MAX_ALLOWED_DOMAINS = 5

# The desk is never on the order path, so a slow answer costs nothing but a slow answer.
REQUEST_TIMEOUT_S = 30

# Only these kinds may reach the web at all.
SEARCH_KINDS = frozenset({"research", "news", "plan"})


class DeskOffline(RuntimeError):
    """No key, no network, or the provider refused. Always recoverable, never fatal."""


@dataclass
class DeskAnswer:
    """What the desk came back with."""

    text: str
    sources: list[str] = field(default_factory=list)
    offline: bool = False

    @classmethod
    def offline_answer(cls, reason: str) -> DeskAnswer:
        return cls(text=f"coach offline ({reason})", sources=[], offline=True)


@dataclass
class SpaceXaiClient:
    """One provider call. No streaming, and no tools the model can invoke on its own."""

    api_key: str | None
    model: str
    allowed_domains: list[str] = field(default_factory=list)
    base_url: str = DEFAULT_BASE_URL
    timeout_s: float = REQUEST_TIMEOUT_S

    def __post_init__(self) -> None:
        if len(self.allowed_domains) > MAX_ALLOWED_DOMAINS:
            raise ValueError(
                f"{len(self.allowed_domains)} allowed domains; the provider caps it at "
                f"{MAX_ALLOWED_DOMAINS}"
            )

    @property
    def available(self) -> bool:
        """Both are required. An unset model would fail mid-session rather than at boot."""
        return bool(self.api_key) and bool(self.model)

    def ask(self, *, kind: str, system: str, user: str) -> DeskAnswer:
        """Ask once. Any failure becomes an offline answer rather than an exception."""
        if not self.api_key:
            return DeskAnswer.offline_answer("no XAI_API_KEY")
        if not self.model:
            return DeskAnswer.offline_answer("copilot.model is unset")

        body: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if kind in SEARCH_KINDS and self.allowed_domains:
            # Domain-filtered search: the desk cites five places, not the open web.
            body["search_parameters"] = {
                "mode": "on",
                "sources": [{"type": "web", "allowed_websites": self.allowed_domains}],
            }

        try:
            payload = self._post("/chat/completions", body)
        except DeskOffline as exc:
            log.warning("desk request failed: %s", exc)
            return DeskAnswer.offline_answer(str(exc))

        return DeskAnswer(text=_extract_text(payload), sources=_extract_sources(payload))

    def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "content-type": "application/json",
                "authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_s) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise DeskOffline(f"provider returned {exc.code}") from exc
        except Exception as exc:
            raise DeskOffline(str(exc)) from exc


def _extract_text(payload: dict[str, Any]) -> str:
    choices = payload.get("choices") or []
    if not choices:
        return "coach offline (empty response)"
    message = choices[0].get("message") or {}
    return str(message.get("content") or "").strip() or "coach offline (empty response)"


def _extract_sources(payload: dict[str, Any]) -> list[str]:
    """Citations, wherever the provider put them. Text-only; never rendered as HTML."""
    citations = payload.get("citations")
    if isinstance(citations, list):
        return [str(c) for c in citations if isinstance(c, str)][:20]
    return []
