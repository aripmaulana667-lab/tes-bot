<?php

namespace App\Http\Controllers;

use App\Models\WatchHistory;
use Illuminate\Http\Request;

class HistoryController extends Controller
{
    public function index(Request $request)
    {
        $history = $request->user()
            ->watchHistory()
            ->with(['anime', 'episode'])
            ->latest('updated_at')
            ->paginate(24);
        return view('user.history', compact('history'));
    }

    public function track(Request $request)
    {
        $data = $request->validate([
            'episode_id' => 'required|integer|exists:episodes,id',
            'progress_seconds' => 'required|integer|min:0',
            'duration_seconds' => 'required|integer|min:0',
        ]);

        $episode = \App\Models\Episode::findOrFail($data['episode_id']);

        $hist = WatchHistory::updateOrCreate(
            [
                'user_id' => $request->user()->id,
                'episode_id' => $episode->id,
            ],
            [
                'anime_id' => $episode->anime_id,
                'progress_seconds' => $data['progress_seconds'],
                'duration_seconds' => $data['duration_seconds'],
                'completed_at' => $data['progress_seconds'] >= max(1, $data['duration_seconds'] * 0.9)
                    ? now()
                    : null,
            ]
        );

        return response()->json(['ok' => true, 'percent' => $hist->progressPercent()]);
    }

    public function destroy(Request $request, WatchHistory $watchHistory)
    {
        abort_unless($watchHistory->user_id === $request->user()->id, 403);
        $watchHistory->delete();
        return back()->with('status', 'Removed from history.');
    }
}
