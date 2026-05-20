<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('episode_servers', function (Blueprint $table) {
            $table->id();
            $table->foreignId('episode_id')->constrained('episodes')->cascadeOnDelete();
            $table->string('server_name');
            $table->enum('type', ['mp4', 'm3u8', 'iframe', 'embed'])->default('iframe');
            $table->text('url');
            $table->string('quality')->default('720p');
            $table->string('language')->default('sub');
            $table->string('subtitle_url')->nullable();
            $table->integer('priority')->default(0);
            $table->boolean('is_active')->default(true);
            $table->timestamps();

            $table->index(['episode_id', 'is_active']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('episode_servers');
    }
};
