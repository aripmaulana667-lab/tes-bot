<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Models\User;
use Illuminate\Http\Request;

class UserAdminController extends Controller
{
    public function index(Request $request)
    {
        $q = User::query();
        if ($term = $request->query('q')) {
            $q->where(fn ($qq) => $qq
                ->where('name', 'like', "%{$term}%")
                ->orWhere('email', 'like', "%{$term}%"));
        }
        $users = $q->latest()->paginate(20);
        return view('admin.users.index', compact('users'));
    }

    public function edit(User $user)
    {
        return view('admin.users.edit', compact('user'));
    }

    public function update(Request $request, User $user)
    {
        $data = $request->validate([
            'role' => 'required|in:user,moderator,admin',
            'is_premium' => 'nullable|boolean',
            'premium_until' => 'nullable|date',
            'is_banned' => 'nullable|boolean',
        ]);
        $data['is_premium'] = (bool) ($data['is_premium'] ?? false);
        $data['is_banned'] = (bool) ($data['is_banned'] ?? false);
        $user->update($data);
        return back()->with('status', 'User updated.');
    }

    public function destroy(User $user)
    {
        abort_if($user->isAdmin() && User::where('role', 'admin')->count() === 1, 422, 'Tidak boleh hapus admin terakhir.');
        $user->delete();
        return redirect()->route('admin.users.index')->with('status', 'User dihapus.');
    }
}
