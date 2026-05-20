@extends('layouts.app')
@section('content')
<section class="max-w-md mx-auto mt-12 px-4">
    <div class="glass rounded-2xl p-6">
        <h1 class="text-2xl font-bold gradient-text mb-4">Buat Akun Baru</h1>
        <form method="POST" action="{{ route('register') }}" class="space-y-3 text-sm">
            @csrf
            <div>
                <label class="block mb-1 text-slate-400">Nama</label>
                <input type="text" name="name" required value="{{ old('name') }}" class="w-full rounded-xl bg-white/5 border border-white/10 px-3 py-2">
                @error('name')<p class="text-rose-300 text-xs mt-1">{{ $message }}</p>@enderror
            </div>
            <div>
                <label class="block mb-1 text-slate-400">Email</label>
                <input type="email" name="email" required value="{{ old('email') }}" class="w-full rounded-xl bg-white/5 border border-white/10 px-3 py-2">
                @error('email')<p class="text-rose-300 text-xs mt-1">{{ $message }}</p>@enderror
            </div>
            <div>
                <label class="block mb-1 text-slate-400">Password</label>
                <input type="password" name="password" required class="w-full rounded-xl bg-white/5 border border-white/10 px-3 py-2">
                @error('password')<p class="text-rose-300 text-xs mt-1">{{ $message }}</p>@enderror
            </div>
            <div>
                <label class="block mb-1 text-slate-400">Konfirmasi Password</label>
                <input type="password" name="password_confirmation" required class="w-full rounded-xl bg-white/5 border border-white/10 px-3 py-2">
            </div>
            <button class="w-full rounded-xl bg-brand-600 hover:bg-brand-500 py-2 shadow-neon">Daftar</button>
        </form>
        <div class="mt-3 text-xs text-slate-400 text-center">Sudah punya akun? <a href="{{ route('login') }}" class="text-brand-300">Login</a></div>
    </div>
</section>
@endsection
