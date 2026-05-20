@extends('layouts.app')

@section('content')
@php
    $metaTitle = $anime->title . ' Episode ' . $episode->number;
    $metaDescription = 'Nonton ' . $anime->title . ' episode ' . $episode->number . ' sub indo kualitas HD.';
    $metaImage = $episode->thumbnailUrl();
@endphp

<section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-2">
    <nav class="text-xs text-slate-400 flex gap-2">
        <a href="{{ route('home') }}" class="hover:text-white">Beranda</a>
        <span>/</span>
        <a href="{{ $anime->url() }}" class="hover:text-white">{{ $anime->title }}</a>
        <span>/</span>
        <span>Episode {{ $episode->number }}</span>
    </nav>

    <div class="mt-4 grid lg:grid-cols-[1fr_320px] gap-6">
        <div>
            <div class="aspect-video w-full bg-black rounded-2xl overflow-hidden relative" x-data="player()" x-init="init()">
                <video id="anime-player" class="video-js vjs-default-skin vjs-big-play-centered w-full h-full" controls preload="auto" data-setup='{"fluid": true}'></video>
            </div>

            <div class="mt-3 flex flex-wrap items-center gap-2">
                <div class="text-xs text-slate-400">Server:</div>
                @forelse ($episode->servers->sortBy('priority') as $server)
                    <button
                        onclick="window.loadServer({{ $server->id }}, {{ Js::from(['type' => $server->type, 'url' => $server->url, 'subtitle' => $server->subtitle_url, 'quality' => $server->quality]) }})"
                        data-server="{{ $server->id }}"
                        class="px-3 py-1.5 rounded-lg border border-white/10 hover:border-brand-400 hover:bg-brand-600/30 text-xs">
                        {{ $server->server_name }} · {{ $server->quality }} · {{ strtoupper($server->language ?? 'sub') }}
                    </button>
                @empty
                    <div class="text-sm text-rose-300">Belum ada server.</div>
                @endforelse
                @auth
                    @if ($episode->download_url)
                        <a href="{{ $episode->download_url }}" target="_blank" class="ml-auto px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs">Download</a>
                    @endif
                @endauth
            </div>

            <div class="mt-4 flex flex-wrap items-center gap-2 text-sm">
                @if ($previous)
                    <a href="{{ $previous->url() }}" class="px-3 py-2 rounded-lg border border-white/10 hover:bg-white/5">← Ep {{ $previous->number }}</a>
                @endif
                <a href="{{ $anime->url() }}" class="px-3 py-2 rounded-lg border border-white/10 hover:bg-white/5">Semua Episode</a>
                @if ($next)
                    <a href="{{ $next->url() }}" class="ml-auto px-3 py-2 rounded-lg bg-brand-600 hover:bg-brand-500">Ep {{ $next->number }} →</a>
                @endif
                <label class="ml-2 flex items-center gap-2 text-xs text-slate-400">
                    <input type="checkbox" id="autoplay-next" checked> Auto Next
                </label>
            </div>

            <div class="mt-6">
                <h1 class="text-2xl font-bold">{{ $anime->title }} — Episode {{ $episode->number }}</h1>
                @if ($episode->title)<h2 class="text-sm text-slate-400 mt-1">{{ $episode->title }}</h2>@endif
                @if ($episode->synopsis)<p class="mt-3 text-slate-200">{{ $episode->synopsis }}</p>@endif
            </div>

            <x-ad-slot slot="video_post" />

            <div class="mt-10">
                <h2 class="text-xl font-semibold mb-3">Komentar Episode</h2>
                @include('partials.comments', ['comments' => $comments, 'commentable_type' => 'episode', 'commentable_id' => $episode->id])
            </div>
        </div>

        <aside class="space-y-4">
            <div class="glass rounded-xl p-3">
                <div class="flex items-center gap-3">
                    <img src="{{ $anime->posterUrl() }}" class="w-16 h-22 object-cover rounded" alt="">
                    <div>
                        <a href="{{ $anime->url() }}" class="font-semibold hover:text-brand-300">{{ $anime->title }}</a>
                        <div class="text-xs text-slate-400">{{ ucfirst($anime->type) }} · {{ ucfirst($anime->status) }}</div>
                    </div>
                </div>
            </div>

            <div class="glass rounded-xl p-3">
                <div class="text-sm font-semibold mb-2">Daftar Episode</div>
                <div class="max-h-96 overflow-y-auto grid grid-cols-4 gap-2">
                    @foreach ($allEpisodes as $ep)
                        <a href="{{ $ep->url() }}" class="aspect-square flex items-center justify-center rounded border text-xs {{ $ep->id === $episode->id ? 'bg-brand-600 border-brand-500' : 'border-white/10 bg-white/5 hover:bg-brand-600/30' }}">{{ $ep->number }}</a>
                    @endforeach
                </div>
            </div>

            <x-ad-slot slot="sidebar" />
        </aside>
    </div>
</section>

@push('scripts')
<script>
window.player = null;
window.currentServer = null;

function initPlayer() {
    if (window.player) return window.player;
    window.player = videojs('anime-player', {
        playbackRates: [0.5, 1, 1.25, 1.5, 2],
        html5: { hls: { overrideNative: true } },
    });
    return window.player;
}

window.loadServer = function(id, opts) {
    const player = initPlayer();
    window.currentServer = id;
    document.querySelectorAll('[data-server]').forEach(el => el.classList.remove('bg-brand-600','border-brand-500'));
    const btn = document.querySelector('[data-server="'+id+'"]');
    if (btn) btn.classList.add('bg-brand-600','border-brand-500');

    if (opts.type === 'iframe' || opts.type === 'embed') {
        // Replace player with iframe
        const container = document.querySelector('#anime-player').closest('.aspect-video');
        container.innerHTML = '<iframe src="'+opts.url+'" allowfullscreen class="w-full h-full" frameborder="0"></iframe>';
        window.player = null;
        return;
    }

    const sourceType = opts.type === 'm3u8' ? 'application/x-mpegURL' : 'video/mp4';
    player.src({ src: opts.url, type: sourceType });

    if (opts.subtitle) {
        try {
            player.addRemoteTextTrack({ kind: 'subtitles', src: opts.subtitle, srclang: 'id', label: 'Indonesia', default: true }, false);
        } catch (e) {}
    }

    player.ready(() => {
        // Resume from saved progress
        const saved = parseFloat(localStorage.getItem('progress_{{ $episode->id }}') || '{{ $progress->progress_seconds ?? 0 }}');
        if (saved > 5) player.currentTime(saved);

        player.on('timeupdate', () => {
            const t = player.currentTime();
            const d = player.duration() || 0;
            localStorage.setItem('progress_{{ $episode->id }}', t);
            if (Math.floor(t) % 10 === 0) trackProgress(t, d);
        });

        @auth
        player.on('ended', () => {
            trackProgress(player.duration(), player.duration());
            const autoNext = document.getElementById('autoplay-next');
            @if ($next)
            if (autoNext && autoNext.checked) {
                window.location.href = '{{ $next->url() }}';
            }
            @endif
        });
        @endauth
    });
};

function trackProgress(t, d) {
    @auth
    apiFetch('{{ route('history.track') }}', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ episode_id: {{ $episode->id }}, progress_seconds: Math.floor(t), duration_seconds: Math.floor(d) })
    }).catch(()=>{});
    @endauth
}

document.addEventListener('DOMContentLoaded', () => {
    const firstButton = document.querySelector('[data-server]');
    if (firstButton) firstButton.click();
});
</script>
@endpush
@endsection
