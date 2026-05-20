<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Builder;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\BelongsToMany;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Database\Eloquent\Relations\MorphMany;
use Illuminate\Support\Str;

class Anime extends Model
{
    use HasFactory;

    protected $fillable = [
        'title', 'title_japanese', 'title_english', 'slug', 'type', 'status',
        'synopsis', 'year', 'season', 'episodes_count', 'duration', 'age_rating',
        'score', 'mal_id', 'anilist_id', 'poster', 'banner', 'trailer_url',
        'studio_id', 'source', 'country', 'is_featured', 'is_published', 'views',
        'schedule_day', 'schedule_time', 'meta_title', 'meta_description',
    ];

    protected $casts = [
        'is_featured' => 'boolean',
        'is_published' => 'boolean',
        'score' => 'float',
        'views' => 'int',
        'year' => 'int',
        'schedule_time' => 'datetime',
    ];

    protected static function booted(): void
    {
        static::creating(function (Anime $anime) {
            if (!$anime->slug) {
                $anime->slug = static::generateUniqueSlug($anime->title);
            }
        });
    }

    public static function generateUniqueSlug(string $title): string
    {
        $base = Str::slug($title);
        $slug = $base;
        $i = 1;
        while (static::where('slug', $slug)->exists()) {
            $slug = $base . '-' . $i++;
        }
        return $slug;
    }

    public function getRouteKeyName(): string
    {
        return 'slug';
    }

    public function genres(): BelongsToMany
    {
        return $this->belongsToMany(Genre::class, 'anime_genre');
    }

    public function studio(): BelongsTo
    {
        return $this->belongsTo(Studio::class);
    }

    public function episodes(): HasMany
    {
        return $this->hasMany(Episode::class)->orderBy('number');
    }

    public function comments(): MorphMany
    {
        return $this->morphMany(Comment::class, 'commentable');
    }

    public function ratings(): HasMany
    {
        return $this->hasMany(Rating::class);
    }

    public function bookmarks(): HasMany
    {
        return $this->hasMany(Bookmark::class);
    }

    public function watchHistory(): HasMany
    {
        return $this->hasMany(WatchHistory::class);
    }

    public function scopeAnime(Builder $q): Builder
    {
        return $q->whereIn('type', ['anime', 'movie', 'ova', 'ona', 'special']);
    }

    public function scopeDonghua(Builder $q): Builder
    {
        return $q->where('type', 'donghua');
    }

    public function scopeOngoing(Builder $q): Builder
    {
        return $q->where('status', 'ongoing');
    }

    public function scopeCompleted(Builder $q): Builder
    {
        return $q->where('status', 'completed');
    }

    public function scopePublished(Builder $q): Builder
    {
        return $q->where('is_published', true);
    }

    public function posterUrl(): string
    {
        if (!$this->poster) {
            return asset('images/no-poster.svg');
        }
        if (str_starts_with($this->poster, 'http')) {
            return $this->poster;
        }
        return asset('storage/' . $this->poster);
    }

    public function bannerUrl(): string
    {
        if (!$this->banner) {
            return $this->posterUrl();
        }
        if (str_starts_with($this->banner, 'http')) {
            return $this->banner;
        }
        return asset('storage/' . $this->banner);
    }

    public function url(): string
    {
        return route('anime.show', $this);
    }

    public function ratingAverage(): float
    {
        return (float) ($this->ratings()->avg('score') ?? 0);
    }
}
