# Music Spectrum Lyrics Studio

Aplikasi web **lokal** untuk Windows yang merender video spektrum musik beserta lirik `.lrc` menggunakan **FFmpeg native / portable**. Frontend React + Vite, backend Python FastAPI, render dilakukan oleh proses FFmpeg lokal sehingga ringan dan cepat di laptop spek rendah sekalipun.

> Aplikasi berjalan sepenuhnya di laptop Anda. Tidak ada upload ke server eksternal.

---

## Fitur

- 15 gaya spectrum visualizer (Neon Bar Smooth, Aurora Bars, Soft White Minimal, Fire Pulse, Ocean Wave, Purple Dream, Green Matrix, Gold Luxury, Candy Pop, Thin Cinematic, Bass Heavy, Pastel Smooth, Frequency Classic, Frequency Glow, Rainbow Energy).
- Lirik sinkron `.lrc` dengan offset milidetik, font, ukuran, warna, outline, shadow, opacity, dan efek fade.
- Background gambar/video — single atau slideshow multi-file (urutan, by-name, random) + dark overlay + blur.
- Logo dengan circle mask, posisi (kiri/kanan atas/bawah/atas tengah), ukuran, opacity, margin.
- Render full + preview 10 detik tanpa harus render penuh.
- Batch render dari folder musik + folder lirik + folder background.
- Pilihan resolusi 720p/1080p/9:16/9:16-FHD/1:1, FPS 24/30/60, preset, CRF, default ringan untuk laptop kentang.
- Progress + log realtime via WebSocket.
- Status FFmpeg & tombol install **FFmpeg portable** otomatis ke `tools/ffmpeg/bin`.
- UI putih bersih, otomatis mengikuti tema gelap sistem.
- Drag-and-drop upload, toast, validasi, progress bar, daftar job batch.

---

## Cara pakai (Windows)

1. Pasang prasyarat berikut **sekali saja**:
   - **Python 3.10+** — https://www.python.org/downloads/windows/ (centang *Add to PATH* saat install).
   - **Node.js 18+** — https://nodejs.org/en/download/.
2. Double-click `setup.bat` — script akan:
   - Membuat virtualenv di `backend/.venv` dan install dependensi backend.
   - Install dependensi frontend lalu build produksi (`frontend/dist`).
   - Membuat folder storage dan menyalin `backend/.env.example` → `backend/.env`.
3. Double-click `start.bat` — backend FastAPI dijalankan di `http://localhost:3000` dan browser default akan terbuka otomatis.
4. Jika FFmpeg belum tersedia, buka tab **Dashboard** lalu klik **Install FFmpeg portable**. Hasilnya disimpan ke `tools/ffmpeg/bin/ffmpeg.exe`.
5. Selesai bekerja? Tutup jendela "MSLS Backend" atau jalankan `stop.bat`.

> Setelah setup selesai, aplikasi **bisa berjalan offline** sepenuhnya kecuali saat mengunduh FFmpeg portable.

### FFmpeg portable manual

Jika tidak ingin mengunduh otomatis, ekstrak FFmpeg manual ke folder berikut sehingga binary ada di:

```
music-spectrum-web-local/
└── tools/
    └── ffmpeg/
        └── bin/
            ├── ffmpeg.exe
            └── ffprobe.exe
```

Build yang direkomendasikan: <https://github.com/BtbN/FFmpeg-Builds/releases> (pilih `ffmpeg-master-latest-win64-gpl.zip`).

Anda juga bisa memakai FFmpeg yang sudah terpasang di PATH (system). Aplikasi akan otomatis memilih sumber dengan urutan: `FFMPEG_PATH` env → `tools/ffmpeg/bin/ffmpeg(.exe)` → `ffmpeg` di PATH.

---

## Struktur project

