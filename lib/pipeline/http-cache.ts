// Rate-limited, disk-cached HTTP calls. Shared by scrape.ts/evidence.ts
// (GET + HTML via cachedFetch) and the contact providers under
// ../providers (POST + JSON via cachedJsonCall) — both need "cache raw
// responses so re-runs cost nothing" and "respect rate limits" (spec
// §9.1, §13). Caching matters even more here: a free-plan provider's
// monthly credit cap makes a repeated call genuinely costly, not just
// slow.

import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

const USER_AGENT =
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36";

let lastRequestAt = 0;

function cachePathFor(
  cacheDir: string,
  namespace: string,
  key: string,
  extension: string,
): string {
  const hash = createHash("sha256").update(key).digest("hex");
  return path.join(cacheDir, namespace, `${hash}.${extension}`);
}

async function waitForRateLimit(minIntervalMs: number): Promise<void> {
  const elapsed = Date.now() - lastRequestAt;
  const remaining = minIntervalMs - elapsed;
  if (remaining > 0) {
    await new Promise((resolve) => setTimeout(resolve, remaining));
  }
  lastRequestAt = Date.now();
}

export interface CacheOptions {
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
  }: CacheOptions,
): Promise<string> {
  const cachePath = cachePathFor(cacheDir, namespace, url, "html");

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

// Returns a cached JSON-serializable result for cacheKey if present;
// otherwise rate-limits and calls fetcher(), caching its result. Unlike
// cachedFetch this doesn't make the HTTP call itself — callers own their
// own request (POST body/headers vary too much across APIs to abstract
// usefully) but get the same "never repeat a call, never skip the rate
// limit" guarantee, which matters more here since a repeated call can
// mean repeated credit spend, not just a wasted request.
export async function cachedJsonCall<T>(
  cacheKey: string,
  {
    namespace,
    minIntervalMs = 2000,
    cacheDir = process.env.SCOUTREACH_CACHE_DIR ?? ".cache",
  }: CacheOptions,
  fetcher: () => Promise<T>,
): Promise<T> {
  const cachePath = cachePathFor(cacheDir, namespace, cacheKey, "json");

  try {
    const cached = await readFile(cachePath, "utf-8");
    return JSON.parse(cached) as T;
  } catch {
    // not cached — fall through to fetch
  }

  await waitForRateLimit(minIntervalMs);

  const result = await fetcher();

  await mkdir(path.dirname(cachePath), { recursive: true });
  await writeFile(cachePath, JSON.stringify(result), "utf-8");

  return result;
}
