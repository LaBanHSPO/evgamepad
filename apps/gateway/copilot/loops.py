"""The four desk loops: plan, news, research/advise, and monitor.

All of them run as in-process worker tasks inside `ev-gateway`, and none of them sit on the order
path. An intent is acknowledged whether or not any of this is running, reachable, or configured —
`ai.ask` returns an offline answer rather than blocking a fire.

Each loop assembles its context from the **read-only** tool registry, so the desk can only ever
describe state it was handed.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any

from .client import DeskAnswer, SpaceXaiClient
from .prompt import system_prompt
from .tools import ToolRegistry

log = logging.getLogger(__name__)

# The news pulse. Slow on purpose: headlines do not change in seconds.
NEWS_INTERVAL_S = 600

# The monitor speaks at most this often, so it advises rather than nags.
MONITOR_INTERVAL_S = 120


@dataclass
class DeskLoops:
    """Owns the desk's periodic work and answers one-off asks."""

    client: SpaceXaiClient
    tools: ToolRegistry
    publish: Any  # async callable: (t, ch, payload) -> None
    symbols: list[str] = field(default_factory=list)
    last_news_ms: int | None = None
    last_monitor_ms: int = 0
    session_plan: str | None = None
    _tasks: list[asyncio.Task] = field(default_factory=list)

    # -- context ---------------------------------------------------------------------

    def context(self) -> dict[str, Any]:
        """Everything the desk is allowed to see, gathered through the allowlist."""
        gathered: dict[str, Any] = {}
        for name in self.tools.names():
            try:
                gathered[name] = self.tools.call(name)
            except Exception:
                log.exception("read-only tool `%s` failed; the desk sees less, not nothing", name)
                gathered[name] = None
        return gathered

    def _user_message(self, kind: str, extra: str | None = None) -> str:
        state = json.dumps(self.context(), default=str, sort_keys=True)[:6000]
        parts = [f"Symbols tonight: {', '.join(self.symbols)}.", f"State: {state}"]
        if extra:
            parts.append(f"Player asked: {extra}")
        return "\n".join(parts)

    # -- one-off asks ----------------------------------------------------------------

    async def ask(self, kind: str, *, question: str | None = None) -> DeskAnswer:
        """Answer one `ai.ask`. Never raises, and never touches an order."""
        message = self._user_message(kind, question)
        # The provider call is blocking, so it goes to a thread rather than stalling the loop
        # that also carries order acks.
        answer = await asyncio.to_thread(
            self.client.ask, kind=kind, system=system_prompt(kind), user=message
        )
        if kind == "plan" and not answer.offline:
            self.session_plan = answer.text
        if kind == "news" and not answer.offline:
            self.last_news_ms = int(time.time() * 1000)
        return answer

    # -- periodic loops --------------------------------------------------------------

    def start(self) -> None:
        """Start the background loops. Safe to call with no API key — they idle politely."""
        loop = asyncio.get_event_loop()
        self._tasks = [
            loop.create_task(self._news_loop()),
        ]

    def stop(self) -> None:
        for task in self._tasks:
            task.cancel()
        self._tasks = []

    async def _news_loop(self) -> None:
        """A headline pulse every ten minutes, and never on the ack path."""
        while True:
            await asyncio.sleep(NEWS_INTERVAL_S)
            if not self.client.available:
                continue
            try:
                answer = await self.ask("news")
                await self.publish("news.item", "ai", {
                    "id": f"news-{int(time.time() * 1000)}",
                    "title": answer.text[:200],
                    "url": answer.sources[0] if answer.sources else "",
                    "source": "desk",
                    "ts": int(time.time() * 1000),
                })
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("news pulse failed; the desk stays offline until the next one")

    async def session_open(self) -> DeskAnswer:
        """The evening's plan: tonight's events, the M5 bias, and what would end the session."""
        return await self.ask("plan")

    async def monitor(self, now_ms: int) -> DeskAnswer | None:
        """Advice after a fill, rate limited so the desk does not nag."""
        if now_ms - self.last_monitor_ms < MONITOR_INTERVAL_S * 1000:
            return None
        self.last_monitor_ms = now_ms
        return await self.ask("advise")
