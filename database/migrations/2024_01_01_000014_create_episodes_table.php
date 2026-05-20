<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('episodes', function (Blueprint $table) {
            $table->id();
            $table->foreignId('anime_id')->constrained('animes')->cascadeOnDelete();
            $table->string('number');
            $table->string('title')->nullable();
            $table->string('slug')->unique();
            $table->text('synopsis')->nullable();
            $table->string('thumbnail')->nullable();
            $table->integer('duration')->nullable()->comment('seconds');
            $table->date('air_date')->nullable();
            $table->unsignedBigInteger('views')->default(0);
            $table->boolean('is_premium')->default(false);
            $table->boolean('is_published')->default(true);
            $table->string('download_url')->nullable();
            $table->timestamps();

            $table->index(['anime_id', 'is_published']);
            $table->unique(['anime_id', 'number']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('episodes');
    }
};
