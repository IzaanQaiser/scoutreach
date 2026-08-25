import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApolloContactProvider } from "./apollo-provider";

describe("ApolloContactProvider", () => {
  let cacheDir: string;
  let fetchSpy: ReturnType<typeof vi.fn>;

  beforeEach(async () => {
    cacheDir = await mkdtemp(path.join(tmpdir(), "scoutreach-apollo-"));
    fetchSpy = vi.fn();
    vi.stubGlobal("fetch", fetchSpy);
  });

  afterEach(async () => {
    vi.unstubAllGlobals();
    await rm(cacheDir, { recursive: true, force: true });
  });

  it("throws if no API key is configured", () => {
    const originalEnv = process.env.APOLLO_API_KEY;
    delete process.env.APOLLO_API_KEY;
    expect(() => new ApolloContactProvider()).toThrow(/APOLLO_API_KEY/);
    if (originalEnv) process.env.APOLLO_API_KEY = originalEnv;
  });

  describe("search", () => {
    it("POSTs to mixed_people/api_search with the x-api-key header and maps the obfuscated response", async () => {
      fetchSpy.mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            total_entries: 1,
            people: [
              {
                id: "abc123",
                first_name: "Jordan",
                last_name_obfuscated: "Sm**h",
                title: "VP of Engineering",
                organization: { name: "Example Co" },
              },
            ],
          }),
          { status: 200 },
        ),
      );

      const provider = new ApolloContactProvider({
        apiKey: "test-key",
        cacheDir,
        minIntervalMs: 0,
      });
      const results = await provider.search("example.com", ["VP of Engineering"]);

      expect(fetchSpy).toHaveBeenCalledTimes(1);
      const [url, init] = fetchSpy.mock.calls[0];
      expect(url).toBe("https://api.apollo.io/api/v1/mixed_people/api_search");
      expect(init.method).toBe("POST");
      expect(init.headers["x-api-key"]).toBe("test-key");

      const body = JSON.parse(init.body);
      expect(body.q_organization_domains_list).toEqual(["example.com"]);
      expect(body.person_titles).toEqual(["VP of Engineering"]);

      expect(results).toEqual([
        {
          apolloId: "abc123",
          first: "Jordan",
          lastObfuscated: "Sm**h",
          title: "VP of Engineering",
          organizationName: "Example Co",
        },
      ]);
    });

    it("never repeats an identical search call — cache hit costs zero network calls", async () => {
      fetchSpy.mockResolvedValue(
        new Response(JSON.stringify({ total_entries: 0, people: [] }), { status: 200 }),
      );
      const provider = new ApolloContactProvider({
        apiKey: "test-key",
        cacheDir,
        minIntervalMs: 0,
      });

      await provider.search("example.com", ["VP of Engineering"]);
      await provider.search("example.com", ["VP of Engineering"]);

      expect(fetchSpy).toHaveBeenCalledTimes(1);
    });
  });

  describe("enrich", () => {
    it("POSTs to people/match with reveal_personal_emails and maps the full profile including tenure", async () => {
      fetchSpy.mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            person: {
              first_name: "Jordan",
              last_name: "Smith",
              title: "VP of Engineering",
              seniority: "vp",
              departments: ["engineering"],
              linkedin_url: "https://linkedin.com/in/jordansmith",
              email: "jordan@example.com",
              email_status: "verified",
              employment_history: [
                { current: true, start_date: "2024-01-01" },
                { current: false, start_date: "2020-01-01" },
              ],
            },
          }),
          { status: 200 },
        ),
      );

      const provider = new ApolloContactProvider({
        apiKey: "test-key",
        cacheDir,
        minIntervalMs: 0,
      });
      const result = await provider.enrich("abc123");

      const [url, init] = fetchSpy.mock.calls[0];
      expect(url).toContain("people/match");
      expect(url).toContain("id=abc123");
      expect(url).toContain("reveal_personal_emails=true");
      expect(init.headers["x-api-key"]).toBe("test-key");

      expect(result.last).toBe("Smith");
      expect(result.seniority).toBe("vp");
      expect(result.department).toBe("engineering");
      expect(result.linkedin).toBe("https://linkedin.com/in/jordansmith");
      expect(result.email).toBe("jordan@example.com");
      expect(result.emailStatus).toBe("valid");
      expect(result.tenureMonths).toBeGreaterThan(0);
    });

    it("never repeats an identical enrich call — a rerun must not re-spend credits", async () => {
      fetchSpy.mockResolvedValue(
        new Response(JSON.stringify({ person: null }), { status: 200 }),
      );
      const provider = new ApolloContactProvider({
        apiKey: "test-key",
        cacheDir,
        minIntervalMs: 0,
      });

      await provider.enrich("abc123");
      await provider.enrich("abc123");

      expect(fetchSpy).toHaveBeenCalledTimes(1);
    });

    it("maps a missing match to all-null fields rather than throwing", async () => {
      fetchSpy.mockResolvedValueOnce(
        new Response(JSON.stringify({ person: null }), { status: 200 }),
      );
      const provider = new ApolloContactProvider({
        apiKey: "test-key",
        cacheDir,
        minIntervalMs: 0,
      });

      const result = await provider.enrich("unknown-id");
      expect(result.email).toBeNull();
      expect(result.emailStatus).toBe("unknown");
    });
  });
});
