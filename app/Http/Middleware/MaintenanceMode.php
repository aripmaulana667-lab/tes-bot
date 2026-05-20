<?php

namespace App\Http\Middleware;

use App\Helpers\SettingsHelper;
use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

class MaintenanceMode
{
    public function handle(Request $request, Closure $next): Response
    {
        if (
            SettingsHelper::maintenance()
            && !$request->is('admin*')
            && !$request->is('login')
            && !$request->is('logout')
            && !$request->user()?->isAdmin()
        ) {
            return response()->view('errors.maintenance', [], 503);
        }
        return $next($request);
    }
}
