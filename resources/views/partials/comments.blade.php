@props(['comments', 'commentable_type', 'commentable_id'])

<div class="space-y-4" x-data>
    @auth
        <form method="POST" action="{{ route('comments.store') }}" class="glass rounded-xl p-3 flex flex-col gap-2">
            @csrf
            <input type="hidden" name="commentable_type" value="{{ $commentable_type }}">
            <input type="hidden" name="commentable_id" value="{{ $commentable_id }}">
            <textarea name="content" rows="3" required minlength="2" maxlength="1000" placeholder="Tulis komentar…" class="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-sm"></textarea>
            <button class="self-end px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-sm">Kirim</button>
        </form>
    @else
        <p class="text-slate-400 text-sm"><a href="{{ route('login') }}" class="text-brand-300">Login</a> untuk berkomentar.</p>
    @endauth

    @forelse ($comments as $comment)
        <div class="glass rounded-xl p-3 text-sm flex gap-3">
            <img src="{{ $comment->user->avatarUrl() }}" alt="" class="w-9 h-9 rounded-full object-cover">
            <div class="flex-1">
                <div class="flex items-baseline gap-2">
                    <strong>{{ $comment->user->name }}</strong>
                    <span class="text-xs text-slate-400">{{ $comment->created_at->diffForHumans() }}</span>
                </div>
                <p class="mt-1 text-slate-200 whitespace-pre-line">{{ $comment->content }}</p>
                <div class="mt-2 flex gap-2 text-xs text-slate-400">
                    @auth
                    <button x-data="{ liked: @json($comment->isLikedBy(auth()->user())), count: {{ $comment->likes_count }} }"
                            @click="apiFetch('{{ route('comments.like', $comment) }}', {method:'POST'}).then(r=>r.json()).then(d=>{ liked=d.liked; count=d.likes })"
                            class="hover:text-rose-300">
                        <span x-text="liked ? '❤️' : '🤍'"></span>
                        <span x-text="count"></span>
                    </button>
                    @endauth
                </div>
                @if ($comment->replies->count())
                    <div class="mt-3 pl-4 border-l border-white/10 space-y-3">
                        @foreach ($comment->replies as $reply)
                            <div class="flex gap-2">
                                <img src="{{ $reply->user->avatarUrl() }}" class="w-7 h-7 rounded-full" alt="">
                                <div>
                                    <div class="flex items-baseline gap-2"><strong class="text-xs">{{ $reply->user->name }}</strong><span class="text-[10px] text-slate-400">{{ $reply->created_at->diffForHumans() }}</span></div>
                                    <p class="text-slate-200 text-xs">{{ $reply->content }}</p>
                                </div>
                            </div>
                        @endforeach
                    </div>
                @endif
            </div>
        </div>
    @empty
        <p class="text-slate-400 text-sm">Belum ada komentar.</p>
    @endforelse
</div>
