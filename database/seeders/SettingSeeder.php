<?php

namespace Database\Seeders;

use App\Models\Setting;
use Illuminate\Database\Seeder;

class SettingSeeder extends Seeder
{
    public function run(): void
    {
        $settings = [
            'site_name' => 'AniStream',
            'site_tagline' => 'Streaming anime & donghua premium subtitle Indonesia',
            'theme_color' => '#7c3aed',
            'maintenance_mode' => false,
            'meta_description' => 'Streaming anime, donghua, dan film animasi terbaru dengan subtitle Indonesia, kualitas HD, dan tanpa iklan untuk member premium.',
            'meta_keywords' => 'streaming anime, nonton anime, anime sub indo, donghua, anime ongoing, anime completed',
            'analytics_code' => '',
        ];

        foreach ($settings as $key => $value) {
            Setting::put($key, $value, 'general');
        }
    }
}
