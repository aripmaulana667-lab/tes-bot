<?php

namespace App\Services\Payment;

use App\Models\Payment;
use Illuminate\Support\Facades\Http;

class XenditGateway implements PaymentGatewayInterface
{
    public function name(): string
    {
        return 'xendit';
    }

    protected function secret(): string
    {
        return (string) config('payment.xendit.secret', '');
    }

    public function createCheckout(Payment $payment): array
    {
        $secret = $this->secret();
        if (!$secret) {
            throw new \RuntimeException('Xendit secret key not configured.');
        }
        $externalId = 'PAY-' . $payment->id . '-' . time();

        $resp = Http::withBasicAuth($secret, '')
            ->acceptJson()
            ->timeout(20)
            ->post('https://api.xendit.co/v2/invoices', [
                'external_id' => $externalId,
                'amount' => (int) round((float) $payment->amount),
                'description' => $payment->plan?->name ?? 'Subscription',
                'payer_email' => $payment->user?->email,
                'currency' => strtoupper($payment->currency ?: 'IDR'),
                'success_redirect_url' => route('billing.success', ['payment' => $payment->id]),
                'failure_redirect_url' => route('billing.cancel', ['payment' => $payment->id]),
            ]);

        if (!$resp->ok()) {
            throw new \RuntimeException('Xendit error: ' . $resp->body());
        }
        $data = $resp->json();
        $payment->update([
            'external_id' => $externalId,
            'transaction_id' => $data['id'] ?? null,
            'raw_response' => $data,
        ]);
        return [
            'url' => $data['invoice_url'] ?? '',
            'external_id' => $externalId,
            'raw' => $data,
        ];
    }

    public function handleWebhook(array $payload, ?string $signature = null): ?Payment
    {
        $externalId = $payload['external_id'] ?? null;
        if (!$externalId) {
            return null;
        }
        $payment = Payment::where('external_id', $externalId)->first();
        if (!$payment) {
            return null;
        }
        $status = strtoupper((string) ($payload['status'] ?? ''));
        $mapped = match ($status) {
            'PAID', 'SETTLED' => 'paid',
            'PENDING' => 'pending',
            'EXPIRED' => 'expired',
            'FAILED' => 'failed',
            default => $payment->status,
        };
        $payment->update([
            'status' => $mapped,
            'paid_at' => $mapped === 'paid' ? now() : $payment->paid_at,
            'raw_response' => $payload,
        ]);
        return $payment;
    }
}
