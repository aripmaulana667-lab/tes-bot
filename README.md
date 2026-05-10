# LiveStream Server + Controller

Aplikasi Python untuk sistem live streaming berbasis Windows VPS/RDP dengan
laptop sebagai controller. Terdiri dari dua bagian:

- **`LiveStreamServer/`** — service yang dijalankan di VPS Windows. Menerima
  upload video, mengelola akun RTMP, dan menjalankan banyak proses FFmpeg
  sekaligus untuk multi-live ke YouTube / Facebook / TikTok / Custom RTMP.
- **`LiveStreamController/`** — aplikasi desktop PySide6 yang dijalankan di
  laptop untuk mengontrol server: dashboard, video gallery, account
  manager, multi-live manager, dan log viewer.

```
LiveStreamServer/                 LiveStreamController/
├── server_app.py                 ├── controller_app.py
├── requirements.txt              ├── requirements.txt
├── config.example.json           ├── config.example.json
├── app/                          ├── app/
│   ├── main.py (FastAPI)         │   ├── ui/main_window.py
│   ├── api/{auth,server,         │   ├── ui/pages/{dashboard,videos,
│   │       videos,accounts,      │   │   accounts,streams,installer,
│   │       streams,system}.py    │   │   logs,settings}.py
│   ├── services/{ffmpeg_         │   ├── ui/widgets/{sidebar,
│   │   installer,ffmpeg_         │   │   stat_card,styles}.py
│   │   runner,stream_manager,    │   ├── api/client.py
│   │   video_service,            │   └── utils/{config,threads}.py
│   │   system_service}.py        │
│   ├── models.py / schemas.py    │
│   ├── auth.py / database.py     │
│   ├── config.py                 │
│   └── utils/{security,paths,    │
│       logging,bootstrap}.py     │
├── videos/  (uploaded media)     │
├── logs/    (per-stream logs)    │
└── bin/     (FFmpeg target)      │
```

---

## 1. Quick start

Cara termudah di Windows: dobel-klik `setup.bat` (sekali) lalu `run.bat` (tiap
kali mau menjalankan) di masing-masing folder.

### Server (Windows VPS / RDP)

1. Install Python 3.10+ dari https://python.org (centang **"Add Python to PATH"**).
2. Salin folder `LiveStreamServer/` ke VPS, dobel-klik `setup.bat` — script
   akan membuat `.venv` dan `pip install -r requirements.txt` otomatis.
3. Dobel-klik `run.bat` untuk start server. Akan muncul **jendela GUI**
   yang menampilkan Host/IP, Port, Username, Password, dan API Token
   lengkap dengan tombol **Copy** di tiap field — tinggal di-copy ke
   controller laptop.

GUI server juga punya:

- Tombol **Show / Hide** untuk password & API token.
- Tombol **Copy ALL** untuk menyalin semua info koneksi sekaligus.
- Tombol **Open /docs** untuk membuka OpenAPI viewer di browser VPS.
- Tombol **Refresh IPs** kalau IP LAN berubah.
- Server log live di bagian bawah jendela.
- Status FFmpeg (installed / belum) ditampilkan di tengah.

Untuk mode tanpa GUI (mis. server berjalan sebagai layanan), pakai:

```bat
python server_app.py --console
```

Atau full command line setup:

```bat
cd LiveStreamServer
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python server_app.py            :: jendela GUI
:: atau
python server_app.py --console  :: tanpa GUI
```

Pada pertama kali dijalankan:

- Folder `C:\LiveStreamServer\{videos,logs,bin}` dibuat otomatis.
- File `config.json` di sebelah `server_app.py` di-generate dengan **API
  token acak** — token ini perlu dipakai dari controller.
- Default user: `admin` / `admin123` (bisa diubah lewat `config.json`).
- Server jalan di `http://0.0.0.0:8765` dan mengekspos OpenAPI di `/docs`.

### Controller (Laptop)

1. Install Python 3.10+ di laptop (centang **"Add Python to PATH"**).
2. Dobel-klik `LiveStreamController\setup.bat` (sekali) untuk install dependency.
3. Dobel-klik `LiveStreamController\run.bat` untuk membuka aplikasi controller.

Atau lewat command line:

```bat
cd LiveStreamController
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python controller_app.py
```

Saat pertama dibuka, controller menampilkan dialog **"Hubungkan ke Server"**:
isi IP/host VPS, port (default `8765`), dan masukkan API token (atau
username `admin` + password `admin123`).

Tip: buka GUI server di VPS, klik tombol **Copy ALL**, paste ke chat /
notepad di laptop, lalu salin masing-masing ke field di controller.

---

## 2. Membuka port di Windows VPS

Aplikasi memakai port TCP `8765` secara default. Pilih salah satu cara
berikut (paling atas paling mudah):

