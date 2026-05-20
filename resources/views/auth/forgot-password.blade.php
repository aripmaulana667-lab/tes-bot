@extends('layouts.app')
@section('content')
<section class="max-w-md mx-auto mt-12 px-4">
    <div class="glass rounded-2xl p-6">
        <h1 class="text-2xl font-bold gradient-text mb-4">Reset Password</h1>
        @if (session('status'))<div class="text-emerald-300 text-xs mb-2">{{ session('status') }}</div>@endif
        <form method="POST" action="{{ route('password.email') }}" class="space-y-3 text-sm">
            @csrf
            <input type="email" name="email" required placeholder="Email akun anda" class="w-full rounded-xl bg-white/5 border border-white/10 px-3 py-2">
            @error('email')<p class="text-rose-300 text-xs">{{ $message }}</p>@enderror
            <button class="w-full rounded-xl bg-brand-600 hover:bg-brand-500 py-2">Kirim Link Reset</button>
        </form>
    </div>
</section>
@endsection
