@extends('layouts.app')
@section('content')
<section class="max-w-7xl mx-auto px-4 mt-6">
    <h1 class="text-3xl font-extrabold gradient-text">Bookmarks</h1>
    <div class="mt-6 grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        @forelse ($bookmarks as $b)
            @if ($b->anime) <x-anime-card :anime="$b->anime" /> @endif
        @empty
            <p class="col-span-full text-slate-400 text-center py-10">Belum ada bookmark.</p>
        @endforelse
    </div>
    <div class="mt-6">{{ $bookmarks->links() }}</div>
</section>
@endsection
