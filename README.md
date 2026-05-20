# AniStream — Streaming Anime & Donghua (Laravel 11)

Aplikasi fullstack streaming anime/donghua dengan Laravel 11. Dirancang untuk **shared hosting cPanel** tanpa VPS/Docker/Redis/Node.js server.

## Tech Stack
- **Backend**: Laravel 11, PHP 8.2+, MySQL
- **Frontend**: Blade + TailwindCSS (CDN) + Alpine.js (CDN)
- **Video Player**: Video.js + HLS.js (MP4 & M3U8)
- **Auth**: Laravel Auth built-in (session-based)
- **Caching**: File cache (default Laravel) — no Redis required
- **Queue**: `sync` (no separate worker needed). Atau gunakan database queue jika perlu
- **Auto-scraping**: Jikan API + AniList GraphQL (dipicu lewat cronjob cPanel)

## Fitur Utama
- Homepage modern: hero, trending, ongoing, completed, donghua, jadwal, top view, rekomendasi
- Detail anime: synopsis, genre, studio, trailer, rating, share sosial, bookmark, JSON-LD schema
- Video player Video.js + HLS.js: MP4/M3U8/iframe, multi-server, subtitle, resume playback, auto-next, quality selector
- Pencarian realtime + filter (genre, studio, tahun, status, type)
- Akun: register, login, forgot/reset password, avatar upload, profile, watch history, bookmarks, komentar dengan like & anti-spam, rating
- Premium membership: VIP badge, premium episode, no ads
- Payment gateway: **Midtrans, PayPal, Stripe, Xendit** (siap aktif via .env)
- Coupon system
- Admin panel: dashboard, manage anime/episode (multi-server), users, genres, studios, plans, coupons, iklan (AdSense + custom), SEO meta per halaman, settings (logo, theme, SMTP, maintenance), database backup
- Auto-scraping cronjob (Jikan & AniList)
- SEO: meta tag dinamis, sitemap.xml otomatis, robots.txt, OpenGraph, JSON-LD
- PWA: manifest.webmanifest + service worker (offline minimal)
- Security: CSRF, XSS escape, SQL injection (Eloquent), security headers middleware, anti-spam komentar, rate limit Laravel built-in
- Cache file-based untuk listing & metadata
- Dark theme purple/black neon, glassmorphism, mobile responsive

## Default Akun
Setelah seeder:
- **Admin**: `admin@anistream.test` / `password`
- **Demo user**: `demo@anistream.test` / `password`

## Install Lokal (developer)

```bash
git clone https://github.com/<user>/anistream.git
cd anistream
cp .env.example .env
composer install --optimize-autoloader --no-dev
php artisan key:generate
# pakai sqlite untuk dev:
touch database/database.sqlite
# di .env, set DB_CONNECTION=sqlite (atau biarkan mysql)
php artisan migrate --seed
php artisan storage:link
php artisan serve
```

Buka http://localhost:8000. Login admin di `/login`, lalu buka `/admin`.

## Deploy ke Shared Hosting cPanel
Lihat [docs/CPANEL.md](docs/CPANEL.md) untuk panduan lengkap.

Ringkasan:
1. Buat database MySQL + user di cPanel
2. Upload semua file ke `~/your-site/` (atau setara). Set `public/` sebagai document root (atau symlink ke `public_html`).
3. Atur `.env` (database, APP_URL, SMTP, payment keys)
4. Jalankan via "Terminal" (jika ada) atau "PHP CLI" cron: `php artisan key:generate`, `php artisan migrate --seed`, `php artisan storage:link`
5. Set cronjob untuk scraping (lihat [docs/CRONJOB.md](docs/CRONJOB.md))

## Cronjob (cPanel)
Tambah satu cron job tunggal pada cPanel:
```
* * * * * cd /home/USER/anistream && /usr/local/bin/php artisan schedule:run >> /dev/null 2>&1
```
Scheduler akan menjalankan otomatis:
- `scrape:jikan --mode=ongoing` (harian 02:00)
- `scrape:jikan --mode=top --pages=2` (mingguan minggu 03:30)
- `scrape:anilist` (harian 04:00)
- `subscriptions:expire` (per jam)

## Struktur Singkat
- `app/Models` — 19 model Eloquent (Anime, Episode, EpisodeServer, Genre, Studio, User, Comment, Rating, Bookmark, WatchHistory, Plan, Subscription, Coupon, Payment, Setting, Ad, SeoMeta, CommentLike, …)
- `app/Services` — `AnimeService`, `ScrapingService`, `Payment/{Midtrans|PayPal|Stripe|Xendit}Gateway`, `PaymentManager`
- `app/Http/Controllers` — Home, Anime, Episode, Search, Genre, Bookmark, History, Profile, Rating, Comment, Auth, Billing, Seo + `Admin/*`
- `app/Http/Middleware` — `AdminMiddleware`, `MaintenanceMode`, `SecurityHeaders`
- `app/Console/Commands` — `SyncJikan`, `SyncAniList`, `ExpireSubscriptions`
- `resources/views` — layouts/components/pages (Tailwind + Alpine)
- `database/migrations` — 27 migrasi
- `database/seeders` — Genre, Studio, User, Plan, Setting, SeoMeta, Anime sample

## Payment Gateways
Cukup isi key di `.env`. Yang kosong otomatis nonaktif.
- `MIDTRANS_SERVER_KEY`, `MIDTRANS_CLIENT_KEY`, `MIDTRANS_IS_PRODUCTION`
- `PAYPAL_MODE`, `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET`
- `STRIPE_KEY`, `STRIPE_SECRET`
- `XENDIT_SECRET_KEY`, `XENDIT_CALLBACK_TOKEN`

Webhook endpoint:
- `POST /billing/webhook/midtrans`
- `POST /billing/webhook/paypal`
- `POST /billing/webhook/stripe`
- `POST /billing/webhook/xendit`

## Lisensi
MIT.
