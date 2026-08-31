"""What `/settings` is allowed to change, and — more importantly — what it is not.

Two lists, doing two different jobs:

- The set `build()` returns is the **only** set of keys that can be written. An unknown key is
  refused, not ignored, so a typo is visible rather than silently dropped.
- `FORBIDDEN_SEGMENTS` and `FORBIDDEN_PHRASES` are a second, independent net. If someone adds an
  entry naming `mode`, `bind`, `secret`, `token`, `credential` or a safety boot-fail, construction
  refuses it at import time and the process does not start.

The second list exists because the first one is edited by people. An allowlist you can extend
without review is a denylist you forgot to write.

Hard safety invariants — demo mode, the bind address, the broker credentials, `copilot.on_hot_path`,
`tilt.gate_close`, `tradingview.auto_trade` — live in YAML and env, where they are boot-fails.
Nothing that can be edited from a browser at runtime may weaken one.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

# Refused at import. Matched as whole dot/underscore segments, not substrings — "report" contains
# "port", and a guard that rejects the report defaults is a guard nobody keeps.
FORBIDDEN_SEGMENTS = frozenset({
    "mode", "live", "demo", "bind", "host", "port", "origin", "secret", "token", "tokens",
    "credential", "credentials", "password", "account", "tool", "tools", "permission",
    "permissions", "path", "paths", "dir", "env", "allowlist",
})

# Whole names of the safety boot-fails. None of them may ever become a database row.
FORBIDDEN_PHRASES = ("auto_trade", "gate_close", "on_hot_path", "webhook_secret")


def segments(key: str) -> set[str]:
    return {part for chunk in key.lower().split(".") for part in chunk.split("_") if part}


class SettingsError(ValueError):
    """A rejected write. The message is safe to show the player."""


@dataclass(frozen=True)
class Setting:
    """One editable preference: how to validate it, and what it means if unset."""

    key: str
    describe: str
    default: Any
    validate: Callable[[Any], Any]

    def __post_init__(self) -> None:
        lowered = self.key.lower()
        clash = segments(self.key) & FORBIDDEN_SEGMENTS
        for phrase in FORBIDDEN_PHRASES:
            if phrase in lowered:
                clash = clash | {phrase}
        if clash:
            raise SettingsError(
                f"setting `{self.key}` names {', '.join(sorted(clash))}; safety and identity live "
                "in config, where they are boot-fails, not in the database"
            )


# -- validators ------------------------------------------------------------------------


def a_bool(value: Any) -> bool:
    if not isinstance(value, bool):
        raise SettingsError("expected true or false")
    return value


def an_int(low: int, high: int) -> Callable[[Any], int]:
    def check(value: Any) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise SettingsError("expected a whole number")
        if not low <= value <= high:
            raise SettingsError(f"expected a number between {low} and {high}")
        return value
    return check


def a_float(low: float, high: float) -> Callable[[Any], float]:
    def check(value: Any) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise SettingsError("expected a number")
        if not low <= float(value) <= high:
            raise SettingsError(f"expected a number between {low} and {high}")
        return float(value)
    return check


def one_of(*options: str) -> Callable[[Any], str]:
    def check(value: Any) -> str:
        if value not in options:
            raise SettingsError(f"expected one of {', '.join(options)}")
        return str(value)
    return check


def a_time(value: Any) -> str:
    """A 24-hour `HH:MM`. The session window is a preference; the risk caps around it are not."""
    text = str(value)
    parts = text.split(":")
    if len(parts) != 2 or not all(p.isdigit() for p in parts):
        raise SettingsError("expected a time as HH:MM")
    hour, minute = int(parts[0]), int(parts[1])
    if not (0 <= hour < 24 and 0 <= minute < 60):
        raise SettingsError("expected a valid time of day")
    return f"{hour:02d}:{minute:02d}"


def a_timezone(value: Any) -> str:
    """An IANA zone the machine actually has. A zone we cannot resolve would silently shift the day."""
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

    try:
        ZoneInfo(str(value))
    except (ZoneInfoNotFoundError, ValueError, KeyError) as exc:
        raise SettingsError(f"`{value}` is not a timezone this machine knows") from exc
    return str(value)


def a_list_of(options: Callable[[], set[str]], *, at_least: int = 0) -> Callable[[Any], list[str]]:
    """A subset of something the **server** decides. The UI can narrow it, never widen it."""
    def check(value: Any) -> list[str]:
        if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
            raise SettingsError("expected a list of names")
        available = options()
        unknown = [v for v in value if v not in available]
        if unknown:
            raise SettingsError(f"not available on this server: {', '.join(sorted(unknown))}")
        if len(value) < at_least:
            raise SettingsError(f"choose at least {at_least}")
        return list(dict.fromkeys(value))
    return check


def a_weekday_set(value: Any) -> list[int]:
    if not isinstance(value, list) or not all(isinstance(v, int) and 0 <= v <= 6 for v in value):
        raise SettingsError("expected weekday numbers, Monday 0 to Sunday 6")
    return sorted(set(value))


TIMEFRAMES = ("M1", "M5", "M15", "M30", "H1", "H4", "D1")


def build(*, server_symbols: Callable[[], set[str]]) -> dict[str, Setting]:
    """The full editable surface.

    `server_symbols` is passed in rather than imported so the allowlist is always the *server's*
    symbol list: the UI chooses among what the gateway already permits and can never introduce a
    symbol the risk config never approved.
    """
    settings = [
        Setting("symbols.enabled", "Which of the server's symbols appear on the HUD",
                [], a_list_of(server_symbols, at_least=1)),
        Setting("chart.timeframes", "Timeframes the replay and HUD step through",
                list(TIMEFRAMES[:4]), a_list_of(lambda: set(TIMEFRAMES), at_least=1)),
        Setting("evening.start", "When the evening begins, local time", "20:00", a_time),
        Setting("evening.end", "When it ends", "23:30", a_time),
        Setting("evening.days", "Which weekdays you trade", [1, 2, 3, 4], a_weekday_set),
        Setting("evening.timezone", "The zone the evening is defined in",
                "Asia/Ho_Chi_Minh", a_timezone),
        Setting("pad.deadzone", "Stick deadzone", 0.15, a_float(0.0, 0.6)),
        Setting("pad.clutch_engage", "Clutch engages above this", 0.80, a_float(0.1, 1.0)),
        Setting("pad.clutch_release", "And releases below this", 0.50, a_float(0.0, 1.0)),
        Setting("pad.rumble", "Rumble on arm, fire and reject", True, a_bool),
        Setting("voice.push_to_talk", "Hold LB+RB to record a memo", True, a_bool),
        Setting("voice.input_gain", "Microphone gain", 1.0, a_float(0.1, 4.0)),
        Setting("coach.speak", "Read the desk's advice aloud", False, a_bool),
        Setting("journal.retention_days", "How long journal rows are kept", 730,
                an_int(30, 3650)),
        Setting("report.default_period", "What the report builder opens on", "month",
                one_of("week", "month", "custom", "session")),
        Setting("report.include_outcome", "Whether the money appendix is on by default", False,
                a_bool),
    ]
    return {setting.key: setting for setting in settings}


def apply(defined: dict[str, Setting], incoming: dict[str, Any]) -> dict[str, Any]:
    """Validate a whole write. One bad key rejects the batch rather than half-applying it."""
    if not isinstance(incoming, dict):
        raise SettingsError("expected an object of settings")

    unknown = sorted(set(incoming) - set(defined))
    if unknown:
        raise SettingsError(f"not an editable setting: {', '.join(unknown)}")

    cleaned: dict[str, Any] = {}
    for key, value in incoming.items():
        try:
            cleaned[key] = defined[key].validate(value)
        except SettingsError as exc:
            raise SettingsError(f"{key}: {exc}") from exc
    return cleaned


def clutch_hysteresis_holds(values: dict[str, Any]) -> None:
    """Engage must stay above release.

    Inverted, the clutch would chatter: a single stick position would read as both engaged and
    released, and the FSM would arm and cancel on alternate frames.
    """
    engage = values.get("pad.clutch_engage")
    release = values.get("pad.clutch_release")
    if engage is not None and release is not None and release >= engage:
        raise SettingsError("pad.clutch_release must sit below pad.clutch_engage")


def dumps(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


def loads(raw: str, fallback: Any) -> Any:
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return fallback
