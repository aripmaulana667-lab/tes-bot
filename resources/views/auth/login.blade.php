@extends('layouts.app')
@section('content')
<section class="max-w-md mx-auto mt-12 px-4">
    <div class="glass rounded-2xl p-6">
        <h1 class="text-2xl font-bold gradient-text mb-4">Login</h1>
        <form method="POST" action="{{ route('login') }}" class="space-y-3 text-sm">
            @csrf
            <div>
                <label class="block mb-1 text-slate-400">Email</label>
                <input type="email" name="email" value="{{ old('email') }}" required class="w-full rounded-xl bg-white/5 border border-white/10 px-3 py-2">
                @error('email')<p class="text-rose-300 text-xs mt-1">{{ $message }}</p>@enderror
            </div>
            <div>
                <label class="block mb-1 text-slate-400">Password</label>
                <input type="password" name="password" required class="w-full rounded-xl bg-white/5 border border-white/10 px-3 py-2">
            </div>
            <label class="flex items-center gap-2 text-slate-400"><input type="checkbox" name="remember" value="1"> Remember me</label>
            <button class="w-full rounded-xl bg-brand-600 hover:bg-brand-500 py-2 shadow-neon">Login</button>
        </form>
        <div class="mt-3 flex justify-between text-xs text-slate-400">
            <a href="{{ route('password.request') }}" class="hover:text-white">Lupa password?</a>
            <a href="{{ route('register') }}" class="hover:text-white">Belum punya akun? Register</a>
        </div>
    </div>
</section>
@endsection
