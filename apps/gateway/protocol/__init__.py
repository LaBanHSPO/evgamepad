"""Protocol v1 — encode, decode, and the frozen message catalog."""

from __future__ import annotations

import json
import time
from typing import Any

from ulid import ULID

from . import catalog
from .catalog import CATALOG, INTENT_TYPES, SAFETY_EXIT_TYPES, Direction, Msg, Spec
from .envelope import (
    CHANNELS,
    MAX_FRAME_BYTES,
    PROTOCOL_VERSION,
    Channel,
    Frame,
    ProtocolError,
    is_cid,
)

__all__ = [
    "CATALOG",
    "CHANNELS",
    "INTENT_TYPES",
    "MAX_FRAME_BYTES",
    "PROTOCOL_VERSION",
    "SAFETY_EXIT_TYPES",
    "Channel",
    "Direction",
    "Frame",
    "Msg",
    "ProtocolError",
    "Spec",
    "catalog",
    "decode",
    "encode",
    "is_cid",
    "new_cid",
    "now_ms",
]


def now_ms() -> int:
    return int(time.time() * 1000)


def new_cid() -> str:
    return str(ULID())


def encode(
    t: str,
    payload: Msg | dict[str, Any] | None = None,
    *,
    seq: int,
    cid: str | None = None,
    ts: int | None = None,
) -> str:
    """Serialise one server frame. Raises before the socket sees anything wrong."""
    spec = _spec(t)
    model = spec.model
    if payload is None:
        obj = model()
    elif isinstance(payload, Msg):
        if not isinstance(payload, model):
            raise ProtocolError("payload_mismatch", f"{t} wants {model.__name__}")
        obj = payload
    else:
        obj = model.model_validate(payload)

    frame = Frame(
        v=PROTOCOL_VERSION,
        t=t,
        seq=seq,
        ts=now_ms() if ts is None else ts,
        ch=spec.ch,
        cid=cid,
        p=obj.model_dump(mode="json", by_alias=True, exclude_none=True),
    )
    raw = json.dumps(
        frame.model_dump(mode="json", exclude_none=True), separators=(",", ":")
    )
    if len(raw.encode()) > MAX_FRAME_BYTES:
        raise ProtocolError("frame_too_large", t)
    return raw


def decode(raw: str | bytes, *, direction: Direction = "c2s") -> tuple[Frame, Msg]:
    """Parse and validate one frame arriving from ``direction``'s sender.

    Every rejection is a :class:`ProtocolError` with a stable ``reason``, so the
    caller can turn it straight into an ``error`` frame.
    """
    data = raw.encode() if isinstance(raw, str) else raw
    if len(data) > MAX_FRAME_BYTES:
        raise ProtocolError("frame_too_large", f"{len(data)} bytes")

    try:
        obj = json.loads(data)
    except ValueError as exc:
        raise ProtocolError("bad_json", str(exc)) from None
    if not isinstance(obj, dict):
        raise ProtocolError("bad_json", "frame must be an object")

    try:
        frame = Frame.model_validate(obj)
    except Exception as exc:
        raise ProtocolError("bad_envelope", _brief(exc)) from None

    if frame.v != PROTOCOL_VERSION:
        raise ProtocolError("bad_version", str(frame.v))

    spec = CATALOG.get(frame.t)
    if spec is None:
        raise ProtocolError("unknown_type", frame.t)
    if spec.dir != direction:
        raise ProtocolError("wrong_direction", frame.t)
    if spec.ch != frame.ch:
        raise ProtocolError("wrong_channel", f"{frame.t} rides {spec.ch}")
    if frame.t in INTENT_TYPES and frame.cid is None:
        raise ProtocolError("missing_cid", frame.t)

    try:
        payload = spec.model.model_validate(frame.p)
    except Exception as exc:
        raise ProtocolError("bad_payload", f"{frame.t}: {_brief(exc)}") from None

    return frame, payload


def _spec(t: str) -> Spec:
    spec = CATALOG.get(t)
    if spec is None:
        raise ProtocolError("unknown_type", t)
    return spec


def _brief(exc: Exception) -> str:
    text = str(exc).replace("\n", " ")
    return text[:200]
