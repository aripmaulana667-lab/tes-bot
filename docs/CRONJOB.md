# Cronjob Setup (cPanel)

AniStream menggunakan **Laravel Scheduler** sehingga Anda **cukup satu cronjob** untuk semua task otomatis.

## 1. Tambah Cronjob di cPanel
**cPanel → Cron Jobs → Add New Cron Job**. Pilih **Common Settings: Once Per Minute (* * * * *)** dan masukkan:

```
* * * * * cd /home/USER/anistream && /usr/local/bin/php artisan schedule:run >> /dev/null 2>&1
```

Ganti `USER` dengan username cPanel Anda dan path `/usr/local/bin/php` dengan path PHP yang sesuai versi 8.2+ (cek di cPanel → Multi PHP CLI Version atau jalankan `which php` di Terminal).

## 2. Jadwal Bawaan
File `routes/console.php` menjadwalkan:

| Command | Frekuensi | Fungsi |
|---------|-----------|--------|
| `scrape:jikan --mode=ongoing` | Setiap hari 02:00 | Sinkron anime ongoing dari Jikan/MAL |
| `scrape:jikan --mode=top --pages=2` | Mingguan, Minggu 03:30 | Top anime |
| `scrape:anilist --type=anime` | Setiap hari 04:00 | Trending anime dari AniList |
| `scrape:anilist --type=donghua` | Setiap hari 04:15 | Trending donghua |
| `subscriptions:expire` | Per jam | Tandai subscription kadaluarsa |

## 3. Jalankan Manual (testing)
```
cd ~/anistream
php artisan scrape:jikan --mode=ongoing
php artisan scrape:anilist
php artisan subscriptions:expire
```

## 4. Disable scheduling per task
Edit `routes/console.php` lalu komentari command yang tidak diinginkan.

## 5. Multiple cron alternative
Jika ingin pisah (tidak pakai scheduler), Anda boleh tambahkan langsung:
```
0 2 * * * cd /home/USER/anistream && /usr/local/bin/php artisan scrape:jikan --mode=ongoing
0 4 * * * cd /home/USER/anistream && /usr/local/bin/php artisan scrape:anilist
0 * * * * cd /home/USER/anistream && /usr/local/bin/php artisan subscriptions:expire
```
