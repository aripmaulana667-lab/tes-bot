@extends('layouts.app')
@section('content')
<section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
    <h1 class="text-3xl font-extrabold gradient-text">Genre</h1>
    <div class="mt-6 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
        @foreach ($genres as $g)
            <a href="{{ route('genre.show', $g) }}" class="glass rounded-xl px-4 py-3 hover:bg-brand-600/30 hover:border-brand-500 transition">
                <div class="text-lg font-semibold">{{ $g->name }}</div>
                <div class="text-xs text-slate-400">{{ $g->animes_count }} judul</div>
            </a>
        @endforeach
    </div>
</section>
@endsection
