<footer class="mt-24 border-t border-white/5 bg-ink-900/50 py-12">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 grid md:grid-cols-4 gap-8 text-sm">
        <div>
            <h3 class="font-semibold text-lg gradient-text">{{ \App\Helpers\SettingsHelper::siteName() }}</h3>
            <p class="text-slate-400 mt-2">{{ \App\Helpers\SettingsHelper::siteTagline() }}</p>
        </div>
        <div>
            <h4 class="font-semibold mb-2">Jelajah</h4>
            <ul class="space-y-1 text-slate-300">
                <li><a href="{{ route('anime.index') }}" class="hover:text-white">Anime</a></li>
                <li><a href="{{ route('anime.donghua') }}" class="hover:text-white">Donghua</a></li>
                <li><a href="{{ route('anime.schedule') }}" class="hover:text-white">Jadwal</a></li>
                <li><a href="{{ route('genre.index') }}" class="hover:text-white">Genre</a></li>
            </ul>
        </div>
        <div>
            <h4 class="font-semibold mb-2">Akun</h4>
            <ul class="space-y-1 text-slate-300">
                <li><a href="{{ route('billing.plans') }}" class="hover:text-white">Premium Plans</a></li>
                @auth
                <li><a href="{{ route('profile.edit') }}" class="hover:text-white">Profile</a></li>
                <li><a href="{{ route('bookmarks.index') }}" class="hover:text-white">Bookmarks</a></li>
                @else
                <li><a href="{{ route('login') }}" class="hover:text-white">Login</a></li>
                <li><a href="{{ route('register') }}" class="hover:text-white">Register</a></li>
                @endauth
            </ul>
        </div>
        <div>
            <h4 class="font-semibold mb-2">Info</h4>
            <ul class="space-y-1 text-slate-300">
                <li><a href="{{ route('sitemap') }}" class="hover:text-white">Sitemap</a></li>
                <li><a href="{{ route('robots') }}" class="hover:text-white">Robots</a></li>
            </ul>
        </div>
    </div>
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-8 pt-6 border-t border-white/5 text-xs text-slate-500 flex flex-col md:flex-row gap-2 md:items-center md:justify-between">
        <div>&copy; {{ now()->year }} {{ \App\Helpers\SettingsHelper::siteName() }}. All rights reserved.</div>
        <div>Built with Laravel · TailwindCSS · Video.js</div>
    </div>
</footer>

@php
    $stickyAd = \App\Models\Ad::where('slot', 'sticky')->where('is_active', true)->first();
@endphp
@if ($stickyAd && $stickyAd->isCurrentlyActive())
<div class="fixed bottom-0 left-0 right-0 z-30">
    <div class="max-w-7xl mx-auto px-2 pb-2">
        <div class="glass border border-white/10 rounded-xl p-2 text-center text-xs flex items-center justify-between">
            <div>{!! $stickyAd->code !!}</div>
            <button onclick="this.closest('.fixed').remove()" class="text-slate-400 hover:text-white px-2">&times;</button>
        </div>
    </div>
</div>
@endif
