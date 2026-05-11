"""15 spectrum visualizer styles using FFmpeg filters (showfreqs/showspectrum/showcqt)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Tuple

from ..models.render import SpectrumConfig


@dataclass
class SpectrumStyle:
    key: str
    label: str
    description: str
    build: Callable[[Tuple[int, int], SpectrumConfig], str]


def _bars(
    size: Tuple[int, int],
    cfg: SpectrumConfig,
    colors: str,
    extra: str = "",
    mode: str = "bar",
) -> str:
    """Use showfreqs for bar visualization."""
    w, h = size
    spectrum_h = max(40, min(cfg.height, h // 2))
    # Window size influences perceived "density"; map slider into 1024..8192.
    win_size = max(1024, min(8192, int(8192 - cfg.density * 25)))
    base = (
        f"[0:a]showfreqs=s={w}x{spectrum_h}:mode={mode}:ascale=log:fscale=lin:"
        f"win_size={win_size}:cmode=combined:colors={colors}"
    )
    if extra:
        base += f":{extra}"
    base += f",format=rgba,colorchannelmixer=aa={cfg.opacity:.3f},split=1[sp]"
    return base + f";[sp]scale={w}:{spectrum_h}[spec]"


def _showspectrum(
    size: Tuple[int, int],
    cfg: SpectrumConfig,
    color: str,
    scale: str = "lin",
) -> str:
    w, h = size
    spectrum_h = max(40, min(cfg.height, h // 2))
    base = (
        f"[0:a]showspectrum=s={w}x{spectrum_h}:slide=scroll:mode=combined:"
        f"color={color}:scale={scale}:saturation=1:fscale=lin"
    )
    base += f",format=rgba,colorchannelmixer=aa={cfg.opacity:.3f}[spec]"
    return base


def _showcqt(size: Tuple[int, int], cfg: SpectrumConfig, count: int = 1, bar_v: str = "5") -> str:
    w, h = size
    spectrum_h = max(60, min(cfg.height, h // 2))
    base = (
        f"[0:a]showcqt=s={w}x{spectrum_h}:count={count}:bar_v={bar_v}:axis=0:tc=0.33:"
        "csp=bt709"
    )
    base += f",format=rgba,colorchannelmixer=aa={cfg.opacity:.3f}[spec]"
    return base


STYLES: Dict[str, SpectrumStyle] = {}


def _register(key: str, label: str, description: str, fn: Callable[[Tuple[int, int], SpectrumConfig], str]):
    STYLES[key] = SpectrumStyle(key=key, label=label, description=description, build=fn)


_register(
    "neon_bar_smooth",
    "Neon Bar Smooth",
    "Bar neon dengan glow halus.",
    lambda s, c: _bars(s, c, "0x00FFE0|0xFF00C8", mode="bar"),
)
_register(
    "aurora_bars",
    "Aurora Bars",
    "Gradient aurora hijau-biru-ungu.",
    lambda s, c: _bars(s, c, "0x00FFAA|0x00C0FF|0xC080FF", mode="bar"),
)
_register(
    "soft_white_minimal",
    "Soft White Minimal",
    "Bar putih tipis, gaya minimal.",
    lambda s, c: _bars(s, c, "0xFFFFFF|0xE0E0E0", mode="line"),
)
_register(
    "fire_pulse",
    "Fire Pulse",
    "Gradient api merah-oranye-kuning.",
    lambda s, c: _bars(s, c, "0xFF3000|0xFF8800|0xFFD800", mode="bar"),
)
_register(
    "ocean_wave",
    "Ocean Wave",
    "Gelombang biru samudra.",
    lambda s, c: _bars(s, c, "0x0080FF|0x00C8FF|0x80FFFF", mode="line"),
)
_register(
    "purple_dream",
    "Purple Dream",
    "Gradient ungu lembut.",
    lambda s, c: _bars(s, c, "0x6020FF|0xB060FF|0xFF80FF", mode="bar"),
)
_register(
    "green_matrix",
    "Green Matrix",
    "Hijau ala matrix.",
    lambda s, c: _bars(s, c, "0x00FF40|0x80FF80", mode="bar"),
)
_register(
    "gold_luxury",
    "Gold Luxury",
    "Emas mewah dengan highlight.",
    lambda s, c: _bars(s, c, "0xFFC020|0xFFE080|0xFFFFE0", mode="bar"),
)
_register(
    "candy_pop",
    "Candy Pop",
    "Pop berwarna pink dan kuning.",
    lambda s, c: _bars(s, c, "0xFF60C0|0xFFE060|0x60E0FF", mode="bar"),
)
_register(
    "thin_cinematic",
    "Thin Cinematic",
    "Bar sangat tipis, sinematik.",
    lambda s, c: _bars(s, c, "0xF0F0F0|0xA0A0FF", mode="line"),
)
_register(
    "bass_heavy",
    "Bass Heavy",
    "Penekanan pada frekuensi bass.",
    lambda s, c: _bars(s, c, "0xFF2050|0xFFB050", mode="bar"),
)
_register(
    "pastel_smooth",
    "Pastel Smooth",
    "Warna pastel halus.",
    lambda s, c: _bars(s, c, "0xFFC0E0|0xC0E0FF|0xC0FFD0", mode="line"),
)
_register(
    "frequency_classic",
    "Frequency Classic",
    "Spectrum klasik berwarna.",
    lambda s, c: _showspectrum(s, c, color="rainbow"),
)
_register(
    "frequency_glow",
    "Frequency Glow",
    "Spectrum dengan glow.",
    lambda s, c: _showspectrum(s, c, color="intensity"),
)
_register(
    "rainbow_energy",
    "Rainbow Energy",
    "Energi pelangi penuh warna.",
    lambda s, c: _showcqt(s, c, count=1, bar_v="6"),
)


def list_styles():
    return [
        {"key": st.key, "label": st.label, "description": st.description}
        for st in STYLES.values()
    ]


def build_spectrum_chain(size: Tuple[int, int], cfg: SpectrumConfig) -> str:
    style = STYLES.get(cfg.style) or STYLES["neon_bar_smooth"]
    return style.build(size, cfg)
