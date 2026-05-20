@extends('admin.layout')
@section('content')
<h1 class="text-2xl font-bold mb-4">{{ $ad->exists ? 'Edit' : 'Tambah' }} Iklan</h1>
<form method="POST" action="{{ $ad->exists ? route('admin.ads.update', $ad) : route('admin.ads.store') }}" enctype="multipart/form-data" class="bg-black/20 border border-white/10 rounded-2xl p-6 space-y-3 text-sm">
    @csrf @if ($ad->exists) @method('PATCH') @endif
    <div><label class="text-slate-400 text-xs">Nama</label><input name="name" required value="{{ old('name', $ad->name) }}" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2"></div>
    <div class="grid md:grid-cols-2 gap-3">
        <div>
            <label class="text-slate-400 text-xs">Slot</label>
            <select name="slot" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2">
                @foreach (['header','sidebar','sticky','popup','popunder','inline','video_pre','video_post','footer'] as $s)
                    <option value="{{ $s }}" @selected(old('slot', $ad->slot) === $s)>{{ $s }}</option>
                @endforeach
            </select>
        </div>
        <div>
            <label class="text-slate-400 text-xs">Type</label>
            <select name="type" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2">
                @foreach (['adsense','script','image','iframe'] as $t)
                    <option value="{{ $t }}" @selected(old('type', $ad->type) === $t)>{{ $t }}</option>
                @endforeach
            </select>
        </div>
        <div><label class="text-slate-400 text-xs">Starts At</label><input type="datetime-local" name="starts_at" value="{{ old('starts_at', optional($ad->starts_at)->format('Y-m-d\TH:i')) }}" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2"></div>
        <div><label class="text-slate-400 text-xs">Ends At</label><input type="datetime-local" name="ends_at" value="{{ old('ends_at', optional($ad->ends_at)->format('Y-m-d\TH:i')) }}" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2"></div>
    </div>
    <div><label class="text-slate-400 text-xs">Code (script/adsense/embed/HTML)</label><textarea name="code" rows="6" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 font-mono">{{ old('code', $ad->code) }}</textarea></div>
    <div class="grid md:grid-cols-2 gap-3">
        <div>
            <label class="text-slate-400 text-xs">Image URL</label>
            <input name="image" value="{{ old('image', $ad->image) }}" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2">
            <input type="file" name="image_upload" accept="image/*" class="text-xs mt-1">
        </div>
        <div><label class="text-slate-400 text-xs">Link target</label><input name="link" value="{{ old('link', $ad->link) }}" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2"></div>
    </div>
    <label class="flex items-center gap-2"><input type="checkbox" name="is_active" value="1" @checked(old('is_active', $ad->is_active))> Aktif</label>
    <button class="px-4 py-2 rounded-lg bg-fuchsia-600">Simpan</button>
</form>
@endsection
