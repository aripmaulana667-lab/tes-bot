"""Audio spectrum visualizer.

Computes a per-frame frequency response from PCM samples and renders one of
ten visualizer styles into an RGBA frame. The renderer is intentionally pure
NumPy + Pillow so it works on low-end PCs without any GPU.

Pipeline:
  ``compute_frames(samples, sr, fps, bars, bass_boost)`` -> ``np.ndarray (N, bars)``
  ``render(...)`` -> RGBA ``PIL.Image`` (composited by the render engine).

Smoothing combines:
  * temporal smoothing controlled by ``smoothness``
  * "fall" decay so peaks don't snap to zero between hits
  * a perceptual log-frequency mapping that makes bass and treble feel even.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


SPECTRUM_STYLES = [
    "Classic Bars",
    "Rounded Bars",
    "Neon Glow Bars",
    "Circular Spectrum",
    "Waveform Line",
    "Smooth Mountain Wave",
    "Particle Spectrum",
    "Mirror Bars",
    "Radial Pulse",
    "Minimal Elegant Spectrum",
]

POSITIONS = ["bottom", "top", "center", "left", "right"]


@dataclass
class SpectrumConfig:
    style: str = "Classic Bars"
    color: str = "#3B82F6"
    color2: str = "#8B5CF6"
    gradient: bool = True
    glow: bool = True
    sensitivity: float = 1.2
    smoothness: float = 0.6
    bass_boost: float = 1.0
    height: float = 0.25  # 0..1 fraction of frame height
    width: float = 0.9    # 0..1 fraction of frame width
    position: str = "bottom"
    transparency: float = 0.95
    bars: int = 64
    fps: int = 30


# ---------------------------------------------------------------------------
# Spectrum computation
# ---------------------------------------------------------------------------


def _logspace_bins(n_bars: int, n_fft: int, sr: int) -> np.ndarray:
    """Return bin indices that group FFT magnitudes into perceptual bands."""
    f_min = 30.0
    f_max = min(16000.0, sr / 2.0)
    edges = np.logspace(math.log10(f_min), math.log10(f_max), n_bars + 1)
    nyquist = sr / 2.0
    bin_edges = np.clip((edges / nyquist) * (n_fft // 2), 0, n_fft // 2).astype(np.int32)
    # Ensure each band has at least one bin.
    for i in range(1, len(bin_edges)):
        if bin_edges[i] <= bin_edges[i - 1]:
            bin_edges[i] = bin_edges[i - 1] + 1
    return bin_edges


def compute_frames(
    samples: np.ndarray,
    sample_rate: int,
    fps: int,
    bars: int = 64,
    bass_boost: float = 1.0,
    sensitivity: float = 1.0,
    smoothness: float = 0.6,
) -> np.ndarray:
    """Compute an ``(num_frames, bars)`` matrix of band amplitudes in [0, 1].

    The smoothing is two-pass: temporal IIR + peak-decay so the visualizer
    looks alive but never jitters.
    """
    if samples.ndim > 1:
        samples = samples.mean(axis=1)
    samples = samples.astype(np.float32, copy=False)

    n_fft = 2048
    hop = max(1, int(sample_rate / fps))
    total = len(samples)
    num_frames = max(1, int(math.ceil(total / hop)))
    window = np.hanning(n_fft).astype(np.float32)

    bin_edges = _logspace_bins(bars, n_fft, sample_rate)
    out = np.zeros((num_frames, bars), dtype=np.float32)

    for i in range(num_frames):
        start = i * hop
        end = start + n_fft
        chunk = samples[start:end]
        if len(chunk) < n_fft:
            chunk = np.pad(chunk, (0, n_fft - len(chunk)))
        spec = np.abs(np.fft.rfft(chunk * window))
        spec = np.log1p(spec)
        for b in range(bars):
            lo = bin_edges[b]
            hi = max(lo + 1, bin_edges[b + 1])
            out[i, b] = spec[lo:hi].mean()

    # Bass boost (low bands get a multiplier).
    if abs(bass_boost - 1.0) > 1e-3:
        boost = np.linspace(bass_boost, 1.0, bars, dtype=np.float32)
        out *= boost[None, :]

    # Sensitivity / normalisation.
    mx = float(np.percentile(out, 99.5)) if out.size else 1.0
    if mx <= 1e-6:
        mx = 1.0
    out /= mx
    out *= sensitivity
    np.clip(out, 0.0, 1.2, out=out)

    # Temporal smoothing — high "smoothness" = more lag (more cinematic).
    smoothness = max(0.0, min(0.95, smoothness))
    if smoothness > 0:
        alpha = 1.0 - smoothness * 0.7
        smoothed = np.zeros_like(out)
        prev = out[0]
        for i in range(num_frames):
            prev = alpha * out[i] + (1 - alpha) * prev
            smoothed[i] = prev
        out = smoothed

    # Peak decay: amplitudes can dip slowly between hits.
    decayed = np.zeros_like(out)
    falloff = 0.85 + 0.1 * smoothness
    held = out[0].copy()
    for i in range(num_frames):
        held = np.maximum(out[i], held * falloff)
        decayed[i] = np.maximum(out[i], held)
    out = decayed * 0.7 + out * 0.3
    return np.clip(out, 0.0, 1.0)


# ---------------------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------------------


def _hex_to_rgba(hex_color: str, alpha: int = 255) -> tuple[int, int, int, int]:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) == 8:
        r, g, b, a = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(h[6:8], 16)
        return (r, g, b, a)
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return (r, g, b, alpha)


def _lerp_color(a, b, t: float):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))


def _gradient_band(cfg: SpectrumConfig, value: float) -> tuple[int, int, int, int]:
    alpha = int(255 * cfg.transparency)
    a = _hex_to_rgba(cfg.color, alpha)
    if not cfg.gradient:
        return a
    b = _hex_to_rgba(cfg.color2, alpha)
    return _lerp_color(a, b, max(0.0, min(1.0, value)))  # type: ignore


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def _placement_rect(cfg: SpectrumConfig, w: int, h: int) -> tuple[int, int, int, int]:
    bw = int(w * cfg.width)
    bh = int(h * cfg.height)
    x = (w - bw) // 2
    if cfg.position == "top":
        y = int(h * 0.06)
    elif cfg.position == "center":
        y = (h - bh) // 2
    elif cfg.position == "left":
        x = int(w * 0.04)
        y = (h - bh) // 2
    elif cfg.position == "right":
        x = w - bw - int(w * 0.04)
        y = (h - bh) // 2
    else:  # bottom
        y = h - bh - int(h * 0.06)
    return x, y, bw, bh


def _maybe_glow(img: Image.Image, cfg: SpectrumConfig) -> Image.Image:
    if not cfg.glow:
        return img
    glow = img.filter(ImageFilter.GaussianBlur(radius=8))
    out = Image.alpha_composite(glow, img)
    return out


def render(
    cfg: SpectrumConfig,
    spectrum: np.ndarray,
    frame_index: int,
    frame_size: tuple[int, int],
    audio_features: Optional[dict] = None,
) -> Image.Image:
    """Render one frame and return an RGBA PIL image of size ``frame_size``."""
    width, height = frame_size
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if frame_index >= len(spectrum):
        frame_index = len(spectrum) - 1
    bands = spectrum[frame_index] if len(spectrum) else np.zeros(cfg.bars)

    style = cfg.style if cfg.style in SPECTRUM_STYLES else SPECTRUM_STYLES[0]

    if style == "Classic Bars":
        _draw_classic_bars(draw, img, bands, cfg, width, height)
    elif style == "Rounded Bars":
        _draw_rounded_bars(draw, img, bands, cfg, width, height)
    elif style == "Neon Glow Bars":
        _draw_neon_bars(draw, img, bands, cfg, width, height)
    elif style == "Circular Spectrum":
        _draw_circular(draw, img, bands, cfg, width, height)
    elif style == "Waveform Line":
        _draw_waveform(draw, img, bands, cfg, width, height, frame_index)
    elif style == "Smooth Mountain Wave":
        _draw_mountain(draw, img, bands, cfg, width, height)
    elif style == "Particle Spectrum":
        _draw_particles(draw, img, bands, cfg, width, height, frame_index)
    elif style == "Mirror Bars":
        _draw_mirror(draw, img, bands, cfg, width, height)
    elif style == "Radial Pulse":
        _draw_radial_pulse(draw, img, bands, cfg, width, height, frame_index)
    elif style == "Minimal Elegant Spectrum":
        _draw_minimal(draw, img, bands, cfg, width, height)

    return _maybe_glow(img, cfg)


# ---------------------------------------------------------------------------
# Style implementations
# ---------------------------------------------------------------------------


def _draw_classic_bars(draw, img, bands, cfg, w, h):
    x, y, bw, bh = _placement_rect(cfg, w, h)
    n = len(bands)
    gap = max(1, int(bw / n * 0.18))
    bar_w = max(2, int((bw - gap * (n - 1)) / n))
    for i, v in enumerate(bands):
        height = int(v * bh)
        if height <= 0:
            continue
        bx = x + i * (bar_w + gap)
        by = y + bh - height
        color = _gradient_band(cfg, v)
        draw.rectangle([bx, by, bx + bar_w, y + bh], fill=color)


def _draw_rounded_bars(draw, img, bands, cfg, w, h):
    x, y, bw, bh = _placement_rect(cfg, w, h)
    n = len(bands)
    gap = max(2, int(bw / n * 0.25))
    bar_w = max(3, int((bw - gap * (n - 1)) / n))
    radius = bar_w // 2
    for i, v in enumerate(bands):
        height = int(v * bh)
        if height <= 1:
            continue
        bx = x + i * (bar_w + gap)
        by = y + bh - height
        color = _gradient_band(cfg, v)
        draw.rounded_rectangle([bx, by, bx + bar_w, y + bh], radius=radius, fill=color)


def _draw_neon_bars(draw, img, bands, cfg, w, h):
    # Glow happens in _maybe_glow; here we paint thinner luminous bars.
    x, y, bw, bh = _placement_rect(cfg, w, h)
    n = len(bands)
    gap = max(3, int(bw / n * 0.4))
    bar_w = max(2, int((bw - gap * (n - 1)) / n))
    alpha = int(255 * cfg.transparency)
    base_color = _hex_to_rgba(cfg.color, alpha)
    glow_color = _hex_to_rgba(cfg.color2, alpha)
    for i, v in enumerate(bands):
        height = int(v * bh)
        if height <= 1:
            continue
        bx = x + i * (bar_w + gap)
        by = y + bh - height
        # Bright core
        draw.rounded_rectangle(
            [bx, by, bx + bar_w, y + bh],
            radius=bar_w // 2,
            fill=_lerp_color(base_color, glow_color, v),
        )


def _draw_circular(draw, img, bands, cfg, w, h):
    cx, cy = w // 2, h // 2
    radius = int(min(w, h) * 0.22 * (0.7 + cfg.height * 1.0))
    n = len(bands)
    max_len = int(min(w, h) * 0.18 * (0.6 + cfg.height * 1.4))
    for i, v in enumerate(bands):
        angle = (i / n) * 2 * math.pi - math.pi / 2
        r1 = radius
        r2 = radius + int(max_len * v)
        x1 = cx + math.cos(angle) * r1
        y1 = cy + math.sin(angle) * r1
        x2 = cx + math.cos(angle) * r2
        y2 = cy + math.sin(angle) * r2
        color = _gradient_band(cfg, v)
        draw.line([(x1, y1), (x2, y2)], fill=color, width=max(2, int(min(w, h) / n / 2)))
    # Inner ring outline
    ring_color = _hex_to_rgba(cfg.color, int(255 * cfg.transparency * 0.4))
    draw.ellipse(
        [cx - radius, cy - radius, cx + radius, cy + radius],
        outline=ring_color,
        width=2,
    )


def _draw_waveform(draw, img, bands, cfg, w, h, frame_index):
    x, y, bw, bh = _placement_rect(cfg, w, h)
    n = len(bands)
    pts: list[tuple[int, int]] = []
    for i, v in enumerate(bands):
        px = x + int(i / max(1, n - 1) * bw)
        py = y + bh // 2 + int((v - 0.5) * bh * 1.2)
        pts.append((px, py))
    color = _hex_to_rgba(cfg.color, int(255 * cfg.transparency))
    draw.line(pts, fill=color, width=max(2, int(bh / 30)))


def _draw_mountain(draw, img, bands, cfg, w, h):
    x, y, bw, bh = _placement_rect(cfg, w, h)
    n = len(bands)
    pts: list[tuple[int, int]] = [(x, y + bh)]
    for i, v in enumerate(bands):
        px = x + int(i / max(1, n - 1) * bw)
        py = y + bh - int(v * bh)
        pts.append((px, py))
    pts.append((x + bw, y + bh))
    color_top = _hex_to_rgba(cfg.color2 if cfg.gradient else cfg.color, int(220 * cfg.transparency))
    color_bottom = _hex_to_rgba(cfg.color, int(160 * cfg.transparency))
    # Approximate fill by drawing many horizontal lines between top edge and bottom
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    o_draw = ImageDraw.Draw(overlay)
    o_draw.polygon(pts, fill=color_bottom)
    img.alpha_composite(overlay)
    # Top outline accent
    draw.line(pts[1:-1], fill=color_top, width=max(2, int(bh / 40)))


def _draw_particles(draw, img, bands, cfg, w, h, frame_index):
    x, y, bw, bh = _placement_rect(cfg, w, h)
    n = len(bands)
    rng = np.random.default_rng(frame_index * 7919 + 13)
    for i, v in enumerate(bands):
        cx = x + int((i + 0.5) / n * bw)
        height = v * bh
        # number of particles scaled by intensity
        count = max(0, int(v * 14))
        color = _gradient_band(cfg, v)
        for _ in range(count):
            ox = int(rng.normal(0, 4))
            oy = int(rng.uniform(-height, 0))
            r = max(1, int(2 + v * 6 + rng.normal(0, 1)))
            px = cx + ox
            py = y + bh + oy
            draw.ellipse([px - r, py - r, px + r, py + r], fill=color)


def _draw_mirror(draw, img, bands, cfg, w, h):
    x, y, bw, bh = _placement_rect(cfg, w, h)
    half = bh // 2
    mid = y + half
    n = len(bands)
    gap = max(1, int(bw / n * 0.2))
    bar_w = max(2, int((bw - gap * (n - 1)) / n))
    for i, v in enumerate(bands):
        height = int(v * half)
        if height <= 0:
            continue
        bx = x + i * (bar_w + gap)
        color = _gradient_band(cfg, v)
        draw.rectangle([bx, mid - height, bx + bar_w, mid], fill=color)
        faded = (color[0], color[1], color[2], int(color[3] * 0.45))
        draw.rectangle([bx, mid, bx + bar_w, mid + height], fill=faded)


def _draw_radial_pulse(draw, img, bands, cfg, w, h, frame_index):
    cx, cy = w // 2, h // 2
    base_r = int(min(w, h) * 0.16)
    avg = float(np.mean(bands)) if len(bands) else 0.0
    pulse = base_r + int(avg * min(w, h) * 0.25)
    # Concentric rings
    for k, factor in enumerate((1.0, 0.7, 0.45)):
        r = int(pulse * (1 + 0.18 * k))
        alpha = int(180 * factor * cfg.transparency)
        ring_color = _hex_to_rgba(cfg.color2 if cfg.gradient and k % 2 else cfg.color, alpha)
        width = max(1, int(min(w, h) / 200))
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=ring_color, width=width)
    # spectrum spokes
    n = len(bands)
    for i, v in enumerate(bands):
        angle = (i / n) * 2 * math.pi - math.pi / 2
        r1 = pulse
        r2 = pulse + int(min(w, h) * 0.12 * v)
        color = _gradient_band(cfg, v)
        draw.line(
            [
                (cx + math.cos(angle) * r1, cy + math.sin(angle) * r1),
                (cx + math.cos(angle) * r2, cy + math.sin(angle) * r2),
            ],
            fill=color,
            width=max(2, int(min(w, h) / n / 3)),
        )


def _draw_minimal(draw, img, bands, cfg, w, h):
    """Tall thin dots/lines, very designer-magazine looking."""
    x, y, bw, bh = _placement_rect(cfg, w, h)
    n = len(bands)
    step = bw / n
    color = _hex_to_rgba(cfg.color, int(255 * cfg.transparency))
    for i, v in enumerate(bands):
        cx = int(x + (i + 0.5) * step)
        height = int(v * bh * 0.95) + 4
        top = y + bh - height
        line_width = max(2, int(step * 0.18))
        # Faint baseline track
        track_color = (color[0], color[1], color[2], int(40 * cfg.transparency))
        draw.line([(cx, y + bh - 4), (cx, y + bh)], fill=track_color, width=line_width)
        if height < 8:
            continue
        draw.rounded_rectangle(
            [cx - line_width // 2, top, cx + line_width // 2, y + bh - 4],
            radius=line_width // 2,
            fill=color,
        )
        # Top dot
        r = line_width
        draw.ellipse([cx - r, top - r, cx + r, top + r], fill=color)


__all__ = [
    "SPECTRUM_STYLES",
    "POSITIONS",
    "SpectrumConfig",
    "compute_frames",
    "render",
]
