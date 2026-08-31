"""Dump the frozen catalog as JSON Schema.

The web's TypeScript types are generated from this file's output, so the catalog has one source
of truth. Run from `apps/gateway`:

    uv run python -m protocol.export_schema --out ../../app/src/protocol/schema.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .envelope import CHANNELS, MAX_FRAME_BYTES, PROTOCOL_VERSION, Envelope
from .messages import CATALOG


def build_schema() -> dict[str, Any]:
    """Whole-catalog schema: the envelope plus every message payload, keyed by wire type."""
    messages: dict[str, Any] = {}
    for t, entry in sorted(CATALOG.items()):
        messages[t] = {
            "direction": entry.direction,
            "ch": entry.ch,
            "payload": entry.model.model_json_schema(by_alias=True),
        }
    return {
        "version": PROTOCOL_VERSION,
        "maxFrameBytes": MAX_FRAME_BYTES,
        "channels": list(CHANNELS),
        "envelope": Envelope.model_json_schema(by_alias=True),
        "messages": messages,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export protocol v1 JSON Schema")
    parser.add_argument("--out", type=Path, default=None, help="Write here instead of stdout")
    args = parser.parse_args(argv)

    text = json.dumps(build_schema(), indent=2, sort_keys=True) + "\n"
    if args.out is None:
        sys.stdout.write(text)
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
