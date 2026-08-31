"""The copilot's tool surface: read-only, by allowlist, forever.

The desk exists to describe what happened and what is in front of you. It has no order tool, no
write tool, and no way to acquire one — a tool is callable only if its name is in `READ_TOOLS`,
and the test beside this module fails the build if a trading or writing verb ever appears here.

This is the second of two structural guarantees. The first is `copilot.on_hot_path: true` being a
phase 1 boot-fail. Neither is a convention either of them can be talked out of.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

# Verbs that must never name a copilot tool. The test asserts this list against the registry.
FORBIDDEN_VERBS = (
    "place", "order", "buy", "sell", "close", "panic", "flatten", "amend", "modify",
    "write", "insert", "update", "delete", "drop", "execute", "send", "submit", "trade",
)


@dataclass(frozen=True)
class Tool:
    """One read-only capability the desk may call."""

    name: str
    describe: str
    call: Callable[..., Any]


class ToolRegistry:
    """Explicit allowlist. Registration refuses anything that reads as an action."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, name: str, describe: str, call: Callable[..., Any]) -> None:
        lowered = name.lower()
        for verb in FORBIDDEN_VERBS:
            if verb in lowered:
                raise ValueError(
                    f"tool `{name}` contains the forbidden verb `{verb}`; the desk is read-only"
                )
        self._tools[name] = Tool(name=name, describe=describe, call=call)

    def names(self) -> list[str]:
        return sorted(self._tools)

    def schema(self) -> list[dict[str, str]]:
        """What the model is told it may call. Nothing outside this list exists to it."""
        return [{"name": t.name, "description": t.describe} for t in self._tools.values()]

    def call(self, name: str, **kwargs: Any) -> Any:
        tool = self._tools.get(name)
        if tool is None:
            raise PermissionError(f"`{name}` is not a copilot tool; the desk is read-only")
        return tool.call(**kwargs)


def build_registry(
    *,
    get_sentinel: Callable[[], dict[str, Any]],
    get_positions: Callable[[], list[dict[str, Any]]],
    get_account: Callable[[], dict[str, Any]],
    get_calendar: Callable[[], list[dict[str, Any]]],
    get_setup: Callable[[], dict[str, Any] | None],
    get_progress: Callable[[], dict[str, Any]],
    get_tilt: Callable[[], dict[str, Any]] | None = None,
    get_journal: Callable[[], dict[str, Any]] | None = None,
) -> ToolRegistry:
    """The full read-only surface. Every name here is a noun, deliberately."""
    registry = ToolRegistry()
    registry.register("get_sentinel", "Current market state: spread, setup, quality, next event",
                      get_sentinel)
    registry.register("get_positions", "Open positions as the broker reports them", get_positions)
    registry.register("get_account", "Balance and equity from the broker", get_account)
    registry.register("get_calendar", "Upcoming high-impact events for tonight's symbols",
                      get_calendar)
    registry.register("get_setup", "The current method tag on the M5 chart", get_setup)
    # Phase 6 and 11 read the journal through this one; it stays a read.
    registry.register("get_progress", "Process figures for this session and recent ones",
                      get_progress)
    # Phase 9. Aggregates only — band, score, and the driver sentences the HUD already shows.
    # The per-component values and the raw pad telemetry never leave the box.
    if get_tilt is not None:
        registry.register("get_tilt", "Current tilt band and what is driving it", get_tilt)
    # Phase 12. Counts and codes only — never the player's own analysis, review notes or memos,
    # which are the parts of a journal that have to stay private to be worth writing.
    if get_journal is not None:
        registry.register("get_journal", "Session counts, consistency, and the top mistake codes",
                          get_journal)
    return registry
