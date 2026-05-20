@extends('layouts.app')
@section('content')
<section class="max-w-md mx-auto mt-16 text-center px-4">
    <div class="text-7xl gradient-text font-extrabold">500</div>
    <p class="mt-3 text-slate-300">Maaf, terjadi kesalahan pada server. Silakan coba lagi.</p>
    <a href="{{ route('home') }}" class="inline-flex mt-6 px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500">Kembali ke Beranda</a>
</section>
@endsection
