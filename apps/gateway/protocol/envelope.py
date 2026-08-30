"""Protocol v1 envelope: ``{v, t, seq, ts, ch, cid, p}``.

Frozen in phase 1. Every client and server frame on ``/ws`` is one of these.
Adding a field, a channel, or a message type after this point is a v2 migration,
which is why the journal layer's messages are declared here even though phases
7-14 implement them.
"""

from __future__ import annotations

import re
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field

PROTOCOL_VERSION = 1

#: A frame larger than this is dropped before parsing. Audio and tape ride HTTP.
MAX_FRAME_BYTES = 65536

Channel = Literal["quotes", "orders", "session", "ai", "voice"]
CHANNELS: tuple[str, ...] = ("quotes", "orders", "session", "ai", "voice")

#: Crockford base32, 26 chars, as emitted by ULID.
_ULID_RE = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$")

Cid = Annotated[str, Field(pattern=_ULID_RE.pattern)]


def is_cid(value: str) -> bool:
    return bool(_ULID_RE.match(value))


class Frame(BaseModel):
    """The wire envelope. ``p`` stays a raw mapping here; the catalog validates it."""

    model_config = ConfigDict(extra="forbid")

    v: int = Field(default=PROTOCOL_VERSION)
    t: str
    seq: int = Field(ge=0)
    ts: int = Field(ge=0, description="Unix milliseconds, sender clock")
    ch: Channel
    cid: Cid | None = None
    p: dict[str, Any] = Field(default_factory=dict)


class ProtocolError(ValueError):
    """Raised for anything that must not reach a handler: oversize, unknown type,
    wrong direction, bad payload."""

    def __init__(self, reason: str, detail: str = "") -> None:
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail
