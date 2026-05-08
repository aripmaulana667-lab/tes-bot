# ClipFlow Studio

> AI-Powered Smart Video Clipper

ClipFlow Studio adalah aplikasi desktop profesional yang otomatis menganalisis
video YouTube, mendeteksi bagian paling menarik menggunakan AI gratis/open-source,
memotong clip pendek, menambahkan subtitle khas clipper, lalu mengekspor video
yang siap diunggah ke **TikTok**, **Instagram Reels**, dan **YouTube Shorts**.

> **Catatan legal**: Aplikasi ini hanya untuk video yang Anda miliki haknya atau
> video yang memang diizinkan untuk diproses. Aplikasi tidak melakukan bypass
> proteksi, login, DRM, konten private, atau batasan platform.

---

## Fitur Utama

- Input URL YouTube + validasi (Python utama, Deno helper sebagai fallback).
- Download otomatis dengan **yt-dlp**, dengan auto-update + Deno fallback log.
- Ekstraksi audio dan transkripsi gratis dengan **faster-whisper**.
- Deteksi highlight berdasarkan kalimat emosional, punchline, pertanyaan kunci,
  perubahan topik, keyword penting, kalimat pendek yang kuat, dan momen
  ber-engagement tinggi.
- Generate clip otomatis 15s / 30s / 45s / 60s / custom.
- Subtitle khas clipper: teks besar, putih, outline hitam, highlight kata
  penting, line-break otomatis, animasi sederhana.
- Export ke TikTok / Reels / Shorts / Custom dengan preset aspect ratio dan
  resolusi (720p, 1080p, 2K).
- Crop mode: center, fit dengan blurred background, manual, dan auto-face/object
  saat library wajah tersedia.
- Quality tier: Draft, Standard, High, Ultra/2K.
- Riwayat project tersimpan di **SQLite**.
- Online installer untuk FFmpeg & Deno (Windows), serta repair package Python.

## Tech Stack

| Komponen        | Teknologi                                     |
|-----------------|-----------------------------------------------|
| Bahasa          | Python 3.11+                                  |
| GUI             | CustomTkinter                                 |
| Downloader      | yt-dlp                                        |
| Helper / Fallback | Deno + TypeScript script lokal              |
| Video Processing| FFmpeg (lokal di `tools/ffmpeg/` atau global) |
| Transkripsi     | faster-whisper (open-source, lokal)           |
| Highlight AI    | sentence-transformers + heuristik NLP lokal   |
| Database        | SQLite                                        |

> **Tidak menggunakan** API berbayar (OpenAI, Gemini, Claude, dll.).

---

## Instalasi (Windows)

```bat
git clone https://github.com/aripmaulana667-lab/tes-bot.git
cd tes-bot\clipflow_studio
setup.bat
```

`setup.bat` akan:

1. Membuat `venv/`.
2. Upgrade pip.
3. Install dependensi dari `requirements.txt`.
4. Membuat folder `outputs/`, `temp/`, `assets/`, `tools/ffmpeg/`, `tools/deno/`.
5. Mengecek ketersediaan FFmpeg dan Deno (global maupun lokal).

