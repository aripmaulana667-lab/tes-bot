<?php

namespace Database\Seeders;

use App\Models\Plan;
use Illuminate\Database\Seeder;
use Illuminate\Support\Str;

class PlanSeeder extends Seeder
{
    public function run(): void
    {
        $plans = [
            [
                'name' => 'Free',
                'description' => 'Akses dasar semua episode publik.',
                'price' => 0,
                'currency' => 'IDR',
                'duration_days' => 365 * 5,
                'features' => ['Streaming standar', '720p', 'Ads'],
                'sort' => 0,
            ],
            [
                'name' => 'Premium Monthly',
                'description' => 'Tanpa iklan, premium episode, kualitas full HD.',
                'price' => 49000,
                'currency' => 'IDR',
                'duration_days' => 30,
                'features' => ['Tanpa iklan', '1080p Full HD', 'Premium episode', 'Download'],
                'sort' => 10,
            ],
            [
                'name' => 'Premium Yearly',
                'description' => 'Hemat 30% bayar setahun sekali.',
                'price' => 390000,
                'currency' => 'IDR',
                'duration_days' => 365,
                'features' => ['Tanpa iklan', '1080p Full HD', 'Premium episode', 'Download', 'Diskon 30%'],
                'sort' => 20,
            ],
        ];
        foreach ($plans as $plan) {
            Plan::updateOrCreate(
                ['slug' => Str::slug($plan['name'])],
                $plan
            );
        }
    }
}
