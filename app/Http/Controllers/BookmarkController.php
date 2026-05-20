<?php

namespace App\Http\Controllers;

use App\Models\Anime;
use App\Models\Bookmark;
use Illuminate\Http\Request;

class BookmarkController extends Controller
{
    public function index(Request $request)
    {
        $bookmarks = $request->user()
            ->bookmarks()
            ->with('anime.genres')
            ->latest()
            ->paginate(24);
        return view('user.bookmarks', compact('bookmarks'));
    }

    public function toggle(Request $request, Anime $anime)
    {
        $existing = Bookmark::where('user_id', $request->user()->id)
            ->where('anime_id', $anime->id)
            ->first();
        if ($existing) {
            $existing->delete();
            return response()->json(['bookmarked' => false]);
        }
        Bookmark::create([
            'user_id' => $request->user()->id,
            'anime_id' => $anime->id,
        ]);
        return response()->json(['bookmarked' => true]);
    }
}
