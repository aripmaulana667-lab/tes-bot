<?php

namespace App\Console\Commands;

use App\Services\ScrapingService;
use Illuminate\Console\Command;

class SyncAniList extends Command
{
    protected $signature = 'scrape:anilist';

    protected $description = 'Fetch trending anime/donghua from AniList GraphQL API.';

    public function handle(ScrapingService $service): int
    {
        $this->info('Syncing from AniList...');
        $count = $service->syncTrending();
        $this->info("Synced {$count} entries.");
        return self::SUCCESS;
    }
}
