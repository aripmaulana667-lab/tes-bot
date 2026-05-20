<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Coupon extends Model
{
    protected $fillable = [
        'code', 'discount_type', 'discount_value',
        'max_uses', 'used', 'expires_at', 'is_active',
    ];

    protected $casts = [
        'expires_at' => 'datetime',
        'is_active' => 'boolean',
        'discount_value' => 'decimal:2',
    ];

    public function isValid(): bool
    {
        if (!$this->is_active) {
            return false;
        }
        if ($this->expires_at && $this->expires_at->isPast()) {
            return false;
        }
        if ($this->max_uses && $this->used >= $this->max_uses) {
            return false;
        }
        return true;
    }

    public function apply(float $amount): float
    {
        if (!$this->isValid()) {
            return $amount;
        }
        if ($this->discount_type === 'percent') {
            return max(0, $amount - ($amount * $this->discount_value / 100));
        }
        return max(0, $amount - $this->discount_value);
    }
}