**Cara 1 — tombol di GUI server:** klik **"Buka Port Firewall"** di GUI
server. Akan muncul prompt UAC, klik *Yes*. Selesai.

**Cara 2 — dobel-klik `open-firewall.bat`:** file ada di folder
`LiveStreamServer/`. Auto minta UAC, otomatis bikin aturan firewall.

**Cara 3 — PowerShell (Administrator) manual:**

```powershell
New-NetFirewallRule -DisplayName "LiveStream API" -Direction Inbound `
    -Protocol TCP -LocalPort 8765 -Action Allow
```

Disarankan membatasi `RemoteAddress` ke IP laptop kamu agar lebih aman, atau
menempatkan server di balik reverse-proxy + HTTPS (mis. Caddy / Nginx).

### Tidak bisa connect dari laptop?

Cek hal-hal berikut secara berurutan:

1. **GUI server kelihatan running?** Status di pojok kanan atas harus
   `● running on :8765` (hijau). Kalau merah / abu-abu, klik *Start Server*.
2. **IP yang dipakai sudah benar?** Di GUI server, dropdown Host / IP
   menampilkan semua IP yang dikenal VPS. Kalau VPS punya IP publik,
   dropdown mungkin hanya menampilkan IP LAN — isi manual IP publik VPS
   di controller.
3. **Firewall Windows sudah dibuka?** Jalankan command PowerShell di atas.
4. **Firewall provider VPS?** Vendor VPS (DigitalOcean / AWS / Azure /
   Hyper-V) biasanya punya firewall terpisah — buka inbound TCP `8765`
   dari IP laptop.
5. **Coba dari VPS sendiri dulu:** klik *Open /docs* di GUI server. Kalau
   browser di VPS bisa buka `/docs`, server jalan normal; masalah ada di
   network / firewall.

---

## 3. Auto Installer FFmpeg

Server app punya endpoint `POST /server/install-ffmpeg` yang dipicu dari
**Installer Panel** di controller:

- Mengunduh FFmpeg Windows static build dari `BtbN/FFmpeg-Builds`.
- Mengekstrak ke `C:\LiveStreamServer\bin\ffmpeg\`.
- Menyimpan path absolut `ffmpeg.exe` ke `config.json`.
- Memverifikasi dengan `ffmpeg -version`.

Ada juga endpoint cek status:
- `GET /server/check-ffmpeg`
- `GET /server/check-deps`
- `GET /server/status`
- `GET /system/resources`

---

## 4. Menjalankan multi-live

1. **Tab Videos** → klik *Upload* untuk meng-upload `.mp4 / .mkv / .mov / .avi`
   dari laptop. Server menyimpan ke `C:\LiveStreamServer\videos`.
2. **Tab Accounts** → tambahkan akun (YouTube / Facebook / TikTok / Custom
   RTMP). Stream key disimpan di SQLite, ditampilkan masked di UI.
3. **Tab Streams** → klik *Start Lives*, pilih beberapa akun sekaligus dan
   satu video. Untuk tiap akun terpilih, server menjalankan satu proses
   FFmpeg dengan parameter:

   ```
   ffmpeg.exe -re -stream_loop -1 -i VIDEO
              -c:v libx264 -preset veryfast -b:v BITRATE
              -maxrate BITRATE -bufsize 2*BITRATE
              -s RESOLUSI -r FPS
              -pix_fmt yuv420p -c:a aac -b:a 128k -ar 44100
              -f flv RTMP_URL/STREAM_KEY
   ```

   Builder ada di `LiveStreamServer/app/services/ffmpeg_runner.py`.

4. Tabel live menampilkan kolom: ID, akun, platform, video, status,
   started_at, bitrate, loop, PID. Kamu bisa **Stop**, **Restart**, atau
   melihat **Logs** real-time.

Mode loop: tiap stream punya checkbox *Loop video*. Jika dimatikan, FFmpeg
berjalan sekali sampai EOF lalu berhenti. Untuk playlist beberapa video,
buat beberapa stream sekaligus pada start.

Auto-restart: centang saat memulai. Jika FFmpeg keluar dengan exit code
non-zero, monitor thread di server akan mencatat error dan men-spawn ulang
proses. Status di DB berubah `running → error → running` dengan log lengkap.

---

## 5. API endpoint (server)

Semua endpoint kecuali `/auth/login` dan `/` butuh header
`X-API-Key: <token>` atau `Authorization: Bearer <token>`.

| Method | Path | Deskripsi |
|--------|------|-----------|
| POST   | `/auth/login` | login username + password → `api_token` |
| GET    | `/server/status` | info app, ffmpeg, jumlah live aktif |
| GET    | `/server/check-ffmpeg` | cek path & versi FFmpeg |
| POST   | `/server/install-ffmpeg?force=true|false` | trigger auto-installer |
| GET    | `/server/check-deps` | cek dependency Python di VPS |
| GET    | `/system/resources` | CPU, RAM, disk, uptime, count live |
| GET    | `/videos` | list semua video |
| POST   | `/videos/upload` | multipart upload (`file`) |
| DELETE | `/videos/{id}` | hapus video |
| PATCH  | `/videos/{id}/rename` | rename file |
| GET    | `/accounts` | list akun |
| POST   | `/accounts` | tambah akun |
| PATCH  | `/accounts/{id}` | update akun |
| DELETE | `/accounts/{id}` | hapus akun |
| GET    | `/streams` | list semua stream |
| GET    | `/streams/{id}` | detail stream |
| POST   | `/streams/start` | start stream baru |
| POST   | `/streams/stop/{id}` | stop |
| POST   | `/streams/restart/{id}` | restart |
| GET    | `/streams/logs/{id}?limit=200` | tail FFmpeg log |

OpenAPI UI: `http://<ip-vps>:8765/docs`.

