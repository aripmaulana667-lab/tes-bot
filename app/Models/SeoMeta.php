<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class SeoMeta extends Model
{
    protected $fillable = ['page_key', 'title', 'description', 'keywords', 'og_image'];
}
