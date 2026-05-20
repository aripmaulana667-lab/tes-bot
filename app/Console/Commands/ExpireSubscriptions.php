<?php

namespace App\Console\Commands;

use App\Models\Subscription;
use App\Models\User;
use Illuminate\Console\Command;

class ExpireSubscriptions extends Command
{
    protected $signature = 'subscriptions:expire';

    protected $description = 'Expire subscriptions whose end date has passed.';

    public function handle(): int
    {
        $now = now();
        $expired = Subscription::where('status', 'active')
            ->where('ends_at', '<', $now)
            ->get();
        foreach ($expired as $sub) {
            $sub->update(['status' => 'expired']);
            $user = $sub->user;
            if ($user && (!$user->premium_until || $user->premium_until->lt($now))) {
                $user->update(['is_premium' => false]);
            }
        }
        $this->info("Expired {$expired->count()} subscriptions.");
        return self::SUCCESS;
    }
}
