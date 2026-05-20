@extends('admin.layout')
@section('content')
<h1 class="text-2xl font-bold mb-4">SEO Per Halaman</h1>
<form method="POST" action="{{ route('admin.seo.store') }}" class="bg-black/20 border border-white/10 rounded-2xl p-4 mb-4 space-y-2 text-sm">
    @csrf
    <input name="page_key" required placeholder="Page key (mis: home, anime.index)" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2">
    <input name="title" required placeholder="Meta title" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2">
    <textarea name="description" placeholder="Meta description" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2"></textarea>
    <input name="keywords" placeholder="Keywords (comma)" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2">
    <input name="og_image" placeholder="OG image URL" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2">
    <button class="px-3 py-2 rounded-lg bg-fuchsia-600">+ Tambah / Update</button>
</form>

<div class="space-y-2">
    @foreach ($metas as $meta)
        <form method="POST" action="{{ route('admin.seo.update', $meta) }}" class="bg-black/20 border border-white/10 rounded-2xl p-3 text-sm space-y-2">
            @csrf @method('PATCH')
            <div class="text-xs text-fuchsia-300">{{ $meta->page_key }}</div>
            <input name="title" value="{{ $meta->title }}" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2">
            <textarea name="description" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2">{{ $meta->description }}</textarea>
            <input name="keywords" value="{{ $meta->keywords }}" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2">
            <input name="og_image" value="{{ $meta->og_image }}" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2">
            <div class="flex gap-2">
                <button class="px-3 py-1.5 rounded-lg bg-emerald-500 text-black">Save</button>
            </div>
        </form>
        <form method="POST" action="{{ route('admin.seo.destroy', $meta) }}" onsubmit="return confirm('Hapus?')" class="-mt-1 text-right">@csrf @method('DELETE')<button class="text-xs text-rose-300">Hapus</button></form>
    @endforeach
</div>
@endsection
