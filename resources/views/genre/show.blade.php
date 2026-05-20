@extends('layouts.app')
@section('content')
<section class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
    <h1 class="text-3xl font-extrabold gradient-text">Genre: {{ $genre->name }}</h1>
    <div class="mt-6 grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        @foreach ($animes as $a)
            <x-anime-card :anime="$a" />
        @endforeach
    </div>
    <div class="mt-6">{{ $animes->links() }}</div>
</section>
@endsection
