"""Dump the frozen catalog as JSON Schema.

The web app's TypeScript types are generated from this file, so the catalog has
exactly one source of truth. ``--check`` fails when the committed schema is
stale, which is what makes a catalog change that skipped regeneration break the
web build instead of drifting into a runtime surprise.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .catalog import json_schema

DEFAULT_OUT = Path("app/src/protocol/schema.json")


def render() -> str:
    return json.dumps(json_schema(), indent=2, sort_keys=True) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument(
        "--check",
        action="store_true",
        help="exit non-zero if the file on disk is stale",
    )
    args = ap.parse_args(argv)

    current = render()
    if args.check:
        if not args.out.is_file() or args.out.read_text() != current:
            print(
                f"{args.out} is stale. Run: "
                "uv run python -m apps.gateway.protocol.export_schema",
                file=sys.stderr,
            )
            return 1
        return 0

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(current)
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
