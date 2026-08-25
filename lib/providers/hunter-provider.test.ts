import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { HunterContactProvider } from "./hunter-provider";

describe("HunterContactProvider", () => {
  let cacheDir: string;
  let fetchSpy: ReturnType<typeof vi.fn>;

  beforeEach(async () => {
    cacheDir = await mkdtemp(path.join(tmpdir(), "scoutreach-hunter-"));
    fetchSpy = vi.fn();
    vi.stubGlobal("fetch", fetchSpy);
  });

  afterEach(async () => {
    vi.unstubAllGlobals();
    await rm(cacheDir, { recursive: true, force: true });
  });

  it("throws if no API key is configured", () => {
    const originalEnv = process.env.HUNTER_API_KEY;
    delete process.env.HUNTER_API_KEY;
    expect(() => new HunterContactProvider()).toThrow(/HUNTER_API_KEY/);
    if (originalEnv) process.env.HUNTER_API_KEY = originalEnv;
  });

  describe("search", () => {
    it("GETs domain-search and maps the full profile Hunter returns in one call", async () => {
      fetchSpy.mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            data: {
              organization: "Example Co",
              emails: [
                {
                  value: "jordan@example.com",
                  confidence: 91,
                  first_name: "Jordan",
                  last_name: "Smith",
                  position: "VP of Engineering",
                  seniority: "executive",
                  department: "engineering",
                  linkedin: "https://linkedin.com/in/jordansmith",
                },
              ],
            },
          }),
          { status: 200 },
        ),
      );

      const provider = new HunterContactProvider({
        apiKey: "test-key",
        cacheDir,
        minIntervalMs: 0,
      });
      const results = await provider.search("example.com", ["VP of Engineering"]);

      expect(fetchSpy).toHaveBeenCalledTimes(1);
      const [url] = fetchSpy.mock.calls[0];
      expect(url).toContain("https://api.hunter.io/v2/domain-search");
      expect(url).toContain("domain=example.com");
      expect(url).toContain("api_key=test-key");

      expect(results).toEqual([
        {
          providerId: null,
          first: "Jordan",
          last: "Smith",
          title: "VP of Engineering",
          seniority: "executive",
          department: "engineering",
          linkedin: "https://linkedin.com/in/jordansmith",
          email: "jordan@example.com",
          emailConfidence: 91,
          organizationName: "Example Co",
        },
      ]);
    });

    it("filters results to matching titles when a title list is given", async () => {
      fetchSpy.mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            data: {
              organization: "Example Co",
              emails: [
                { value: "a@example.com", confidence: 80, first_name: "A", last_name: "One", position: "VP of Engineering", seniority: null, department: null, linkedin: null },
                { value: "b@example.com", confidence: 70, first_name: "B", last_name: "Two", position: "Sales Development Rep", seniority: null, department: null, linkedin: null },
              ],
            },
          }),
          { status: 200 },
        ),
      );

      const provider = new HunterContactProvider({
        apiKey: "test-key",
        cacheDir,
        minIntervalMs: 0,
      });
      const results = await provider.search("example.com", ["VP of Engineering"]);

      expect(results).toHaveLength(1);
      expect(results[0].email).toBe("a@example.com");
    });

    it("falls back to all results when nothing matches the title list, rather than returning nothing", async () => {
      fetchSpy.mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            data: {
              organization: "Example Co",
              emails: [
                { value: "a@example.com", confidence: 80, first_name: "A", last_name: "One", position: "Office Manager", seniority: null, department: null, linkedin: null },
              ],
            },
          }),
          { status: 200 },
        ),
      );

      const provider = new HunterContactProvider({
        apiKey: "test-key",
        cacheDir,
        minIntervalMs: 0,
      });
      const results = await provider.search("example.com", ["VP of Engineering"]);
      expect(results).toHaveLength(1);
    });

    it("never repeats an identical search call and never caches the API key in the cache key", async () => {
      fetchSpy.mockResolvedValue(
        new Response(JSON.stringify({ data: { organization: null, emails: [] } }), { status: 200 }),
      );
      const provider = new HunterContactProvider({
        apiKey: "test-key",
        cacheDir,
        minIntervalMs: 0,
      });

      await provider.search("example.com", []);
      await provider.search("example.com", []);

      expect(fetchSpy).toHaveBeenCalledTimes(1);
    });
  });

  describe("verifyEmail", () => {
    it("GETs email-verifier and maps Hunter's status vocabulary", async () => {
      fetchSpy.mockResolvedValueOnce(
        new Response(
          JSON.stringify({ data: { email: "jordan@example.com", status: "valid", score: 95 } }),
          { status: 200 },
        ),
      );

      const provider = new HunterContactProvider({
        apiKey: "test-key",
        cacheDir,
        minIntervalMs: 0,
      });
      const result = await provider.verifyEmail("jordan@example.com");

      const [url] = fetchSpy.mock.calls[0];
      expect(url).toContain("https://api.hunter.io/v2/email-verifier");
      expect(result).toEqual({ email: "jordan@example.com", status: "valid", score: 95 });
    });

    it.each([
      ["valid", "valid"],
      ["accept_all", "risky"],
      ["webmail", "risky"],
      ["invalid", "invalid"],
      ["disposable", "invalid"],
      ["unknown", "unknown"],
    ])("maps Hunter status %s to %s", async (hunterStatus, expected) => {
      fetchSpy.mockResolvedValueOnce(
        new Response(
          JSON.stringify({ data: { email: "x@example.com", status: hunterStatus, score: 50 } }),
          { status: 200 },
        ),
      );
      const provider = new HunterContactProvider({
        apiKey: "test-key",
        cacheDir,
        minIntervalMs: 0,
      });
      const result = await provider.verifyEmail("x@example.com");
      expect(result.status).toBe(expected);
    });

    it("never re-verifies an identical email twice", async () => {
      fetchSpy.mockResolvedValue(
        new Response(JSON.stringify({ data: { email: "x@example.com", status: "valid", score: 90 } }), {
          status: 200,
        }),
      );
      const provider = new HunterContactProvider({
        apiKey: "test-key",
        cacheDir,
        minIntervalMs: 0,
      });

      await provider.verifyEmail("x@example.com");
      await provider.verifyEmail("x@example.com");

      expect(fetchSpy).toHaveBeenCalledTimes(1);
    });
  });
});
