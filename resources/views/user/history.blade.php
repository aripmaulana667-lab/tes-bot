@extends('layouts.app')
@section('content')
<section class="max-w-7xl mx-auto px-4 mt-6">
    <h1 class="text-3xl font-extrabold gradient-text">Riwayat Tontonan</h1>
    <div class="mt-6 grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        @forelse ($history as $h)
            @if ($h->anime && $h->episode)
            <div class="glass rounded-xl p-3 flex gap-3">
                <img src="{{ $h->anime->posterUrl() }}" class="w-20 h-28 object-cover rounded">
                <div class="flex-1 text-sm">
                    <a href="{{ $h->episode->url() }}" class="font-semibold hover:text-brand-300 line-clamp-2">{{ $h->anime->title }} — Ep {{ $h->episode->number }}</a>
                    <div class="text-xs text-slate-400 mt-1">{{ gmdate('H:i:s', (int) $h->progress_seconds) }} / {{ gmdate('H:i:s', (int) $h->duration_seconds) }}</div>
                    <div class="mt-2 h-1 rounded bg-white/10 overflow-hidden"><div class="h-full bg-brand-500" style="width: {{ $h->progressPercent() }}%"></div></div>
                    <form method="POST" action="{{ route('history.destroy', $h) }}" class="mt-2">
                        @csrf @method('DELETE')
                        <button class="text-xs text-rose-300 hover:text-rose-200">Hapus</button>
                    </form>
                </div>
            </div>
            @endif
        @empty
            <p class="col-span-full text-slate-400 text-center py-10">Belum ada riwayat.</p>
        @endforelse
    </div>
    <div class="mt-6">{{ $history->links() }}</div>
</section>
@endsection
