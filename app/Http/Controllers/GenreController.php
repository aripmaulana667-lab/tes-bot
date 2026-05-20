<?php

namespace App\Http\Controllers;

use App\Models\Genre;

class GenreController extends Controller
{
    public function index()
    {
        $genres = Genre::withCount('animes')->orderBy('name')->get();
        return view('genre.index', compact('genres'));
    }

    public function show(Genre $genre)
    {
        $animes = $genre->animes()
            ->where('is_published', true)
            ->with('genres')
            ->orderByDesc('updated_at')
            ->paginate(24);
        return view('genre.show', compact('genre', 'animes'));
    }
}
