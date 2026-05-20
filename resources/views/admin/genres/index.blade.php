@extends('admin.layout')
@section('content')
<h1 class="text-2xl font-bold mb-4">Genre</h1>
<form method="POST" action="{{ route('admin.genres.store') }}" class="flex gap-2 text-sm mb-4">@csrf
    <input name="name" required placeholder="Nama genre baru" class="bg-white/5 border border-white/10 rounded-lg px-3 py-2 flex-1">
    <button class="px-3 py-2 rounded-lg bg-fuchsia-600">+ Tambah</button>
</form>
<div class="grid md:grid-cols-3 gap-3 text-sm">
    @foreach ($genres as $g)
        <div class="bg-black/20 border border-white/10 rounded-xl p-3 flex justify-between gap-2">
            <form method="POST" action="{{ route('admin.genres.update', $g) }}" class="flex gap-2 flex-1">@csrf @method('PATCH')
                <input name="name" value="{{ $g->name }}" class="bg-white/5 border border-white/10 rounded px-2 py-1 flex-1">
                <button class="text-emerald-300 text-xs">Save</button>
            </form>
            <form method="POST" action="{{ route('admin.genres.destroy', $g) }}" onsubmit="return confirm('Hapus?')">@csrf @method('DELETE')<button class="text-rose-300 text-xs">×</button></form>
        </div>
    @endforeach
</div>
<div class="mt-4">{{ $genres->links() }}</div>
@endsection
