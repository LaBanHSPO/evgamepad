"""Arcade skins: the artwork the matrix and city HUDs paint.

The catalog is the production contract. Screens never hard-code `/uploads/...` as the only path —
they fetch this list and follow the URLs the gateway returns. Assets themselves are served from
`app/public` so Vite's copy into `dist/` and the gateway's FileResponse stay the same files.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

# apps/gateway/arcade/catalog.py -> repo root
ROOT = Path(__file__).resolve().parents[3]
PUBLIC = ROOT / "app" / "public"

ASSET_FILES: dict[str, Path] = {
    "matrix": PUBLIC / "uploads" / "matrix-like-bg-fullhd.png",
    "city": PUBLIC / "uploads" / "contra-like-bg-full-hd.png",
    "boom-big": PUBLIC / "sprites" / "boom-big.png",
    "boom-mid": PUBLIC / "sprites" / "boom-mid.png",
    "boom-small": PUBLIC / "sprites" / "boom-small.png",
    "heart-full": PUBLIC / "sprites" / "heart-full.png",
    "heart-empty": PUBLIC / "sprites" / "heart-empty.png",
    "hero-fire": PUBLIC / "sprites" / "hero-fire.png",
    "hero-kneel": PUBLIC / "sprites" / "hero-kneel.png",
}

CONTENT_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}


def asset_url(name: str) -> str:
    return f"/api/arcade/assets/{name}"


def asset_path(name: str) -> Path | None:
    path = ASSET_FILES.get(name)
    if path is None or not path.is_file():
        return None
    return path


SKINS: tuple[dict[str, Any], ...] = (
    {
        "id": "matrix",
        "label": "HUD on matrix art",
        "screen": "artmatrix",
        "tone": "terminal",
        "background": asset_url("matrix"),
        "fallback": "/uploads/matrix-like-bg-fullhd.png",
        "sprites": {},
    },
    {
        "id": "city",
        "label": "Fire on city art",
        "screen": "artcontra",
        "tone": "contra",
        "background": asset_url("city"),
        "fallback": "/uploads/contra-like-bg-full-hd.png",
        "sprites": {
            "boomBig": asset_url("boom-big"),
            "boomMid": asset_url("boom-mid"),
            "boomSmall": asset_url("boom-small"),
            "heartFull": asset_url("heart-full"),
            "heartEmpty": asset_url("heart-empty"),
            "heroFire": asset_url("hero-fire"),
            "heroKneel": asset_url("hero-kneel"),
        },
        "spriteFallbacks": {
            "boomBig": "/sprites/boom-big.png",
            "boomMid": "/sprites/boom-mid.png",
            "boomSmall": "/sprites/boom-small.png",
            "heartFull": "/sprites/heart-full.png",
            "heartEmpty": "/sprites/heart-empty.png",
            "heroFire": "/sprites/hero-fire.png",
            "heroKneel": "/sprites/hero-kneel.png",
        },
    },
)


def list_skins() -> list[dict[str, Any]]:
    """Catalog with `ready` so a missing file is visible, not a broken background."""
    out: list[dict[str, Any]] = []
    for skin in SKINS:
        asset_name = "matrix" if skin["id"] == "matrix" else "city"
        row = dict(skin)
        row["ready"] = asset_path(asset_name) is not None
        out.append(row)
    return out


def get_skin(skin_id: str) -> dict[str, Any] | None:
    for skin in list_skins():
        if skin["id"] == skin_id:
            return skin
    return None
