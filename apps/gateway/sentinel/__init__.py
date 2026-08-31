"""The always-on market sentinel. Deterministic, and it never waits on the desk."""

from .engine import SentinelEngine, SentinelTick

__all__ = ["SentinelEngine", "SentinelTick"]
