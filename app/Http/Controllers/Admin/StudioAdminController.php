<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Models\Studio;
use Illuminate\Http\Request;

class StudioAdminController extends Controller
{
    public function index()
    {
        return view('admin.studios.index', ['studios' => Studio::orderBy('name')->paginate(40)]);
    }

    public function store(Request $request)
    {
        Studio::create($request->validate([
            'name' => 'required|string|max:100|unique:studios,name',
            'country' => 'nullable|string|max:50',
        ]));
        return back()->with('status', 'Studio ditambahkan.');
    }

    public function update(Request $request, Studio $studio)
    {
        $studio->update($request->validate([
            'name' => 'required|string|max:100',
            'country' => 'nullable|string|max:50',
        ]));
        return back()->with('status', 'Studio diperbarui.');
    }

    public function destroy(Studio $studio)
    {
        $studio->delete();
        return back()->with('status', 'Studio dihapus.');
    }
}
