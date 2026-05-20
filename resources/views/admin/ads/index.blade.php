@extends('admin.layout')
@section('content')
<div class="flex items-center justify-between mb-4">
    <h1 class="text-2xl font-bold">Iklan</h1>
    <a href="{{ route('admin.ads.create') }}" class="px-3 py-1.5 rounded-lg bg-fuchsia-600 text-sm">+ Iklan Baru</a>
</div>
<div class="overflow-x-auto rounded-2xl border border-white/10 bg-black/20">
    <table class="w-full text-sm">
        <thead class="text-xs uppercase text-slate-400"><tr><th class="p-3 text-left">Nama</th><th class="p-3 text-left">Slot</th><th class="p-3 text-left">Type</th><th class="p-3 text-left">Aktif</th><th class="p-3">Aksi</th></tr></thead>
        <tbody>
        @foreach ($ads as $ad)
            <tr class="border-t border-white/5">
                <td class="p-3">{{ $ad->name }}</td>
                <td class="p-3">{{ $ad->slot }}</td>
                <td class="p-3">{{ $ad->type }}</td>
                <td class="p-3">{{ $ad->is_active ? '✓' : '×' }}</td>
                <td class="p-3 flex gap-2 text-xs">
                    <a href="{{ route('admin.ads.edit', $ad) }}" class="text-emerald-300">Edit</a>
                    <form method="POST" action="{{ route('admin.ads.destroy', $ad) }}" onsubmit="return confirm('Hapus?')">@csrf @method('DELETE')<button class="text-rose-300">Hapus</button></form>
                </td>
            </tr>
        @endforeach
        </tbody>
    </table>
</div>
<div class="mt-4">{{ $ads->links() }}</div>
@endsection
