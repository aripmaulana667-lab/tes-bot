@extends('admin.layout')
@section('content')
<h1 class="text-2xl font-bold">Plan & Coupon</h1>

<div class="mt-6 grid md:grid-cols-2 gap-6">
    <div>
        <h2 class="font-semibold mb-3">Subscription Plans</h2>
        <form method="POST" action="{{ route('admin.plans.store') }}" class="bg-black/20 border border-white/10 rounded-2xl p-4 space-y-2 text-sm">
            @csrf
            <input name="name" required placeholder="Nama" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2">
            <textarea name="description" placeholder="Deskripsi" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2"></textarea>
            <div class="grid grid-cols-3 gap-2">
                <input name="price" type="number" step="0.01" placeholder="Harga" class="bg-white/5 border border-white/10 rounded-lg px-3 py-2">
                <input name="currency" value="IDR" class="bg-white/5 border border-white/10 rounded-lg px-3 py-2">
                <input name="duration_days" type="number" placeholder="Hari" class="bg-white/5 border border-white/10 rounded-lg px-3 py-2">
            </div>
            <textarea name="features" placeholder="Fitur (1 per baris)" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2"></textarea>
            <button class="px-3 py-2 rounded-lg bg-fuchsia-600">+ Tambah Plan</button>
        </form>

        <div class="mt-4 space-y-3">
            @foreach ($plans as $plan)
                <form method="POST" action="{{ route('admin.plans.update', $plan) }}" class="bg-black/20 border border-white/10 rounded-2xl p-3 text-sm space-y-2">
                    @csrf @method('PATCH')
                    <input name="name" value="{{ $plan->name }}" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2">
                    <div class="grid grid-cols-3 gap-2">
                        <input name="price" type="number" step="0.01" value="{{ $plan->price }}" class="bg-white/5 border border-white/10 rounded-lg px-3 py-2">
                        <input name="currency" value="{{ $plan->currency }}" class="bg-white/5 border border-white/10 rounded-lg px-3 py-2">
                        <input name="duration_days" type="number" value="{{ $plan->duration_days }}" class="bg-white/5 border border-white/10 rounded-lg px-3 py-2">
                    </div>
                    <textarea name="features" rows="3" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2">{{ implode("\n", $plan->features ?? []) }}</textarea>
                    <textarea name="description" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2">{{ $plan->description }}</textarea>
                    <input type="hidden" name="sort" value="{{ $plan->sort }}">
                    <label class="flex items-center gap-2"><input type="checkbox" name="is_active" value="1" @checked($plan->is_active)> Active</label>
                    <div class="flex gap-2"><button class="px-3 py-1.5 rounded-lg bg-emerald-500 text-black">Save</button>
                    </div>
                </form>
                <form method="POST" action="{{ route('admin.plans.destroy', $plan) }}" onsubmit="return confirm('Hapus plan?')" class="-mt-2 text-right">@csrf @method('DELETE')<button class="text-xs text-rose-300">Hapus plan</button></form>
            @endforeach
        </div>
    </div>

    <div>
        <h2 class="font-semibold mb-3">Coupons</h2>
        <form method="POST" action="{{ route('admin.coupons.store') }}" class="bg-black/20 border border-white/10 rounded-2xl p-4 space-y-2 text-sm">
            @csrf
            <input name="code" required placeholder="Kode kupon" class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 uppercase">
            <div class="grid grid-cols-2 gap-2">
                <select name="discount_type" class="bg-white/5 border border-white/10 rounded-lg px-3 py-2"><option value="percent">Percent</option><option value="fixed">Fixed</option></select>
                <input name="discount_value" type="number" step="0.01" placeholder="Nilai" class="bg-white/5 border border-white/10 rounded-lg px-3 py-2">
            </div>
            <div class="grid grid-cols-2 gap-2">
                <input name="max_uses" type="number" placeholder="Max uses" class="bg-white/5 border border-white/10 rounded-lg px-3 py-2">
                <input name="expires_at" type="datetime-local" class="bg-white/5 border border-white/10 rounded-lg px-3 py-2">
            </div>
            <button class="px-3 py-2 rounded-lg bg-fuchsia-600">+ Tambah Coupon</button>
        </form>

        <ul class="mt-4 space-y-2 text-sm">
            @foreach ($coupons as $c)
                <li class="bg-black/20 border border-white/10 rounded-xl p-3 flex justify-between gap-3">
                    <div>
                        <div class="font-mono font-semibold">{{ $c->code }}</div>
                        <div class="text-xs text-slate-400">{{ $c->discount_type === 'percent' ? $c->discount_value . '%' : 'Rp ' . number_format($c->discount_value) }} · used {{ $c->used_count }}/{{ $c->max_uses ?? '∞' }} · expires {{ optional($c->expires_at)->format('Y-m-d') ?? '—' }}</div>
                    </div>
                    <form method="POST" action="{{ route('admin.coupons.destroy', $c) }}" onsubmit="return confirm('Hapus?')">@csrf @method('DELETE')<button class="text-rose-300 text-xs">×</button></form>
                </li>
            @endforeach
        </ul>
    </div>
</div>
@endsection
