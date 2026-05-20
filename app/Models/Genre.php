<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsToMany;
use Illuminate\Support\Str;

class Genre extends Model
{
    use HasFactory;

    protected $fillable = ['name', 'slug', 'description'];

    protected static function booted(): void
    {
        static::creating(function (Genre $genre) {
            if (!$genre->slug) {
                $genre->slug = Str::slug($genre->name);
            }
        });
    }

    public function animes(): BelongsToMany
    {
        return $this->belongsToMany(Anime::class, 'anime_genre');
    }

    public function getRouteKeyName(): string
    {
        return 'slug';
    }
}
