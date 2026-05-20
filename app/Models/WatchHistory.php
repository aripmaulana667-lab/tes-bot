<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class WatchHistory extends Model
{
    protected $table = 'watch_histories';

    protected $fillable = [
        'user_id', 'anime_id', 'episode_id', 'progress_seconds',
        'duration_seconds', 'completed_at',
    ];

    protected $casts = [
        'completed_at' => 'datetime',
        'progress_seconds' => 'int',
        'duration_seconds' => 'int',
    ];

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    public function anime(): BelongsTo
    {
        return $this->belongsTo(Anime::class);
    }

    public function episode(): BelongsTo
    {
        return $this->belongsTo(Episode::class);
    }

    public function progressPercent(): int
    {
        if (!$this->duration_seconds) {
            return 0;
        }
        return (int) min(100, round(($this->progress_seconds / $this->duration_seconds) * 100));
    }
}
