@extends('layouts.app')
@section('content')
<section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
    <h1 class="text-3xl font-extrabold gradient-text">Cari Anime</h1>

    <form method="GET" action="{{ route('search.index') }}" class="mt-4 glass rounded-2xl p-4 grid md:grid-cols-7 gap-3 text-sm">
        <input name="q" value="{{ $filters['q'] ?? '' }}" placeholder="Cari judul…" class="md:col-span-2 rounded-xl bg-white/5 border border-white/10 px-3 py-2">
        <select name="type" class="rounded-xl bg-white/5 border border-white/10 px-3 py-2">
            <option value="">Type</option>
            @foreach (['anime','donghua','movie','ova','ona','special'] as $t)
                <option value="{{ $t }}" @selected(($filters['type'] ?? '') === $t)>{{ ucfirst($t) }}</option>
            @endforeach
        </select>
        <select name="status" class="rounded-xl bg-white/5 border border-white/10 px-3 py-2">
            <option value="">Status</option>
            @foreach (['ongoing','completed','upcoming','hiatus'] as $s)
                <option value="{{ $s }}" @selected(($filters['status'] ?? '') === $s)>{{ ucfirst($s) }}</option>
            @endforeach
        </select>
        <select name="genre" class="rounded-xl bg-white/5 border border-white/10 px-3 py-2">
            <option value="">Genre</option>
            @foreach ($genres as $g)
                <option value="{{ $g->slug }}" @selected(($filters['genre'] ?? '') === $g->slug)>{{ $g->name }}</option>
            @endforeach
        </select>
        <select name="studio" class="rounded-xl bg-white/5 border border-white/10 px-3 py-2">
            <option value="">Studio</option>
            @foreach ($studios as $s)
                <option value="{{ $s->slug }}" @selected(($filters['studio'] ?? '') === $s->slug)>{{ $s->name }}</option>
            @endforeach
        </select>
        <select name="year" class="rounded-xl bg-white/5 border border-white/10 px-3 py-2">
            <option value="">Tahun</option>
            @foreach (range(date('Y')+1, 1990) as $y)
                <option value="{{ $y }}" @selected(($filters['year'] ?? '') == $y)>{{ $y }}</option>
            @endforeach
        </select>
        <button class="rounded-xl bg-brand-600 hover:bg-brand-500 px-4 py-2">Cari</button>
    </form>

    <div class="mt-6 grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        @forelse($animes as $a)
            <x-anime-card :anime="$a" />
        @empty
            <p class="col-span-full text-center text-slate-400 py-10">Tidak ada hasil.</p>
        @endforelse
    </div>
    <div class="mt-6">{{ $animes->links() }}</div>
</section>
@endsection
