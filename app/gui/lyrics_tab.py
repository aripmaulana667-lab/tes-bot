"""Lyrics tab."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.core import lyrics_extractor

from .state import AppState, StateBus
from .widgets import Card, ColorPicker, FilePicker, SliderRow, labeled


class LyricsTab(QWidget):
    def __init__(self, state: AppState, bus: StateBus, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.state = state
        self.bus = bus
        self._loaded_data: Optional[lyrics_extractor.LyricsData] = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 12, 16, 16)
        outer.setSpacing(14)

        # ---- Source -------------------------------------------------------
        source_card = Card("Source")
        self.enable = QCheckBox("Show lyrics in video")
        self.enable.setChecked(state.lyrics.enabled)
        self.enable.toggled.connect(self._on_enable)
        source_card.addWidget(self.enable)

        scan_row = QHBoxLayout()
        scan_btn = QPushButton("Read lyrics from current audio")
        scan_btn.clicked.connect(self._scan)
        scan_row.addWidget(scan_btn)

        import_btn = QPushButton("Import .lrc file…")
        import_btn.clicked.connect(self._import_lrc)
        scan_row.addWidget(import_btn)

        scan_row.addStretch(1)
        source_card.addLayout(scan_row)

        self.status = QLabel("No lyrics loaded yet.")
        self.status.setObjectName("Subtle")
        source_card.addWidget(self.status)

        self.text_area = QPlainTextEdit()
        self.text_area.setReadOnly(False)
        self.text_area.setPlaceholderText(
            "Loaded lyrics will appear here. You can paste a LRC file for synced lyrics, "
            "or just plain text for unsynced/static display."
        )
        self.text_area.setMinimumHeight(160)
        source_card.addWidget(self.text_area)

        fallback_row = QHBoxLayout()
        fallback_row.addWidget(QLabel("If lyrics aren't synced:"))
        self.fallback = QComboBox()
        self.fallback.addItems(["Show all lyrics as static text", "Disable lyrics for this song", "Use Static text below"])
        fallback_row.addWidget(self.fallback)
        fallback_row.addStretch(1)
        source_card.addLayout(fallback_row)

        self.static_text = QPlainTextEdit()
        self.static_text.setPlaceholderText(
            "Static text shown when there are no lyrics at all (optional)."
        )
        self.static_text.setMaximumHeight(80)
        self.static_text.setPlainText(state.lyrics.static_text)
        self.static_text.textChanged.connect(self._on_static_text)
        source_card.addWidget(self.static_text)

        outer.addWidget(source_card)

        # ---- Style --------------------------------------------------------
        style_card = Card("Lyric style")
        self.font_combo = QComboBox()
        self._populate_fonts()
        self.font_combo.setCurrentText(state.lyrics.font_family)
        self.font_combo.currentTextChanged.connect(self._on_font_family)
        style_card.addLayout(labeled("Font", self.font_combo))

        custom_font_row = QHBoxLayout()
        self.font_path = FilePicker("Custom font file (optional)", "file", "Fonts (*.ttf *.otf)")
        self.font_path.set_value(state.lyrics.font_path)
        self.font_path.changed.connect(self._on_font_path)
        custom_font_row.addWidget(self.font_path)
        style_card.addLayout(labeled("Font file", self.font_path))

        self.font_size = QSpinBox()
        self.font_size.setRange(16, 200)
        self.font_size.setValue(state.lyrics.font_size)
        self.font_size.valueChanged.connect(self._on_font_size)
        style_card.addLayout(labeled("Font size", self.font_size))

        self.color = ColorPicker(state.lyrics.color)
        self.color.changed.connect(self._on_color)
        style_card.addLayout(labeled("Text color", self.color))

        self.outline_color = ColorPicker(state.lyrics.outline_color)
        self.outline_color.changed.connect(self._on_outline_color)
        style_card.addLayout(labeled("Outline color", self.outline_color))

        self.outline = QCheckBox("Outline")
        self.outline.setChecked(state.lyrics.outline)
        self.outline.toggled.connect(self._on_outline)
        self.shadow = QCheckBox("Shadow")
        self.shadow.setChecked(state.lyrics.shadow)
        self.shadow.toggled.connect(self._on_shadow)
        self.bold = QCheckBox("Bold")
        self.bold.setChecked(state.lyrics.bold)
        self.bold.toggled.connect(self._on_bold)
        self.italic = QCheckBox("Italic")
        self.italic.setChecked(state.lyrics.italic)
        self.italic.toggled.connect(self._on_italic)
        check_row = QHBoxLayout()
        for cb in (self.outline, self.shadow, self.bold, self.italic):
            check_row.addWidget(cb)
        check_row.addStretch(1)
        style_card.addLayout(check_row)

        self.outline_width = SliderRow("Outline width", 0, 12, state.lyrics.outline_width, 1)
        self.outline_width.changed.connect(self._on_outline_width)
        style_card.addWidget(self.outline_width)

        self.position = QComboBox()
        self.position.addItems(["top", "center", "bottom"])
        self.position.setCurrentText(state.lyrics.position)
        self.position.currentTextChanged.connect(self._on_position)
        style_card.addLayout(labeled("Position", self.position))

        self.align = QComboBox()
        self.align.addItems(["left", "center", "right"])
        self.align.setCurrentText(state.lyrics.align)
        self.align.currentTextChanged.connect(self._on_align)
        style_card.addLayout(labeled("Alignment", self.align))

        self.animation = QComboBox()
        self.animation.addItems(["none", "fade", "slide"])
        self.animation.setCurrentText(state.lyrics.animation)
        self.animation.currentTextChanged.connect(self._on_animation)
        style_card.addLayout(labeled("Animation", self.animation))

        self.karaoke = QCheckBox("Karaoke highlight (when timestamps support it)")
        self.karaoke.setChecked(state.lyrics.karaoke)
        self.karaoke.toggled.connect(self._on_karaoke)
        style_card.addWidget(self.karaoke)

        self.highlight_color = ColorPicker(state.lyrics.highlight_color)
        self.highlight_color.changed.connect(self._on_highlight_color)
        style_card.addLayout(labeled("Highlight color", self.highlight_color))

        outer.addWidget(style_card)

        bus.audio_chosen.connect(lambda _p: self._scan(auto=True))

    # ---------------------------------------------------------------- handlers

    def _populate_fonts(self) -> None:
        db = QFontDatabase()
        families = sorted(set(db.families()))
        bundled = []
        fonts_dir = Path(__file__).resolve().parent.parent / "assets" / "fonts"
        if fonts_dir.exists():
            for p in fonts_dir.glob("*.ttf"):
                bundled.append(p.stem)
        all_fonts = sorted(set(bundled + families + ["Inter", "Segoe UI", "Arial"]))
        self.font_combo.addItems(all_fonts)

    def _on_enable(self, checked: bool) -> None:
        self.state.lyrics.enabled = checked
        self.bus.state_changed.emit()

    def _on_static_text(self) -> None:
        self.state.lyrics.static_text = self.static_text.toPlainText()
        self.bus.state_changed.emit()

    def _on_font_family(self, v: str) -> None:
        self.state.lyrics.font_family = v
        self.bus.state_changed.emit()

    def _on_font_path(self, v: str) -> None:
        self.state.lyrics.font_path = v
        self.bus.state_changed.emit()

    def _on_font_size(self, v: int) -> None:
        self.state.lyrics.font_size = v
        self.bus.state_changed.emit()

    def _on_color(self, v: str) -> None:
        self.state.lyrics.color = v
        self.bus.state_changed.emit()

    def _on_outline_color(self, v: str) -> None:
        self.state.lyrics.outline_color = v
        self.bus.state_changed.emit()

    def _on_outline(self, checked: bool) -> None:
        self.state.lyrics.outline = checked
        self.bus.state_changed.emit()

    def _on_shadow(self, checked: bool) -> None:
        self.state.lyrics.shadow = checked
        self.bus.state_changed.emit()

    def _on_bold(self, checked: bool) -> None:
        self.state.lyrics.bold = checked
        self.bus.state_changed.emit()

    def _on_italic(self, checked: bool) -> None:
        self.state.lyrics.italic = checked
        self.bus.state_changed.emit()

    def _on_outline_width(self, v: float) -> None:
        self.state.lyrics.outline_width = int(v)
        self.bus.state_changed.emit()

    def _on_position(self, v: str) -> None:
        self.state.lyrics.position = v
        self.bus.state_changed.emit()

    def _on_align(self, v: str) -> None:
        self.state.lyrics.align = v
        self.bus.state_changed.emit()

    def _on_animation(self, v: str) -> None:
        self.state.lyrics.animation = v
        self.bus.state_changed.emit()

    def _on_karaoke(self, checked: bool) -> None:
        self.state.lyrics.karaoke = checked
        self.bus.state_changed.emit()

    def _on_highlight_color(self, v: str) -> None:
        self.state.lyrics.highlight_color = v
        self.bus.state_changed.emit()

    def _scan(self, auto: bool = False) -> None:
        path = self.state.audio_path
        if not path or not os.path.exists(path):
            if not auto:
                self.status.setText("Pick an audio file in the Input tab first.")
            return
        data = lyrics_extractor.extract(path)
        self._loaded_data = data
        if data.empty:
            self.status.setText("No lyrics found in the file's metadata or sidecar .lrc.")
            self.text_area.setPlainText("")
        else:
            kind = "Synced" if data.synced else "Unsynced"
            self.status.setText(f"{kind} lyrics loaded from {data.source or 'unknown source'} — {len(data.lines)} line(s)")
            self.text_area.setPlainText(self._format_data(data))
        self.bus.state_changed.emit()

    def _import_lrc(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import .lrc file", "", "LRC (*.lrc);;Text (*.txt);;All files (*.*)")
        if not path:
            return
        data = lyrics_extractor.from_lrc_file(path)
        self._loaded_data = data
        kind = "Synced" if data.synced else "Unsynced"
        self.status.setText(f"{kind} lyrics imported from {Path(path).name} — {len(data.lines)} line(s)")
        self.text_area.setPlainText(self._format_data(data))
        self.bus.state_changed.emit()

    def _format_data(self, data: lyrics_extractor.LyricsData) -> str:
        out = []
        for line in data.lines:
            if line.time is not None:
                m = int(line.time // 60)
                s = line.time - m * 60
                out.append(f"[{m:02d}:{s:05.2f}]{line.text}")
            else:
                out.append(line.text)
        return "\n".join(out)

    def current_data(self) -> Optional[lyrics_extractor.LyricsData]:
        # If the user edited the text area we re-parse it on the fly.
        text = self.text_area.toPlainText().strip()
        if not text:
            return self._loaded_data
        return lyrics_extractor.parse_lrc(text)
