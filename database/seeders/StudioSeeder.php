<?php

namespace Database\Seeders;

use App\Models\Studio;
use Illuminate\Database\Seeder;
use Illuminate\Support\Str;

class StudioSeeder extends Seeder
{
    public function run(): void
    {
        $studios = [
            ['MAPPA', 'JP'],
            ['Madhouse', 'JP'],
            ['Studio Ghibli', 'JP'],
            ['Kyoto Animation', 'JP'],
            ['Bones', 'JP'],
            ['Wit Studio', 'JP'],
            ['ufotable', 'JP'],
            ['A-1 Pictures', 'JP'],
            ['Sunrise', 'JP'],
            ['Trigger', 'JP'],
            ['Production I.G', 'JP'],
            ['CloverWorks', 'JP'],
            ['Shaft', 'JP'],
            ['Tencent Penguin Pictures', 'CN'],
            ['bilibili', 'CN'],
            ['Haoliners', 'CN'],
            ['Big Firebird Cultural Media', 'CN'],
            ['Foch Films', 'CN'],
        ];
        foreach ($studios as [$name, $country]) {
            Studio::firstOrCreate(
                ['slug' => Str::slug($name)],
                ['name' => $name, 'country' => $country]
            );
        }
    }
}
