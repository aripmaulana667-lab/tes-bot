@props(['slot'])
@php
    $ad = \Illuminate\Support\Facades\Cache::remember('ad_' . $slot, 60, function () use ($slot) {
        return \App\Models\Ad::where('slot', $slot)->where('is_active', true)->latest()->first();
    });
@endphp
@if ($ad && $ad->isCurrentlyActive())
    <div class="ad-slot ad-{{ $slot }} my-4">
        @if ($ad->type === 'image' && $ad->image)
            <a href="{{ $ad->link ?: '#' }}" target="_blank" rel="noopener" class="block">
                <img src="{{ str_starts_with($ad->image, 'http') ? $ad->image : asset('storage/'.$ad->image) }}" alt="{{ $ad->name }}" class="w-full rounded-xl">
            </a>
        @elseif ($ad->type === 'iframe')
            <iframe src="{{ $ad->url }}" class="w-full" frameborder="0"></iframe>
        @else
            {!! $ad->code !!}
        @endif
    </div>
@endif
