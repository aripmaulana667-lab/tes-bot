@extends('admin.layout')
@section('content')
<h1 class="text-2xl font-bold mb-4">Settings Website</h1>

<form method="POST" action="{{ route('admin.settings.update') }}" enctype="multipart/form-data" class="bg-black/20 border border-white/10 rounded-2xl p-6 space-y-4 text-sm">
    @csrf @method('PATCH')

    <h2 class="text-lg font-semibold">Identitas</h2>
    <div class="grid md:grid-cols-2 gap-3">
        <div><label class="text-slate-400 text-xs">Site Name</label><input name="site_name" value="{{ \App\Helpers\SettingsHelper::get('site_name') }}" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2"></div>
        <div><label class="text-slate-400 text-xs">Tagline</label><input name="site_tagline" value="{{ \App\Helpers\SettingsHelper::get('site_tagline') }}" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2"></div>
        <div><label class="text-slate-400 text-xs">Theme Color (hex)</label><input name="theme_color" value="{{ \App\Helpers\SettingsHelper::get('theme_color', '#7c3aed') }}" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2"></div>
        <div><label class="text-slate-400 text-xs">Meta Description</label><input name="meta_description" value="{{ \App\Helpers\SettingsHelper::get('meta_description') }}" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2"></div>
        <div><label class="text-slate-400 text-xs">Meta Keywords</label><input name="meta_keywords" value="{{ \App\Helpers\SettingsHelper::get('meta_keywords') }}" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2"></div>
        <div><label class="text-slate-400 text-xs">Analytics Code (HTML)</label><textarea name="analytics_code" rows="3" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 font-mono">{{ \App\Helpers\SettingsHelper::get('analytics_code') }}</textarea></div>
    </div>

    <h2 class="text-lg font-semibold">Logo & Favicon</h2>
    <div class="grid md:grid-cols-2 gap-3">
        <div>
            <label class="text-slate-400 text-xs">Logo URL</label>
            <input name="site_logo" value="{{ \App\Helpers\SettingsHelper::get('site_logo') }}" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2">
            <input type="file" name="site_logo_upload" accept="image/*" class="text-xs mt-1">
        </div>
        <div>
            <label class="text-slate-400 text-xs">Favicon URL</label>
            <input name="site_favicon" value="{{ \App\Helpers\SettingsHelper::get('site_favicon') }}" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2">
            <input type="file" name="site_favicon_upload" accept="image/*" class="text-xs mt-1">
        </div>
    </div>

    <h2 class="text-lg font-semibold">Maintenance Mode</h2>
    <label class="flex items-center gap-2"><input type="checkbox" name="maintenance_mode" value="1" @checked(\App\Helpers\SettingsHelper::get('maintenance_mode'))> Aktifkan</label>

    <h2 class="text-lg font-semibold mt-6">SMTP Email</h2>
    <div class="grid md:grid-cols-3 gap-3">
        <div><label class="text-slate-400 text-xs">Host</label><input name="smtp_host" value="{{ \App\Helpers\SettingsHelper::get('smtp_host') }}" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2"></div>
        <div><label class="text-slate-400 text-xs">Port</label><input name="smtp_port" value="{{ \App\Helpers\SettingsHelper::get('smtp_port') }}" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2"></div>
        <div><label class="text-slate-400 text-xs">Encryption</label><input name="smtp_encryption" value="{{ \App\Helpers\SettingsHelper::get('smtp_encryption', 'tls') }}" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2"></div>
        <div><label class="text-slate-400 text-xs">Username</label><input name="smtp_username" value="{{ \App\Helpers\SettingsHelper::get('smtp_username') }}" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2"></div>
        <div><label class="text-slate-400 text-xs">Password</label><input type="password" name="smtp_password" value="" placeholder="••••" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2"></div>
        <div><label class="text-slate-400 text-xs">From Address</label><input name="smtp_from_address" value="{{ \App\Helpers\SettingsHelper::get('smtp_from_address') }}" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2"></div>
        <div><label class="text-slate-400 text-xs">From Name</label><input name="smtp_from_name" value="{{ \App\Helpers\SettingsHelper::get('smtp_from_name') }}" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2"></div>
    </div>

    <button class="px-4 py-2 rounded-lg bg-fuchsia-600">Simpan Pengaturan</button>
</form>

<form method="POST" action="{{ route('admin.settings.backup') }}" class="mt-6 bg-black/20 border border-white/10 rounded-2xl p-4 text-sm">
    @csrf
    <h2 class="text-lg font-semibold">Backup Database</h2>
    <p class="text-slate-400 text-xs mb-3">Membuat file SQL dari database aktif. Pastikan <code>mysqldump</code> tersedia di server.</p>
    <button class="px-4 py-2 rounded-lg bg-amber-500 text-black">Download Backup SQL</button>
</form>
@endsection
