<?php

namespace App\Services;

use App\Models\Anime;
use Illuminate\Database\Eloquent\Builder;
use Illuminate\Database\Eloquent\Collection;
use Illuminate\Pagination\LengthAwarePaginator;
use Illuminate\Support\Facades\Cache;

class AnimeService
{
    public function featured(int $limit = 8): Collection
    {
        return Cache::remember('home.featured', 300, function () use ($limit) {
            return Anime::published()
                ->where('is_featured', true)
                ->with('genres')
                ->latest('updated_at')
                ->limit($limit)
                ->get();
        });
    }

    public function trending(int $limit = 12): Collection
    {
        return Cache::remember('home.trending', 300, function () use ($limit) {
            return Anime::published()
                ->with('genres')
                ->orderByDesc('views')
                ->limit($limit)
                ->get();
        });
    }

    public function latestEpisodes(int $limit = 24): Collection
    {
        return Cache::remember('home.latest_episodes', 120, function () use ($limit) {
            return \App\Models\Episode::with('anime')
                ->where('is_published', true)
                ->whereHas('anime', fn ($q) => $q->published())
                ->latest('created_at')
                ->limit($limit)
                ->get();
        });
    }

    public function ongoing(int $limit = 12): Collection
    {
        return Cache::remember('home.ongoing', 300, function () use ($limit) {
            return Anime::published()
                ->ongoing()
                ->anime()
                ->with('genres')
                ->latest()
                ->limit($limit)
                ->get();
        });
    }

    public function completed(int $limit = 12): Collection
    {
        return Cache::remember('home.completed', 300, function () use ($limit) {
            return Anime::published()
                ->completed()
                ->anime()
                ->with('genres')
                ->latest()
                ->limit($limit)
                ->get();
        });
    }

    public function popularDonghua(int $limit = 12): Collection
    {
        return Cache::remember('home.donghua', 300, function () use ($limit) {
            return Anime::published()
                ->donghua()
                ->with('genres')
                ->orderByDesc('views')
                ->limit($limit)
                ->get();
        });
    }

    public function topView(int $limit = 10): Collection
    {
        return Cache::remember('home.top_view', 600, function () use ($limit) {
            return Anime::published()
                ->orderByDesc('views')
                ->limit($limit)
                ->get();
        });
    }

    public function recommendations(int $limit = 12): Collection
    {
        return Cache::remember('home.recommendations', 600, function () use ($limit) {
            return Anime::published()
                ->where('score', '>=', 7)
                ->orderByDesc('score')
                ->limit($limit)
                ->get();
        });
    }

    public function schedule(): array
    {
        return Cache::remember('home.schedule', 300, function () {
            $days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
            $byDay = [];
            foreach ($days as $day) {
                $byDay[$day] = Anime::published()
                    ->ongoing()
                    ->where('schedule_day', $day)
                    ->orderBy('schedule_time')
                    ->get();
            }
            return $byDay;
        });
    }

    public function search(array $filters, int $perPage = 24): LengthAwarePaginator
    {
        $q = Anime::published()->with(['genres', 'studio']);

        $this->applyFilters($q, $filters);

        $sort = $filters['sort'] ?? 'latest';
        match ($sort) {
            'popular' => $q->orderByDesc('views'),
            'rating' => $q->orderByDesc('score'),
            'oldest' => $q->oldest(),
            'name' => $q->orderBy('title'),
            default => $q->latest('updated_at'),
        };

        return $q->paginate($perPage)->withQueryString();
    }

    protected function applyFilters(Builder $q, array $filters): void
    {
        if (!empty($filters['q'])) {
            $term = trim((string) $filters['q']);
            $q->where(function ($qq) use ($term) {
                $qq->where('title', 'like', "%{$term}%")
                    ->orWhere('title_japanese', 'like', "%{$term}%")
                    ->orWhere('title_english', 'like', "%{$term}%")
                    ->orWhere('synopsis', 'like', "%{$term}%");
            });
        }
        if (!empty($filters['genre'])) {
            $q->whereHas('genres', fn ($g) => $g->where('genres.slug', $filters['genre']));
        }
        if (!empty($filters['studio'])) {
            $q->whereHas('studio', fn ($s) => $s->where('studios.slug', $filters['studio']));
        }
        if (!empty($filters['year'])) {
            $q->where('year', (int) $filters['year']);
        }
        if (!empty($filters['type'])) {
            $q->where('type', $filters['type']);
        }
        if (!empty($filters['status'])) {
            $q->where('status', $filters['status']);
        }
    }

    public function relatedAnimes(Anime $anime, int $limit = 8): Collection
    {
        $genreIds = $anime->genres->pluck('id')->all();
        if (empty($genreIds)) {
            return Anime::published()->where('id', '!=', $anime->id)->limit($limit)->get();
        }
        return Anime::published()
            ->where('id', '!=', $anime->id)
            ->whereHas('genres', fn ($g) => $g->whereIn('genres.id', $genreIds))
            ->orderByDesc('views')
            ->limit($limit)
            ->get();
    }

    public function incrementView(Anime $anime): void
    {
        $anime->newQuery()->where('id', $anime->id)->increment('views');
    }
}
