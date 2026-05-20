<?php

use App\Http\Controllers\Admin\AdAdminController;
use App\Http\Controllers\Admin\AdminController;
use App\Http\Controllers\Admin\AnimeAdminController;
use App\Http\Controllers\Admin\EpisodeAdminController;
use App\Http\Controllers\Admin\GenreAdminController;
use App\Http\Controllers\Admin\PlanAdminController;
use App\Http\Controllers\Admin\SeoController as AdminSeoController;
use App\Http\Controllers\Admin\SettingsController;
use App\Http\Controllers\Admin\StudioAdminController;
use App\Http\Controllers\Admin\UserAdminController;
use App\Http\Controllers\AnimeController;
use App\Http\Controllers\Auth\AuthController;
use App\Http\Controllers\BillingController;
use App\Http\Controllers\BookmarkController;
use App\Http\Controllers\CommentController;
use App\Http\Controllers\EpisodeController;
use App\Http\Controllers\GenreController;
use App\Http\Controllers\HistoryController;
use App\Http\Controllers\HomeController;
use App\Http\Controllers\ProfileController;
use App\Http\Controllers\RatingController;
use App\Http\Controllers\SearchController;
use App\Http\Controllers\SeoController;
use Illuminate\Support\Facades\Route;

// ============================
// Public pages
// ============================
Route::get('/', HomeController::class)->name('home');

Route::get('/anime', [AnimeController::class, 'index'])->name('anime.index');
Route::get('/ongoing', [AnimeController::class, 'ongoing'])->name('anime.ongoing');
Route::get('/completed', [AnimeController::class, 'completed'])->name('anime.completed');
Route::get('/donghua', [AnimeController::class, 'donghua'])->name('anime.donghua');
Route::get('/schedule', [AnimeController::class, 'schedule'])->name('anime.schedule');
Route::get('/anime/{anime}', [AnimeController::class, 'show'])->name('anime.show');
Route::get('/anime/{anime}/{episode}', [EpisodeController::class, 'show'])
    ->name('episode.show')
    ->scopeBindings();

Route::get('/genre', [GenreController::class, 'index'])->name('genre.index');
Route::get('/genre/{genre}', [GenreController::class, 'show'])->name('genre.show');

Route::get('/search', [SearchController::class, 'index'])->name('search.index');
Route::get('/api/search', [SearchController::class, 'realtime'])->name('search.realtime');

// SEO + PWA
Route::get('/sitemap.xml', [SeoController::class, 'sitemap'])->name('sitemap');
Route::get('/robots.txt', [SeoController::class, 'robots'])->name('robots');
Route::get('/manifest.webmanifest', [SeoController::class, 'manifest'])->name('manifest');

// ============================
// Auth
// ============================
Route::middleware('guest')->group(function () {
    Route::get('/login', [AuthController::class, 'showLogin'])->name('login');
    Route::post('/login', [AuthController::class, 'login']);

    Route::get('/register', [AuthController::class, 'showRegister'])->name('register');
    Route::post('/register', [AuthController::class, 'register']);

    Route::get('/forgot-password', [AuthController::class, 'showForgotPassword'])->name('password.request');
    Route::post('/forgot-password', [AuthController::class, 'sendResetLink'])->name('password.email');

    Route::get('/reset-password/{token}', [AuthController::class, 'showResetPassword'])->name('password.reset');
    Route::post('/reset-password', [AuthController::class, 'resetPassword'])->name('password.update');
});

Route::post('/logout', [AuthController::class, 'logout'])->middleware('auth')->name('logout');

// ============================
// Authenticated user routes
// ============================
Route::middleware('auth')->group(function () {
    Route::get('/profile', [ProfileController::class, 'edit'])->name('profile.edit');
    Route::patch('/profile', [ProfileController::class, 'update'])->name('profile.update');

    Route::get('/bookmarks', [BookmarkController::class, 'index'])->name('bookmarks.index');
    Route::post('/bookmarks/{anime}/toggle', [BookmarkController::class, 'toggle'])->name('bookmarks.toggle');

    Route::get('/history', [HistoryController::class, 'index'])->name('history.index');
    Route::post('/history/track', [HistoryController::class, 'track'])->name('history.track');
    Route::delete('/history/{watchHistory}', [HistoryController::class, 'destroy'])->name('history.destroy');

    Route::post('/comments', [CommentController::class, 'store'])->name('comments.store');
    Route::post('/comments/{comment}/like', [CommentController::class, 'like'])->name('comments.like');
    Route::delete('/comments/{comment}', [CommentController::class, 'destroy'])->name('comments.destroy');

    Route::post('/anime/{anime}/rate', [RatingController::class, 'store'])->name('ratings.store');

    // Premium / Billing
    Route::get('/billing/plans', [BillingController::class, 'plans'])->name('billing.plans');
    Route::post('/billing/checkout/{plan}', [BillingController::class, 'checkout'])->name('billing.checkout');
    Route::get('/billing/success/{payment}', [BillingController::class, 'success'])->name('billing.success');
    Route::get('/billing/cancel/{payment}', [BillingController::class, 'cancel'])->name('billing.cancel');
});

