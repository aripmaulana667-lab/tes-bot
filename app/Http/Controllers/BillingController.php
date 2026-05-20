<?php

namespace App\Http\Controllers;

use App\Models\Coupon;
use App\Models\Payment;
use App\Models\Plan;
use App\Models\Subscription;
use App\Services\Payment\PaymentManager;
use Illuminate\Http\Request;

class BillingController extends Controller
{
    public function plans(PaymentManager $manager)
    {
        return view('billing.plans', [
            'plans' => Plan::where('is_active', true)->orderBy('sort')->get(),
            'enabled' => $manager->enabled(),
        ]);
    }

    public function checkout(Request $request, Plan $plan, PaymentManager $manager)
    {
        $data = $request->validate([
            'method' => 'required|in:midtrans,paypal,stripe,xendit',
            'coupon' => 'nullable|string|max:50',
        ]);

        $coupon = null;
        $amount = (float) $plan->price;
        if (!empty($data['coupon'])) {
            $coupon = Coupon::where('code', $data['coupon'])->first();
            if ($coupon && $coupon->isValid()) {
                $amount = $coupon->apply($amount);
            }
        }

        $payment = Payment::create([
            'user_id' => $request->user()->id,
            'plan_id' => $plan->id,
            'coupon_id' => $coupon?->id,
            'amount' => $amount,
            'currency' => $plan->currency ?: 'IDR',
            'status' => 'pending',
            'method' => $data['method'],
        ]);

        try {
            $gateway = $manager->get($data['method']);
            $result = $gateway->createCheckout($payment);
            return redirect()->away($result['url']);
        } catch (\Throwable $e) {
            $payment->update(['status' => 'failed', 'raw_response' => ['error' => $e->getMessage()]]);
            return back()->withErrors(['method' => 'Gateway error: ' . $e->getMessage()]);
        }
    }

    public function success(Request $request, Payment $payment)
    {
        abort_unless($payment->user_id === $request->user()->id, 403);
        return view('billing.result', ['payment' => $payment, 'success' => true]);
    }

    public function cancel(Request $request, Payment $payment)
    {
        abort_unless($payment->user_id === $request->user()->id, 403);
        return view('billing.result', ['payment' => $payment, 'success' => false]);
    }

    public function webhook(Request $request, string $gateway, PaymentManager $manager)
    {
        $payload = $request->all();
        $signature = $request->header('X-Signature') ?? $request->header('Stripe-Signature');
        try {
            $g = $manager->get($gateway);
            $payment = $g->handleWebhook($payload, $signature);
            if ($payment && $payment->status === 'paid' && $payment->plan_id) {
                $this->activateSubscription($payment);
            }
        } catch (\Throwable $e) {
            return response()->json(['error' => $e->getMessage()], 400);
        }
        return response()->json(['ok' => true]);
    }

    protected function activateSubscription(Payment $payment): void
    {
        $plan = $payment->plan;
        if (!$plan) {
            return;
        }
        $user = $payment->user;
        $starts = now();
        $ends = $starts->copy()->addDays($plan->duration_days);
        $sub = Subscription::create([
            'user_id' => $user->id,
            'plan_id' => $plan->id,
            'starts_at' => $starts,
            'ends_at' => $ends,
            'status' => 'active',
            'payment_method' => $payment->method,
            'transaction_id' => $payment->transaction_id,
        ]);
        $payment->update(['subscription_id' => $sub->id]);

        $user->update([
            'is_premium' => true,
            'premium_until' => $ends,
        ]);
    }
}
