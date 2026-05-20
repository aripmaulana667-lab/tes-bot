<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('animes', function (Blueprint $table) {
            $table->id();
            $table->string('title');
            $table->string('title_japanese')->nullable();
            $table->string('title_english')->nullable();
            $table->string('slug')->unique();
            $table->enum('type', ['anime', 'donghua', 'movie', 'ova', 'ona', 'special'])->default('anime');
            $table->enum('status', ['ongoing', 'completed', 'upcoming', 'hiatus'])->default('ongoing');
            $table->text('synopsis')->nullable();
            $table->integer('year')->nullable();
            $table->string('season')->nullable();
            $table->integer('episodes_count')->default(0);
            $table->integer('duration')->nullable()->comment('per episode in minutes');
            $table->string('age_rating')->nullable();
            $table->decimal('score', 4, 2)->nullable();
            $table->integer('mal_id')->nullable()->unique();
            $table->integer('anilist_id')->nullable()->unique();
            $table->string('poster')->nullable();
            $table->string('banner')->nullable();
            $table->string('trailer_url')->nullable();
            $table->foreignId('studio_id')->nullable()->constrained('studios')->nullOnDelete();
            $table->string('source')->nullable();
            $table->string('country')->default('JP');
            $table->boolean('is_featured')->default(false);
            $table->boolean('is_published')->default(true);
            $table->unsignedBigInteger('views')->default(0);
            $table->string('schedule_day')->nullable();
            $table->time('schedule_time')->nullable();
            $table->string('meta_title')->nullable();
            $table->text('meta_description')->nullable();
            $table->timestamps();

            $table->index(['type', 'status', 'is_published']);
            $table->index('year');
            $table->index('views');
            $table->index('is_featured');
            $table->index('schedule_day');
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('animes');
    }
};
