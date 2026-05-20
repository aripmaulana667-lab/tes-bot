<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('ratings', function (Blueprint $table) {
            $table->id();
            $table->foreignId('user_id')->constrained('users')->cascadeOnDelete();
            $table->foreignId('anime_id')->constrained('animes')->cascadeOnDelete();
            $table->tinyInteger('score')->comment('1-10');
            $table->text('review')->nullable();
            $table->timestamps();
            $table->unique(['user_id', 'anime_id']);
            $table->index('anime_id');
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('ratings');
    }
};
