<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Models\Ad;
use Illuminate\Http\Request;

class AdAdminController extends Controller
{
    public function index()
    {
        $ads = Ad::latest()->paginate(20);
        return view('admin.ads.index', compact('ads'));
    }

    public function create()
    {
        return view('admin.ads.form', ['ad' => new Ad()]);
    }

    public function store(Request $request)
    {
        $ad = Ad::create($this->validateData($request));
        return redirect()->route('admin.ads.index')->with('status', 'Iklan ditambahkan.');
    }

    public function edit(Ad $ad)
    {
        return view('admin.ads.form', compact('ad'));
    }

    public function update(Request $request, Ad $ad)
    {
        $ad->update($this->validateData($request));
        return back()->with('status', 'Iklan diperbarui.');
    }

    public function destroy(Ad $ad)
    {
        $ad->delete();
        return back()->with('status', 'Iklan dihapus.');
    }

    protected function validateData(Request $request): array
    {
        $data = $request->validate([
            'name' => 'required|string|max:100',
            'slot' => 'required|in:header,sidebar,sticky,popup,popunder,inline,video_pre,video_post,footer',
            'type' => 'required|in:adsense,script,image,iframe',
            'code' => 'nullable|string',
            'image' => 'nullable|string|max:500',
            'image_upload' => 'nullable|image|max:4096',
            'link' => 'nullable|string|max:500',
            'is_active' => 'nullable|boolean',
            'starts_at' => 'nullable|date',
            'ends_at' => 'nullable|date',
        ]);
        if ($request->hasFile('image_upload')) {
            $data['image'] = $request->file('image_upload')->store('ads', 'public');
        }
        unset($data['image_upload']);
        $data['is_active'] = (bool) ($data['is_active'] ?? false);
        return $data;
    }
}
