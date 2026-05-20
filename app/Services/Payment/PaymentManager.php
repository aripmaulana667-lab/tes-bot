<?php

namespace App\Services\Payment;

class PaymentManager
{
    /**
     * @return array<string,PaymentGatewayInterface>
     */
    public function gateways(): array
    {
        return [
            'midtrans' => new MidtransGateway(),
            'paypal' => new PayPalGateway(),
            'stripe' => new StripeGateway(),
            'xendit' => new XenditGateway(),
        ];
    }

    public function get(string $name): PaymentGatewayInterface
    {
        $g = $this->gateways();
        if (!isset($g[$name])) {
            throw new \InvalidArgumentException("Unknown payment gateway: {$name}");
        }
        return $g[$name];
    }

    public function enabled(): array
    {
        return array_filter([
            'midtrans' => (bool) config('payment.midtrans.server_key'),
            'paypal' => (bool) config('payment.paypal.client_id'),
            'stripe' => (bool) config('payment.stripe.secret'),
            'xendit' => (bool) config('payment.xendit.secret'),
        ]);
    }
}
