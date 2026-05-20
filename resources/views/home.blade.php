@extends('layouts.app')

@section('content')
<section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
    @if($featured->count())
    <div x-data="{ idx: 0, total: {{ $featured->count() }} }" x-init="setInterval(() => idx = (idx+1) % total, 8000)" class="relative h-[420px] md:h-[520px] rounded-3xl overflow-hidden shadow-2xl">
        @foreach ($featured as $i => $a)
            <div x-show="idx === {{ $i }}" x-transition.opacity.duration.700ms class="absolute inset-0">
                <img src="{{ $a->bannerUrl() }}" alt="{{ $a->title }}" class="w-full h-full object-cover">
                <div class="absolute inset-0 bg-gradient-to-r from-ink-900 via-ink-900/80 to-transparent"></div>
                <div class="absolute inset-0 flex items-end p-6 md:p-10">
                    <div class="max-w-2xl">
                        <div class="flex gap-2 text-xs uppercase tracking-wider text-slate-300">
                            <span class="px-2 py-1 rounded-full bg-brand-600/30 border border-brand-400/30">{{ ucfirst($a->type) }}</span>
                            <span class="px-2 py-1 rounded-full bg-emerald-500/20 border border-emerald-400/30">{{ ucfirst($a->status) }}</span>
                            @if($a->score) <span class="px-2 py-1 rounded-full bg-amber-500/30 border border-amber-400/30">⭐ {{ number_format((float)$a->score,1) }}</span> @endif
                        </div>
                        <h1 class="text-3xl md:text-5xl font-extrabold mt-3 gradient-text">{{ $a->title }}</h1>
                        <p class="mt-3 text-slate-200 line-clamp-3 max-w-xl">{{ \Illuminate\Support\Str::limit($a->synopsis, 220) }}</p>
                        <div class="mt-4 flex gap-2">
                            <a href="{{ $a->url() }}" class="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 shadow-neon">
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white" class="w-4 h-4"><path d="M8 5v14l11-7z"/></svg>
                                Tonton Sekarang
                            </a>
                            <a href="{{ $a->url() }}#info" class="px-4 py-2 rounded-xl border border-white/10 hover:bg-white/5">Detail</a>
                        </div>
                    </div>
                </div>
            </div>
        @endforeach
        <div class="absolute bottom-4 right-6 flex gap-2">
            @foreach ($featured as $i => $a)
                <button @click="idx={{ $i }}" :class="idx === {{ $i }} ? 'bg-white w-8' : 'bg-white/30 w-3'" class="h-2 rounded-full transition-all"></button>
            @endforeach
        </div>
    </div>
    @endif
</section>

<x-ad-slot slot="header" />

@if ($latestEpisodes->count())
<section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-10">
    <x-section-heading title="Episode Terbaru" :href="route('anime.ongoing')" />
    <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        @foreach ($latestEpisodes->take(12) as $ep)
            <x-episode-card :episode="$ep" />
        @endforeach
    </div>
</section>
@endif

<section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-10">
    <x-section-heading title="Trending" />
    <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        @foreach ($trending as $a)
            <x-anime-card :anime="$a" />
        @endforeach
    </div>
</section>

<section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-10 grid lg:grid-cols-3 gap-8">
    <div class="lg:col-span-2">
        <x-section-heading title="Anime Ongoing" :href="route('anime.ongoing')" />
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            @foreach ($ongoing as $a)
                <x-anime-card :anime="$a" />
            @endforeach
        </div>

        <div class="mt-10">
            <x-section-heading title="Anime Completed" :href="route('anime.completed')" />
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                @foreach ($completed as $a)
                    <x-anime-card :anime="$a" />
                @endforeach
            </div>
        </div>

        <div class="mt-10">
            <x-section-heading title="Donghua Populer" :href="route('anime.donghua')" />
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                @foreach ($donghua as $a)
                    <x-anime-card :anime="$a" />
                @endforeach
            </div>
        </div>

        <div class="mt-10">
            <x-section-heading title="Rekomendasi" />
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                @foreach ($recommendations as $a)
                    <x-anime-card :anime="$a" />
                @endforeach
            </div>
        </div>
    </div>

    <aside class="space-y-8">
        <div>
            <x-section-heading title="Top View" />
            <ol class="space-y-3">
                @foreach ($topView as $i => $a)
                <li>
                    <a href="{{ $a->url() }}" class="flex gap-3 items-center group">
                        <span class="text-2xl font-extrabold w-8 text-center gradient-text">{{ str_pad($i+1, 2, '0', STR_PAD_LEFT) }}</span>
                        <img src="{{ $a->posterUrl() }}" class="w-12 h-16 object-cover rounded" alt="{{ $a->title }}">
                        <div>
                            <div class="text-sm font-semibold line-clamp-1 group-hover:text-brand-300">{{ $a->title }}</div>
                            <div class="text-xs text-slate-400">{{ number_format($a->views) }} views · {{ ucfirst($a->type) }}</div>
                        </div>
                    </a>
                </li>
                @endforeach
            </ol>
        </div>

        <div>
            <x-section-heading title="Genre" :href="route('genre.index')" />
            <div class="flex flex-wrap gap-2">
                @foreach($genres as $g)
                    <a href="{{ route('genre.show', $g) }}" class="px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-xs hover:bg-brand-600 hover:border-brand-500">{{ $g->name }}</a>
                @endforeach
            </div>
        </div>

        <x-ad-slot slot="sidebar" />
    </aside>
</section>

<section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-12">
    <x-section-heading title="Jadwal Rilis Mingguan" :href="route('anime.schedule')" />
    <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
        @foreach (['monday'=>'Senin','tuesday'=>'Selasa','wednesday'=>'Rabu','thursday'=>'Kamis','friday'=>'Jumat','saturday'=>'Sabtu','sunday'=>'Minggu'] as $key => $label)
            <div class="glass rounded-xl p-3">
                <div class="text-sm font-semibold text-brand-300 mb-2">{{ $label }}</div>
                <ul class="space-y-2 text-xs">
                    @forelse(($schedule[$key] ?? collect())->take(5) as $a)
                        <li><a href="{{ $a->url() }}" class="hover:text-white text-slate-300">{{ $a->schedule_time?->format('H:i') }} · {{ $a->title }}</a></li>
                    @empty
                        <li class="text-slate-500">—</li>
                    @endforelse
                </ul>
            </div>
        @endforeach
    </div>
</section>

<x-ad-slot slot="footer" />
@endsection
