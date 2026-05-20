<nav x-data="{ open: false, search: '' }" class="fixed top-0 left-0 right-0 z-40 backdrop-blur-xl bg-ink-900/70 border-b border-white/5">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-16">
            <div class="flex items-center gap-8">
                <a href="{{ route('home') }}" class="flex items-center gap-2 group">
                    <span class="inline-flex items-center justify-center w-9 h-9 rounded-xl bg-brand-600 shadow-neon group-hover:bg-brand-500 transition">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-5 h-5 text-white"><path d="M8 5v14l11-7z" /></svg>
                    </span>
                    <span class="font-bold text-lg gradient-text">{{ \App\Helpers\SettingsHelper::siteName() }}</span>
                </a>
                <div class="hidden md:flex items-center gap-1 text-sm">
                    <a href="{{ route('anime.index') }}" class="px-3 py-2 rounded-lg hover:bg-white/5">Anime</a>
                    <a href="{{ route('anime.donghua') }}" class="px-3 py-2 rounded-lg hover:bg-white/5">Donghua</a>
                    <a href="{{ route('anime.ongoing') }}" class="px-3 py-2 rounded-lg hover:bg-white/5">Ongoing</a>
                    <a href="{{ route('anime.completed') }}" class="px-3 py-2 rounded-lg hover:bg-white/5">Completed</a>
                    <a href="{{ route('anime.schedule') }}" class="px-3 py-2 rounded-lg hover:bg-white/5">Jadwal</a>
                    <a href="{{ route('genre.index') }}" class="px-3 py-2 rounded-lg hover:bg-white/5">Genre</a>
                </div>
            </div>

            <div class="hidden md:flex items-center gap-4 flex-1 max-w-md ml-6 relative" x-data="{ q: '', results: [], open: false }">
                <div class="relative w-full">
                    <input
                        type="text"
                        x-model="q"
                        @input.debounce.300ms="if(q.length>=2){ apiFetch('/api/search?q='+encodeURIComponent(q)).then(r=>r.json()).then(d=>{ results=d.results||[]; open=true }) } else { results=[]; open=false }"
                        @keydown.escape="open=false"
                        @click.outside="open=false"
                        placeholder="Cari anime / donghua…"
                        class="w-full rounded-xl bg-white/5 border border-white/10 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-500/30 pl-10 pr-4 py-2 text-sm placeholder-slate-400" />
                    <svg class="w-4 h-4 absolute left-3 top-3 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M21 21l-4.35-4.35M11 19a8 8 0 100-16 8 8 0 000 16z" stroke-linecap="round" stroke-linejoin="round"/></svg>
                </div>
                <div x-show="open && results.length" x-cloak x-transition class="absolute top-12 left-0 right-0 glass rounded-xl shadow-xl border border-white/10 p-2 z-50">
                    <template x-for="r in results" :key="r.id">
                        <a :href="r.url" class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-white/5">
                            <img :src="r.poster" class="w-10 h-14 object-cover rounded" :alt="r.title">
                            <div>
                                <div class="text-sm font-medium" x-text="r.title"></div>
                                <div class="text-xs text-slate-400" x-text="(r.type||'')+' • '+(r.year||'')+' • ⭐ '+(r.score||'-')"></div>
                            </div>
                        </a>
                    </template>
                </div>
            </div>

            <div class="hidden md:flex items-center gap-2">
                @auth
                    <a href="{{ route('billing.plans') }}" class="hidden sm:inline-flex text-xs px-3 py-1.5 rounded-lg border border-amber-400/40 text-amber-300 hover:bg-amber-400/10">
                        @if(auth()->user()->isPremium()) Premium @else Upgrade @endif
                    </a>
                    <div class="relative" x-data="{ open: false }">
                        <button @click="open = !open" class="flex items-center gap-2 px-2 py-1 rounded-xl hover:bg-white/5">
                            <img src="{{ auth()->user()->avatarUrl() }}" class="w-8 h-8 rounded-full object-cover" alt="avatar">
                            <span class="text-sm">{{ auth()->user()->name }}</span>
                        </button>
                        <div x-show="open" x-cloak @click.outside="open=false" x-transition class="absolute right-0 mt-2 w-48 glass border border-white/10 rounded-xl py-2 text-sm">
                            <a href="{{ route('profile.edit') }}" class="block px-4 py-2 hover:bg-white/5">Profile</a>
                            <a href="{{ route('bookmarks.index') }}" class="block px-4 py-2 hover:bg-white/5">Bookmarks</a>
                            <a href="{{ route('history.index') }}" class="block px-4 py-2 hover:bg-white/5">Riwayat</a>
                            @if(auth()->user()->isModerator())
                                <a href="{{ route('admin.dashboard') }}" class="block px-4 py-2 hover:bg-white/5 text-amber-300">Admin Panel</a>
                            @endif
                            <form method="POST" action="{{ route('logout') }}">@csrf
                                <button class="block w-full text-left px-4 py-2 hover:bg-white/5 text-rose-300">Logout</button>
                            </form>
                        </div>
                    </div>
                @else
                    <a href="{{ route('login') }}" class="text-sm px-3 py-1.5 rounded-lg hover:bg-white/5">Login</a>
                    <a href="{{ route('register') }}" class="text-sm px-3 py-1.5 rounded-lg bg-brand-600 hover:bg-brand-500 shadow-neon">Register</a>
                @endauth
            </div>

            <button @click="open = !open" class="md:hidden p-2 rounded-lg hover:bg-white/5">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-6 h-6"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5M3.75 17.25h16.5"/></svg>
            </button>
        </div>

        <div x-show="open" x-cloak class="md:hidden border-t border-white/10 py-3 space-y-1 text-sm">
            <form action="{{ route('search.index') }}" method="GET" class="px-2 py-1">
                <input type="text" name="q" placeholder="Cari…" class="w-full rounded-lg bg-white/5 border border-white/10 px-3 py-2">
            </form>
            <a href="{{ route('anime.index') }}" class="block px-3 py-2 hover:bg-white/5 rounded-lg">Anime</a>
            <a href="{{ route('anime.donghua') }}" class="block px-3 py-2 hover:bg-white/5 rounded-lg">Donghua</a>
            <a href="{{ route('anime.ongoing') }}" class="block px-3 py-2 hover:bg-white/5 rounded-lg">Ongoing</a>
            <a href="{{ route('anime.completed') }}" class="block px-3 py-2 hover:bg-white/5 rounded-lg">Completed</a>
            <a href="{{ route('anime.schedule') }}" class="block px-3 py-2 hover:bg-white/5 rounded-lg">Jadwal</a>
            <a href="{{ route('genre.index') }}" class="block px-3 py-2 hover:bg-white/5 rounded-lg">Genre</a>
            @auth
                <a href="{{ route('bookmarks.index') }}" class="block px-3 py-2 hover:bg-white/5 rounded-lg">Bookmarks</a>
                <a href="{{ route('history.index') }}" class="block px-3 py-2 hover:bg-white/5 rounded-lg">Riwayat</a>
                @if(auth()->user()->isModerator())
                    <a href="{{ route('admin.dashboard') }}" class="block px-3 py-2 text-amber-300 hover:bg-white/5 rounded-lg">Admin</a>
                @endif
                <form method="POST" action="{{ route('logout') }}">@csrf
                    <button class="w-full text-left px-3 py-2 text-rose-300 hover:bg-white/5 rounded-lg">Logout</button>
                </form>
            @else
                <a href="{{ route('login') }}" class="block px-3 py-2 hover:bg-white/5 rounded-lg">Login</a>
                <a href="{{ route('register') }}" class="block px-3 py-2 hover:bg-white/5 rounded-lg">Register</a>
            @endauth
        </div>
    </div>
</nav>
