@extends('layouts.app')
@section('content')
<section class="max-w-md mx-auto mt-12 px-4 text-center">
    <div class="glass rounded-2xl p-8">
        @if ($success && $payment->status === 'paid')
            <h1 class="text-2xl font-bold gradient-text">Pembayaran Berhasil</h1>
            <p class="mt-2 text-slate-300">Akun Premium anda telah aktif. Selamat menikmati!</p>
        @elseif ($success)
            <h1 class="text-2xl font-bold gradient-text">Menunggu Konfirmasi</h1>
            <p class="mt-2 text-slate-300">Status pembayaran sedang diproses. Refresh halaman ini setelah beberapa menit.</p>
        @else
            <h1 class="text-2xl font-bold gradient-text">Pembayaran Dibatalkan</h1>
            <p class="mt-2 text-slate-300">Anda dapat mencoba metode pembayaran lain.</p>
        @endif
        <div class="mt-6 text-xs text-slate-400">
            ID Transaksi: {{ $payment->external_id ?? $payment->id }}<br>
            Status: <strong>{{ ucfirst($payment->status) }}</strong>
        </div>
        <a href="{{ route('home') }}" class="inline-flex mt-6 px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500">Kembali ke Beranda</a>
    </div>
</section>
@endsection
