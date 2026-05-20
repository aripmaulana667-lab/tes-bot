@extends('admin.layout')
@section('content')
<div class="flex items-center justify-between mb-4">
    <div>
        <h1 class="text-2xl font-bold">Episodes — {{ $anime->title }}</h1>
        <a href="{{ route('admin.animes.index') }}" class="text-xs text-slate-400 hover:text-white">← Kembali ke daftar anime</a>
    </div>
    <div class="flex gap-2">
        <form method="POST" action="{{ route('admin.animes.episodes.batch', $anime) }}" enctype="multipart/form-data" class="flex items-center gap-2 text-xs">
            @csrf
            <label class="text-slate-400">Upload CSV (number,title,url,server,type,quality,language):</label>
            <input type="file" name="csv" accept=".csv" required class="text-xs">
            <button class="px-2 py-1 rounded bg-amber-500 text-black">Batch Import</button>
        </form>
        <a href="{{ route('admin.animes.episodes.create', $anime) }}" class="px-3 py-1.5 rounded-lg bg-fuchsia-600 text-sm">+ Episode</a>
    </div>
</div>

<div class="overflow-x-auto rounded-2xl border border-white/10 bg-black/20">
    <table class="w-full text-sm">
        <thead class="text-xs uppercase text-slate-400">
            <tr><th class="text-left p-3">No</th><th class="text-left p-3">Title</th><th class="text-left p-3">Servers</th><th class="text-left p-3">Premium</th><th class="text-left p-3">Aksi</th></tr>
        </thead>
        <tbody>
            @foreach ($episodes as $ep)
                <tr class="border-t border-white/5">
                    <td class="p-3 font-semibold">{{ $ep->number }}</td>
                    <td class="p-3">{{ $ep->title ?? 'Episode '.$ep->number }}</td>
                    <td class="p-3">{{ $ep->servers->count() }}</td>
                    <td class="p-3">{{ $ep->is_premium ? '⭐' : '—' }}</td>
                    <td class="p-3 flex gap-2 text-xs">
                        <a href="{{ route('admin.animes.episodes.edit', [$anime, $ep]) }}" class="text-emerald-300">Edit</a>
                        <form method="POST" action="{{ route('admin.animes.episodes.destroy', [$anime, $ep]) }}" onsubmit="return confirm('Hapus?')">@csrf @method('DELETE')<button class="text-rose-300">Hapus</button></form>
                    </td>
                </tr>
            @endforeach
        </tbody>
    </table>
</div>
<div class="mt-4">{{ $episodes->links() }}</div>
@endsection
