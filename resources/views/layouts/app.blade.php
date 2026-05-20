<!DOCTYPE html>
<html lang="id" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="csrf-token" content="{{ csrf_token() }}">
    <meta name="theme-color" content="{{ \App\Helpers\SettingsHelper::themeColor() }}">

    @php
        $defaultTitle = \App\Helpers\SettingsHelper::siteName();
        $metaTitle = $metaTitle ?? ($title ?? $defaultTitle);
        $metaDescription = $metaDescription ?? (string) \App\Models\Setting::get('meta_description', \App\Helpers\SettingsHelper::siteTagline());
        $metaKeywords = $metaKeywords ?? (string) \App\Models\Setting::get('meta_keywords', '');
        $metaImage = $metaImage ?? asset('images/og-default.svg');
    @endphp

    <title>{{ $metaTitle }} — {{ $defaultTitle }}</title>
    <meta name="description" content="{{ $metaDescription }}">
    @if ($metaKeywords)<meta name="keywords" content="{{ $metaKeywords }}">@endif

    <meta property="og:title" content="{{ $metaTitle }}">
    <meta property="og:description" content="{{ $metaDescription }}">
    <meta property="og:image" content="{{ $metaImage }}">
    <meta property="og:type" content="website">
    <meta property="og:url" content="{{ url()->current() }}">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{{ $metaTitle }}">
    <meta name="twitter:description" content="{{ $metaDescription }}">
    <meta name="twitter:image" content="{{ $metaImage }}">

    <link rel="manifest" href="{{ route('manifest') }}">
    <link rel="icon" href="{{ \App\Helpers\SettingsHelper::siteFavicon() ? asset('storage/' . \App\Helpers\SettingsHelper::siteFavicon()) : asset('images/favicon.svg') }}">

    @stack('schema')

    <script src="https://cdn.tailwindcss.com"></script>
    <script>
      tailwind.config = {
        darkMode: 'class',
        theme: {
          extend: {
            colors: {
              brand: {
                50: '#f5f3ff', 100: '#ede9fe', 200: '#ddd6fe', 300: '#c4b5fd',
                400: '#a78bfa', 500: '#8b5cf6', 600: '#7c3aed', 700: '#6d28d9',
                800: '#5b21b6', 900: '#4c1d95',
              },
              ink: {
                900: '#0b0617', 800: '#100a23', 700: '#1a1232', 600: '#251947', 500: '#2f1f5c',
              },
            },
            fontFamily: { sans: ['Inter', 'system-ui', 'sans-serif'] },
            boxShadow: { neon: '0 0 24px rgba(124, 58, 237, 0.55)' },
          },
        },
      };
    </script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">

    <link href="https://vjs.zencdn.net/8.10.0/video-js.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js" defer></script>
    <style>
        body { font-family: 'Inter', system-ui, sans-serif; background:
            radial-gradient(1200px 800px at 10% -10%, rgba(124,58,237,0.16), transparent 60%),
            radial-gradient(900px 600px at 110% 10%, rgba(244,63,94,0.12), transparent 60%),
            #0b0617;
        }
        .glass { background: rgba(255,255,255,0.04); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.06); }
        .scroll-snap-x { scroll-snap-type: x mandatory; }
        .scroll-snap-x > * { scroll-snap-align: start; }
        .no-scrollbar::-webkit-scrollbar { display: none; }
        .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
        .gradient-text { background: linear-gradient(135deg, #c4b5fd, #f0abfc); -webkit-background-clip: text; background-clip: text; color: transparent; }
        .anime-card:hover .anime-overlay { opacity: 1; }
    </style>
    @stack('head')
</head>
<body class="bg-ink-900 text-slate-100 min-h-screen antialiased">

@include('partials.navbar')

<main class="pt-20">
    @if (session('status'))
        <div class="max-w-7xl mx-auto px-4 mt-4">
            <div class="glass border border-emerald-400/30 text-emerald-200 rounded-xl px-4 py-2 text-sm">{{ session('status') }}</div>
        </div>
    @endif

    {{ $slot ?? '' }}
    @yield('content')
</main>

@include('partials.footer')
@include('partials.ads-popup')

<script src="https://vjs.zencdn.net/8.10.0/video.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/hls.js@1.5.13/dist/hls.min.js"></script>

<script>
    // CSRF setup for fetch
    window.csrfToken = document.querySelector('meta[name=csrf-token]').getAttribute('content');
    window.apiFetch = (url, opts = {}) => {
        opts.headers = Object.assign({
            'X-CSRF-TOKEN': window.csrfToken,
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json',
        }, opts.headers || {});
        return fetch(url, opts);
    };

    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => navigator.serviceWorker.register('/sw.js').catch(() => {}));
    }
</script>
@stack('scripts')
</body>
</html>
