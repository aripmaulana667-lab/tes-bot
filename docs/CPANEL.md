# Panduan Install di Shared Hosting cPanel

Panduan ini mengasumsikan akun cPanel standar dengan PHP 8.2+, MySQL/MariaDB, dan akses File Manager + Cron Jobs.

## 1. Siapkan PHP & ekstensi
Di **MultiPHP Manager**, set domain ke PHP 8.2 (atau lebih baru).

Pastikan ekstensi aktif (di **Select PHP Version → Extensions**):
- `bcmath`, `ctype`, `curl`, `dom`, `fileinfo`, `mbstring`, `openssl`, `pdo`, `pdo_mysql`, `tokenizer`, `xml`, `gd` (untuk upload gambar), `zip`

## 2. Buat database MySQL
1. Buka **MySQL Databases** di cPanel
2. Buat database baru (mis. `useracc_anistream`)
3. Buat user MySQL + password kuat, lalu **Add User to Database** dengan ALL PRIVILEGES

Catat: hostname biasanya `localhost`.

## 3. Upload source code
Ada 2 pola umum:

### Pola A — Struktur Laravel utuh
1. Buat folder `~/anistream` (di luar `public_html`)
2. Upload semua file project ke `~/anistream`
3. **Pindahkan/symlink** isi folder `public/` ke `public_html` (atau jadikan subdomain dengan document root `public/`)
4. Edit `public_html/index.php` agar path require menunjuk ke `~/anistream`:
   ```php
   require __DIR__.'/../anistream/vendor/autoload.php';
   $app = require_once __DIR__.'/../anistream/bootstrap/app.php';
   ```

### Pola B — Subdomain langsung
1. Buat subdomain `anistream.domain.com` dengan document root `~/anistream/public`
2. Upload seluruh isi project ke `~/anistream/`

## 4. Install dependency
Buka **Terminal** di cPanel (jika tersedia), lalu:
```bash
cd ~/anistream
composer install --optimize-autoloader --no-dev
```
Jika tidak ada Terminal di cPanel:
- Upload `vendor/` hasil `composer install` dari komputer lokal, atau
- Gunakan Cron sekali untuk: `cd /home/USER/anistream && /usr/local/bin/php composer.phar install --no-dev`

## 5. Setup `.env`
```bash
cp .env.example .env
nano .env
```
Set minimal:
```
APP_ENV=production
APP_DEBUG=false
APP_URL=https://anistream.domain.com
DB_CONNECTION=mysql
DB_HOST=localhost
DB_DATABASE=useracc_anistream
DB_USERNAME=useracc_anistream
DB_PASSWORD=xxx
SESSION_DRIVER=file
CACHE_STORE=file
QUEUE_CONNECTION=sync
MAIL_MAILER=smtp
MAIL_HOST=mail.domain.com
MAIL_PORT=465
MAIL_USERNAME=noreply@domain.com
MAIL_PASSWORD=xxx
MAIL_ENCRYPTION=ssl
MAIL_FROM_ADDRESS=noreply@domain.com
```

Lalu:
```bash
php artisan key:generate
php artisan migrate --seed --force
php artisan storage:link
php artisan optimize
```

## 6. Permission
```bash
chmod -R 775 storage bootstrap/cache
```
(Jika di cPanel pakai `chown -R USER:USER` sesuai username hosting.)

## 7. Cronjob
Buka **Cron Jobs** di cPanel. Tambah:
```
* * * * * cd /home/USER/anistream && /usr/local/bin/php artisan schedule:run >> /dev/null 2>&1
```
Lihat [CRONJOB.md](CRONJOB.md) untuk detail.

## 8. Selesai
Buka URL situs. Login admin via `/login` dengan akun seeder, lalu kunjungi `/admin`.

### Hardening tambahan
- Set `APP_DEBUG=false`, `APP_ENV=production`
- Aktifkan SSL (AutoSSL / Let's Encrypt)
- Jangan commit `.env` ke repo publik
- Gunakan password admin kuat, hapus akun demo seed
- Atur reCAPTCHA / Cloudflare Turnstile sendiri pada form komentar (opsional)

### Troubleshooting
- **500 Internal Server Error**: cek `storage/logs/laravel.log`. Pastikan `chmod -R 775 storage bootstrap/cache` & ownership benar.
- **No application encryption key**: jalankan `php artisan key:generate`.
- **Database connection refused**: pastikan `DB_HOST=localhost`, user MySQL sudah punya privilege.
- **Image upload error**: cek `storage/app/public` exist & `php artisan storage:link` sudah dijalankan.
- **Sitemap.xml kosong**: pastikan ada anime published. Cache bisa dibersihkan dengan `php artisan optimize:clear`.
