@extends('admin.layout')
@section('content')
<h1 class="text-2xl font-bold">User</h1>
<form method="GET" class="mt-4 flex gap-2"><input name="q" value="{{ request('q') }}" placeholder="Cari nama/email…" class="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm"><button class="px-3 py-2 bg-white/5 rounded-lg text-sm">Filter</button></form>
<div class="mt-4 overflow-x-auto rounded-2xl border border-white/10 bg-black/20">
    <table class="w-full text-sm">
        <thead class="text-xs uppercase text-slate-400"><tr><th class="p-3 text-left">Name</th><th class="p-3 text-left">Email</th><th class="p-3 text-left">Role</th><th class="p-3 text-left">Premium</th><th class="p-3 text-left">Status</th><th class="p-3">Aksi</th></tr></thead>
        <tbody>
        @foreach ($users as $u)
            <tr class="border-t border-white/5">
                <td class="p-3">{{ $u->name }}</td>
                <td class="p-3">{{ $u->email }}</td>
                <td class="p-3 capitalize">{{ $u->role }}</td>
                <td class="p-3">{{ $u->is_premium ? '⭐' : '—' }}</td>
                <td class="p-3">{{ $u->is_banned ? 'BANNED' : 'OK' }}</td>
                <td class="p-3 flex gap-2 text-xs">
                    <a href="{{ route('admin.users.edit', $u) }}" class="text-emerald-300">Edit</a>
                    <form method="POST" action="{{ route('admin.users.destroy', $u) }}" onsubmit="return confirm('Hapus user?')">@csrf @method('DELETE')<button class="text-rose-300">Hapus</button></form>
                </td>
            </tr>
        @endforeach
        </tbody>
    </table>
</div>
<div class="mt-4">{{ $users->withQueryString()->links() }}</div>
@endsection
