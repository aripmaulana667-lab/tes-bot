<?php

namespace App\Http\Controllers;

use App\Models\Anime;
use App\Models\Genre;
use App\Models\Studio;
use App\Services\AnimeService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class SearchController extends Controller
{
    public function index(Request $request, AnimeService $service)
    {
        $filters = $request->only(['q', 'genre', 'studio', 'year', 'type', 'status', 'sort']);
        $animes = $service->search($filters, 24);
        return view('search.index', [
            'animes' => $animes,
            'filters' => $filters,
            'genres' => Genre::orderBy('name')->get(),
            'studios' => Studio::orderBy('name')->get(),
            'years' => range((int) date('Y') + 1, 1990),
        ]);
    }

    public function realtime(Request $request): JsonResponse
    {
        $term = trim((string) $request->query('q', ''));
        if (mb_strlen($term) < 2) {
            return response()->json(['results' => []]);
        }
        $results = Anime::published()
            ->where(function ($q) use ($term) {
                $q->where('title', 'like', "%{$term}%")
                    ->orWhere('title_japanese', 'like', "%{$term}%")
                    ->orWhere('title_english', 'like', "%{$term}%");
            })
            ->orderByDesc('views')
            ->limit(8)
            ->get()
            ->map(fn (Anime $a) => [
                'id' => $a->id,
                'title' => $a->title,
                'slug' => $a->slug,
                'url' => $a->url(),
                'type' => $a->type,
                'status' => $a->status,
                'year' => $a->year,
                'score' => $a->score,
                'poster' => $a->posterUrl(),
            ]);
        return response()->json(['results' => $results]);
    }
}
