<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Models\Anime;
use App\Models\Comment;
use App\Models\Episode;
use App\Models\Payment;
use App\Models\Subscription;
use App\Models\User;
use App\Models\WatchHistory;

class AdminController extends Controller
{
    public function dashboard()
    {
        return view('admin.dashboard', [
            'stats' => [
                'users' => User::count(),
                'premium' => User::where('is_premium', true)->count(),
                'animes' => Anime::count(),
                'episodes' => Episode::count(),
                'views' => Anime::sum('views') + Episode::sum('views'),
                'comments' => Comment::count(),
                'subscriptions' => Subscription::where('status', 'active')->count(),
                'revenue' => Payment::where('status', 'paid')->sum('amount'),
            ],
            'recentAnimes' => Anime::latest()->take(10)->get(),
            'recentUsers' => User::latest()->take(10)->get(),
            'recentPayments' => Payment::with(['user', 'plan'])->latest()->take(10)->get(),
        ]);
    }
}
