<?php

namespace App\Helpers;

use App\Models\Setting;

class SettingsHelper
{
    public static function get(string $key, mixed $default = null): mixed
    {
        return Setting::get($key, $default);
    }

    public static function siteName(): string
    {
        return (string) Setting::get('site_name', config('app.name', 'AniStream'));
    }

    public static function siteTagline(): string
    {
        return (string) Setting::get('site_tagline', 'Streaming anime dan donghua premium');
    }

    public static function siteLogo(): ?string
    {
        return Setting::get('site_logo');
    }

    public static function siteFavicon(): ?string
    {
        return Setting::get('site_favicon');
    }

    public static function themeColor(): string
    {
        return (string) Setting::get('theme_color', '#7c3aed');
    }

    public static function maintenance(): bool
    {
        return (bool) Setting::get('maintenance_mode', false);
    }
}
