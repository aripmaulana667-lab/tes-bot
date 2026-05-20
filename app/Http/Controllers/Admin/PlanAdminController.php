<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Models\Coupon;
use App\Models\Plan;
use Illuminate\Http\Request;

class PlanAdminController extends Controller
{
    public function index()
    {
        return view('admin.plans.index', [
            'plans' => Plan::orderBy('sort')->get(),
            'coupons' => Coupon::latest()->get(),
        ]);
    }

    public function storePlan(Request $request)
    {
        $data = $request->validate([
            'name' => 'required|string|max:100',
            'description' => 'nullable|string',
            'price' => 'required|numeric|min:0',
            'currency' => 'required|string|max:8',
            'duration_days' => 'required|integer|min:1',
            'features' => 'nullable|string',
            'is_active' => 'nullable|boolean',
            'sort' => 'nullable|integer',
        ]);
        $data['features'] = $data['features']
            ? array_filter(array_map('trim', preg_split('/\r?\n/', (string) $data['features'])))
            : [];
        $data['is_active'] = (bool) ($data['is_active'] ?? true);
        Plan::create($data);
        return back()->with('status', 'Plan ditambahkan.');
    }

    public function updatePlan(Request $request, Plan $plan)
    {
        $data = $request->validate([
            'name' => 'required|string|max:100',
            'description' => 'nullable|string',
            'price' => 'required|numeric|min:0',
            'currency' => 'required|string|max:8',
            'duration_days' => 'required|integer|min:1',
            'features' => 'nullable|string',
            'is_active' => 'nullable|boolean',
            'sort' => 'nullable|integer',
        ]);
        $data['features'] = $data['features']
            ? array_filter(array_map('trim', preg_split('/\r?\n/', (string) $data['features'])))
            : [];
        $data['is_active'] = (bool) ($data['is_active'] ?? true);
        $plan->update($data);
        return back()->with('status', 'Plan diperbarui.');
    }

    public function destroyPlan(Plan $plan)
    {
        $plan->delete();
        return back()->with('status', 'Plan dihapus.');
    }

    public function storeCoupon(Request $request)
    {
        $data = $request->validate([
            'code' => 'required|string|max:50|unique:coupons,code',
            'discount_type' => 'required|in:percent,fixed',
            'discount_value' => 'required|numeric|min:0',
            'max_uses' => 'nullable|integer|min:1',
            'expires_at' => 'nullable|date',
            'is_active' => 'nullable|boolean',
        ]);
        $data['is_active'] = (bool) ($data['is_active'] ?? true);
        Coupon::create($data);
        return back()->with('status', 'Coupon ditambahkan.');
    }

    public function destroyCoupon(Coupon $coupon)
    {
        $coupon->delete();
        return back()->with('status', 'Coupon dihapus.');
    }
}
