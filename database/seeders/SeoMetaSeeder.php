<?php

namespace Database\Seeders;

use App\Models\SeoMeta;
use Illuminate\Database\Seeder;

class SeoMetaSeeder extends Seeder
{
    public function run(): void
    {
        $pages = [
            ['page_key' => 'home', 'title' => 'AniStream — Streaming Anime & Donghua Sub Indo', 'description' => 'Nonton anime, donghua, dan film animasi terbaru sub indo gratis kualitas HD.'],
            ['page_key' => 'anime.index', 'title' => 'Daftar Anime — AniStream', 'description' => 'Jelajahi koleksi lengkap anime ongoing, completed, dan upcoming.'],
            ['page_key' => 'donghua', 'title' => 'Donghua Sub Indo — AniStream', 'description' => 'Nonton donghua populer sub indo kualitas HD.'],
            ['page_key' => 'schedule', 'title' => 'Jadwal Rilis Anime — AniStream', 'description' => 'Jadwal rilis anime mingguan paling lengkap.'],
            ['page_key' => 'search', 'title' => 'Search — AniStream', 'description' => 'Cari anime, donghua, genre, atau studio favorit.'],
        ];
        foreach ($pages as $page) {
            SeoMeta::updateOrCreate(['page_key' => $page['page_key']], $page);
        }
    }
}
