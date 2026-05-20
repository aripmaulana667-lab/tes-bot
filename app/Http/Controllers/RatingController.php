<?php

namespace App\Http\Controllers;

use App\Models\Anime;
use App\Models\Rating;
use Illuminate\Http\Request;

class RatingController extends Controller
{
    public function store(Request $request, Anime $anime)
    {
        $data = $request->validate([
            'score' => 'required|integer|min:1|max:10',
            'review' => 'nullable|string|max:2000',
        ]);
        $rating = Rating::updateOrCreate(
            ['user_id' => $request->user()->id, 'anime_id' => $anime->id],
            ['score' => $data['score'], 'review' => $data['review'] ?? null]
        );

        $avg = $anime->ratings()->avg('score');
        $anime->update(['score' => $avg]);

        if ($request->expectsJson()) {
            return response()->json([
                'rating' => $rating,
                'average' => round($avg, 2),
            ]);
        }
        return back()->with('status', 'Rating saved.');
    }
}
