"""Protocol v1 — the frozen wire contract between the HUD and the gateway.

One source of truth: the Pydantic models here. The web's TypeScript types are generated from
this catalog's exported JSON Schema, so a catalog change that is not regenerated fails the
web build instead of drifting silently.
"""

from __future__ import annotations

from .envelope import (
    CHANNELS,
    MAX_FRAME_BYTES,
    PROTOCOL_VERSION,
    Channel,
    Envelope,
    ProtocolError,
    decode,
    is_ulid,
    new_cid,
)
from .messages import CATALOG, CatalogEntry, Direction, Message

__all__ = [
    "CATALOG",
    "CHANNELS",
    "MAX_FRAME_BYTES",
    "PROTOCOL_VERSION",
    "CatalogEntry",
    "Channel",
    "Direction",
    "Envelope",
    "Message",
    "ProtocolError",
    "decode",
    "is_ulid",
    "new_cid",
    "validate_frame",
]


def validate_frame(env: Envelope, *, expect: Direction | None = None) -> Message:
    """Validate an envelope's payload against the frozen catalog.

    Raises `ProtocolError` for an unknown type, a wrong-direction frame, a channel that does not
    match the catalog, or a payload the model refuses. Callers get a typed message or nothing.
    """
    entry = CATALOG.get(env.t)
    if entry is None:
        raise ProtocolError(f"unknown message type `{env.t}`")
    if expect is not None and entry.direction != expect:
        raise ProtocolError(f"`{env.t}` is {entry.direction}, not {expect}")
    if env.ch != entry.ch:
        raise ProtocolError(f"`{env.t}` rides `{entry.ch}`, not `{env.ch}`")
    try:
        return entry.model.model_validate(env.p)
    except Exception as exc:  # pydantic ValidationError, surfaced as a protocol failure
        raise ProtocolError(f"`{env.t}` payload invalid: {exc}") from exc
