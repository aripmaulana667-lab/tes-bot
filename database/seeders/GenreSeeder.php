<?php

namespace Database\Seeders;

use App\Models\Genre;
use Illuminate\Database\Seeder;
use Illuminate\Support\Str;

class GenreSeeder extends Seeder
{
    public function run(): void
    {
        $genres = [
            'Action', 'Adventure', 'Comedy', 'Drama', 'Fantasy', 'Horror',
            'Mystery', 'Romance', 'Sci-Fi', 'Slice of Life', 'Sports',
            'Supernatural', 'Thriller', 'Mecha', 'Music', 'Psychological',
            'Historical', 'Magic', 'Martial Arts', 'School', 'Isekai',
            'Cultivation', 'Wuxia', 'Xianxia', 'Demons', 'Vampire',
            'Game', 'Military', 'Police', 'Shounen', 'Shoujo', 'Seinen',
            'Josei', 'Ecchi', 'Harem',
        ];
        foreach ($genres as $name) {
            Genre::firstOrCreate(['slug' => Str::slug($name)], ['name' => $name]);
        }
    }
}
