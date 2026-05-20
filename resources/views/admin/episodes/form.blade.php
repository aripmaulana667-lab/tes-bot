@extends('admin.layout')
@section('content')
<h1 class="text-2xl font-bold mb-4">{{ $episode->exists ? 'Edit' : 'Tambah' }} Episode — {{ $anime->title }}</h1>

<form method="POST" action="{{ $episode->exists ? route('admin.animes.episodes.update', [$anime, $episode]) : route('admin.animes.episodes.store', $anime) }}" enctype="multipart/form-data" class="space-y-4 bg-black/20 rounded-2xl border border-white/10 p-6">
    @csrf
    @if ($episode->exists) @method('PATCH') @endif

    <div class="grid md:grid-cols-3 gap-3 text-sm">
        <div><label class="text-slate-400 text-xs">Number</label><input name="number" required value="{{ old('number', $episode->number) }}" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2"></div>
        <div class="md:col-span-2"><label class="text-slate-400 text-xs">Title</label><input name="title" value="{{ old('title', $episode->title) }}" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2"></div>
        <div><label class="text-slate-400 text-xs">Air Date</label><input type="date" name="air_date" value="{{ old('air_date', optional($episode->air_date)->format('Y-m-d')) }}" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2"></div>
        <div><label class="text-slate-400 text-xs">Durasi (detik)</label><input type="number" name="duration" value="{{ old('duration', $episode->duration) }}" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2"></div>
        <div><label class="text-slate-400 text-xs">Download URL</label><input name="download_url" value="{{ old('download_url', $episode->download_url) }}" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2"></div>
    </div>

    <div>
        <label class="text-slate-400 text-xs">Synopsis</label>
        <textarea name="synopsis" rows="3" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2">{{ old('synopsis', $episode->synopsis) }}</textarea>
    </div>

    <div class="grid md:grid-cols-2 gap-3 text-sm">
        <div>
            <label class="text-slate-400 text-xs">Thumbnail URL</label>
            <input name="thumbnail" value="{{ old('thumbnail', $episode->thumbnail) }}" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2">
            <input type="file" name="thumbnail_upload" accept="image/*" class="text-xs mt-1">
        </div>
        <div class="flex items-center gap-6 text-sm">
            <label class="flex items-center gap-2"><input type="checkbox" name="is_premium" value="1" @checked(old('is_premium', $episode->is_premium))> Premium</label>
            <label class="flex items-center gap-2"><input type="checkbox" name="is_published" value="1" @checked(old('is_published', $episode->is_published ?? true))> Published</label>
        </div>
    </div>

    <h3 class="text-lg font-semibold mt-6">Servers Streaming</h3>
    <p class="text-xs text-slate-400">Tambah multiple server: MP4 / M3U8 / iframe. Player akan otomatis mendeteksi tipe.</p>

    <div x-data='{ servers: @json($episode->servers?->values() ?? collect()->all()), add() { this.servers.push({server_name: "", type: "m3u8", url: "", quality: "720p", language: "sub", subtitle_url: "", priority: 0, is_active: true}); } }' class="space-y-3">
        <template x-for="(s, i) in servers" :key="i">
            <div class="grid md:grid-cols-7 gap-2 items-center bg-white/5 p-3 rounded-xl text-xs">
                <input :name="'servers['+i+'][id]'" :value="s.id" type="hidden">
                <input :name="'servers['+i+'][server_name]'" x-model="s.server_name" placeholder="Nama server" class="bg-black/30 border border-white/10 rounded px-2 py-1">
                <select :name="'servers['+i+'][type]'" x-model="s.type" class="bg-black/30 border border-white/10 rounded px-2 py-1">
                    <option value="mp4">MP4</option><option value="m3u8">M3U8 (HLS)</option><option value="iframe">Iframe</option><option value="embed">Embed</option>
                </select>
                <input :name="'servers['+i+'][url]'" x-model="s.url" placeholder="URL" class="bg-black/30 border border-white/10 rounded px-2 py-1 md:col-span-2">
                <input :name="'servers['+i+'][quality]'" x-model="s.quality" placeholder="720p" class="bg-black/30 border border-white/10 rounded px-2 py-1">
                <select :name="'servers['+i+'][language]'" x-model="s.language" class="bg-black/30 border border-white/10 rounded px-2 py-1">
                    <option value="sub">Sub</option><option value="dub">Dub</option><option value="raw">Raw</option>
                </select>
                <div class="flex gap-1 items-center">
                    <input :name="'servers['+i+'][priority]'" x-model.number="s.priority" type="number" placeholder="prio" class="bg-black/30 border border-white/10 rounded px-2 py-1 w-16">
                    <label class="flex items-center gap-1"><input type="checkbox" :name="'servers['+i+'][is_active]'" x-model="s.is_active" value="1"> aktif</label>
                    <button type="button" @click="servers.splice(i,1)" class="text-rose-300">×</button>
                </div>
                <input :name="'servers['+i+'][subtitle_url]'" x-model="s.subtitle_url" placeholder="Subtitle URL (opsional)" class="bg-black/30 border border-white/10 rounded px-2 py-1 md:col-span-7">
            </div>
        </template>
        <button type="button" @click="add()" class="px-3 py-1.5 rounded bg-emerald-500 text-black text-sm">+ Tambah Server</button>
    </div>

    <button class="px-4 py-2 rounded-lg bg-fuchsia-600 hover:bg-fuchsia-500">Simpan</button>
</form>
@endsection
