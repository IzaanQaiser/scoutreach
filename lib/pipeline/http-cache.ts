// Rate-limited, disk-cached HTTP GET. Shared by scrape.ts and evidence.ts —
// both need "cache raw responses so re-runs cost nothing" and "respect
// rate limits" (spec §9.1, §13). Extracted here rather than duplicated
// because both stages need it verbatim.

import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

const USER_AGENT =
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36";

let lastRequestAt = 0;

function cachePathFor(cacheDir: string, namespace: string, url: string): string {
  const hash = createHash("sha256").update(url).digest("hex");
  return path.join(cacheDir, namespace, `${hash}.html`);
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
  // Read at call time (not module load) so per-call/per-test overrides
  // actually take effect — a prior version captured this as a top-level
  // const from the env var, which meant it was fixed at first import and
  // silently ignored later overrides within the same process.
  cacheDir?: string;
}

// Returns cached HTML if present; otherwise fetches, rate-limits, and
// caches. Never re-fetches a URL that's already on disk.
export async function cachedFetch(
  url: string,
  {
    namespace,
    minIntervalMs = 2000,
    cacheDir = process.env.SCOUTREACH_CACHE_DIR ?? ".cache",
  }: CachedFetchOptions,
): Promise<string> {
  const cachePath = cachePathFor(cacheDir, namespace, url);

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
