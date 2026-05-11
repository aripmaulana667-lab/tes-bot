"""Logo loading / circle-crop / placement.

Kept lazy: callers compute the prepared logo once per render and then paste it
into every frame.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw


LOGO_POSITIONS = [
    "top-left",
    "top-right",
    "top-center",
    "center",
    "bottom-left",
    "bottom-right",
    "bottom-center",
]

SUPPORTED_EXTS = {".png", ".jpg", ".jpeg", ".webp"}


@dataclass
class LogoConfig:
    enabled: bool = False
    path: str = ""
    size: float = 0.12  # fraction of min(width, height)
    position: str = "top-right"
    opacity: float = 1.0
    circle: bool = False


def is_supported(path: str | Path) -> bool:
    return Path(path).suffix.lower() in SUPPORTED_EXTS


def _circle_crop(img: Image.Image) -> Image.Image:
    size = min(img.size)
    img = img.crop(
        (
            (img.width - size) // 2,
            (img.height - size) // 2,
            (img.width + size) // 2,
            (img.height + size) // 2,
        )
    ).convert("RGBA")
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(img, (0, 0), mask=mask)
    return out


def prepare(cfg: LogoConfig, frame_size: tuple[int, int]) -> Optional[Image.Image]:
    """Load + resize + opacity adjust the logo. Returns ``None`` if disabled."""
    if not cfg.enabled or not cfg.path:
        return None
    p = Path(cfg.path)
    if not p.exists():
        return None
    try:
        img = Image.open(p).convert("RGBA")
    except OSError:
        return None

    target = max(8, int(min(frame_size) * max(0.01, min(1.0, cfg.size))))
    # Preserve aspect ratio.
    if img.width >= img.height:
        new_w = target
        new_h = max(1, int(img.height * target / img.width))
    else:
        new_h = target
        new_w = max(1, int(img.width * target / img.height))
    img = img.resize((new_w, new_h), Image.LANCZOS)

    if cfg.circle:
        img = _circle_crop(img)

    if cfg.opacity < 0.999:
        alpha = img.split()[-1]
        alpha = alpha.point(lambda v: int(v * max(0.0, min(1.0, cfg.opacity))))
        img.putalpha(alpha)

    return img


def position_for(
    cfg: LogoConfig,
    frame_size: tuple[int, int],
    logo_size: tuple[int, int],
) -> tuple[int, int]:
    fw, fh = frame_size
    lw, lh = logo_size
    margin = max(12, int(min(fw, fh) * 0.025))
    pos = cfg.position
    if pos == "top-left":
        return margin, margin
    if pos == "top-right":
        return fw - lw - margin, margin
    if pos == "top-center":
        return (fw - lw) // 2, margin
    if pos == "center":
        return (fw - lw) // 2, (fh - lh) // 2
    if pos == "bottom-left":
        return margin, fh - lh - margin
    if pos == "bottom-right":
        return fw - lw - margin, fh - lh - margin
    if pos == "bottom-center":
        return (fw - lw) // 2, fh - lh - margin
    return margin, margin


def paste(frame: Image.Image, cfg: LogoConfig, prepared: Optional[Image.Image]) -> None:
    if prepared is None:
        return
    pos = position_for(cfg, frame.size, prepared.size)
    frame.alpha_composite(prepared, pos)


__all__ = [
    "LogoConfig",
    "LOGO_POSITIONS",
    "SUPPORTED_EXTS",
    "is_supported",
    "prepare",
    "position_for",
    "paste",
]
