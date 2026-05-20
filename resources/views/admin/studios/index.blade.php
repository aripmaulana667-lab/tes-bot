@extends('admin.layout')
@section('content')
<h1 class="text-2xl font-bold mb-4">Studio</h1>
<form method="POST" action="{{ route('admin.studios.store') }}" class="flex gap-2 text-sm mb-4">@csrf
    <input name="name" required placeholder="Nama studio" class="bg-white/5 border border-white/10 rounded-lg px-3 py-2 flex-1">
    <input name="country" placeholder="JP/CN/KR" class="bg-white/5 border border-white/10 rounded-lg px-3 py-2 w-24">
    <button class="px-3 py-2 rounded-lg bg-fuchsia-600">+ Tambah</button>
</form>
<div class="grid md:grid-cols-3 gap-3 text-sm">
    @foreach ($studios as $s)
        <div class="bg-black/20 border border-white/10 rounded-xl p-3 flex gap-2">
            <form method="POST" action="{{ route('admin.studios.update', $s) }}" class="flex gap-2 flex-1">@csrf @method('PATCH')
                <input name="name" value="{{ $s->name }}" class="bg-white/5 border border-white/10 rounded px-2 py-1 flex-1">
                <input name="country" value="{{ $s->country }}" class="bg-white/5 border border-white/10 rounded px-2 py-1 w-16">
                <button class="text-emerald-300 text-xs">Save</button>
            </form>
            <form method="POST" action="{{ route('admin.studios.destroy', $s) }}" onsubmit="return confirm('Hapus?')">@csrf @method('DELETE')<button class="text-rose-300 text-xs">×</button></form>
        </div>
    @endforeach
</div>
<div class="mt-4">{{ $studios->links() }}</div>
@endsection
