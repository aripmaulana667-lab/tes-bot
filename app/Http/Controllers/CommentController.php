<?php

namespace App\Http\Controllers;

use App\Models\Anime;
use App\Models\Comment;
use App\Models\CommentLike;
use App\Models\Episode;
use Illuminate\Http\Request;

class CommentController extends Controller
{
    public function store(Request $request)
    {
        $data = $request->validate([
            'content' => 'required|string|min:2|max:1000',
            'commentable_type' => 'required|in:anime,episode',
            'commentable_id' => 'required|integer',
            'parent_id' => 'nullable|integer|exists:comments,id',
        ]);

        $modelClass = $data['commentable_type'] === 'anime' ? Anime::class : Episode::class;
        $model = $modelClass::findOrFail($data['commentable_id']);

        if ($this->looksLikeSpam($data['content'])) {
            return response()->json(['error' => 'Komentar terdeteksi sebagai spam.'], 422);
        }

        $comment = Comment::create([
            'user_id' => $request->user()->id,
            'commentable_type' => $modelClass,
            'commentable_id' => $model->id,
            'parent_id' => $data['parent_id'] ?? null,
            'content' => $data['content'],
            'is_approved' => true,
            'is_spam' => false,
        ]);

        $comment->load('user');

        if ($request->expectsJson()) {
            return response()->json([
                'comment' => [
                    'id' => $comment->id,
                    'content' => $comment->content,
                    'created_at' => $comment->created_at->diffForHumans(),
                    'user' => [
                        'name' => $comment->user->name,
                        'avatar' => $comment->user->avatarUrl(),
                    ],
                ],
            ]);
        }
        return back()->with('status', 'Comment posted.');
    }

    public function like(Request $request, Comment $comment)
    {
        $existing = CommentLike::where('comment_id', $comment->id)
            ->where('user_id', $request->user()->id)
            ->first();
        if ($existing) {
            $existing->delete();
            $comment->decrement('likes_count');
            return response()->json(['liked' => false, 'likes' => $comment->fresh()->likes_count]);
        }
        CommentLike::create([
            'comment_id' => $comment->id,
            'user_id' => $request->user()->id,
        ]);
        $comment->increment('likes_count');
        return response()->json(['liked' => true, 'likes' => $comment->fresh()->likes_count]);
    }

    public function destroy(Request $request, Comment $comment)
    {
        abort_unless(
            $comment->user_id === $request->user()->id || $request->user()->isModerator(),
            403
        );
        $comment->delete();
        return back()->with('status', 'Comment deleted.');
    }

    protected function looksLikeSpam(string $content): bool
    {
        $urls = preg_match_all('/https?:\/\//i', $content);
        if ($urls >= 3) {
            return true;
        }
        $banned = ['viagra', 'casino', 'porn', 'xxx-sex', 'crypto airdrop'];
        foreach ($banned as $word) {
            if (stripos($content, $word) !== false) {
                return true;
            }
        }
        return false;
    }
}
