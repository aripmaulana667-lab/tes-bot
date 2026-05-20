<?php

use Illuminate\Console\Scheduling\Schedule;
use Illuminate\Foundation\Inspiring;
use Illuminate\Support\Facades\Artisan;
use Illuminate\Support\Facades\Schedule as ScheduleFacade;

Artisan::command('inspire', function () {
    $this->comment(Inspiring::quote());
})->purpose('Display an inspiring quote');

// Schedule callbacks executed when running `php artisan schedule:run`.
ScheduleFacade::command('scrape:jikan --mode=ongoing')->dailyAt('02:00');
ScheduleFacade::command('scrape:jikan --mode=top --pages=2')->weeklyOn(0, '03:30');
ScheduleFacade::command('scrape:anilist')->dailyAt('04:00');
ScheduleFacade::command('subscriptions:expire')->hourly();
