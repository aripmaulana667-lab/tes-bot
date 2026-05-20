<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Models\Anime;
use App\Models\Genre;
use App\Models\Studio;
use App\Services\ScrapingService;
use Illuminate\Http\Request;
use Illuminate\Support\Str;

class AnimeAdminController extends Controller
{
    public function index(Request $request)
    {
        $q = Anime::query()->with('genres', 'studio');
        if ($term = $request->query('q')) {
            $q->where('title', 'like', "%{$term}%");
        }
        if ($type = $request->query('type')) {
            $q->where('type', $type);
        }
        $animes = $q->latest()->paginate(20);
        return view('admin.animes.index', compact('animes'));
    }

    public function create()
    {
        return view('admin.animes.form', [
            'anime' => new Anime(),
            'genres' => Genre::orderBy('name')->get(),
            'studios' => Studio::orderBy('name')->get(),
        ]);
    }

    public function store(Request $request)
    {
        $data = $this->validateData($request);
        $anime = Anime::create($data);
        $anime->genres()->sync($request->input('genres', []));
        return redirect()->route('admin.animes.edit', $anime)->with('status', 'Anime ditambahkan.');
    }

    public function edit(Anime $anime)
    {
        return view('admin.animes.form', [
            'anime' => $anime,
            'genres' => Genre::orderBy('name')->get(),
            'studios' => Studio::orderBy('name')->get(),
        ]);
    }

    public function update(Request $request, Anime $anime)
    {
        $data = $this->validateData($request, $anime);
        $anime->update($data);
        $anime->genres()->sync($request->input('genres', []));
        return back()->with('status', 'Anime diperbarui.');
    }

    public function destroy(Anime $anime)
    {
        $anime->delete();
        return redirect()->route('admin.animes.index')->with('status', 'Anime dihapus.');
    }

    public function bulkImport(Request $request, ScrapingService $scraper)
    {
        $source = $request->input('source', 'jikan');
        $count = 0;
        if ($source === 'jikan') {
            $count = $scraper->syncTop(1);
        } elseif ($source === 'anilist') {
            $count = $scraper->syncTrending();
        } else {
            $count = $scraper->syncOngoing();
        }
        return back()->with('status', "Imported {$count} entries from {$source}.");
    }

    protected function validateData(Request $request, ?Anime $anime = null): array
    {
        $data = $request->validate([
            'title' => 'required|string|max:255',
            'title_japanese' => 'nullable|string|max:255',
            'title_english' => 'nullable|string|max:255',
            'slug' => 'nullable|string|max:255',
            'type' => 'required|in:anime,donghua,movie,ova,ona,special',
            'status' => 'required|in:ongoing,completed,upcoming,hiatus',
            'synopsis' => 'nullable|string',
            'year' => 'nullable|integer|min:1900|max:2100',
            'season' => 'nullable|string|max:50',
            'episodes_count' => 'nullable|integer|min:0',
            'duration' => 'nullable|integer|min:0',
            'age_rating' => 'nullable|string|max:50',
            'score' => 'nullable|numeric|min:0|max:10',
            'poster' => 'nullable|string|max:500',
            'banner' => 'nullable|string|max:500',
            'poster_upload' => 'nullable|image|max:4096',
            'banner_upload' => 'nullable|image|max:8192',
            'trailer_url' => 'nullable|string|max:500',
            'studio_id' => 'nullable|exists:studios,id',
            'source' => 'nullable|string|max:100',
            'country' => 'nullable|string|max:10',
            'is_featured' => 'nullable|boolean',
            'is_published' => 'nullable|boolean',
            'schedule_day' => 'nullable|in:monday,tuesday,wednesday,thursday,friday,saturday,sunday',
            'schedule_time' => 'nullable|date_format:H:i',
            'meta_title' => 'nullable|string|max:255',
            'meta_description' => 'nullable|string|max:500',
        ]);

        if (empty($data['slug'])) {
            $data['slug'] = Anime::generateUniqueSlug($data['title']);
        } else {
            $data['slug'] = Str::slug($data['slug']);
        }

        if ($request->hasFile('poster_upload')) {
            $data['poster'] = $request->file('poster_upload')->store('animes/posters', 'public');
        }
        if ($request->hasFile('banner_upload')) {
            $data['banner'] = $request->file('banner_upload')->store('animes/banners', 'public');
        }
        unset($data['poster_upload'], $data['banner_upload']);

        $data['is_featured'] = (bool) ($data['is_featured'] ?? false);
        $data['is_published'] = (bool) ($data['is_published'] ?? true);

        return $data;
    }
}
