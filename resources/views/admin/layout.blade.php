<!DOCTYPE html>
<html lang="id" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="csrf-token" content="{{ csrf_token() }}">
    <title>{{ $title ?? 'Admin' }} — {{ \App\Helpers\SettingsHelper::siteName() }} Admin</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js" defer></script>
    <style>body{font-family:Inter,system-ui,sans-serif;background:#0b0617;color:white;}</style>
</head>
<body class="min-h-screen flex">

<aside class="w-60 bg-black/40 border-r border-white/5 flex-shrink-0 hidden md:block">
    <div class="p-4 border-b border-white/5">
        <a href="{{ route('admin.dashboard') }}" class="text-lg font-bold text-fuchsia-300">{{ \App\Helpers\SettingsHelper::siteName() }} Admin</a>
    </div>
    <nav class="p-3 text-sm space-y-1">
        @php $section = request()->segment(2); @endphp
        <a href="{{ route('admin.dashboard') }}" class="block px-3 py-2 rounded-lg {{ $section === null ? 'bg-fuchsia-600' : 'hover:bg-white/5' }}">Dashboard</a>
        <a href="{{ route('admin.animes.index') }}" class="block px-3 py-2 rounded-lg {{ $section === 'animes' ? 'bg-fuchsia-600' : 'hover:bg-white/5' }}">Anime</a>
        <a href="{{ route('admin.genres.index') }}" class="block px-3 py-2 rounded-lg {{ $section === 'genres' ? 'bg-fuchsia-600' : 'hover:bg-white/5' }}">Genre</a>
        <a href="{{ route('admin.studios.index') }}" class="block px-3 py-2 rounded-lg {{ $section === 'studios' ? 'bg-fuchsia-600' : 'hover:bg-white/5' }}">Studio</a>
        <a href="{{ route('admin.users.index') }}" class="block px-3 py-2 rounded-lg {{ $section === 'users' ? 'bg-fuchsia-600' : 'hover:bg-white/5' }}">User</a>
        <a href="{{ route('admin.plans.index') }}" class="block px-3 py-2 rounded-lg {{ $section === 'plans' ? 'bg-fuchsia-600' : 'hover:bg-white/5' }}">Plan & Coupon</a>
        <a href="{{ route('admin.ads.index') }}" class="block px-3 py-2 rounded-lg {{ $section === 'ads' ? 'bg-fuchsia-600' : 'hover:bg-white/5' }}">Iklan</a>
        <a href="{{ route('admin.seo.index') }}" class="block px-3 py-2 rounded-lg {{ $section === 'seo' ? 'bg-fuchsia-600' : 'hover:bg-white/5' }}">SEO</a>
        <a href="{{ route('admin.settings.edit') }}" class="block px-3 py-2 rounded-lg {{ $section === 'settings' ? 'bg-fuchsia-600' : 'hover:bg-white/5' }}">Settings</a>
        <a href="{{ route('home') }}" class="block px-3 py-2 rounded-lg hover:bg-white/5 text-emerald-300">→ Lihat Website</a>
        <form method="POST" action="{{ route('logout') }}">@csrf<button class="block w-full text-left px-3 py-2 rounded-lg text-rose-300 hover:bg-white/5">Logout</button></form>
    </nav>
</aside>

<main class="flex-1 p-6 overflow-x-auto">
    @if (session('status'))<div class="mb-4 px-4 py-2 rounded-xl bg-emerald-500/20 border border-emerald-400/30 text-emerald-200 text-sm">{{ session('status') }}</div>@endif
    @if ($errors->any())<div class="mb-4 px-4 py-2 rounded-xl bg-rose-500/20 border border-rose-400/30 text-rose-200 text-sm">
        @foreach ($errors->all() as $e)<div>{{ $e }}</div>@endforeach
    </div>@endif
    {{ $slot ?? '' }}
    @yield('content')
</main>
</body>
</html>
