<?php

namespace App\Http\Controllers;

use App\Models\Anime;
use App\Models\Episode;
use App\Models\WatchHistory;
use Illuminate\Http\Request;

class EpisodeController extends Controller
{
    public function show(Anime $anime, Episode $episode, Request $request)
    {
        abort_unless($episode->anime_id === $anime->id, 404);
        abort_unless($episode->is_published && $anime->is_published, 404);

        if ($episode->is_premium) {
            $user = $request->user();
            if (!$user || !$user->isPremium()) {
                return view('episode.premium_required', [
                    'anime' => $anime,
                    'episode' => $episode,
                ]);
            }
        }

        $episode->newQuery()->where('id', $episode->id)->increment('views');

        $episode->loadMissing(['servers' => fn ($q) => $q->where('is_active', true)]);

        $next = $episode->nextEpisode();
        $previous = $episode->previousEpisode();

        $progress = null;
        if ($user = $request->user()) {
            $progress = WatchHistory::where('user_id', $user->id)
                ->where('episode_id', $episode->id)
                ->first();
        }

        return view('episode.show', [
            'anime' => $anime,
            'episode' => $episode,
            'next' => $next,
            'previous' => $previous,
            'progress' => $progress,
            'allEpisodes' => $anime->episodes()->where('is_published', true)->get(),
            'comments' => $episode->comments()
                ->with(['user', 'replies.user'])
                ->whereNull('parent_id')
                ->where('is_approved', true)
                ->latest()
                ->take(30)
                ->get(),
        ]);
    }
}
