"""Chart screenshots, attached by hand.

The whole security posture is in one sentence: **the client never names a file.** The server reads
the magic bytes to decide what the thing actually is, generates a ULID for it, and writes that ULID
under the data volume. A client-supplied filename is stored as a label and never touches a path, so
there is no `../` to defend against — the dangerous concatenation does not exist.

No SVG and no HTML, ever. Both are documents that execute, and an image upload that can run script
is a stored XSS with a `.png` on the end.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path

from ulid import ULID

# What a chart screenshot may be. The value is the extension; the key is the magic-byte signature.
SIGNATURES: tuple[tuple[bytes, str, str], ...] = (
    (b"\x89PNG\r\n\x1a\n", "image/png", "png"),
    (b"\xff\xd8\xff", "image/jpeg", "jpg"),
    (b"RIFF", "image/webp", "webp"),          # confirmed further by the WEBP tag at offset 8
)

MAX_BYTES = 8 * 1024 * 1024
MAX_DIMENSION = 8_000


class AttachmentError(ValueError):
    """The upload is not an image this journal stores. The reason is safe to show the player."""


@dataclass(frozen=True)
class Attachment:
    """A stored screenshot. `id` is both the row key and the filename stem."""

    id: str
    mime: str
    extension: str
    bytes: int
    width: int | None
    height: int | None

    def filename(self) -> str:
        return f"{self.id}.{self.extension}"


def sniff(data: bytes) -> tuple[str, str]:
    """What the bytes actually are. The client's content-type is a hint and is never trusted."""
    for signature, mime, extension in SIGNATURES:
        if not data.startswith(signature):
            continue
        if mime == "image/webp" and data[8:12] != b"WEBP":
            continue
        return mime, extension
    raise AttachmentError("only PNG, JPEG and WebP screenshots are stored")


def dimensions(data: bytes, mime: str) -> tuple[int | None, int | None]:
    """Width and height from the header, without decoding the image.

    Unknown dimensions are `None`, not zero: the cap below only rejects what it can actually
    measure, so an unusual but valid encoding is stored rather than refused on a guess.
    """
    try:
        if mime == "image/png":
            width, height = struct.unpack(">II", data[16:24])
            return width, height
        if mime == "image/webp" and data[12:16] == b"VP8 ":
            width, height = struct.unpack("<HH", data[26:30])
            return width & 0x3FFF, height & 0x3FFF
        if mime == "image/jpeg":
            return _jpeg_dimensions(data)
    except (struct.error, IndexError):
        return None, None
    return None, None


def _jpeg_dimensions(data: bytes) -> tuple[int | None, int | None]:
    """Walk the JPEG segments to the start-of-frame marker."""
    offset = 2
    while offset + 9 < len(data):
        if data[offset] != 0xFF:
            return None, None
        marker = data[offset + 1]
        length = struct.unpack(">H", data[offset + 2:offset + 4])[0]
        # SOF0..SOF3 and SOF5..SOF15 carry the frame size; the rest are skipped.
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            height, width = struct.unpack(">HH", data[offset + 5:offset + 9])
            return width, height
        offset += 2 + length
    return None, None


def store(data: bytes, *, directory: Path) -> Attachment:
    """Validate, name, and write. Every failure is a refusal, never a partial write."""
    if not data:
        raise AttachmentError("the upload was empty")
    if len(data) > MAX_BYTES:
        raise AttachmentError(f"screenshots are capped at {MAX_BYTES // (1024 * 1024)} MB")

    mime, extension = sniff(data)
    width, height = dimensions(data, mime)
    if width is not None and (width > MAX_DIMENSION or (height or 0) > MAX_DIMENSION):
        raise AttachmentError(f"screenshots are capped at {MAX_DIMENSION} px on a side")

    attachment = Attachment(id=str(ULID()), mime=mime, extension=extension, bytes=len(data),
                            width=width, height=height)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / attachment.filename()).write_bytes(data)
    return attachment


def path_for(attachment_id: str, extension: str, *, directory: Path) -> Path:
    """Resolve a stored file from its **row**, never from the URL.

    The id is checked against the ULID alphabet before it is used as a path component, so even a
    corrupted row cannot walk out of the directory.
    """
    if not attachment_id.isalnum() or len(attachment_id) != 26:
        raise AttachmentError("not a stored attachment id")
    if not extension.isalnum():
        raise AttachmentError("not a stored attachment type")
    return directory / f"{attachment_id}.{extension}"


def usage(directory: Path) -> dict[str, int]:
    """How much disk the screenshots hold. Shown so the player can see it before it matters."""
    if not directory.exists():
        return {"files": 0, "bytes": 0}
    files = [f for f in directory.iterdir() if f.is_file()]
    return {"files": len(files), "bytes": sum(f.stat().st_size for f in files)}
