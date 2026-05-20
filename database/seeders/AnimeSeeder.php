<?php

namespace Database\Seeders;

use App\Models\Anime;
use App\Models\Episode;
use App\Models\EpisodeServer;
use App\Models\Genre;
use App\Models\Studio;
use Illuminate\Database\Seeder;

class AnimeSeeder extends Seeder
{
    public function run(): void
    {
        // Sample-set anime/donghua data; can be replaced or extended via the scraping commands.
        $data = [
            [
                'title' => 'Frieren: Beyond Journey\'s End',
                'title_japanese' => '葬送のフリーレン',
                'title_english' => 'Frieren: Beyond Journey\'s End',
                'type' => 'anime',
                'status' => 'completed',
                'synopsis' => 'After defeating the Demon King, Frieren the elf mage embarks on a journey of self-discovery, exploring what it means to live alongside humans.',
                'year' => 2023,
                'episodes_count' => 28,
                'duration' => 24,
                'score' => 9.3,
                'poster' => 'https://cdn.myanimelist.net/images/anime/1015/138006l.jpg',
                'banner' => 'https://cdn.myanimelist.net/images/anime/1015/138006l.jpg',
                'studio' => 'Madhouse',
                'genres' => ['Adventure', 'Drama', 'Fantasy'],
                'is_featured' => true,
                'schedule_day' => 'friday',
                'schedule_time' => '23:00',
            ],
            [
                'title' => 'Jujutsu Kaisen Season 2',
                'title_japanese' => '呪術廻戦',
                'type' => 'anime',
                'status' => 'completed',
                'synopsis' => 'Yuji Itadori continues his battle against cursed spirits and powerful sorcerers in the Shibuya Incident arc.',
                'year' => 2023,
                'episodes_count' => 23,
                'duration' => 24,
                'score' => 8.6,
                'poster' => 'https://cdn.myanimelist.net/images/anime/1792/138022l.jpg',
                'studio' => 'MAPPA',
                'genres' => ['Action', 'Supernatural', 'Shounen'],
                'is_featured' => true,
                'schedule_day' => 'thursday',
            ],
            [
                'title' => 'Attack on Titan: The Final Season',
                'title_japanese' => '進撃の巨人',
                'type' => 'anime',
                'status' => 'completed',
                'synopsis' => 'The Survey Corps faces the ultimate truth as the world prepares for the final battle for humanity.',
                'year' => 2023,
                'episodes_count' => 28,
                'duration' => 24,
                'score' => 9.0,
                'poster' => 'https://cdn.myanimelist.net/images/anime/1517/100633l.jpg',
                'studio' => 'MAPPA',
                'genres' => ['Action', 'Drama', 'Fantasy'],
                'is_featured' => true,
            ],
            [
                'title' => 'Demon Slayer: Hashira Training Arc',
                'title_japanese' => '鬼滅の刃',
                'type' => 'anime',
                'status' => 'completed',
                'synopsis' => 'The Hashira begin training the Demon Slayer Corps to prepare for the upcoming battle with Muzan Kibutsuji.',
                'year' => 2024,
                'episodes_count' => 8,
                'duration' => 24,
                'score' => 8.1,
                'poster' => 'https://cdn.myanimelist.net/images/anime/1976/142046l.jpg',
                'studio' => 'ufotable',
                'genres' => ['Action', 'Fantasy', 'Shounen'],
                'is_featured' => true,
            ],
            [
                'title' => 'Chainsaw Man',
                'type' => 'anime',
                'status' => 'completed',
                'synopsis' => 'Denji is a young man who, alongside his pet devil dog Pochita, becomes the Chainsaw Devil to pay off his deceased father\'s debts.',
                'year' => 2022,
                'episodes_count' => 12,
                'duration' => 24,
                'score' => 8.5,
                'poster' => 'https://cdn.myanimelist.net/images/anime/1806/126216l.jpg',
                'studio' => 'MAPPA',
                'genres' => ['Action', 'Supernatural'],
            ],
            [
                'title' => 'Spy x Family Season 2',
                'type' => 'anime',
                'status' => 'completed',
                'synopsis' => 'The Forger family continues their secret mission while keeping up the appearance of a normal household.',
                'year' => 2023,
                'episodes_count' => 12,
                'duration' => 24,
                'score' => 8.4,
                'poster' => 'https://cdn.myanimelist.net/images/anime/1421/137915l.jpg',
                'studio' => 'CloverWorks',
                'genres' => ['Action', 'Comedy', 'Slice of Life'],
            ],
            [
                'title' => 'One Piece',
                'type' => 'anime',
                'status' => 'ongoing',
                'synopsis' => 'Monkey D. Luffy and the Straw Hat Pirates sail the Grand Line in search of the legendary treasure known as the One Piece.',
                'year' => 1999,
                'episodes_count' => 1100,
                'duration' => 24,
                'score' => 8.8,
                'poster' => 'https://cdn.myanimelist.net/images/anime/1244/138851l.jpg',
                'studio' => 'Sunrise',
                'genres' => ['Action', 'Adventure', 'Comedy', 'Shounen'],
                'schedule_day' => 'sunday',
                'schedule_time' => '09:30',
            ],
            [
                'title' => 'Sousou no Frieren Movie',
                'type' => 'movie',
                'status' => 'completed',
                'synopsis' => 'A movie compilation of Frieren\'s journey across the continent.',
                'year' => 2024,
                'duration' => 120,
                'score' => 8.7,
                'poster' => 'https://cdn.myanimelist.net/images/anime/1015/138006l.jpg',
                'studio' => 'Madhouse',
                'genres' => ['Adventure', 'Drama'],
            ],
            [
                'title' => 'The Daily Life of the Immortal King',
                'title_japanese' => '仙王的日常生活',
                'type' => 'donghua',
                'status' => 'completed',
                'synopsis' => 'A teenage genius cultivator tries to live as a normal high school student while hiding his immense powers.',
                'year' => 2020,
                'episodes_count' => 60,
                'duration' => 18,
                'score' => 8.2,
                'poster' => 'https://cdn.myanimelist.net/images/anime/1758/138851l.jpg',
                'studio' => 'Haoliners',
                'genres' => ['Action', 'Comedy', 'Cultivation', 'Fantasy', 'School'],
            ],
            [
                'title' => 'Battle Through the Heavens',
                'title_japanese' => '斗破苍穹',
                'type' => 'donghua',
                'status' => 'ongoing',
                'synopsis' => 'Xiao Yan, once a genius, lost his cultivation abilities. He embarks on a journey to reclaim his powers and become a master.',
                'year' => 2017,
                'episodes_count' => 130,
                'duration' => 20,
                'score' => 8.0,
                'poster' => 'https://cdn.myanimelist.net/images/anime/1758/138851l.jpg',
                'studio' => 'Tencent Penguin Pictures',
                'genres' => ['Action', 'Adventure', 'Cultivation', 'Fantasy', 'Wuxia'],
                'schedule_day' => 'saturday',
                'schedule_time' => '20:00',
            ],
            [
                'title' => 'Soul Land (Douluo Dalu)',
                'title_japanese' => '斗罗大陆',
                'type' => 'donghua',
                'status' => 'ongoing',
                'synopsis' => 'After his death, Tang San reincarnates in a world of soul masters and spirit beasts where he must rise to become the strongest.',
                'year' => 2018,
                'episodes_count' => 250,
                'duration' => 22,
                'score' => 8.4,
                'poster' => 'https://cdn.myanimelist.net/images/anime/1758/138851l.jpg',
                'studio' => 'Tencent Penguin Pictures',
                'genres' => ['Action', 'Adventure', 'Cultivation', 'Fantasy', 'Xianxia'],
                'schedule_day' => 'sunday',
                'schedule_time' => '12:00',
            ],
            [
                'title' => 'Mushoku Tensei II',
                'type' => 'anime',
                'status' => 'ongoing',
                'synopsis' => 'Rudeus Greyrat continues his journey of growth in a fantasy world he was reincarnated into.',
                'year' => 2024,
                'episodes_count' => 12,
                'duration' => 24,
                'score' => 8.6,
                'poster' => 'https://cdn.myanimelist.net/images/anime/1015/138006l.jpg',
                'studio' => 'Studio Bind',
                'genres' => ['Adventure', 'Drama', 'Fantasy', 'Isekai'],
                'schedule_day' => 'monday',
                'schedule_time' => '23:30',
            ],
        ];

        foreach ($data as $entry) {
            $studio = $entry['studio'] ?? null;
            $studioId = null;
            if ($studio) {
                $studioModel = Studio::firstOrCreate(
                    ['slug' => \Illuminate\Support\Str::slug($studio)],
                    ['name' => $studio]
                );
                $studioId = $studioModel->id;
            }
            $payload = collect($entry)->except(['studio', 'genres'])->toArray();
            $payload['studio_id'] = $studioId;
            $payload['is_published'] = true;
            $payload['slug'] = Anime::generateUniqueSlug($entry['title']);
            $payload['views'] = random_int(2000, 250000);

            $anime = Anime::updateOrCreate(
                ['slug' => $payload['slug']],
                $payload
            );

            if (!empty($entry['genres'])) {
                $genreIds = [];
                foreach ($entry['genres'] as $gName) {
                    $g = Genre::firstOrCreate(
                        ['slug' => \Illuminate\Support\Str::slug($gName)],
                        ['name' => $gName]
                    );
                    $genreIds[] = $g->id;
                }
                $anime->genres()->sync($genreIds);
            }

            // Create demo episodes for the first 4 anime
            if (!empty($entry['episodes_count'])) {
                $count = min(12, (int) $entry['episodes_count']);
                for ($i = 1; $i <= $count; $i++) {
                    $ep = Episode::updateOrCreate(
                        ['anime_id' => $anime->id, 'number' => (string) $i],
                        [
                            'title' => 'Episode ' . $i,
                            'slug' => $anime->slug . '-episode-' . $i,
                            'synopsis' => 'Sinopsis episode ' . $i . ' dari ' . $anime->title,
                            'duration' => 1440,
                            'air_date' => now()->subWeeks($count - $i)->toDateString(),
                            'is_premium' => $i > 6,
                            'is_published' => true,
                            'views' => random_int(100, 50000),
                            'thumbnail' => $anime->poster,
                        ]
                    );

                    EpisodeServer::firstOrCreate(
                        ['episode_id' => $ep->id, 'server_name' => 'Demo HD'],
                        [
                            'type' => 'mp4',
                            'url' => 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',
                            'quality' => '720p',
                            'language' => 'sub',
                            'priority' => 1,
                            'is_active' => true,
                        ]
                    );
                    EpisodeServer::firstOrCreate(
                        ['episode_id' => $ep->id, 'server_name' => 'Demo HLS'],
                        [
                            'type' => 'm3u8',
                            'url' => 'https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8',
                            'quality' => '1080p',
                            'language' => 'sub',
                            'priority' => 2,
                            'is_active' => true,
                        ]
                    );
                }
            }
        }
    }
}
