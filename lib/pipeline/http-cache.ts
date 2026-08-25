// Rate-limited, disk-cached HTTP GET. Shared by scrape.ts and (later)
// evidence.ts — both need "cache raw responses so re-runs cost nothing"
// and "respect rate limits" (spec §9.1, §13). Extracted here rather than
// duplicated because both stages need it verbatim.

import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

const CACHE_DIR = process.env.SCOUTREACH_CACHE_DIR ?? ".cache";
const USER_AGENT =
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36";

let lastRequestAt = 0;

function cachePathFor(namespace: string, url: string): string {
  const hash = createHash("sha256").update(url).digest("hex");
  return path.join(CACHE_DIR, namespace, `${hash}.html`);
}

async function waitForRateLimit(minIntervalMs: number): Promise<void> {
  const elapsed = Date.now() - lastRequestAt;
  const remaining = minIntervalMs - elapsed;
  if (remaining > 0) {
    await new Promise((resolve) => setTimeout(resolve, remaining));
  }
  lastRequestAt = Date.now();
}

export interface CachedFetchOptions {
  namespace: string;
  minIntervalMs?: number;
}

// Returns cached HTML if present; otherwise fetches, rate-limits, and
// caches. Never re-fetches a URL that's already on disk.
export async function cachedFetch(
  url: string,
  { namespace, minIntervalMs = 2000 }: CachedFetchOptions,
): Promise<string> {
  const cachePath = cachePathFor(namespace, url);

  try {
    return await readFile(cachePath, "utf-8");
  } catch {
    // not cached — fall through to fetch
  }

  await waitForRateLimit(minIntervalMs);

  const response = await fetch(url, {
    headers: { "User-Agent": USER_AGENT },
  });
  if (!response.ok) {
    throw new Error(`GET ${url} failed: ${response.status} ${response.statusText}`);
  }
  const html = await response.text();

  await mkdir(path.dirname(cachePath), { recursive: true });
  await writeFile(cachePath, html, "utf-8");

  return html;
}
