<?php

namespace App\Http\Controllers;

use App\Models\Anime;
use App\Services\AnimeService;
use Illuminate\Http\Request;

class AnimeController extends Controller
{
    public function show(Anime $anime, AnimeService $service)
    {
        abort_unless($anime->is_published, 404);

        $service->incrementView($anime);

        $anime->loadMissing(['genres', 'studio', 'episodes']);
        $related = $service->relatedAnimes($anime);

        return view('anime.show', [
            'anime' => $anime,
            'related' => $related,
            'recentComments' => $anime->comments()
                ->with(['user', 'replies.user'])
                ->whereNull('parent_id')
                ->where('is_approved', true)
                ->latest()
                ->take(20)
                ->get(),
        ]);
    }

    public function index(Request $request, AnimeService $service)
    {
        $filters = $request->only(['q', 'genre', 'studio', 'year', 'type', 'status', 'sort']);
        $items = $service->search($filters, 24);
        return view('anime.index', [
            'animes' => $items,
            'filters' => $filters,
        ]);
    }

    public function ongoing(AnimeService $service)
    {
        $items = $service->search(['status' => 'ongoing'], 24);
        return view('anime.index', [
            'animes' => $items,
            'filters' => ['status' => 'ongoing'],
            'pageTitle' => 'Anime Ongoing',
        ]);
    }

    public function completed(AnimeService $service)
    {
        $items = $service->search(['status' => 'completed'], 24);
        return view('anime.index', [
            'animes' => $items,
            'filters' => ['status' => 'completed'],
            'pageTitle' => 'Anime Completed',
        ]);
    }

    public function donghua(AnimeService $service)
    {
        $items = $service->search(['type' => 'donghua'], 24);
        return view('anime.index', [
            'animes' => $items,
            'filters' => ['type' => 'donghua'],
            'pageTitle' => 'Donghua',
        ]);
    }

    public function schedule(AnimeService $service)
    {
        return view('anime.schedule', [
            'schedule' => $service->schedule(),
        ]);
    }
}
