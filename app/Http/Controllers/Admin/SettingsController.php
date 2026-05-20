<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Models\Setting;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Artisan;
use Illuminate\Support\Facades\Storage;

class SettingsController extends Controller
{
    public function edit()
    {
        return view('admin.settings.edit', [
            'settings' => Setting::all()->keyBy('key'),
        ]);
    }

    public function update(Request $request)
    {
        $data = $request->validate([
            'site_name' => 'nullable|string|max:100',
            'site_tagline' => 'nullable|string|max:255',
            'site_logo' => 'nullable|string|max:500',
            'site_logo_upload' => 'nullable|image|max:2048',
            'site_favicon' => 'nullable|string|max:500',
            'site_favicon_upload' => 'nullable|image|max:512',
            'theme_color' => 'nullable|string|max:30',
            'maintenance_mode' => 'nullable|boolean',
            'smtp_host' => 'nullable|string|max:255',
            'smtp_port' => 'nullable|integer',
            'smtp_username' => 'nullable|string|max:255',
            'smtp_password' => 'nullable|string|max:255',
            'meta_description' => 'nullable|string|max:500',
            'meta_keywords' => 'nullable|string|max:500',
            'analytics_code' => 'nullable|string',
        ]);

        if ($request->hasFile('site_logo_upload')) {
            $data['site_logo'] = $request->file('site_logo_upload')->store('branding', 'public');
        }
        if ($request->hasFile('site_favicon_upload')) {
            $data['site_favicon'] = $request->file('site_favicon_upload')->store('branding', 'public');
        }
        unset($data['site_logo_upload'], $data['site_favicon_upload']);

        foreach ($data as $key => $value) {
            Setting::put($key, $value, 'general');
        }
        return back()->with('status', 'Settings tersimpan.');
    }

    public function backupDatabase()
    {
        $filename = 'backup-' . now()->format('Y_m_d_His') . '.sql';
        $path = storage_path('app/backups');
        if (!is_dir($path)) {
            mkdir($path, 0755, true);
        }

        $db = config('database.connections.' . config('database.default'));
        $file = $path . '/' . $filename;

        if (($db['driver'] ?? null) === 'mysql') {
            $cmd = sprintf(
                "mysqldump -h%s -P%s -u%s %s %s > %s",
                escapeshellarg((string) $db['host']),
                escapeshellarg((string) $db['port']),
                escapeshellarg((string) $db['username']),
                $db['password'] ? '-p' . escapeshellarg((string) $db['password']) : '',
                escapeshellarg((string) $db['database']),
                escapeshellarg($file)
            );
            @shell_exec($cmd);
        } else {
            file_put_contents($file, '-- Backup placeholder. mysqldump tidak tersedia untuk driver ' . ($db['driver'] ?? 'unknown'));
        }
        if (!file_exists($file) || filesize($file) < 10) {
            return back()->withErrors(['backup' => 'Backup gagal — pastikan mysqldump tersedia di hosting.']);
        }
        return response()->download($file)->deleteFileAfterSend(false);
    }
}
