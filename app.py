"""Streamlit UI for the ASMR Seamless Loop Maker.

Supports two modes:

* **Single video** – upload one clip and turn it into a long ASMR loop.
* **Batch processing** – upload many clips at once and process them with the
  same settings; each result gets its own preview and download button.
"""

from __future__ import annotations

import io
import os
import shutil
import tempfile
import time
import zipfile
from pathlib import Path
from typing import List, Optional

import streamlit as st

from asmr_loop_maker import ProcessResult, process_video

st.set_page_config(
    page_title="ASMR Seamless Loop Maker",
    page_icon="🎧",
    layout="centered",
)

st.title("ASMR Seamless Loop Maker")
st.caption(
    "Ubah video pendek menjadi loop ASMR berdurasi panjang dengan transisi visual "
    "dan audio yang halus. Mendukung mode single & batch."
)


def _format_seconds(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds - hours * 3600 - minutes * 60
    if hours:
        return f"{hours:d}j {minutes:02d}m {secs:05.2f}d"
    if minutes:
        return f"{minutes:d}m {secs:05.2f}d"
    return f"{secs:.2f}d"


def _build_zip(results: List[ProcessResult]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for r in results:
            arcname = Path(r.output_path).name
            zf.write(r.output_path, arcname=arcname)
    return buf.getvalue()


with st.sidebar:
    st.header("Parameter")
    mode = st.radio(
        "Mode",
        ["Single video", "Batch processing"],
        help="Pilih mode untuk memproses satu file atau banyak file sekaligus.",
    )
    output_hours = st.number_input(
        "Durasi output (jam)",
        min_value=0.05,
        max_value=12.0,
        value=1.0,
        step=0.05,
        help="Durasi total video ASMR yang akan dihasilkan.",
    )
    crossfade_seconds = st.number_input(
        "Crossfade (detik)",
        min_value=0.0,
        max_value=10.0,
        value=0.5,
        step=0.1,
        help="Lama transisi blending antar pengulangan loop (video + audio).",
    )
    min_segment_seconds = st.number_input(
        "Minimal panjang segmen loop (detik)",
        min_value=0.5,
        max_value=60.0,
        value=2.0,
        step=0.5,
        help="Jarak minimum antara frame awal dan frame akhir kandidat loop.",
    )
    signature_size = st.number_input(
        "Signature size (px)",
        min_value=32,
        max_value=256,
        value=96,
        step=16,
        help="Ukuran thumbnail untuk analisis kemiripan frame.",
    )

st.markdown(
    "**Format yang didukung:** MP4, MOV, MKV. Output selalu MP4 (H.264 + AAC)."
)

accept_multiple = mode == "Batch processing"
uploaded = st.file_uploader(
    "Upload video pendek" + (" (boleh banyak)" if accept_multiple else ""),
    type=["mp4", "mov", "mkv"],
    accept_multiple_files=accept_multiple,
)

if accept_multiple:
    files = uploaded or []
else:
    files = [uploaded] if uploaded is not None else []

start_disabled = len(files) == 0
go = st.button("Buat Video ASMR", type="primary", disabled=start_disabled)

if "asmr_results" not in st.session_state:
    st.session_state.asmr_results = []
if "asmr_work_dir" not in st.session_state:
    st.session_state.asmr_work_dir = None


def _reset_previous_work() -> None:
    old = st.session_state.asmr_work_dir
    if old and os.path.isdir(old):
        shutil.rmtree(old, ignore_errors=True)
    st.session_state.asmr_work_dir = None
    st.session_state.asmr_results = []


if go and files:
    _reset_previous_work()
    work_root = tempfile.mkdtemp(prefix="asmr_streamlit_")
    st.session_state.asmr_work_dir = work_root

    overall_status = st.empty()
    overall_progress = st.progress(0.0, text="Mulai…")
    total = len(files)
    results: List[ProcessResult] = []

    for idx, uploaded_file in enumerate(files, start=1):
        st.markdown(f"### {idx}/{total} — `{uploaded_file.name}`")
        per_status = st.empty()
        per_progress = st.progress(0.0, text="Mulai…")

        input_path = os.path.join(work_root, f"in_{idx}_{uploaded_file.name}")
        with open(input_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        output_name = Path(uploaded_file.name).stem + "_asmr_loop.mp4"
        output_path = os.path.join(work_root, output_name)

        def _on_progress(p: float, msg: str, _bar=per_progress, _status=per_status) -> None:
            pct = max(0.0, min(1.0, p))
            _bar.progress(pct, text=f"{msg} ({pct * 100:.1f}%)")
            _status.info(msg)

        try:
            t0 = time.time()
            result = process_video(
                input_path=input_path,
                output_path=output_path,
                output_hours=float(output_hours),
                crossfade_seconds=float(crossfade_seconds),
                min_segment_seconds=float(min_segment_seconds),
                signature_size=int(signature_size),
                on_progress=_on_progress,
            )
            elapsed = time.time() - t0
        except Exception as exc:  # noqa: BLE001 - surface per-file failures to UI
            per_progress.empty()
            per_status.empty()
            st.error(f"Gagal memproses `{uploaded_file.name}`: {exc}")
            continue

        per_progress.progress(1.0, text="Selesai")
        per_status.success(f"Selesai dalam {elapsed:.1f} detik.")
        a = result.analysis
        st.markdown(
            "\n".join(
                [
                    f"- **Start loop:** {a.start_seconds:.3f} d ({a.start_frame} frame)",
                    f"- **End loop:** {a.end_seconds:.3f} d ({a.end_frame} frame)",
                    f"- **Durasi loop efektif:** {_format_seconds(a.duration_seconds)} @ {a.fps:.2f} fps",
                    f"- **Skor kemulusan** (lebih kecil = lebih halus): `{a.score:.4f}`",
                    f"- **Pixel diff:** `{a.pixel_diff:.4f}` | **Hist correlation:** `{a.hist_correlation:.4f}`",
                    f"- **Audio:** {'tersedia' if result.has_audio else 'tidak ada (output silent)'}",
                ]
            )
        )

        if os.path.exists(output_path):
            try:
                st.video(output_path)
            except Exception:  # noqa: BLE001 - preview is best-effort
                st.info("Preview tidak tersedia di browser, gunakan tombol download.")
            with open(output_path, "rb") as f:
                st.download_button(
                    label=f"Download {output_name}",
                    data=f.read(),
                    file_name=output_name,
                    mime="video/mp4",
                    key=f"download_{idx}",
                )
        results.append(result)
        overall_progress.progress(idx / total, text=f"{idx}/{total} selesai")

    overall_progress.progress(1.0, text="Semua file selesai")
    if results:
        overall_status.success(f"Selesai memproses {len(results)} dari {total} video.")
    else:
        overall_status.error("Tidak ada video yang berhasil diproses.")
    st.session_state.asmr_results = results

if st.session_state.asmr_results and len(st.session_state.asmr_results) > 1:
    st.markdown("---")
    st.subheader("Batch download")
    try:
        zip_bytes = _build_zip(st.session_state.asmr_results)
        st.download_button(
            label=f"Download semua ({len(st.session_state.asmr_results)} file) sebagai ZIP",
            data=zip_bytes,
            file_name="asmr_loops.zip",
            mime="application/zip",
            key="download_all_zip",
        )
    except FileNotFoundError:
        st.info("File output sudah dihapus dari sesi ini. Jalankan ulang untuk men-download ZIP.")

with st.expander("Cara kerja singkat"):
    st.markdown(
        """
        1. Aplikasi membaca seluruh frame video upload menggunakan OpenCV.
        2. Setiap frame diberi *signature* berupa thumbnail grayscale + histogram HSV.
        3. Algoritma membandingkan semua pasangan frame (dengan jarak minimal sesuai
           pengaturan) untuk mencari pasangan paling mirip → titik loop terbaik.
        4. Segmen loop di-encode ulang berkali-kali sampai mencapai durasi target.
           Antar pengulangan, frame ekor dan frame kepala di-blend (`α` linear).
        5. Audio loop diproses dengan prinsip yang sama menggunakan `soundfile`.
        6. Video dan audio digabungkan dengan FFmpeg (H.264 + AAC, faststart).
        """
    )
