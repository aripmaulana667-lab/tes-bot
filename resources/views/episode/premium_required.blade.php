@extends('layouts.app')
@section('content')
<section class="max-w-3xl mx-auto px-4 mt-10 text-center">
    <div class="glass rounded-3xl p-10 shadow-neon border border-amber-400/30">
        <div class="text-6xl">🌟</div>
        <h1 class="text-3xl font-bold mt-3 gradient-text">Episode Premium</h1>
        <p class="text-slate-300 mt-2">Episode {{ $episode->number }} dari <strong>{{ $anime->title }}</strong> hanya tersedia untuk member premium.</p>
        <a href="{{ route('billing.plans') }}" class="inline-flex mt-6 px-6 py-3 rounded-xl bg-gradient-to-r from-amber-500 to-rose-500 text-white font-semibold shadow-neon">Upgrade Premium</a>
        <div class="mt-4"><a href="{{ $anime->url() }}" class="text-slate-400 hover:text-white text-sm">← Kembali ke detail anime</a></div>
    </div>
</section>
@endsection
