@extends('layouts.app')
@section('content')
<section class="max-w-3xl mx-auto px-4 mt-6">
    <h1 class="text-3xl font-extrabold gradient-text">Profile</h1>

    <form method="POST" action="{{ route('profile.update') }}" enctype="multipart/form-data" class="glass rounded-2xl p-6 mt-6 space-y-4 text-sm">
        @csrf
        @method('PATCH')

        <div class="flex items-center gap-4">
            <img src="{{ $user->avatarUrl() }}" alt="" class="w-20 h-20 rounded-full object-cover border border-white/10">
            <div>
                <label class="text-slate-400 text-xs">Ganti Avatar</label>
                <input type="file" name="avatar" accept="image/*" class="block mt-1 text-xs">
            </div>
        </div>

        <div class="grid md:grid-cols-2 gap-3">
            <div><label class="text-slate-400 text-xs">Nama</label><input name="name" value="{{ old('name', $user->name) }}" required class="w-full rounded-xl bg-white/5 border border-white/10 px-3 py-2"></div>
            <div><label class="text-slate-400 text-xs">Username</label><input name="username" value="{{ old('username', $user->username) }}" class="w-full rounded-xl bg-white/5 border border-white/10 px-3 py-2"></div>
            <div class="md:col-span-2"><label class="text-slate-400 text-xs">Email</label><input type="email" name="email" value="{{ old('email', $user->email) }}" required class="w-full rounded-xl bg-white/5 border border-white/10 px-3 py-2"></div>
            <div class="md:col-span-2"><label class="text-slate-400 text-xs">Bio</label><textarea name="bio" rows="3" class="w-full rounded-xl bg-white/5 border border-white/10 px-3 py-2">{{ old('bio', $user->bio) }}</textarea></div>
            <div><label class="text-slate-400 text-xs">Password Baru</label><input type="password" name="password" class="w-full rounded-xl bg-white/5 border border-white/10 px-3 py-2"></div>
            <div><label class="text-slate-400 text-xs">Konfirmasi Password</label><input type="password" name="password_confirmation" class="w-full rounded-xl bg-white/5 border border-white/10 px-3 py-2"></div>
        </div>

        <div class="text-xs text-slate-400">
            Status: {{ $user->is_premium ? 'Premium hingga '.optional($user->premium_until)->format('Y-m-d') : 'Reguler' }}
        </div>

        <button class="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500">Simpan Perubahan</button>
    </form>
</section>
@endsection
