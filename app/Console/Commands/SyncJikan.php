<?php

namespace App\Console\Commands;

use App\Services\ScrapingService;
use Illuminate\Console\Command;

class SyncJikan extends Command
{
    protected $signature = 'scrape:jikan {--mode=ongoing : ongoing|top} {--pages=2}';

    protected $description = 'Fetch anime data from Jikan API (MyAnimeList).';

    public function handle(ScrapingService $service): int
    {
        $mode = (string) $this->option('mode');
        $pages = (int) $this->option('pages');
        $this->info("Syncing from Jikan ({$mode})...");
        $count = $mode === 'top' ? $service->syncTop($pages) : $service->syncOngoing();
        $this->info("Synced {$count} entries.");
        return self::SUCCESS;
    }
}
