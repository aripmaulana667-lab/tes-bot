<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class EpisodeServer extends Model
{
    use HasFactory;

    protected $fillable = [
        'episode_id', 'server_name', 'type', 'url', 'quality',
        'language', 'subtitle_url', 'priority', 'is_active',
    ];

    protected $casts = [
        'is_active' => 'boolean',
    ];

    public function episode(): BelongsTo
    {
        return $this->belongsTo(Episode::class);
    }
}
