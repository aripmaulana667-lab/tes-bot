@extends('admin.layout')
@section('content')
<h1 class="text-2xl font-bold mb-4">Edit User: {{ $user->name }}</h1>
<form method="POST" action="{{ route('admin.users.update', $user) }}" class="space-y-3 max-w-md bg-black/20 rounded-2xl border border-white/10 p-6 text-sm">
    @csrf @method('PATCH')
    <div>
        <label class="text-slate-400 text-xs">Role</label>
        <select name="role" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2">
            @foreach (['user','moderator','admin'] as $r)
                <option value="{{ $r }}" @selected($user->role === $r)>{{ ucfirst($r) }}</option>
            @endforeach
        </select>
    </div>
    <label class="flex items-center gap-2"><input type="checkbox" name="is_premium" value="1" @checked($user->is_premium)> Premium</label>
    <div><label class="text-slate-400 text-xs">Premium Until</label><input type="datetime-local" name="premium_until" value="{{ optional($user->premium_until)->format('Y-m-d\TH:i') }}" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2"></div>
    <label class="flex items-center gap-2"><input type="checkbox" name="is_banned" value="1" @checked($user->is_banned)> Banned</label>
    <button class="px-4 py-2 rounded-lg bg-fuchsia-600">Simpan</button>
</form>
@endsection
