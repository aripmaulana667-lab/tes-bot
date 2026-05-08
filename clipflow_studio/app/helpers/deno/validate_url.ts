// validate_url.ts — Deno helper used as a fallback for Python URL validation.
//
// Usage:
//   deno run --allow-net --allow-read validate_url.ts <url>
//
// Output: a single JSON object printed on stdout, e.g.
//   {"valid": true, "platform": "youtube", "url": "https://...", "error": null}

const YOUTUBE_HOSTS = new Set([
  "youtube.com",
  "www.youtube.com",
  "m.youtube.com",
  "youtu.be",
  "music.youtube.com",
]);

function emit(payload: Record<string, unknown>): void {
  console.log(JSON.stringify(payload));
}

function classify(url: string): { valid: boolean; platform: string | null; error: string | null } {
  let parsed: URL;
  try {
    parsed = new URL(url);
  } catch (_err) {
    return { valid: false, platform: null, error: "invalid_url" };
  }
  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
    return { valid: false, platform: null, error: "unsupported_protocol" };
  }
  if (!YOUTUBE_HOSTS.has(parsed.hostname)) {
    return { valid: false, platform: null, error: "not_youtube" };
  }
  if (parsed.hostname === "youtu.be" && parsed.pathname.length > 1) {
    return { valid: true, platform: "youtube", error: null };
  }
  if (parsed.searchParams.has("v") || parsed.pathname.startsWith("/shorts/")) {
    return { valid: true, platform: "youtube", error: null };
  }
  return { valid: false, platform: "youtube", error: "missing_video_id" };
}

const args = Deno.args;
if (args.length === 0) {
  emit({ valid: false, platform: null, url: null, error: "no_url_argument" });
  Deno.exit(1);
}

const url = args[0];
const result = classify(url);
emit({
  valid: result.valid,
  platform: result.platform,
  url,
  error: result.error,
});
Deno.exit(result.valid ? 0 : 0); // exit 0 even on invalid so we can read stdout
