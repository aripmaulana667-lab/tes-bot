<?php

namespace App\Services\Payment;

use App\Models\Payment;
use Illuminate\Support\Facades\Http;

class MidtransGateway implements PaymentGatewayInterface
{
    public function name(): string
    {
        return 'midtrans';
    }

    protected function baseUrl(): string
    {
        return config('payment.midtrans.is_production', false)
            ? 'https://app.midtrans.com/snap/v1'
            : 'https://app.sandbox.midtrans.com/snap/v1';
    }

    protected function serverKey(): string
    {
        return (string) config('payment.midtrans.server_key', '');
    }

    public function createCheckout(Payment $payment): array
    {
        $serverKey = $this->serverKey();
        if (!$serverKey) {
            throw new \RuntimeException('Midtrans server key not configured.');
        }

        $orderId = 'INV-' . $payment->id . '-' . time();
        $payload = [
            'transaction_details' => [
                'order_id' => $orderId,
                'gross_amount' => (int) round((float) $payment->amount),
            ],
            'customer_details' => [
                'first_name' => $payment->user?->name ?? 'Guest',
                'email' => $payment->user?->email ?? 'guest@example.com',
            ],
            'item_details' => [
                [
                    'id' => 'plan-' . ($payment->plan_id ?? 0),
                    'price' => (int) round((float) $payment->amount),
                    'quantity' => 1,
                    'name' => $payment->plan?->name ?? 'Subscription',
                ],
            ],
            'callbacks' => [
                'finish' => route('billing.success', ['payment' => $payment->id]),
            ],
        ];

        $resp = Http::withBasicAuth($serverKey, '')
            ->acceptJson()
            ->timeout(20)
            ->post($this->baseUrl() . '/transactions', $payload);

        if (!$resp->ok()) {
            throw new \RuntimeException('Midtrans error: ' . $resp->body());
        }

        $data = $resp->json();
        $payment->update([
            'external_id' => $orderId,
            'transaction_id' => $data['token'] ?? null,
            'raw_response' => $data,
        ]);

        return [
            'url' => $data['redirect_url'] ?? '',
            'external_id' => $orderId,
            'raw' => $data,
        ];
    }

    public function handleWebhook(array $payload, ?string $signature = null): ?Payment
    {
        $orderId = $payload['order_id'] ?? null;
        if (!$orderId) {
            return null;
        }
        $payment = Payment::where('external_id', $orderId)->first();
        if (!$payment) {
            return null;
        }
        $status = strtolower((string) ($payload['transaction_status'] ?? ''));
        $mapped = match ($status) {
            'settlement', 'capture' => 'paid',
            'pending' => 'pending',
            'cancel', 'deny', 'failure' => 'failed',
            'expire' => 'expired',
            'refund' => 'refunded',
            default => $payment->status,
        };
        $payment->update([
            'status' => $mapped,
            'raw_response' => $payload,
            'paid_at' => $mapped === 'paid' ? now() : $payment->paid_at,
        ]);
        return $payment;
    }
}
