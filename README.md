# ASMR Seamless Loop Maker

Aplikasi Python + Streamlit untuk mengubah video pendek (misal 8 detik) menjadi
video ASMR berdurasi panjang (1 jam, 3 jam, dst) dengan loop yang halus.
Aplikasi mencari sendiri titik loop terbaik berdasarkan analisis frame, lalu
menyambung pengulangan dengan **crossfade visual** dan **crossfade audio**
sehingga tidak ada potongan kasar.

## Fitur

- Upload video MP4 / MOV / MKV (single atau batch).
- Analisis otomatis titik loop terbaik:
  - Signature per-frame (thumbnail grayscale + histogram HSV).
  - Skor gabungan *pixel difference* + *histogram correlation*.
  - Minimum panjang segmen loop bisa diatur.
- Looping video sampai durasi target dengan crossfade linear antar pengulangan.
- Looping audio dengan crossfade `alpha` linear (anti-klik) memakai `soundfile`.
- Output MP4 final dengan codec H.264 + audio AAC, `+faststart`.
- UI Streamlit dengan progress bar, ringkasan analisis, preview, dan tombol
  download (termasuk download semua hasil batch sebagai ZIP).
- CLI untuk single file maupun batch processing folder.

## Struktur file

```
.
├── app.py                 # Streamlit UI (single + batch)
├── asmr_loop_maker.py     # Engine + CLI
├── requirements.txt
└── README.md
```

## Instalasi

### 1. Install FFmpeg

FFmpeg wajib ada di `PATH` karena dipakai untuk encoding video (H.264),
encoding audio (AAC), ekstraksi audio, dan muxing.

- **Ubuntu / Debian**

  ```bash
  sudo apt update
  sudo apt install -y ffmpeg
  ```

- **macOS (Homebrew)**

  ```bash
  brew install ffmpeg
  ```

- **Windows**

  Download build resmi dari <https://www.gyan.dev/ffmpeg/builds/> atau
  <https://www.ffmpeg.org/download.html>, ekstrak, lalu tambahkan folder `bin`
  ke environment variable `PATH`.

Verifikasi instalasi:

```bash
ffmpeg -version
```

### 2. Install dependency Python

Disarankan memakai virtual environment.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

Dependency:

- `opencv-python` – membaca frame video & analisis.
- `numpy` – perhitungan signature, pixel diff, crossfade.
- `streamlit` – UI web.
- `soundfile` – baca/tulis WAV untuk crossfade audio.

> Catatan: di beberapa distro Linux, `soundfile` butuh `libsndfile` di sistem.
> Jika ada error, install dengan `sudo apt install libsndfile1`.

## Menjalankan aplikasi

### Mode UI (Streamlit)

```bash
streamlit run app.py
```

Lalu buka URL yang ditampilkan (biasanya `http://localhost:8501`).

Di UI kamu bisa:

1. Pilih **Single video** atau **Batch processing** di sidebar.
2. Upload satu atau beberapa video.
3. Atur durasi output (jam), durasi crossfade (detik), dan minimal panjang
   segmen loop.
4. Klik **Buat Video ASMR**, tunggu progress, lalu preview & download MP4
   hasil. Pada mode batch tersedia tombol download ZIP berisi semua hasil.

### Mode CLI

Single file:

```bash
python asmr_loop_maker.py path/to/clip.mp4 \
    --output path/to/output.mp4 \
    --hours 1 \
    --crossfade 0.5 \
    --min-segment 2.0
```

Banyak file sekaligus (output jadi folder):

```bash
python asmr_loop_maker.py clip1.mp4 clip2.mp4 clip3.mp4 \
    --output ./asmr_outputs \
    --hours 3 \
    --crossfade 0.75
```

Batch dari satu folder (rekursif):

```bash
python asmr_loop_maker.py \
    --batch-dir ./clips \
    --output ./asmr_outputs \
    --hours 1 \
    --crossfade 0.5
```

Opsi penting:

| Opsi | Default | Keterangan |
| --- | --- | --- |
| `--hours` | `1.0` | Durasi output dalam jam. |
| `--crossfade` | `0.5` | Durasi crossfade visual + audio (detik). |
| `--min-segment` | `2.0` | Panjang minimum segmen loop (detik). |
| `--signature-size` | `96` | Ukuran thumbnail signature frame. |
| `--batch-dir` | – | Folder berisi video untuk diproses semua. |

Untuk help lengkap: `python asmr_loop_maker.py --help`.

## Cara kerja aplikasi

1. **Baca frame** (`read_video_frames`) — semua frame didekode via OpenCV.
2. **Frame signature** (`frame_signature`) — setiap frame di-resize ke
   `signature_size x signature_size`, diubah ke grayscale ternormalisasi, dan
   diberi histogram HSV (32 x 32 bin) yang dinormalisasi.
3. **Skor kemiripan** (`compare_signatures`) — kombinasi:
   - `mean(|gray_a - gray_b|)` (60% bobot).
   - `(1 - corr(hist_a, hist_b)) / 2` dari `cv2.compareHist` dengan metrik
     `HISTCMP_CORREL` (40% bobot).
4. **Cari titik loop terbaik** (`find_best_loop_points`) — untuk setiap calon
   frame awal `s`, dihitung skor terhadap semua frame `e` dengan
   `e - s >= min_segment_seconds * fps`. Pasangan dengan skor terkecil yang
   menang. Implementasinya vektorial (NumPy) sehingga cukup cepat.
5. **Encoding video loop** (`make_looped_video`) — segmen `frames[s..e]`
   ditulis ke FFmpeg sebagai raw `bgr24`. Setiap akhir pengulangan, `K` frame
   terakhir di-blend dengan `K` frame pertama pengulangan berikutnya:

   ```
   frame_output = frame_akhir * (1 - alpha) + frame_awal * alpha
   ```

6. **Audio loop** (`extract_audio` + `make_looped_audio`) — segmen audio
   diekstrak via FFmpeg, lalu pada setiap sambungan `K` sampel terakhir
   di-mix linear dengan `K` sampel awal:

   ```
   sample_output = sample_akhir * (1 - alpha) + sample_awal * alpha
   ```

7. **Mux** (`mux_video_audio`) — video loop dan audio loop digabung dengan
   FFmpeg ke MP4 (H.264 + AAC) dengan `+faststart` agar siap streaming.

Pipeline lengkap dijalankan oleh `process_video()`.

## Tips & catatan

- Video sumber sebaiknya pendek (beberapa detik) supaya semua frame muat di
  memori. Loop yang efektif untuk ASMR biasanya 2–6 detik.
- Output 3+ jam akan menghasilkan file besar; gunakan codec hemat / atur `crf`
  jika perlu (lihat `_spawn_video_encoder` di `asmr_loop_maker.py`).
- Bila input tidak punya audio stream, output akan tetap dibuat namun silent.
- Jika analisis selalu memilih start=0 dan end=akhir, coba naikkan
  `--min-segment` atau perpanjang video sumber agar variasi loop lebih banyak.
