@extends('layouts.app')

@section('content')
<section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
    <h1 class="text-3xl font-extrabold gradient-text">{{ $pageTitle ?? 'Daftar Anime' }}</h1>

    <form method="GET" class="mt-6 glass rounded-2xl p-4 grid md:grid-cols-6 gap-3 items-end text-sm">
        <div class="md:col-span-2">
            <label class="block text-xs text-slate-400 mb-1">Cari</label>
            <input type="text" name="q" value="{{ $filters['q'] ?? '' }}" placeholder="Judul…" class="w-full rounded-xl bg-white/5 border border-white/10 px-3 py-2">
        </div>
        <div>
            <label class="block text-xs text-slate-400 mb-1">Type</label>
            <select name="type" class="w-full rounded-xl bg-white/5 border border-white/10 px-3 py-2">
                <option value="">Semua</option>
                @foreach (['anime','donghua','movie','ova','ona','special'] as $t)
                    <option value="{{ $t }}" @selected(($filters['type'] ?? '') === $t)>{{ ucfirst($t) }}</option>
                @endforeach
            </select>
        </div>
        <div>
            <label class="block text-xs text-slate-400 mb-1">Status</label>
            <select name="status" class="w-full rounded-xl bg-white/5 border border-white/10 px-3 py-2">
                <option value="">Semua</option>
                @foreach (['ongoing','completed','upcoming','hiatus'] as $s)
                    <option value="{{ $s }}" @selected(($filters['status'] ?? '') === $s)>{{ ucfirst($s) }}</option>
                @endforeach
            </select>
        </div>
        <div>
            <label class="block text-xs text-slate-400 mb-1">Genre</label>
            <select name="genre" class="w-full rounded-xl bg-white/5 border border-white/10 px-3 py-2">
                <option value="">Semua</option>
                @foreach (\App\Models\Genre::orderBy('name')->get() as $g)
                    <option value="{{ $g->slug }}" @selected(($filters['genre'] ?? '') === $g->slug)>{{ $g->name }}</option>
                @endforeach
            </select>
        </div>
        <div>
            <label class="block text-xs text-slate-400 mb-1">Sort</label>
            <select name="sort" class="w-full rounded-xl bg-white/5 border border-white/10 px-3 py-2">
                @foreach (['latest'=>'Terbaru','popular'=>'Populer','rating'=>'Rating','name'=>'Nama','oldest'=>'Terlama'] as $k => $v)
                    <option value="{{ $k }}" @selected(($filters['sort'] ?? '') === $k)>{{ $v }}</option>
                @endforeach
            </select>
        </div>
        <div class="md:col-span-6 flex gap-2">
            <button class="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500">Filter</button>
            <a href="{{ url()->current() }}" class="px-4 py-2 rounded-xl border border-white/10 hover:bg-white/5">Reset</a>
        </div>
    </form>

    <div class="mt-6 grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        @forelse ($animes as $a)
            <x-anime-card :anime="$a" />
        @empty
            <p class="col-span-full text-center text-slate-400 py-12">Tidak ada hasil.</p>
        @endforelse
    </div>

    <div class="mt-8">{{ $animes->links() }}</div>
</section>
@endsection