### Linux / macOS

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python run.py
```

> Pada Linux/macOS, install FFmpeg dan Deno melalui package manager bawaan
> (mis. `apt install ffmpeg`, `brew install deno`). Online installer di dalam
> aplikasi saat ini hanya men-download binary resmi untuk Windows.

---

## Menjalankan Aplikasi

```bat
run.bat
```

atau

```bash
python run.py
```

Aplikasi akan menampilkan splash screen yang melaporkan status dependency,
lalu masuk ke jendela utama dengan sidebar:

- **Input URL**
- **Analyze Clips**
- **Preview / Select Clips**
- **Subtitle Settings**
- **Export Settings**
- **Dependency Status**
- **History**

---

## Install FFmpeg Otomatis

Buka menu **Dependency Status** → klik **Install FFmpeg Online**.

- Aplikasi akan men-download build FFmpeg resmi (Windows) ke
  `tools/ffmpeg/`.
- Path FFmpeg lokal disimpan ke `app/utils/config.py` (file `config.json`).
- Tidak perlu mengubah `PATH` Windows.

## Install Deno Otomatis

Buka menu **Dependency Status** → klik **Install Deno Online**.

- Aplikasi men-download Deno resmi ke `tools/deno/deno.exe`.
- Path Deno disimpan ke konfigurasi.
- Aplikasi akan menggunakan Deno lokal terlebih dahulu.

## Apa Fungsi Deno?

Deno **bukan** downloader utama. Deno hanya menjadi helper/fallback untuk:

- Validasi URL ringan (`app/helpers/deno/validate_url.ts`).
- Mengambil metadata video sederhana (`app/helpers/deno/fetch_metadata.ts`).
- Menyimpan log error jika yt-dlp gagal.

yt-dlp tetap downloader utama untuk semua media.

---

## Cek Dependency

Halaman **Dependency Status** menampilkan status semua dependency:

- Python, pip, FFmpeg, Deno, yt-dlp, faster-whisper, sentence-transformers,
  CustomTkinter, SQLite, Git (opsional).
- Tombol Check / Install / Repair tiap dependency.
- Tombol global: Check All Dependencies, Install Missing Dependencies,
  Open Tools Folder, Open Config Folder, Check Deno, Install Deno Online,
  Repair Deno.

Semua proses install berjalan di background thread sehingga GUI tidak freeze.

---

## Cara Export Video

1. Pilih clip yang ingin diekspor.
2. Pilih **platform** (TikTok / Reels / Shorts / Custom).
3. Pilih **aspect ratio**, **resolusi**, **FPS**, dan **crop mode**.
4. Pilih **quality** (Draft / Standard / High / Ultra).
5. Klik **Export Selected Clips**.
6. File hasil tersimpan di folder `outputs/`.

---

## Struktur Project

```
clipflow_studio/
├── app/
│   ├── main.py
│   ├── helpers/
│   │   └── deno/
│   │       ├── validate_url.ts
│   │       └── fetch_metadata.ts
│   ├── ui/
│   │   ├── main_window.py
│   │   ├── dependency_page.py
│   │   └── styles.py
│   ├── core/
│   │   ├── downloader.py
│   │   ├── deno_helper.py
│   │   ├── transcriber.py
│   │   ├── highlight_detector.py
│   │   ├── clip_generator.py
│   │   ├── subtitle_renderer.py
│   │   ├── export_presets.py
│   │   ├── exporter.py
│   │   └── dependency_manager.py
│   ├── database/
│   │   └── db.py
│   └── utils/
│       ├── config.py
│       └── logger.py
├── assets/
├── outputs/
├── temp/
├── tools/
│   ├── ffmpeg/
│   └── deno/
├── requirements.txt
├── README.md
├── setup.bat
├── run.bat
└── run.py
```

---

## Troubleshooting Umum

| Masalah                          | Solusi                                                                |
|----------------------------------|-----------------------------------------------------------------------|
| `python` tidak dikenal           | Install Python 3.11+ dari python.org dan centang **Add to PATH**.     |
| `pip install` gagal              | Pastikan koneksi internet stabil; coba lagi `pip install -r requirements.txt`. |
| FFmpeg tidak ditemukan           | Buka Dependency Status → **Install FFmpeg Online**.                   |
| Deno tidak ditemukan             | Buka Dependency Status → **Install Deno Online**.                     |
| yt-dlp gagal download            | Klik **Update yt-dlp** atau coba lagi; cek log error di Deno fallback.|
| Antivirus memblokir file ZIP     | Whitelist folder `tools/` pada antivirus.                              |
| Permission error saat extract    | Jalankan ulang aplikasi sebagai administrator.                        |
| Transkripsi lambat               | Pilih model whisper lebih kecil (`base`/`small`) di Settings.         |
| Export gagal                     | Periksa FFmpeg terinstall dan log di `app/utils/logger.py` (file `clipflow.log`). |

---

## Lisensi & Kepatuhan

Aplikasi hanya boleh digunakan untuk video yang Anda miliki haknya atau yang
memiliki izin pemrosesan. Tidak boleh digunakan untuk bypass proteksi, login,
DRM, konten private, atau batasan platform.