---

## 6. Database

SQLite (`C:\LiveStreamServer\database.db`) dengan SQLAlchemy. Tabel:

- `users(id, username, password_hash, api_token, created_at)`
- `videos(id, filename, original_name, path, size, duration, created_at)`
- `accounts(id, name, platform, rtmp_url, stream_key, default_bitrate,
  default_resolution, is_active, created_at)`
- `streams(id, account_id, video_id, status, pid, bitrate, resolution, fps,
  audio_bitrate, preset, loop, auto_restart, started_at, stopped_at,
  last_error, log_path)`
- `stream_logs(id, stream_id, message, level, created_at)`
- `settings(key, value)`

Kode akses DB modular (`app/database.py`, `app/models.py`) — pindah ke
PostgreSQL hanya butuh ganti `database_url` di `config.json` ke
`postgresql+psycopg2://user:pwd@host/db` dan `pip install psycopg2-binary`.

---

## 7. Build .exe dengan PyInstaller

### Server

```bat
cd LiveStreamServer
pip install pyinstaller
pyinstaller --noconfirm --onefile --name LiveStreamServer ^
    --add-data "config.example.json;." ^
    server_app.py
```

Output: `dist\LiveStreamServer.exe`. Jalankan langsung di VPS — semua folder
auto-create di `C:\LiveStreamServer\`.

### Controller

```bat
cd LiveStreamController
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name LiveStreamController ^
    --add-data "config.example.json;." ^
    controller_app.py
```

Output: `dist\LiveStreamController.exe`. Untuk auto-update otomatis kamu bisa
pakai `--icon` dan `--version-file`.

---

## 8. Catatan keamanan

- API token generate acak (`secrets.token_urlsafe(32)`) saat server pertama
  start — ganti `default_admin_password` di `config.json` segera setelah
  install.
- Stream key tidak pernah dikirim balik dalam bentuk plain — controller
  hanya menerima `stream_key_masked` (`abc***...***xyz`). Update key dari
  controller akan menimpa, kosongkan field untuk membiarkan tetap.
- Semua endpoint kecuali login pakai dependency `require_token`.
- Path traversal divalidasi di `app/utils/paths.py` (basename + regex sanitiser
  + `commonpath` check). Hanya ekstensi `.mp4 .mkv .mov .avi` yang diterima.
- FFmpeg dijalankan dengan `CREATE_NO_WINDOW` di Windows agar tidak memunculkan
  console kosong tiap stream.
- CORS allow_origins=`*` untuk memudahkan controller dari LAN; di public
  deploy, batasi ke IP/host laptop, atau gunakan reverse proxy + auth basic.

## 9. Optimasi agar ringan & stabil

- FFmpeg subprocess via `subprocess.Popen` + thread reader yang menulis ke
  file & buffer 500 line terakhir di RAM (tidak ada I/O blocking di
  request).
- Monitor thread server (interval 3s) memantau exit code tiap proses dan
  melakukan restart bila `auto_restart=True`.
- Default preset `veryfast` (ringan untuk libx264). Untuk VPS lebih
  bertenaga, pakai `fast` / `medium`. Untuk VPS lemah, pakai `ultrafast`.
- Resolusi default 720p `1280x720` agar irit CPU; bisa per-akun di Account
  Manager.
- DB `SQLite` dipakai dengan `check_same_thread=False` — cocok untuk satu
  proses uvicorn (single worker). Hindari menjalankan dengan `--workers > 1`
  karena state stream manager in-memory.
- Controller pakai `QThread` untuk semua call HTTP — UI tidak pernah freeze
  saat upload besar atau saat server lambat respond.

---

## 10. Cara menjalankan ringkas

```bat
:: Server VPS
cd LiveStreamServer && python server_app.py

:: Controller laptop
cd LiveStreamController && python controller_app.py
```

Selesai — buka tab *Installer* dari controller, klik **Install FFmpeg**, lalu
upload video dan tambah akun. Klik **Start Lives** untuk memulai banyak live
sekaligus.
