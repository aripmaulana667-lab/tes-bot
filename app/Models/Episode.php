<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Database\Eloquent\Relations\MorphMany;
use Illuminate\Support\Str;

class Episode extends Model
{
    use HasFactory;

    protected $fillable = [
        'anime_id', 'number', 'title', 'slug', 'synopsis', 'thumbnail',
        'duration', 'air_date', 'views', 'is_premium', 'is_published',
        'download_url',
    ];

    protected $casts = [
        'is_premium' => 'boolean',
        'is_published' => 'boolean',
        'air_date' => 'date',
        'views' => 'int',
        'duration' => 'int',
    ];

    protected static function booted(): void
    {
        static::creating(function (Episode $episode) {
            if (!$episode->slug) {
                $anime = $episode->anime ?: Anime::find($episode->anime_id);
                $base = ($anime ? $anime->slug : 'episode') . '-episode-' . Str::slug($episode->number);
                $slug = $base;
                $i = 1;
                while (static::where('slug', $slug)->exists()) {
                    $slug = $base . '-' . $i++;
                }
                $episode->slug = $slug;
            }
        });
    }

    public function getRouteKeyName(): string
    {
        return 'slug';
    }

    public function anime(): BelongsTo
    {
        return $this->belongsTo(Anime::class);
    }

    public function servers(): HasMany
    {
        return $this->hasMany(EpisodeServer::class)->orderBy('priority');
    }

    public function comments(): MorphMany
    {
        return $this->morphMany(Comment::class, 'commentable');
    }

    public function watchHistory(): HasMany
    {
        return $this->hasMany(WatchHistory::class);
    }

    public function thumbnailUrl(): string
    {
        if (!$this->thumbnail) {
            return $this->anime ? $this->anime->bannerUrl() : asset('images/no-poster.svg');
        }
        if (str_starts_with($this->thumbnail, 'http')) {
            return $this->thumbnail;
        }
        return asset('storage/' . $this->thumbnail);
    }

    public function url(): string
    {
        return route('episode.show', ['anime' => $this->anime->slug, 'episode' => $this]);
    }

    public function nextEpisode(): ?Episode
    {
        return static::where('anime_id', $this->anime_id)
            ->where('is_published', true)
            ->whereRaw('CAST(number AS UNSIGNED) > ?', [(int) $this->number])
            ->orderByRaw('CAST(number AS UNSIGNED) asc')
            ->first();
    }

    public function previousEpisode(): ?Episode
    {
        return static::where('anime_id', $this->anime_id)
            ->where('is_published', true)
            ->whereRaw('CAST(number AS UNSIGNED) < ?', [(int) $this->number])
            ->orderByRaw('CAST(number AS UNSIGNED) desc')
            ->first();
    }
}
