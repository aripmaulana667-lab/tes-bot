<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Support\Str;

class Studio extends Model
{
    use HasFactory;

    protected $fillable = ['name', 'slug', 'country'];

    protected static function booted(): void
    {
        static::creating(function (Studio $studio) {
            if (!$studio->slug) {
                $studio->slug = Str::slug($studio->name);
            }
        });
    }

    public function animes(): HasMany
    {
        return $this->hasMany(Anime::class);
    }

    public function getRouteKeyName(): string
    {
        return 'slug';
    }
}
