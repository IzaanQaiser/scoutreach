import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

describe("cachedFetch", () => {
  let cacheDir: string;
  let fetchSpy: ReturnType<typeof vi.fn>;

  beforeEach(async () => {
    cacheDir = await mkdtemp(path.join(tmpdir(), "scoutreach-cache-"));
    process.env.SCOUTREACH_CACHE_DIR = cacheDir;
    fetchSpy = vi.fn(async () => new Response("<html>ok</html>", { status: 200 }));
    vi.stubGlobal("fetch", fetchSpy);
  });

  afterEach(async () => {
    vi.unstubAllGlobals();
    vi.resetModules();
    delete process.env.SCOUTREACH_CACHE_DIR;
    await rm(cacheDir, { recursive: true, force: true });
  });

  it("fetches over the network on a cache miss", async () => {
    const { cachedFetch } = await import("./http-cache");
    const html = await cachedFetch("https://example.com/a", {
      namespace: "test",
      minIntervalMs: 0,
    });
    expect(html).toBe("<html>ok</html>");
    expect(fetchSpy).toHaveBeenCalledTimes(1);
  });

  it("makes zero network calls on a repeat request for the same URL", async () => {
    const { cachedFetch } = await import("./http-cache");
    await cachedFetch("https://example.com/a", { namespace: "test", minIntervalMs: 0 });
    await cachedFetch("https://example.com/a", { namespace: "test", minIntervalMs: 0 });
    await cachedFetch("https://example.com/a", { namespace: "test", minIntervalMs: 0 });

    expect(fetchSpy).toHaveBeenCalledTimes(1);
  });

  it("caches different URLs independently", async () => {
    const { cachedFetch } = await import("./http-cache");
    await cachedFetch("https://example.com/a", { namespace: "test", minIntervalMs: 0 });
    await cachedFetch("https://example.com/b", { namespace: "test", minIntervalMs: 0 });

    expect(fetchSpy).toHaveBeenCalledTimes(2);
  });
});
