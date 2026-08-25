import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { cachedFetch } from "./http-cache";

describe("cachedFetch", () => {
  let cacheDir: string;
  let fetchSpy: ReturnType<typeof vi.fn>;

  beforeEach(async () => {
    cacheDir = await mkdtemp(path.join(tmpdir(), "scoutreach-cache-"));
    fetchSpy = vi.fn(async () => new Response("<html>ok</html>", { status: 200 }));
    vi.stubGlobal("fetch", fetchSpy);
  });

  afterEach(async () => {
    vi.unstubAllGlobals();
    await rm(cacheDir, { recursive: true, force: true });
  });

  it("fetches over the network on a cache miss", async () => {
    const html = await cachedFetch("https://example.com/a", {
      namespace: "test",
      minIntervalMs: 0,
      cacheDir,
    });
    expect(html).toBe("<html>ok</html>");
    expect(fetchSpy).toHaveBeenCalledTimes(1);
  });

  it("makes zero network calls on a repeat request for the same URL", async () => {
    await cachedFetch("https://example.com/a", { namespace: "test", minIntervalMs: 0, cacheDir });
    await cachedFetch("https://example.com/a", { namespace: "test", minIntervalMs: 0, cacheDir });
    await cachedFetch("https://example.com/a", { namespace: "test", minIntervalMs: 0, cacheDir });

    expect(fetchSpy).toHaveBeenCalledTimes(1);
  });

  it("caches different URLs independently", async () => {
    await cachedFetch("https://example.com/a", { namespace: "test", minIntervalMs: 0, cacheDir });
    await cachedFetch("https://example.com/b", { namespace: "test", minIntervalMs: 0, cacheDir });

    expect(fetchSpy).toHaveBeenCalledTimes(2);
  });
});
