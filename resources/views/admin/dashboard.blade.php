@extends('admin.layout')
@section('content')
<h1 class="text-2xl font-bold">Dashboard</h1>

<div class="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
    @foreach ([
        ['Users', $stats['users'], 'fuchsia'],
        ['Premium', $stats['premium'], 'amber'],
        ['Anime', $stats['animes'], 'emerald'],
        ['Episodes', $stats['episodes'], 'cyan'],
        ['Views', number_format($stats['views']), 'rose'],
        ['Comments', $stats['comments'], 'lime'],
        ['Active Subs', $stats['subscriptions'], 'sky'],
        ['Revenue', 'IDR '.number_format((float) $stats['revenue']), 'orange'],
    ] as $card)
        <div class="rounded-2xl p-4 bg-{{ $card[2] }}-500/10 border border-{{ $card[2] }}-400/30">
            <div class="text-xs uppercase text-{{ $card[2] }}-300 tracking-wider">{{ $card[0] }}</div>
            <div class="text-2xl font-extrabold mt-1">{{ $card[1] }}</div>
        </div>
    @endforeach
</div>

<div class="mt-8 grid lg:grid-cols-2 gap-6">
    <div class="rounded-2xl bg-black/20 border border-white/10 p-4">
        <h2 class="font-semibold mb-3">Anime Terbaru</h2>
        <ul class="text-sm space-y-2">
            @foreach ($recentAnimes as $a)
                <li class="flex items-center justify-between gap-2">
                    <a href="{{ route('admin.animes.edit', $a) }}" class="hover:text-fuchsia-300 line-clamp-1">{{ $a->title }}</a>
                    <span class="text-xs text-slate-400">{{ ucfirst($a->status) }}</span>
                </li>
            @endforeach
        </ul>
    </div>
    <div class="rounded-2xl bg-black/20 border border-white/10 p-4">
        <h2 class="font-semibold mb-3">User Terbaru</h2>
        <ul class="text-sm space-y-2">
            @foreach ($recentUsers as $u)
                <li class="flex justify-between gap-2">
                    <span>{{ $u->name }} <small class="text-slate-400">({{ $u->email }})</small></span>
                    <span class="text-xs text-slate-400">{{ $u->created_at->diffForHumans() }}</span>
                </li>
            @endforeach
        </ul>
    </div>
    <div class="rounded-2xl bg-black/20 border border-white/10 p-4 lg:col-span-2">
        <h2 class="font-semibold mb-3">Pembayaran Terbaru</h2>
        <div class="overflow-x-auto">
            <table class="w-full text-sm">
                <thead class="text-xs text-slate-400 uppercase">
                    <tr><th class="text-left py-2">User</th><th class="text-left">Plan</th><th class="text-left">Method</th><th class="text-left">Amount</th><th class="text-left">Status</th></tr>
                </thead>
                <tbody>
                @foreach ($recentPayments as $p)
                    <tr class="border-t border-white/5"><td class="py-2">{{ $p->user?->name ?? '—' }}</td><td>{{ $p->plan?->name ?? '—' }}</td><td>{{ $p->method }}</td><td>{{ $p->currency }} {{ number_format($p->amount, 0, ',', '.') }}</td><td>{{ $p->status }}</td></tr>
                @endforeach
                </tbody>
            </table>
        </div>
    </div>
</div>
@endsection
