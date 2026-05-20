@extends('layouts.app')
@section('content')
<section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
    <h1 class="text-3xl font-extrabold gradient-text">Jadwal Rilis Anime</h1>
    <div class="mt-6 grid md:grid-cols-2 lg:grid-cols-4 gap-4">
        @foreach (['monday'=>'Senin','tuesday'=>'Selasa','wednesday'=>'Rabu','thursday'=>'Kamis','friday'=>'Jumat','saturday'=>'Sabtu','sunday'=>'Minggu'] as $key => $label)
            <div class="glass rounded-2xl p-4">
                <div class="text-lg font-semibold text-brand-300 mb-3">{{ $label }}</div>
                <ul class="space-y-3 text-sm">
                    @forelse($schedule[$key] ?? collect() as $a)
                        <li class="flex gap-3 items-center">
                            <img src="{{ $a->posterUrl() }}" class="w-12 h-16 object-cover rounded" alt="">
                            <div>
                                <a href="{{ $a->url() }}" class="font-medium hover:text-brand-300 line-clamp-1">{{ $a->title }}</a>
                                <div class="text-xs text-slate-400">{{ $a->schedule_time?->format('H:i') ?? '—' }}</div>
                            </div>
                        </li>
                    @empty
                        <li class="text-slate-500 text-sm">—</li>
                    @endforelse
                </ul>
            </div>
        @endforeach
    </div>
</section>
@endsection
