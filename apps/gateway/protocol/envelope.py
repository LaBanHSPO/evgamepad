"""Protocol v1 envelope: `{v, t, seq, ts, ch, cid, p}`.

Frozen in phase 1. Every frame on the game socket — both directions — is this shape.
A frame larger than `MAX_FRAME_BYTES` is refused before it reaches a handler, because the
socket's whole job is prioritising order acks; audio and tape ride HTTP instead.
"""

from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from ulid import ULID

PROTOCOL_VERSION = 1

# 64 KiB. Phase 1 config exposes this as `gateway.max_frame_bytes`; the two must agree.
MAX_FRAME_BYTES = 65536

Channel = Literal["quotes", "orders", "session", "ai", "voice"]

CHANNELS: tuple[str, ...] = ("quotes", "orders", "session", "ai", "voice")


class ProtocolError(ValueError):
    """A frame that cannot be trusted: oversized, malformed, or off-catalog."""


def new_cid() -> str:
    """Fresh ULID for an idempotent client intent."""
    return str(ULID())


def is_ulid(value: str) -> bool:
    try:
        ULID.from_str(value)
    except (ValueError, TypeError):
        return False
    return True


class Envelope(BaseModel):
    """The only frame shape on the wire.

    `cid` is the client's idempotency key: the same `cid` replayed after a reconnect must not
    place a second order. `seq` is per-connection and monotonic, so `hello`/`lastSeq` can resync.
    """

    model_config = ConfigDict(extra="forbid")

    v: int = Field(default=PROTOCOL_VERSION, description="Protocol version")
    t: str = Field(description="Message type, e.g. `intent.open`")
    seq: int = Field(ge=0, description="Per-connection monotonic sequence")
    ts: int = Field(ge=0, description="Unix milliseconds at send")
    ch: Channel = Field(description="Channel this message rides")
    cid: str | None = Field(default=None, description="ULID idempotency key")
    p: dict[str, Any] = Field(default_factory=dict, description="Message payload")

    @field_validator("v")
    @classmethod
    def _only_v1(cls, v: int) -> int:
        if v != PROTOCOL_VERSION:
            raise ValueError(f"unsupported protocol version {v}; this build speaks v{PROTOCOL_VERSION}")
        return v

    @field_validator("cid")
    @classmethod
    def _cid_is_ulid(cls, v: str | None) -> str | None:
        if v is not None and not is_ulid(v):
            raise ValueError("cid must be a ULID")
        return v

    def encode(self) -> str:
        """Serialise and enforce the frame cap on the way out."""
        raw = self.model_dump_json(exclude_none=True)
        size = len(raw.encode("utf-8"))
        if size > MAX_FRAME_BYTES:
            raise ProtocolError(f"frame {size}B exceeds {MAX_FRAME_BYTES}B cap (t={self.t})")
        return raw


def decode(raw: str | bytes) -> Envelope:
    """Parse an inbound frame, refusing anything oversized or malformed."""
    payload = raw.encode("utf-8") if isinstance(raw, str) else raw
    if len(payload) > MAX_FRAME_BYTES:
        raise ProtocolError(f"frame {len(payload)}B exceeds {MAX_FRAME_BYTES}B cap")
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ProtocolError(f"frame is not JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ProtocolError("frame must be a JSON object")
    return Envelope.model_validate(data)
