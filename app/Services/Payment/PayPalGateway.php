<?php

namespace App\Services\Payment;

use App\Models\Payment;
use Illuminate\Support\Facades\Http;

class PayPalGateway implements PaymentGatewayInterface
{
    public function name(): string
    {
        return 'paypal';
    }

    protected function base(): string
    {
        return config('payment.paypal.mode', 'sandbox') === 'live'
            ? 'https://api-m.paypal.com'
            : 'https://api-m.sandbox.paypal.com';
    }

    protected function clientId(): string
    {
        return (string) config('payment.paypal.client_id', '');
    }

    protected function clientSecret(): string
    {
        return (string) config('payment.paypal.client_secret', '');
    }

    protected function token(): string
    {
        $clientId = $this->clientId();
        $secret = $this->clientSecret();
        if (!$clientId || !$secret) {
            throw new \RuntimeException('PayPal credentials not configured.');
        }
        $resp = Http::asForm()
            ->withBasicAuth($clientId, $secret)
            ->timeout(20)
            ->post($this->base() . '/v1/oauth2/token', ['grant_type' => 'client_credentials']);
        if (!$resp->ok()) {
            throw new \RuntimeException('PayPal auth error: ' . $resp->body());
        }
        return (string) ($resp->json('access_token') ?? '');
    }

    public function createCheckout(Payment $payment): array
    {
        $token = $this->token();
        $currency = strtoupper($payment->currency ?: 'USD');
        $resp = Http::withToken($token)
            ->acceptJson()
            ->timeout(20)
            ->post($this->base() . '/v2/checkout/orders', [
                'intent' => 'CAPTURE',
                'purchase_units' => [[
                    'amount' => [
                        'currency_code' => $currency,
                        'value' => number_format((float) $payment->amount, 2, '.', ''),
                    ],
                    'description' => $payment->plan?->name ?? 'Subscription',
                    'custom_id' => (string) $payment->id,
                ]],
                'application_context' => [
                    'return_url' => route('billing.success', ['payment' => $payment->id]),
                    'cancel_url' => route('billing.cancel', ['payment' => $payment->id]),
                ],
            ]);

        if (!$resp->ok()) {
            throw new \RuntimeException('PayPal error: ' . $resp->body());
        }
        $data = $resp->json();
        $approve = null;
        foreach (($data['links'] ?? []) as $link) {
            if (($link['rel'] ?? '') === 'approve') {
                $approve = $link['href'] ?? null;
                break;
            }
        }
        $payment->update([
            'external_id' => $data['id'] ?? null,
            'transaction_id' => $data['id'] ?? null,
            'raw_response' => $data,
        ]);
        return [
            'url' => $approve ?? '',
            'external_id' => $data['id'] ?? null,
            'raw' => $data,
        ];
    }

    public function handleWebhook(array $payload, ?string $signature = null): ?Payment
    {
        $event = $payload['event_type'] ?? null;
        $orderId = data_get($payload, 'resource.id')
            ?? data_get($payload, 'resource.supplementary_data.related_ids.order_id');
        if (!$orderId) {
            return null;
        }
        $payment = Payment::where('external_id', $orderId)->orWhere('transaction_id', $orderId)->first();
        if (!$payment) {
            return null;
        }
        if (in_array($event, ['CHECKOUT.ORDER.APPROVED', 'PAYMENT.CAPTURE.COMPLETED'], true)) {
            $payment->update(['status' => 'paid', 'paid_at' => now(), 'raw_response' => $payload]);
        } elseif (in_array($event, ['CHECKOUT.ORDER.VOIDED', 'PAYMENT.CAPTURE.DENIED'], true)) {
            $payment->update(['status' => 'failed', 'raw_response' => $payload]);
        } else {
            $payment->update(['raw_response' => $payload]);
        }
        return $payment;
    }
}
