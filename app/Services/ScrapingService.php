<?php

namespace App\Services;

use App\Models\Anime;
use App\Models\Episode;
use App\Models\Genre;
use App\Models\Studio;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Str;

/**
 * Auto-scraping service.
 *
 * Sources:
 *  - Jikan API (MyAnimeList): https://api.jikan.moe/v4
 *  - AniList GraphQL: https://graphql.anilist.co
 *
 * Both endpoints are public and require no API key, making them
 * compatible with shared hosting environments.
 */
class ScrapingService
{
    protected string $jikanBase = 'https://api.jikan.moe/v4';
    protected string $anilistEndpoint = 'https://graphql.anilist.co';

    public function fetchJikanTopAnime(int $page = 1, int $limit = 25): array
    {
        $resp = Http::timeout(20)->get($this->jikanBase . '/top/anime', [
            'page' => $page,
            'limit' => $limit,
        ]);
        if (!$resp->ok()) {
            Log::warning('Jikan top anime failed', ['status' => $resp->status()]);
            return [];
        }
        return (array) $resp->json('data', []);
    }

    public function fetchJikanSeasonNow(): array
    {
        $resp = Http::timeout(20)->get($this->jikanBase . '/seasons/now');
        if (!$resp->ok()) {
            return [];
        }
        return (array) $resp->json('data', []);
    }

    public function fetchAniListTrending(int $perPage = 30): array
    {
        $query = <<<'GQL'
        query ($page: Int, $perPage: Int) {
          Page(page: $page, perPage: $perPage) {
            media(sort: TRENDING_DESC, type: ANIME) {
              id idMal title { romaji english native }
              description format status episodes duration
              seasonYear season averageScore
              coverImage { extraLarge large }
              bannerImage
              countryOfOrigin
              genres
              studios { nodes { name } }
              trailer { id site }
            }
          }
        }
        GQL;

        $resp = Http::timeout(20)->post($this->anilistEndpoint, [
            'query' => $query,
            'variables' => ['page' => 1, 'perPage' => $perPage],
        ]);
        if (!$resp->ok()) {
            return [];
        }
        return (array) data_get($resp->json(), 'data.Page.media', []);
    }

    public function importFromJikan(array $entry): ?Anime
    {
        if (!isset($entry['mal_id'])) {
            return null;
        }

        $studio = null;
        if (!empty($entry['studios'][0]['name'])) {
            $studio = Studio::firstOrCreate(
                ['slug' => Str::slug($entry['studios'][0]['name'])],
                ['name' => $entry['studios'][0]['name']]
            );
        }

        $type = strtolower((string) ($entry['type'] ?? 'TV'));
        $type = match (true) {
            str_contains($type, 'movie') => 'movie',
            str_contains($type, 'ova') => 'ova',
            str_contains($type, 'ona') => 'ona',
            str_contains($type, 'special') => 'special',
            default => 'anime',
        };

        $status = strtolower((string) ($entry['status'] ?? ''));
        $status = match (true) {
            str_contains($status, 'airing'), str_contains($status, 'ongoing') => 'ongoing',
            str_contains($status, 'finished'), str_contains($status, 'completed') => 'completed',
            str_contains($status, 'not yet'), str_contains($status, 'upcoming') => 'upcoming',
            default => 'ongoing',
        };

        $anime = Anime::updateOrCreate(
            ['mal_id' => $entry['mal_id']],
            [
                'title' => $entry['title'] ?? 'Untitled',
                'title_japanese' => $entry['title_japanese'] ?? null,
                'title_english' => $entry['title_english'] ?? null,
                'slug' => Anime::generateUniqueSlug($entry['title'] ?? 'untitled-' . $entry['mal_id']),
                'type' => $type,
                'status' => $status,
                'synopsis' => $entry['synopsis'] ?? null,
                'year' => $entry['year'] ?? (isset($entry['aired']['from']) ? (int) substr($entry['aired']['from'], 0, 4) : null),
                'season' => $entry['season'] ?? null,
                'episodes_count' => $entry['episodes'] ?? 0,
                'duration' => $this->parseDuration($entry['duration'] ?? null),
                'age_rating' => $entry['rating'] ?? null,
                'score' => $entry['score'] ?? null,
                'poster' => $entry['images']['jpg']['large_image_url'] ?? ($entry['images']['jpg']['image_url'] ?? null),
                'banner' => $entry['images']['jpg']['large_image_url'] ?? null,
                'trailer_url' => $entry['trailer']['url'] ?? null,
                'studio_id' => $studio?->id,
                'source' => $entry['source'] ?? null,
                'country' => 'JP',
                'is_published' => true,
            ]
        );

        if (!empty($entry['genres'])) {
            $genreIds = [];
            foreach ($entry['genres'] as $g) {
                $name = $g['name'] ?? null;
                if (!$name) {
                    continue;
                }
                $genre = Genre::firstOrCreate(
                    ['slug' => Str::slug($name)],
                    ['name' => $name]
                );
                $genreIds[] = $genre->id;
            }
            $anime->genres()->sync($genreIds);
        }

        return $anime;
    }

