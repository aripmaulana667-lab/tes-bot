<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Models\Anime;
use App\Models\Episode;
use App\Models\EpisodeServer;
use Illuminate\Http\Request;
use Illuminate\Support\Str;

class EpisodeAdminController extends Controller
{
    public function index(Request $request, Anime $anime)
    {
        $episodes = $anime->episodes()->with('servers')->paginate(30);
        return view('admin.episodes.index', compact('anime', 'episodes'));
    }

    public function create(Anime $anime)
    {
        return view('admin.episodes.form', [
            'anime' => $anime,
            'episode' => new Episode(['anime_id' => $anime->id]),
        ]);
    }

    public function store(Request $request, Anime $anime)
    {
        $data = $this->validateData($request, $anime);
        $episode = $anime->episodes()->create($data);
        $this->syncServers($episode, $request);
        return redirect()->route('admin.animes.episodes.index', $anime)->with('status', 'Episode ditambahkan.');
    }

    public function edit(Anime $anime, Episode $episode)
    {
        abort_unless($episode->anime_id === $anime->id, 404);
        $episode->load('servers');
        return view('admin.episodes.form', compact('anime', 'episode'));
    }

    public function update(Request $request, Anime $anime, Episode $episode)
    {
        abort_unless($episode->anime_id === $anime->id, 404);
        $data = $this->validateData($request, $anime, $episode);
        $episode->update($data);
        $this->syncServers($episode, $request);
        return back()->with('status', 'Episode diperbarui.');
    }

    public function destroy(Anime $anime, Episode $episode)
    {
        abort_unless($episode->anime_id === $anime->id, 404);
        $episode->delete();
        return back()->with('status', 'Episode dihapus.');
    }

    public function batchUpload(Request $request, Anime $anime)
    {
        $data = $request->validate([
            'csv' => 'required|file|max:4096',
        ]);
        $path = $data['csv']->getRealPath();
        $count = 0;
        if (($handle = fopen($path, 'r')) !== false) {
            $headers = null;
            while (($row = fgetcsv($handle)) !== false) {
                if (!$headers) {
                    $headers = $row;
                    continue;
                }
                $rec = array_combine($headers, $row);
                if (empty($rec['number'])) {
                    continue;
                }
                $ep = Episode::updateOrCreate(
                    ['anime_id' => $anime->id, 'number' => $rec['number']],
                    [
                        'title' => $rec['title'] ?? null,
                        'is_premium' => !empty($rec['is_premium']),
                        'is_published' => true,
                        'air_date' => $rec['air_date'] ?? null,
                        'duration' => $rec['duration'] ?? null,
                    ]
                );
                if (!empty($rec['url'])) {
                    EpisodeServer::create([
                        'episode_id' => $ep->id,
                        'server_name' => $rec['server'] ?? 'Default',
                        'type' => $rec['type'] ?? 'iframe',
                        'url' => $rec['url'],
                        'quality' => $rec['quality'] ?? '720p',
                        'language' => $rec['language'] ?? 'sub',
                        'priority' => (int) ($rec['priority'] ?? 0),
                        'is_active' => true,
                    ]);
                }
                $count++;
            }
            fclose($handle);
        }
        return back()->with('status', "Imported {$count} episodes.");
    }

    protected function validateData(Request $request, Anime $anime, ?Episode $episode = null): array
    {
        $data = $request->validate([
            'number' => 'required|string|max:20',
            'title' => 'nullable|string|max:255',
            'slug' => 'nullable|string|max:255',
            'synopsis' => 'nullable|string',
            'thumbnail' => 'nullable|string|max:500',
            'thumbnail_upload' => 'nullable|image|max:4096',
            'duration' => 'nullable|integer|min:0',
            'air_date' => 'nullable|date',
            'is_premium' => 'nullable|boolean',
            'is_published' => 'nullable|boolean',
            'download_url' => 'nullable|string|max:500',
        ]);
        if (empty($data['slug'])) {
            $data['slug'] = Str::slug($anime->slug . '-episode-' . $data['number']);
        }
        if ($request->hasFile('thumbnail_upload')) {
            $data['thumbnail'] = $request->file('thumbnail_upload')->store('episodes/thumbnails', 'public');
        }
        unset($data['thumbnail_upload']);
        $data['is_premium'] = (bool) ($data['is_premium'] ?? false);
        $data['is_published'] = (bool) ($data['is_published'] ?? true);
        return $data;
    }

    protected function syncServers(Episode $episode, Request $request): void
    {
        $servers = $request->input('servers', []);
        $keepIds = [];
        foreach ($servers as $s) {
            if (empty($s['url']) || empty($s['server_name'])) {
                continue;
            }
            if (!empty($s['id'])) {
                $server = EpisodeServer::where('episode_id', $episode->id)->find($s['id']);
                if ($server) {
                    $server->update([
                        'server_name' => $s['server_name'],
                        'type' => $s['type'] ?? 'iframe',
                        'url' => $s['url'],
                        'quality' => $s['quality'] ?? '720p',
                        'language' => $s['language'] ?? 'sub',
                        'subtitle_url' => $s['subtitle_url'] ?? null,
                        'priority' => (int) ($s['priority'] ?? 0),
                        'is_active' => !empty($s['is_active']),
                    ]);
                    $keepIds[] = $server->id;
                }
            } else {
                $server = EpisodeServer::create([
                    'episode_id' => $episode->id,
                    'server_name' => $s['server_name'],
                    'type' => $s['type'] ?? 'iframe',
                    'url' => $s['url'],
                    'quality' => $s['quality'] ?? '720p',
                    'language' => $s['language'] ?? 'sub',
                    'subtitle_url' => $s['subtitle_url'] ?? null,
                    'priority' => (int) ($s['priority'] ?? 0),
                    'is_active' => !empty($s['is_active']),
                ]);
                $keepIds[] = $server->id;
            }
        }
        EpisodeServer::where('episode_id', $episode->id)
            ->whereNotIn('id', $keepIds)
            ->delete();
    }
}
