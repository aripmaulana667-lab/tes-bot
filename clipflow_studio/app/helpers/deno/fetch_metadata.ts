// fetch_metadata.ts — Deno helper to grab basic public metadata for a YouTube video.
//
// This script does NOT bypass DRM, login, or private content. It just fetches
// the public oEmbed endpoint, which exposes the title and channel for public
// videos. If oEmbed fails it falls back to a lightweight HTML scrape of the
// public watch page (only the <title> tag).
//
// Usage:
//   deno run --allow-net --allow-read fetch_metadata.ts <url>
//
// Output: a single JSON object on stdout, e.g.
//   {"status": "ok", "platform": "youtube", "title": "...", "url": "..."}

interface MetadataResult {
  status: "ok" | "error";
  platform: string;
  title: string | null;
  url: string;
  error: string | null;
}

function emit(payload: MetadataResult): void {
  console.log(JSON.stringify(payload));
}

async function fetchOEmbed(url: string): Promise<string | null> {
  const endpoint = `https://www.youtube.com/oembed?url=${encodeURIComponent(url)}&format=json`;
  try {
    const resp = await fetch(endpoint, {
      headers: { "User-Agent": "ClipFlowStudio/0.1 (oembed)" },
    });
    if (!resp.ok) {
      return null;
    }
    const json = await resp.json();
    if (typeof json.title === "string") {
      return json.title;
    }
  } catch (_err) {
    return null;
  }
  return null;
}

async function fetchHtmlTitle(url: string): Promise<string | null> {
  try {
    const resp = await fetch(url, {
      headers: { "User-Agent": "ClipFlowStudio/0.1 (fallback)" },
    });
    if (!resp.ok) {
      return null;
    }
    const text = await resp.text();
    const match = text.match(/<title>([^<]+)<\/title>/i);
    if (!match) return null;
    return match[1].replace(/ - YouTube$/, "").trim();
  } catch (_err) {
    return null;
  }
}

const args = Deno.args;
if (args.length === 0) {
  emit({
    status: "error",
    platform: "youtube",
    title: null,
    url: "",
    error: "no_url_argument",
  });
  Deno.exit(1);
}

const url = args[0];
let title = await fetchOEmbed(url);
if (!title) {
  title = await fetchHtmlTitle(url);
}

if (title) {
  emit({
    status: "ok",
    platform: "youtube",
    title,
    url,
    error: null,
  });
} else {
  emit({
    status: "error",
    platform: "youtube",
    title: null,
    url,
    error: "metadata_unavailable",
  });
}
