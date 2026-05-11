"""Pydantic models for render requests and job status."""
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class LyricsConfig(BaseModel):
    file: Optional[str] = Field(default=None, description="Filename inside storage/lyrics")
    offset_ms: int = 0
    font: str = "Arial"
    font_size: int = 36
    bottom_margin: int = 80
    color: str = "#FFFFFF"
    outline_color: str = "#000000"
    outline_size: int = 2
    shadow_color: str = "#000000"
    shadow_size: int = 1
    opacity: float = 1.0
    fade_ms: int = 250


class SpectrumConfig(BaseModel):
    style: str = "neon_bar_smooth"
    height: int = 180
    density: int = 80
    opacity: float = 0.9


class LogoConfig(BaseModel):
    file: Optional[str] = None
    circle: bool = True
    position: Literal[
        "top_left",
        "top_right",
        "bottom_left",
        "bottom_right",
        "top_center",
    ] = "top_right"
    size: int = 128
    opacity: float = 1.0
    margin: int = 24


class BackgroundConfig(BaseModel):
    mode: Literal["single", "multiple"] = "single"
    files: List[str] = Field(default_factory=list)
    slideshow_duration: float = 4.0
    randomize: bool = False
    dark_overlay: float = 0.35
    blur: int = 0


class RenderConfig(BaseModel):
    resolution: Literal[
        "1280x720", "1920x1080", "720x1280", "1080x1920", "1080x1080"
    ] = "1280x720"
    fps: Literal[24, 30, 60] = 30
    crf: int = Field(default=24, ge=14, le=35)
    preset: Literal[
        "ultrafast", "veryfast", "faster", "fast", "medium"
    ] = "veryfast"


class RenderRequest(BaseModel):
    music_file: str
    output_name: Optional[str] = None
    lyrics: LyricsConfig = Field(default_factory=LyricsConfig)
    spectrum: SpectrumConfig = Field(default_factory=SpectrumConfig)
    logo: LogoConfig = Field(default_factory=LogoConfig)
    background: BackgroundConfig = Field(default_factory=BackgroundConfig)
    render: RenderConfig = Field(default_factory=RenderConfig)
    preview_seconds: int = 10


BatchBgMode = Literal["sequence", "by_name", "random"]


class BatchRenderRequest(BaseModel):
    music_dir: str
    lyrics_dir: str
    background_dir: str
    match_mode: BatchBgMode = "sequence"
    multi_background: bool = False
    lyrics: LyricsConfig = Field(default_factory=LyricsConfig)
    spectrum: SpectrumConfig = Field(default_factory=SpectrumConfig)
    logo: LogoConfig = Field(default_factory=LogoConfig)
    background: BackgroundConfig = Field(default_factory=BackgroundConfig)
    render: RenderConfig = Field(default_factory=RenderConfig)


JobStatus = Literal["pending", "rendering", "done", "failed", "skipped", "cancelled"]
JobKind = Literal["preview", "full", "batch", "batch_item"]


class JobInfo(BaseModel):
    id: str
    kind: JobKind
    status: JobStatus
    progress: float = 0.0
    message: str = ""
    output_file: Optional[str] = None
    music_file: Optional[str] = None
    error: Optional[str] = None
    created_at: float
    updated_at: float
    duration: float = 0.0
    parent_id: Optional[str] = None
    children: List[str] = Field(default_factory=list)


class FFmpegStatus(BaseModel):
    available: bool
    source: str
    path: str = ""
    version: str = ""
    error: str = ""
