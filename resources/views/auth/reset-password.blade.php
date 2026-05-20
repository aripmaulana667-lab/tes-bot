@extends('layouts.app')
@section('content')
<section class="max-w-md mx-auto mt-12 px-4">
    <div class="glass rounded-2xl p-6">
        <h1 class="text-2xl font-bold gradient-text mb-4">Atur Password Baru</h1>
        <form method="POST" action="{{ route('password.update') }}" class="space-y-3 text-sm">
            @csrf
            <input type="hidden" name="token" value="{{ $token }}">
            <input type="email" name="email" required value="{{ old('email', $email) }}" class="w-full rounded-xl bg-white/5 border border-white/10 px-3 py-2">
            <input type="password" name="password" required placeholder="Password baru" class="w-full rounded-xl bg-white/5 border border-white/10 px-3 py-2">
            <input type="password" name="password_confirmation" required placeholder="Konfirmasi password" class="w-full rounded-xl bg-white/5 border border-white/10 px-3 py-2">
            @error('email')<p class="text-rose-300 text-xs">{{ $message }}</p>@enderror
            <button class="w-full rounded-xl bg-brand-600 hover:bg-brand-500 py-2">Reset Password</button>
        </form>
    </div>
</section>
@endsection
