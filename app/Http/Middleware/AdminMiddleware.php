<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

class AdminMiddleware
{
    public function handle(Request $request, Closure $next): Response
    {
        $user = $request->user();
        if (!$user || !$user->isModerator()) {
            abort(403, 'Hanya admin yang dapat mengakses halaman ini.');
        }
        return $next($request);
    }
}
