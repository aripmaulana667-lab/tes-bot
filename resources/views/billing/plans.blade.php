@extends('layouts.app')
@section('content')
<section class="max-w-7xl mx-auto px-4 mt-6">
    <h1 class="text-3xl font-extrabold gradient-text text-center">Pilih Paket Premium</h1>
    <p class="text-center text-slate-400 mt-2">Buka episode premium, kualitas HD, tanpa iklan.</p>

    <div class="mt-10 grid md:grid-cols-3 gap-6">
        @foreach ($plans as $plan)
            <div class="glass rounded-2xl p-6 border @if($plan->price > 0) border-brand-500/30 shadow-neon @else border-white/10 @endif">
                <div class="flex items-baseline justify-between">
                    <h2 class="text-xl font-semibold">{{ $plan->name }}</h2>
                    @if ($plan->price > 0)<span class="text-xs px-2 py-0.5 bg-amber-500 text-black rounded-full">Premium</span>@endif
                </div>
                <div class="mt-3 text-3xl font-extrabold">
                    @if ($plan->price > 0)
                        {{ $plan->currency }} {{ number_format($plan->price, 0, ',', '.') }}
                    @else
                        Gratis
                    @endif
                </div>
                <div class="text-xs text-slate-400">untuk {{ $plan->duration_days }} hari</div>
                <p class="text-sm text-slate-300 mt-3">{{ $plan->description }}</p>
                <ul class="mt-3 space-y-1 text-sm text-slate-300">
                    @foreach (($plan->features ?? []) as $feature)
                        <li>✓ {{ $feature }}</li>
                    @endforeach
                </ul>
                @if ($plan->price > 0)
                <form method="POST" action="{{ route('billing.checkout', $plan) }}" class="mt-5 space-y-2 text-sm">
                    @csrf
                    <label class="block text-slate-400 text-xs">Metode pembayaran</label>
                    <select name="method" class="w-full rounded-xl bg-white/5 border border-white/10 px-3 py-2">
                        @foreach ($enabled as $g => $on)
                            @if ($on)<option value="{{ $g }}">{{ ucfirst($g) }}</option>@endif
                        @endforeach
                    </select>
                    @if (empty($enabled))
                        <p class="text-xs text-rose-300">Belum ada gateway pembayaran aktif. Hubungi admin.</p>
                    @endif
                    <input name="coupon" placeholder="Kode kupon (opsional)" class="w-full rounded-xl bg-white/5 border border-white/10 px-3 py-2">
                    <button class="w-full py-2 rounded-xl bg-brand-600 hover:bg-brand-500 disabled:opacity-50" @disabled(empty($enabled))>Bayar Sekarang</button>
                </form>
                @endif
            </div>
        @endforeach
    </div>
</section>
@endsection
