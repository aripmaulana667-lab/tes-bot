<?php

namespace App\Services\Payment;

use App\Models\Payment;
use Illuminate\Support\Facades\Http;

class StripeGateway implements PaymentGatewayInterface
{
    public function name(): string
    {
        return 'stripe';
    }

    protected function secret(): string
    {
        return (string) config('payment.stripe.secret', '');
    }

    public function createCheckout(Payment $payment): array
    {
        $secret = $this->secret();
        if (!$secret) {
            throw new \RuntimeException('Stripe secret key not configured.');
        }

        $resp = Http::asForm()
            ->withToken($secret)
            ->timeout(20)
            ->post('https://api.stripe.com/v1/checkout/sessions', [
                'mode' => 'payment',
                'success_url' => route('billing.success', ['payment' => $payment->id]),
                'cancel_url' => route('billing.cancel', ['payment' => $payment->id]),
                'line_items[0][price_data][currency]' => strtolower($payment->currency ?: 'usd'),
                'line_items[0][price_data][product_data][name]' => $payment->plan?->name ?? 'Subscription',
                'line_items[0][price_data][unit_amount]' => (int) round((float) $payment->amount * 100),
                'line_items[0][quantity]' => 1,
                'metadata[payment_id]' => (string) $payment->id,
            ]);

        if (!$resp->ok()) {
            throw new \RuntimeException('Stripe error: ' . $resp->body());
        }

        $data = $resp->json();
        $payment->update([
            'external_id' => $data['id'] ?? null,
            'transaction_id' => $data['id'] ?? null,
            'raw_response' => $data,
        ]);

        return [
            'url' => $data['url'] ?? '',
            'external_id' => $data['id'] ?? null,
            'raw' => $data,
        ];
    }

    public function handleWebhook(array $payload, ?string $signature = null): ?Payment
    {
        $event = $payload['type'] ?? null;
        $sessionId = data_get($payload, 'data.object.id');
        if (!$sessionId) {
            return null;
        }
        $payment = Payment::where('external_id', $sessionId)
            ->orWhere('transaction_id', $sessionId)
            ->first();
        if (!$payment) {
            return null;
        }

        if ($event === 'checkout.session.completed' || $event === 'checkout.session.async_payment_succeeded') {
            $payment->update([
                'status' => 'paid',
                'paid_at' => now(),
                'raw_response' => $payload,
            ]);
        } elseif ($event === 'checkout.session.async_payment_failed' || $event === 'checkout.session.expired') {
            $payment->update(['status' => 'failed', 'raw_response' => $payload]);
        } else {
            $payment->update(['raw_response' => $payload]);
        }
        return $payment;
    }
}
