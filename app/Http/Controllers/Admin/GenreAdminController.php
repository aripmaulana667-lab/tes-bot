<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Models\Genre;
use Illuminate\Http\Request;

class GenreAdminController extends Controller
{
    public function index()
    {
        return view('admin.genres.index', ['genres' => Genre::orderBy('name')->paginate(40)]);
    }

    public function store(Request $request)
    {
        $data = $request->validate(['name' => 'required|string|max:100|unique:genres,name']);
        Genre::create($data);
        return back()->with('status', 'Genre ditambahkan.');
    }

    public function update(Request $request, Genre $genre)
    {
        $data = $request->validate(['name' => 'required|string|max:100']);
        $genre->update($data);
        return back()->with('status', 'Genre diperbarui.');
    }

    public function destroy(Genre $genre)
    {
        $genre->delete();
        return back()->with('status', 'Genre dihapus.');
    }
}
