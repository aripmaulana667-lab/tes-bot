@extends('admin.layout')
@section('content')
<h1 class="text-2xl font-bold mb-4">{{ $anime->exists ? 'Edit' : 'Tambah' }} Anime</h1>

<form method="POST" action="{{ $anime->exists ? route('admin.animes.update', $anime) : route('admin.animes.store') }}" enctype="multipart/form-data" class="space-y-4 bg-black/20 rounded-2xl border border-white/10 p-6">
    @csrf
    @if ($anime->exists) @method('PATCH') @endif

    <div class="grid md:grid-cols-2 gap-3 text-sm">
        <div><label class="text-slate-400 text-xs">Judul</label><input name="title" value="{{ old('title', $anime->title) }}" required class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2"></div>
        <div><label class="text-slate-400 text-xs">Slug</label><input name="slug" value="{{ old('slug', $anime->slug) }}" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2"></div>
        <div><label class="text-slate-400 text-xs">Title Japanese</label><input name="title_japanese" value="{{ old('title_japanese', $anime->title_japanese) }}" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2"></div>
        <div><label class="text-slate-400 text-xs">Title English</label><input name="title_english" value="{{ old('title_english', $anime->title_english) }}" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2"></div>
        <div>
            <label class="text-slate-400 text-xs">Type</label>
            <select name="type" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2">
                @foreach (['anime','donghua','movie','ova','ona','special'] as $t)
                    <option value="{{ $t }}" @selected(old('type', $anime->type) === $t)>{{ ucfirst($t) }}</option>
                @endforeach
            </select>
        </div>
        <div>
            <label class="text-slate-400 text-xs">Status</label>
            <select name="status" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2">
                @foreach (['ongoing','completed','upcoming','hiatus'] as $s)
                    <option value="{{ $s }}" @selected(old('status', $anime->status) === $s)>{{ ucfirst($s) }}</option>
                @endforeach
            </select>
        </div>
        <div><label class="text-slate-400 text-xs">Tahun</label><input type="number" name="year" value="{{ old('year', $anime->year) }}" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2"></div>
        <div><label class="text-slate-400 text-xs">Season</label><input name="season" value="{{ old('season', $anime->season) }}" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2"></div>
        <div><label class="text-slate-400 text-xs">Total Episode</label><input type="number" name="episodes_count" value="{{ old('episodes_count', $anime->episodes_count) }}" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2"></div>
        <div><label class="text-slate-400 text-xs">Durasi (menit)</label><input type="number" name="duration" value="{{ old('duration', $anime->duration) }}" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2"></div>
        <div><label class="text-slate-400 text-xs">Score</label><input type="number" step="0.1" min="0" max="10" name="score" value="{{ old('score', $anime->score) }}" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2"></div>
        <div><label class="text-slate-400 text-xs">Age Rating</label><input name="age_rating" value="{{ old('age_rating', $anime->age_rating) }}" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2"></div>
        <div>
            <label class="text-slate-400 text-xs">Studio</label>
            <select name="studio_id" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2">
                <option value="">—</option>
                @foreach ($studios as $s)
                    <option value="{{ $s->id }}" @selected(old('studio_id', $anime->studio_id) == $s->id)>{{ $s->name }}</option>
                @endforeach
            </select>
        </div>
        <div><label class="text-slate-400 text-xs">Country (JP/CN/KR)</label><input name="country" value="{{ old('country', $anime->country) }}" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2"></div>
        <div><label class="text-slate-400 text-xs">Source</label><input name="source" value="{{ old('source', $anime->source) }}" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2"></div>
        <div><label class="text-slate-400 text-xs">Trailer URL</label><input name="trailer_url" value="{{ old('trailer_url', $anime->trailer_url) }}" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2"></div>
        <div>
            <label class="text-slate-400 text-xs">Schedule Day</label>
            <select name="schedule_day" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2">
                <option value="">—</option>
                @foreach (['monday','tuesday','wednesday','thursday','friday','saturday','sunday'] as $d)
                    <option value="{{ $d }}" @selected(old('schedule_day', $anime->schedule_day) === $d)>{{ ucfirst($d) }}</option>
                @endforeach
            </select>
        </div>
        <div><label class="text-slate-400 text-xs">Schedule Time (HH:mm)</label><input name="schedule_time" value="{{ old('schedule_time', $anime->schedule_time?->format('H:i')) }}" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2"></div>
    </div>

    <div>
        <label class="text-slate-400 text-xs">Sinopsis</label>
        <textarea name="synopsis" rows="5" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2">{{ old('synopsis', $anime->synopsis) }}</textarea>
    </div>

    <div class="grid md:grid-cols-2 gap-3 text-sm">
        <div>
            <label class="text-slate-400 text-xs">Poster URL</label>
            <input name="poster" value="{{ old('poster', $anime->poster) }}" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2">
            <label class="text-slate-400 text-xs mt-2 block">atau Upload</label>
            <input type="file" name="poster_upload" accept="image/*" class="text-xs">
        </div>
        <div>
            <label class="text-slate-400 text-xs">Banner URL</label>
            <input name="banner" value="{{ old('banner', $anime->banner) }}" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2">
            <label class="text-slate-400 text-xs mt-2 block">atau Upload</label>
            <input type="file" name="banner_upload" accept="image/*" class="text-xs">
        </div>
    </div>

    <div>
        <label class="text-slate-400 text-xs">Genre</label>
        <select name="genres[]" multiple size="8" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2">
            @foreach ($genres as $g)
                <option value="{{ $g->id }}" @selected(in_array($g->id, old('genres', $anime->genres?->pluck('id')?->toArray() ?? [])))>{{ $g->name }}</option>
            @endforeach
        </select>
        <p class="text-xs text-slate-500 mt-1">Ctrl+klik untuk pilih banyak</p>
    </div>

    <div class="grid md:grid-cols-2 gap-3 text-sm">
        <div><label class="text-slate-400 text-xs">Meta Title</label><input name="meta_title" value="{{ old('meta_title', $anime->meta_title) }}" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2"></div>
        <div><label class="text-slate-400 text-xs">Meta Description</label><input name="meta_description" value="{{ old('meta_description', $anime->meta_description) }}" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2"></div>
    </div>

    <div class="flex gap-4 text-sm">
        <label class="flex items-center gap-2"><input type="checkbox" name="is_featured" value="1" @checked(old('is_featured', $anime->is_featured))> Featured</label>
        <label class="flex items-center gap-2"><input type="checkbox" name="is_published" value="1" @checked(old('is_published', $anime->is_published ?? true))> Published</label>
    </div>

    <button class="px-4 py-2 rounded-lg bg-fuchsia-600 hover:bg-fuchsia-500">Simpan</button>
</form>
@endsection
