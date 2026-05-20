@props(['anime'])

<a href="{{ $anime->url() }}" class="group anime-card relative block rounded-2xl overflow-hidden border border-white/5 bg-ink-800 hover:border-brand-500/50 transition shadow-lg hover:shadow-neon">
    <div class="aspect-[2/3] overflow-hidden">
        <img loading="lazy" src="{{ $anime->posterUrl() }}" alt="{{ $anime->title }}" class="w-full h-full object-cover group-hover:scale-105 transition duration-500">
    </div>
    <div class="anime-overlay absolute inset-0 bg-gradient-to-t from-ink-900 via-ink-900/50 to-transparent opacity-90 group-hover:opacity-100"></div>
    <div class="absolute top-2 left-2 flex gap-1">
        <span class="text-[10px] px-2 py-0.5 rounded-full bg-black/70 text-white uppercase">{{ $anime->type }}</span>
        @if ($anime->status === 'ongoing')
            <span class="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/80 text-white uppercase">ON</span>
        @endif
    </div>
    @if ($anime->score)
        <div class="absolute top-2 right-2 text-[11px] px-2 py-0.5 rounded-full bg-amber-500/90 text-black font-semibold">⭐ {{ number_format((float) $anime->score, 1) }}</div>
    @endif
    <div class="absolute bottom-0 left-0 right-0 p-3">
        <h3 class="text-sm font-semibold line-clamp-2">{{ $anime->title }}</h3>
        <div class="text-[11px] text-slate-300 mt-1 line-clamp-1">{{ $anime->year }} · {{ ucfirst($anime->status) }} · {{ $anime->episodes_count ? $anime->episodes_count.' eps' : '–' }}</div>
    </div>
</a>
