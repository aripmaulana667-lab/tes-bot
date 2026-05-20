<?php /** @var \App\Models\Ad|null $popupAd */ ?>
@php
    $popupAd = \App\Models\Ad::where('slot', 'popup')->where('is_active', true)->first();
@endphp
@if ($popupAd && $popupAd->isCurrentlyActive())
<div x-data="{ show: !localStorage.getItem('popup_ad_seen_{{ $popupAd->id }}') }" x-show="show" x-cloak class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
    <div class="relative max-w-md w-full glass border border-white/10 rounded-2xl p-6">
        <button @click="show=false; localStorage.setItem('popup_ad_seen_{{ $popupAd->id }}', '1')" class="absolute top-3 right-3 text-slate-400 hover:text-white">&times;</button>
        {!! $popupAd->code !!}
        @if($popupAd->image)
            <a href="{{ $popupAd->link ?: '#' }}" target="_blank" rel="noopener"><img src="{{ str_starts_with($popupAd->image, 'http') ? $popupAd->image : asset('storage/'.$popupAd->image) }}" alt="{{ $popupAd->name }}" class="rounded-xl"></a>
        @endif
    </div>
</div>
@endif

@php
    $popunder = \App\Models\Ad::where('slot', 'popunder')->where('is_active', true)->first();
@endphp
@if ($popunder && $popunder->isCurrentlyActive() && $popunder->type === 'script')
<script>
{!! $popunder->code !!}
</script>
@endif
