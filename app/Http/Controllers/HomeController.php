<?php

namespace App\Http\Controllers;

use App\Models\Genre;
use App\Services\AnimeService;

class HomeController extends Controller
{
    public function __invoke(AnimeService $service)
    {
        return view('home', [
            'featured' => $service->featured(),
            'latestEpisodes' => $service->latestEpisodes(24),
            'trending' => $service->trending(12),
            'ongoing' => $service->ongoing(12),
            'completed' => $service->completed(12),
            'donghua' => $service->popularDonghua(12),
            'topView' => $service->topView(10),
            'recommendations' => $service->recommendations(12),
            'genres' => Genre::orderBy('name')->limit(30)->get(),
            'schedule' => $service->schedule(),
        ]);
    }
}
