<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Models\SeoMeta;
use Illuminate\Http\Request;

class SeoController extends Controller
{
    public function index()
    {
        return view('admin.seo.index', [
            'metas' => SeoMeta::orderBy('page_key')->get(),
        ]);
    }

    public function store(Request $request)
    {
        $data = $request->validate([
            'page_key' => 'required|string|max:100',
            'title' => 'nullable|string|max:255',
            'description' => 'nullable|string|max:500',
            'keywords' => 'nullable|string|max:255',
            'og_image' => 'nullable|string|max:500',
        ]);
        SeoMeta::updateOrCreate(['page_key' => $data['page_key']], $data);
        return back()->with('status', 'SEO meta tersimpan.');
    }

    public function update(Request $request, SeoMeta $seo)
    {
        $data = $request->validate([
            'title' => 'nullable|string|max:255',
            'description' => 'nullable|string|max:500',
            'keywords' => 'nullable|string|max:255',
            'og_image' => 'nullable|string|max:500',
        ]);
        $seo->update($data);
        return back()->with('status', 'SEO meta diperbarui.');
    }

    public function destroy(SeoMeta $seo)
    {
        $seo->delete();
        return back()->with('status', 'SEO meta dihapus.');
    }
}