```
music-spectrum-web-local/
├── frontend/                React + Vite
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── backend/                 FastAPI
│   ├── app/
│   │   ├── routers/         endpoint API (health, ffmpeg, render, outputs, ws, assets)
│   │   ├── services/        FFmpeg, LRC, spectrum styles, jobs, render, batch
│   │   ├── models/          schema pydantic
│   │   └── config.py
│   ├── main.py
│   ├── requirements.txt
│   └── .env.example
├── storage/
│   ├── music/
│   ├── lyrics/
│   ├── backgrounds/
│   ├── logos/
│   ├── outputs/             hasil render disimpan di sini
│   └── temp/
├── tools/ffmpeg/            FFmpeg portable (auto-install)
├── setup.bat
├── start.bat
├── stop.bat
└── README.md
```

---

## Endpoint backend

Semua endpoint di-prefix `/api`. WebSocket: `/ws`.

| Method | Path | Keterangan |
| ------ | ---- | ---------- |
| GET    | `/api/health` | Status service + daftar style spectrum. |
| GET    | `/api/ffmpeg/status` | Status FFmpeg (path, source, version). |
| POST   | `/api/ffmpeg/install` | Unduh FFmpeg portable ke `tools/ffmpeg`. |
| GET    | `/api/assets/{category}` | List file di storage (music/lyrics/backgrounds/logos). |
| POST   | `/api/assets/{category}` | Upload file ke storage (multipart). |
| DELETE | `/api/assets/{category}/{name}` | Hapus file di storage. |
| POST   | `/api/render/preview` | Mulai render preview 10 detik. |
| POST   | `/api/render/full` | Mulai render full video. |
| POST   | `/api/render/batch` | Mulai batch render dari folder. |
| GET    | `/api/render/jobs` | Daftar semua job. |
| GET    | `/api/render/{job_id}/status` | Status job. |
| GET    | `/api/render/{job_id}/log` | Log FFmpeg untuk job. |
| GET    | `/api/render/{job_id}/download` | Unduh output. |
| POST   | `/api/render/{job_id}/cancel` | Batalkan job berjalan. |
| GET    | `/api/outputs` | Daftar file output. |
| DELETE | `/api/outputs/{filename}` | Hapus output. |
| POST   | `/api/outputs/open-folder` | Buka folder output di Explorer. |
| WS     | `/ws` | Stream realtime job progress + log. |

---

## Mode batch

Pilih folder berisi musik, lirik, dan background. Aplikasi akan:

1. Mencocokkan setiap file musik dengan file lirik yang **nama dasarnya sama** (`lagu1.mp3` ↔ `lagu1.lrc`).
2. Memilih background sesuai mode:
   - **Sequence** — urut file di folder background.
   - **By name** — nama background sama dengan nama musik.
   - **Random** — diacak.
3. Untuk *sequence* / *random* tersedia opsi **multi background** (jadi slideshow per video).
4. File musik tanpa pasangan lirik **dilewati** dan dicatat ke log.
5. Output disimpan ke `storage/outputs` dengan nama dasar mengikuti nama musik.

Status setiap item: `pending`, `rendering`, `done`, `failed`, `skipped`, `cancelled`.

---

## Tips performa untuk laptop kentang

- Pilih resolusi `1280x720` + FPS `30`.
- Pakai preset `ultrafast` atau `veryfast`, CRF `24-28`.
- Matikan *blur* atau atur ke 0 untuk render lebih cepat.
- Gunakan satu background statis (jpg) untuk hasil paling ringan.
- Tutup aplikasi lain yang berat saat render.

---

## Pengembangan (developer)

Backend dev:
```
cd backend
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Frontend dev:
```
cd frontend
npm install
npm run dev          # http://localhost:3000 dengan proxy ke backend :8000
```

---

## Catatan

- FFmpeg.wasm tidak digunakan — render final selalu memakai FFmpeg native/portable.
- Semua file disimpan lokal di folder project, tidak dikirim ke internet.
- Aplikasi diuji dengan FFmpeg ≥ 5.x. Versi lama mungkin tidak mendukung beberapa filter (`showcqt`, `showfreqs`).

Selamat berkreasi!
