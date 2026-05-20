@props(['title', 'href' => null])
<div class="flex items-end justify-between mb-4">
    <h2 class="text-xl md:text-2xl font-semibold tracking-tight">{{ $title }}</h2>
    @if ($href)
        <a href="{{ $href }}" class="text-sm text-brand-300 hover:text-brand-200">Lihat semua →</a>
    @endif
</div>
