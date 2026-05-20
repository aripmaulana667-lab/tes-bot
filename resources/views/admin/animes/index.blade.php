@extends('admin.layout')
@section('content')
<div class="flex justify-between items-center mb-4">
    <h1 class="text-2xl font-bold">Manajemen Anime</h1>
    <div class="flex gap-2">
        <form method="POST" action="{{ route('admin.animes.bulk_import') }}" class="flex gap-2">@csrf
            <select name="source" class="bg-white/5 border border-white/10 rounded-lg px-2 py-1 text-sm">
                <option value="ongoing">Jikan Ongoing</option>
                <option value="jikan">Jikan Top</option>
                <option value="anilist">AniList Trending</option>
            </select>
            <button class="px-3 py-1.5 rounded-lg bg-amber-500 text-black text-sm">Auto Import</button>
        </form>
        <a href="{{ route('admin.animes.create') }}" class="px-3 py-1.5 rounded-lg bg-fuchsia-600 hover:bg-fuchsia-500 text-sm">+ Anime Baru</a>
    </div>
</div>

<form method="GET" class="mb-4 flex gap-2">
    <input name="q" value="{{ request('q') }}" placeholder="Cari…" class="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm">
    <select name="type" class="bg-white/5 border border-white/10 rounded-lg px-2 py-2 text-sm">
        <option value="">Semua Type</option>
        @foreach (['anime','donghua','movie','ova','ona','special'] as $t)
            <option value="{{ $t }}" @selected(request('type') === $t)>{{ ucfirst($t) }}</option>
        @endforeach
    </select>
    <button class="px-3 py-2 rounded-lg bg-white/5 text-sm">Filter</button>
</form>

<div class="overflow-x-auto rounded-2xl border border-white/10 bg-black/20">
    <table class="w-full text-sm">
        <thead class="text-xs uppercase text-slate-400">
            <tr>
                <th class="text-left p-3">Title</th>
                <th class="text-left p-3">Type</th>
                <th class="text-left p-3">Status</th>
                <th class="text-left p-3">Eps</th>
                <th class="text-left p-3">Views</th>
                <th class="text-left p-3">Action</th>
            </tr>
        </thead>
        <tbody>
        @foreach ($animes as $a)
            <tr class="border-t border-white/5">
                <td class="p-3 flex items-center gap-2">
                    <img src="{{ $a->posterUrl() }}" class="w-8 h-12 object-cover rounded">
                    <a href="{{ route('admin.animes.edit', $a) }}" class="hover:text-fuchsia-300">{{ $a->title }}</a>
                </td>
                <td class="p-3 capitalize">{{ $a->type }}</td>
                <td class="p-3 capitalize">{{ $a->status }}</td>
                <td class="p-3">{{ $a->episodes_count }}</td>
                <td class="p-3">{{ number_format($a->views) }}</td>
                <td class="p-3 flex gap-2 text-xs">
                    <a href="{{ route('admin.animes.edit', $a) }}" class="text-emerald-300">Edit</a>
                    <a href="{{ route('admin.animes.episodes.index', $a) }}" class="text-amber-300">Episodes</a>
                    <form method="POST" action="{{ route('admin.animes.destroy', $a) }}" onsubmit="return confirm('Hapus anime ini?')">@csrf @method('DELETE')<button class="text-rose-300">Hapus</button></form>
                </td>
            </tr>
        @endforeach
        </tbody>
    </table>
</div>
<div class="mt-4">{{ $animes->withQueryString()->links() }}</div>
@endsection
