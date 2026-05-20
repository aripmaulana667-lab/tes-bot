<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;

class DatabaseSeeder extends Seeder
{
    public function run(): void
    {
        $this->call([
            GenreSeeder::class,
            StudioSeeder::class,
            UserSeeder::class,
            PlanSeeder::class,
            SettingSeeder::class,
            SeoMetaSeeder::class,
            AnimeSeeder::class,
        ]);
    }
}
