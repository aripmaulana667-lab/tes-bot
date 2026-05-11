# Music Spectrum Lyric Video Maker

A modern, lightweight desktop app for Windows (and Linux as a bonus) that
auto-generates **music spectrum + lyrics videos** from a single song or an
entire folder. Built with Python + PySide6 and a thin FFmpeg pipeline so it
runs comfortably on low-end laptops.

## Highlights

- 8 tabs for an editor-style workflow: **Input**, **Background**, **Logo**,
  **Lyrics**, **Spectrum Style**, **Render Settings**, **Preview**, **Log**.
- **10 spectrum visualizer styles** — Classic Bars, Rounded Bars, Neon Glow,
  Circular, Waveform Line, Mountain Wave, Particle, Mirror Bars, Radial
  Pulse and Minimal Elegant.
- Reads **synced + unsynced lyrics** from audio metadata (USLT/SYLT, FLAC,
  M4A, OGG) or sidecar `.lrc` files, with automatic cleaning that strips
  `[...]` and `(...)` while keeping timestamps and line order untouched.
- Karaoke-style highlight when timestamps are available; lyrics never appear
  earlier than the timestamp written in the file.
- Background can be a solid color, gradient, single image, single video, or
  **multiple files** that rotate through the song (manual list, folder by
  order, or folder by random) with ken-burns and fade transitions.
- **Batch render** an entire folder — three background-pairing modes
  (`by order`, `by matching name`, `random`).
- Auto-detect hardware encoders (NVIDIA NVENC, Intel QSV, AMD AMF) and fall
  back to `libx264` on potato PCs.
- Built-in **Install FFmpeg Online** button — no manual setup required.
- Persistent config in `config.json`, full log panel with save/clear.

## 1. Install

### Windows (recommended path)

1. Install Python 3.10+ from <https://python.org/downloads/> (tick *Add
   Python to PATH* during the installer).
2. Double-click `setup.bat`. It creates a `.venv`, installs the
   dependencies and reports whether FFmpeg is available.
3. Launch with `run.bat`.
4. If FFmpeg is missing, open the **Render** tab and click
   **Install FFmpeg Online** — it downloads a static FFmpeg build from
   <https://github.com/BtbN/FFmpeg-Builds> and configures the path for you.

### Manual install (any OS)

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m app.main
```

## 2. Run

- **Windows**: `run.bat`
- **Anywhere**: activate the venv, then `python -m app.main`

## 3. Using the app

1. **Input** tab — pick a single song or a folder of songs (MP3, WAV,
   FLAC, M4A, AAC). Pick an output folder.
2. **Background** tab — choose color / gradient / image / video, or enable
   **multi-background** to rotate through several files.
3. **Logo** tab — optional brand overlay with size, position, opacity and
   circle-crop.
4. **Lyrics** tab — auto-load lyrics from the song, import a `.lrc`, or
   type/paste your own. Customize font, color, outline, position and
   karaoke highlight.
5. **Spectrum** tab — pick one of the 10 visualizer styles, set color,
   gradient, glow, sensitivity, smoothness, bass boost, bars, FPS, etc.
6. **Render** tab — resolution, FPS, quality, encoder. Hit **Render**. Use
   one of the presets for low-end machines.
7. **Preview** tab — render a single low-resolution still frame at any
   timestamp to sanity-check the look.
8. **Log** tab — full timestamped console; save it for debugging.

### 3.1 Rendering one song

1. Input → "Single file" → pick the song.
2. Tune Background / Lyrics / Spectrum to taste.
3. Render tab → choose preset (e.g. *Balanced 1080p*) → press **Render**.
4. Output `.mp4` is written to your Output folder.

### 3.2 Rendering a batch

1. Input → "Batch (folder)" → pick the folder of songs.
2. Optionally point the **Background folder** field at a folder of images
   and choose a pairing mode:
   - **By order** — sort the backgrounds by filename and walk them in
     lockstep with the audio files.
   - **By matching name** — `song.mp3` pairs with `song.jpg` or
     `song.mp4` etc.
   - **Random** — random pick per song.
3. Render tab → **Render**.

### 3.3 Changing the spectrum style

Spectrum tab → "Style" dropdown — pick one of ten styles. Each style
inherits all the colour, sensitivity, smoothness, height/width/position
options. Use **Preview** to verify the look.

### 3.4 Multi-background in a single video

Background tab → enable **Multi-background mode**. Pick:

- **Manually picked files** — explicit list of files.
- **Folder — by order** — pull from a folder in name order.
- **Folder — random** — pick randomly each interval.

Set "seconds per background" to control rotation pace; "Transition" to
`fade` for smooth crossfades or `cut` for hard cuts. "Ken Burns" adds a
subtle zoom/pan to still images so they don't look static.

### 3.5 Troubleshooting FFmpeg

- **Render tab → FFmpeg → "Install FFmpeg Online"** downloads a current
  static build (BtbN on Windows, johnvansickle on Linux) into
  `app/assets/ffmpeg/`.
- **Pick path…** lets you point the app at an existing FFmpeg binary.
- **Test** runs `ffmpeg -version` to confirm it works and prints the
  detected hardware encoders (NVENC / QSV / AMF).
- **Reset path** clears the saved path so the app re-detects from `PATH`.

If you get `ffmpeg exited with code …` during render, open the Log tab —
the relevant ffmpeg stderr lines are appended live.

## 4. Folder layout

```
music-spectrum-lyric-video-maker/
├── app/
│   ├── main.py
│   ├── gui/        # PySide6 GUI: one file per tab
│   ├── core/       # render engine, ffmpeg manager, lyrics, spectrum…
│   ├── styles/     # QSS + Qt palette
│   └── assets/     # fonts, icons, optional bundled ffmpeg
├── output/         # generated mp4 files
├── temp/           # scratch space
├── logs/           # saved render logs
├── setup.bat
├── run.bat
├── requirements.txt
└── config.json     # persisted preferences
```

## 5. Performance tips for low-end PCs

- Use the **Fast 720p** preset on the Render tab.
- Lower the number of spectrum bars to ~48.
- Disable "Glow" on the Spectrum tab for the cheapest render.
- For batch render, keep backgrounds as images — videos are slower.
- Hardware encoders give the biggest speedup; if your GPU supports NVENC /
  QSV / AMF, the encoder dropdown will auto-select it.

## 6. License & credits

This project is offered as-is for personal use. FFmpeg downloads come from
the [BtbN/FFmpeg-Builds](https://github.com/BtbN/FFmpeg-Builds) (Windows)
and [johnvansickle.com](https://johnvansickle.com/ffmpeg/) (Linux) static
builds — see their respective licences before redistribution.
