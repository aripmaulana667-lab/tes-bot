@extends('layouts.app')

@section('content')
@php
    $metaTitle = $anime->meta_title ?: $anime->title;
    $metaDescription = $anime->meta_description ?: \Illuminate\Support\Str::limit(strip_tags($anime->synopsis ?? ''), 160);
    $metaImage = $anime->bannerUrl();
@endphp

@push('schema')
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "TVSeries",
  "name": "{{ $anime->title }}",
  "alternateName": "{{ $anime->title_english }}",
  "image": "{{ $anime->posterUrl() }}",
  "description": "{{ \Illuminate\Support\Str::limit(strip_tags($anime->synopsis ?? ''), 200) }}",
  "datePublished": "{{ $anime->year }}",
  "numberOfEpisodes": {{ (int) $anime->episodes_count }},
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": {{ (float) $anime->score ?: 0 }},
    "ratingCount": {{ max(1, $anime->ratings()->count()) }}
  }
}
</script>
@endpush

<section class="relative">
    <div class="absolute inset-0 h-[420px] overflow-hidden">
        <img src="{{ $anime->bannerUrl() }}" class="w-full h-full object-cover blur-sm scale-110 opacity-40" alt="">
        <div class="absolute inset-0 bg-gradient-to-b from-transparent via-ink-900/70 to-ink-900"></div>
    </div>

    <div class="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-10 pb-12 grid md:grid-cols-[260px_1fr] gap-8">
        <div>
            <img src="{{ $anime->posterUrl() }}" alt="{{ $anime->title }}" class="w-full rounded-2xl shadow-2xl">

            @auth
                <div class="mt-4 flex flex-wrap gap-2">
                    <button
                        x-data="{ active: @json($anime->bookmarks()->where('user_id', auth()->id())->exists()) }"
                        @click="apiFetch('{{ route('bookmarks.toggle', $anime) }}', {method:'POST'}).then(r=>r.json()).then(d=>{ active=d.bookmarked })"
                        :class="active ? 'bg-rose-500/30 border-rose-400' : 'bg-white/5 border-white/10 hover:bg-white/10'"
                        class="px-3 py-2 rounded-xl border text-sm flex items-center gap-2">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 24 24" class="w-4 h-4"><path d="M5 5a3 3 0 013-3h8a3 3 0 013 3v17l-7-4-7 4V5z"/></svg>
                        <span x-text="active ? 'Tersimpan' : 'Bookmark'"></span>
                    </button>

                    <a href="#rate" class="px-3 py-2 rounded-xl border border-white/10 hover:bg-white/5 text-sm">⭐ Beri Rating</a>
                </div>
            @endauth

            <div class="mt-4 glass rounded-xl p-3 text-xs space-y-2 text-slate-300">
                <div><strong class="text-slate-100">Type:</strong> {{ ucfirst($anime->type) }}</div>
                <div><strong class="text-slate-100">Status:</strong> {{ ucfirst($anime->status) }}</div>
                <div><strong class="text-slate-100">Episode:</strong> {{ $anime->episodes_count }}</div>
                <div><strong class="text-slate-100">Studio:</strong> {{ $anime->studio?->name ?? '—' }}</div>
                <div><strong class="text-slate-100">Tahun:</strong> {{ $anime->year ?? '—' }}</div>
                <div><strong class="text-slate-100">Durasi:</strong> {{ $anime->duration ? $anime->duration.' menit' : '—' }}</div>
                <div><strong class="text-slate-100">Rating:</strong> {{ $anime->age_rating ?? '—' }}</div>
                <div><strong class="text-slate-100">Score:</strong> ⭐ {{ number_format((float)$anime->score, 2) }} ({{ $anime->ratings()->count() }} pengguna)</div>
                <div><strong class="text-slate-100">Views:</strong> {{ number_format($anime->views) }}</div>
                <div class="pt-2 border-t border-white/5">
                    <div class="flex gap-2 mt-1 flex-wrap">
                        @foreach ($anime->genres as $g)
                            <a href="{{ route('genre.show', $g) }}" class="px-2 py-0.5 rounded-full bg-white/5 border border-white/10 text-[10px] hover:bg-brand-600">{{ $g->name }}</a>
                        @endforeach
                    </div>
                </div>
            </div>

            <div class="mt-3 flex gap-2 text-xs justify-center">
                @php $url = url()->current(); $title = urlencode($anime->title); @endphp
                <a target="_blank" rel="noopener" href="https://twitter.com/intent/tweet?url={{ urlencode($url) }}&text={{ $title }}" class="px-3 py-2 rounded-lg bg-sky-500/20 border border-sky-400/30 hover:bg-sky-500/30">𝕏</a>
                <a target="_blank" rel="noopener" href="https://www.facebook.com/sharer/sharer.php?u={{ urlencode($url) }}" class="px-3 py-2 rounded-lg bg-blue-600/20 border border-blue-400/30 hover:bg-blue-600/30">f</a>
                <a target="_blank" rel="noopener" href="https://api.whatsapp.com/send?text={{ $title }}%20{{ urlencode($url) }}" class="px-3 py-2 rounded-lg bg-emerald-500/20 border border-emerald-400/30 hover:bg-emerald-500/30">WA</a>
            </div>
        </div>

        <div id="info">
            <div class="flex flex-wrap items-center gap-2 text-xs uppercase tracking-wider text-slate-300">
                <span class="px-2 py-1 rounded-full bg-brand-600/30 border border-brand-400/30">{{ ucfirst($anime->type) }}</span>
                <span class="px-2 py-1 rounded-full bg-emerald-500/20 border border-emerald-400/30">{{ ucfirst($anime->status) }}</span>
                @if($anime->year) <span class="px-2 py-1 rounded-full bg-amber-500/20 border border-amber-400/30">{{ $anime->year }}</span> @endif
            </div>
            <h1 class="text-3xl md:text-5xl font-extrabold mt-3 gradient-text">{{ $anime->title }}</h1>
            @if ($anime->title_japanese)<p class="text-slate-400 mt-1 text-sm">{{ $anime->title_japanese }}</p>@endif

            @if ($anime->trailer_url)
                <div class="mt-5">
                    <a href="{{ $anime->trailer_url }}" target="_blank" rel="noopener" class="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500">▶ Tonton Trailer</a>
                </div>
            @endif

            <p class="mt-5 leading-relaxed text-slate-200">{{ $anime->synopsis }}</p>

            <div class="mt-8">
                <h2 class="text-xl font-semibold mb-3">Daftar Episode</h2>
                @if ($anime->episodes->count())
                    <div class="grid grid-cols-3 sm:grid-cols-5 md:grid-cols-8 gap-2">
                        @foreach ($anime->episodes as $ep)
                            <a href="{{ $ep->url() }}" class="relative aspect-square flex flex-col items-center justify-center rounded-lg border border-white/10 bg-white/5 hover:bg-brand-600 hover:border-brand-500 transition text-sm">
                                <span class="font-semibold">Eps {{ $ep->number }}</span>
                                @if($ep->is_premium)<span class="absolute top-1 right-1 text-[9px] px-1 rounded bg-amber-500 text-black">PRO</span>@endif
                            </a>
                        @endforeach
                    </div>
                @else
                    <p class="text-slate-400 text-sm">Belum ada episode.</p>
                @endif
            </div>

            <div class="mt-10" id="rate">
                <h2 class="text-xl font-semibold mb-3">Rating & Review</h2>
                @auth
                    @php $myRating = $anime->ratings()->where('user_id', auth()->id())->first(); @endphp
                    <form method="POST" action="{{ route('ratings.store', $anime) }}" class="glass rounded-xl p-4 text-sm space-y-3">
                        @csrf
                        <div class="flex items-center gap-3">
                            <span class="text-slate-300">Score:</span>
                            <select name="score" class="bg-white/5 border border-white/10 rounded-lg px-2 py-1">
                                @for ($i=1;$i<=10;$i++)
                                    <option value="{{ $i }}" @selected($myRating && $myRating->score==$i)>{{ $i }}</option>
                                @endfor
                            </select>
                            <span class="text-amber-400">⭐</span>
                            <span class="text-slate-300">Rata-rata: <strong>{{ number_format((float) $anime->score, 2) }}</strong></span>
                        </div>
                        <textarea name="review" rows="3" placeholder="Tulis review (opsional)" class="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2">{{ $myRating?->review }}</textarea>
                        <button class="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500">Simpan Rating</button>
                    </form>
                @else
                    <p class="text-slate-400 text-sm"><a href="{{ route('login') }}" class="text-brand-300">Login</a> untuk memberikan rating.</p>
                @endauth
            </div>

            <div class="mt-10">
                <h2 class="text-xl font-semibold mb-3">Komentar</h2>
                @include('partials.comments', ['comments' => $recentComments, 'commentable_type' => 'anime', 'commentable_id' => $anime->id])
            </div>

            @if ($related->count())
            <div class="mt-12">
                <x-section-heading title="Anime Terkait" />
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                    @foreach ($related as $a)
                        <x-anime-card :anime="$a" />
                    @endforeach
                </div>
            </div>
            @endif
        </div>
    </div>
</section>
@endsection
