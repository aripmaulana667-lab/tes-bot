<?php

namespace App\Services\Payment;

use App\Models\Payment;

interface PaymentGatewayInterface
{
    /**
     * Create a checkout/payment session and return a redirect/payment URL.
     *
     * @return array{url:string,external_id:?string,raw:array}
     */
    public function createCheckout(Payment $payment): array;

    /**
     * Process an incoming webhook/callback from the gateway and update the payment status.
     */
    public function handleWebhook(array $payload, ?string $signature = null): ?Payment;

    /**
     * Identifier for this gateway (e.g. midtrans, paypal, stripe, xendit).
     */
    public function name(): string;
}