    public function importFromAniList(array $entry): ?Anime
    {
        $studio = null;
        if (!empty($entry['studios']['nodes'][0]['name'])) {
            $name = $entry['studios']['nodes'][0]['name'];
            $studio = Studio::firstOrCreate(['slug' => Str::slug($name)], ['name' => $name]);
        }

        $country = $entry['countryOfOrigin'] ?? 'JP';
        $type = $country === 'CN' ? 'donghua' : 'anime';
        if (!empty($entry['format'])) {
            $f = strtoupper((string) $entry['format']);
            if ($f === 'MOVIE') {
                $type = 'movie';
            } elseif ($f === 'OVA') {
                $type = 'ova';
            } elseif ($f === 'ONA') {
                $type = 'ona';
            } elseif ($f === 'SPECIAL') {
                $type = 'special';
            }
        }

        $status = strtolower((string) ($entry['status'] ?? ''));
        $status = match ($status) {
            'releasing' => 'ongoing',
            'finished' => 'completed',
            'not_yet_released' => 'upcoming',
            default => 'ongoing',
        };

        $title = $entry['title']['english']
            ?? ($entry['title']['romaji']
                ?? ($entry['title']['native'] ?? 'Untitled'));

        $description = $entry['description'] ?? null;
        if ($description) {
            $description = strip_tags($description);
        }

        $trailer = null;
        if (!empty($entry['trailer']['id']) && !empty($entry['trailer']['site'])) {
            if ($entry['trailer']['site'] === 'youtube') {
                $trailer = 'https://www.youtube.com/watch?v=' . $entry['trailer']['id'];
            }
        }

        $key = $entry['idMal'] ? ['mal_id' => $entry['idMal']] : ['anilist_id' => $entry['id']];

        $anime = Anime::updateOrCreate(
            $key,
            [
                'title' => $title,
                'title_english' => $entry['title']['english'] ?? null,
                'title_japanese' => $entry['title']['native'] ?? null,
                'slug' => Anime::generateUniqueSlug($title),
                'type' => $type,
                'status' => $status,
                'synopsis' => $description,
                'year' => $entry['seasonYear'] ?? null,
                'season' => $entry['season'] ?? null,
                'episodes_count' => $entry['episodes'] ?? 0,
                'duration' => $entry['duration'] ?? null,
                'score' => isset($entry['averageScore']) ? $entry['averageScore'] / 10 : null,
                'poster' => $entry['coverImage']['extraLarge'] ?? ($entry['coverImage']['large'] ?? null),
                'banner' => $entry['bannerImage'] ?? null,
                'trailer_url' => $trailer,
                'studio_id' => $studio?->id,
                'country' => $country,
                'is_published' => true,
                'anilist_id' => $entry['id'] ?? null,
            ]
        );

        if (!empty($entry['genres'])) {
            $ids = [];
            foreach ($entry['genres'] as $g) {
                $genre = Genre::firstOrCreate(['slug' => Str::slug($g)], ['name' => $g]);
                $ids[] = $genre->id;
            }
            $anime->genres()->sync($ids);
        }

        return $anime;
    }

    protected function parseDuration(?string $duration): ?int
    {
        if (!$duration) {
            return null;
        }
        if (preg_match('/(\d+)\s*min/i', $duration, $m)) {
            return (int) $m[1];
        }
        return null;
    }

    public function syncOngoing(): int
    {
        $count = 0;
        $entries = $this->fetchJikanSeasonNow();
        foreach ($entries as $entry) {
            if ($this->importFromJikan($entry)) {
                $count++;
            }
        }
        return $count;
    }

    public function syncTop(int $pages = 2): int
    {
        $count = 0;
        for ($p = 1; $p <= $pages; $p++) {
            $entries = $this->fetchJikanTopAnime($p);
            foreach ($entries as $entry) {
                if ($this->importFromJikan($entry)) {
                    $count++;
                }
            }
        }
        return $count;
    }

    public function syncTrending(): int
    {
        $count = 0;
        foreach ($this->fetchAniListTrending() as $entry) {
            if ($this->importFromAniList($entry)) {
                $count++;
            }
        }
        return $count;
    }
}
