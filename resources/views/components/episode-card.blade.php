@props(['episode'])

<a href="{{ $episode->url() }}" class="group block rounded-2xl overflow-hidden border border-white/5 bg-ink-800 hover:border-brand-500/50 transition shadow-lg">
    <div class="aspect-video overflow-hidden relative">
        <img loading="lazy" src="{{ $episode->thumbnailUrl() }}" class="w-full h-full object-cover group-hover:scale-105 transition duration-500" alt="{{ $episode->anime?->title }}">
        <div class="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 bg-black/40 transition">
            <span class="w-12 h-12 rounded-full bg-brand-600 flex items-center justify-center shadow-neon">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white" class="w-6 h-6"><path d="M8 5v14l11-7z"/></svg>
            </span>
        </div>
        <div class="absolute bottom-2 left-2 text-xs px-2 py-0.5 rounded-full bg-black/70">Ep {{ $episode->number }}</div>
        @if ($episode->is_premium)
            <div class="absolute top-2 right-2 text-[10px] px-2 py-0.5 rounded-full bg-amber-500 text-black font-semibold uppercase">Premium</div>
        @endif
    </div>
    <div class="p-3">
        <h4 class="text-sm font-medium line-clamp-1">{{ $episode->anime?->title }}</h4>
        <p class="text-xs text-slate-400 line-clamp-1">{{ $episode->title ?? 'Episode '.$episode->number }}</p>
    </div>
</a>