// Payment gateway webhooks (no CSRF, no auth)
Route::post('/billing/webhook/{gateway}', [BillingController::class, 'webhook'])
    ->where('gateway', 'midtrans|paypal|stripe|xendit')
    ->name('billing.webhook');

// ============================
// Admin Panel
// ============================
Route::prefix('admin')->name('admin.')->middleware(['auth', 'admin'])->group(function () {
    Route::get('/', [AdminController::class, 'dashboard'])->name('dashboard');

    Route::get('/animes', [AnimeAdminController::class, 'index'])->name('animes.index');
    Route::get('/animes/create', [AnimeAdminController::class, 'create'])->name('animes.create');
    Route::post('/animes', [AnimeAdminController::class, 'store'])->name('animes.store');
    Route::get('/animes/{anime}/edit', [AnimeAdminController::class, 'edit'])->name('animes.edit');
    Route::patch('/animes/{anime}', [AnimeAdminController::class, 'update'])->name('animes.update');
    Route::delete('/animes/{anime}', [AnimeAdminController::class, 'destroy'])->name('animes.destroy');
    Route::post('/animes/bulk-import', [AnimeAdminController::class, 'bulkImport'])->name('animes.bulk_import');

    Route::get('/animes/{anime}/episodes', [EpisodeAdminController::class, 'index'])->name('animes.episodes.index');
    Route::get('/animes/{anime}/episodes/create', [EpisodeAdminController::class, 'create'])->name('animes.episodes.create');
    Route::post('/animes/{anime}/episodes', [EpisodeAdminController::class, 'store'])->name('animes.episodes.store');
    Route::get('/animes/{anime}/episodes/{episode}/edit', [EpisodeAdminController::class, 'edit'])->name('animes.episodes.edit');
    Route::patch('/animes/{anime}/episodes/{episode}', [EpisodeAdminController::class, 'update'])->name('animes.episodes.update');
    Route::delete('/animes/{anime}/episodes/{episode}', [EpisodeAdminController::class, 'destroy'])->name('animes.episodes.destroy');
    Route::post('/animes/{anime}/episodes/batch', [EpisodeAdminController::class, 'batchUpload'])->name('animes.episodes.batch');

    Route::get('/users', [UserAdminController::class, 'index'])->name('users.index');
    Route::get('/users/{user}/edit', [UserAdminController::class, 'edit'])->name('users.edit');
    Route::patch('/users/{user}', [UserAdminController::class, 'update'])->name('users.update');
    Route::delete('/users/{user}', [UserAdminController::class, 'destroy'])->name('users.destroy');

    Route::get('/genres', [GenreAdminController::class, 'index'])->name('genres.index');
    Route::post('/genres', [GenreAdminController::class, 'store'])->name('genres.store');
    Route::patch('/genres/{genre}', [GenreAdminController::class, 'update'])->name('genres.update');
    Route::delete('/genres/{genre}', [GenreAdminController::class, 'destroy'])->name('genres.destroy');

    Route::get('/studios', [StudioAdminController::class, 'index'])->name('studios.index');
    Route::post('/studios', [StudioAdminController::class, 'store'])->name('studios.store');
    Route::patch('/studios/{studio}', [StudioAdminController::class, 'update'])->name('studios.update');
    Route::delete('/studios/{studio}', [StudioAdminController::class, 'destroy'])->name('studios.destroy');

    Route::get('/plans', [PlanAdminController::class, 'index'])->name('plans.index');
    Route::post('/plans', [PlanAdminController::class, 'storePlan'])->name('plans.store');
    Route::patch('/plans/{plan}', [PlanAdminController::class, 'updatePlan'])->name('plans.update');
    Route::delete('/plans/{plan}', [PlanAdminController::class, 'destroyPlan'])->name('plans.destroy');
    Route::post('/coupons', [PlanAdminController::class, 'storeCoupon'])->name('coupons.store');
    Route::delete('/coupons/{coupon}', [PlanAdminController::class, 'destroyCoupon'])->name('coupons.destroy');

    Route::get('/ads', [AdAdminController::class, 'index'])->name('ads.index');
    Route::get('/ads/create', [AdAdminController::class, 'create'])->name('ads.create');
    Route::post('/ads', [AdAdminController::class, 'store'])->name('ads.store');
    Route::get('/ads/{ad}/edit', [AdAdminController::class, 'edit'])->name('ads.edit');
    Route::patch('/ads/{ad}', [AdAdminController::class, 'update'])->name('ads.update');
    Route::delete('/ads/{ad}', [AdAdminController::class, 'destroy'])->name('ads.destroy');

    Route::get('/seo', [AdminSeoController::class, 'index'])->name('seo.index');
    Route::post('/seo', [AdminSeoController::class, 'store'])->name('seo.store');
    Route::patch('/seo/{seo}', [AdminSeoController::class, 'update'])->name('seo.update');
    Route::delete('/seo/{seo}', [AdminSeoController::class, 'destroy'])->name('seo.destroy');

    Route::get('/settings', [SettingsController::class, 'edit'])->name('settings.edit');
    Route::patch('/settings', [SettingsController::class, 'update'])->name('settings.update');
    Route::post('/settings/backup', [SettingsController::class, 'backupDatabase'])->name('settings.backup');
});
