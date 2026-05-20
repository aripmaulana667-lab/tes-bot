<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Support\Facades\Cache;

class Setting extends Model
{
    protected $fillable = ['key', 'value', 'group', 'type'];

    public static function get(string $key, mixed $default = null): mixed
    {
        $value = Cache::rememberForever('setting_' . $key, function () use ($key) {
            $setting = static::where('key', $key)->first();
            return $setting?->value;
        });

        return $value ?? $default;
    }

    public static function put(string $key, mixed $value, string $group = 'general', string $type = 'string'): void
    {
        $value = is_array($value) || is_object($value) ? json_encode($value) : (string) $value;
        static::updateOrCreate(['key' => $key], ['value' => $value, 'group' => $group, 'type' => $type]);
        Cache::forget('setting_' . $key);
    }

    public static function all_cached(): array
    {
        return Cache::rememberForever('settings_all', function () {
            return static::all()->pluck('value', 'key')->toArray();
        });
    }

    protected static function booted(): void
    {
        static::saved(function () {
            Cache::forget('settings_all');
        });
        static::deleted(function () {
            Cache::forget('settings_all');
        });
    }
}
