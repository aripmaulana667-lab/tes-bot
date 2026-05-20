<?php

namespace App\Http\Controllers;

use App\Models\Anime;
use App\Models\Genre;
use Illuminate\Http\Response;

class SeoController extends Controller
{
    public function sitemap()
    {
        $xml = '<?xml version="1.0" encoding="UTF-8"?>' . "\n";
        $xml .= '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' . "\n";

        $base = rtrim(config('app.url'), '/');
        $xml .= $this->urlNode($base . '/', '1.0', 'daily');
        $xml .= $this->urlNode($base . '/anime', '0.9', 'daily');
        $xml .= $this->urlNode($base . '/donghua', '0.9', 'daily');
        $xml .= $this->urlNode($base . '/schedule', '0.7', 'daily');
        $xml .= $this->urlNode($base . '/search', '0.5', 'weekly');

        Genre::orderBy('name')->each(function (Genre $g) use (&$xml, $base) {
            $xml .= $this->urlNode($base . '/genre/' . $g->slug, '0.6', 'weekly');
        });

        Anime::published()->select('slug', 'updated_at')->orderByDesc('updated_at')->limit(5000)->each(function (Anime $a) use (&$xml, $base) {
            $xml .= $this->urlNode($base . '/anime/' . $a->slug, '0.8', 'weekly', $a->updated_at);
        });

        $xml .= '</urlset>';

        return response($xml, 200)->header('Content-Type', 'application/xml');
    }

    protected function urlNode(string $loc, string $priority, string $changefreq, $lastmod = null): string
    {
        $out = "  <url>\n";
        $out .= "    <loc>" . htmlspecialchars($loc) . "</loc>\n";
        if ($lastmod) {
            $out .= "    <lastmod>" . (is_string($lastmod) ? $lastmod : $lastmod->toAtomString()) . "</lastmod>\n";
        }
        $out .= "    <changefreq>{$changefreq}</changefreq>\n";
        $out .= "    <priority>{$priority}</priority>\n";
        $out .= "  </url>\n";
        return $out;
    }

    public function robots(): Response
    {
        $base = rtrim(config('app.url'), '/');
        $body = "User-agent: *\nAllow: /\nDisallow: /admin\nDisallow: /api/internal\nSitemap: {$base}/sitemap.xml\n";
        return response($body, 200)->header('Content-Type', 'text/plain');
    }

    public function manifest()
    {
        $name = \App\Helpers\SettingsHelper::siteName();
        $color = \App\Helpers\SettingsHelper::themeColor();
        return response()->json([
            'name' => $name,
            'short_name' => $name,
            'start_url' => '/',
            'display' => 'standalone',
            'background_color' => '#0b0617',
            'theme_color' => $color,
            'description' => \App\Helpers\SettingsHelper::siteTagline(),
            'icons' => [
                ['src' => asset('images/icon-192.png'), 'sizes' => '192x192', 'type' => 'image/png'],
                ['src' => asset('images/icon-512.png'), 'sizes' => '512x512', 'type' => 'image/png'],
            ],
        ]);
    }
}
