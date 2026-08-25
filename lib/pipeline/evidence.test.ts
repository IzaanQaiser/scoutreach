import { readFileSync } from "node:fs";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  crawlEvidence,
  crawlEvidenceForCompanies,
  evidenceStatusFor,
  extractPageEvidence,
} from "./evidence";

describe("extractPageEvidence", () => {
  it("extracts an exact-substring snippet and title from a real fetched page", () => {
    // fixture is a trimmed, real slice of https://www.avoca.ai/blog
    // (fetched 2026-08-25) — kept small, but the snippet text below is
    // verbatim from the live page, not synthesized
    const html = readFileSync("tests/fixtures/company-blog-real-slice.html", "utf-8");
    const result = extractPageEvidence(html);

    expect(result.title).toBe("Blog | Avoca AI");
    expect(result.snippet).toBe(
      "AI strategy, product updates, and stories from the field. Subscribe for new posts in your inbox.",
    );
  });

  it("strips script/style/nav/footer noise before extracting text", () => {
    const html = `
      <html><head><title>Noisy Co</title></head>
      <body>
        <script>window.__DATA__ = { secret: "should not appear" };</script>
        <nav>Home About Careers</nav>
        <main><p>This is the real paragraph content that should be extracted as the snippet.</p></main>
        <footer>Copyright 2026 Noisy Co, all rights reserved.</footer>
      </body></html>
    `;
    const result = extractPageEvidence(html);
    expect(result.snippet).toBe(
      "This is the real paragraph content that should be extracted as the snippet.",
    );
    expect(result.snippet).not.toContain("secret");
    expect(result.snippet).not.toContain("Copyright");
  });

  it("returns a null snippet when a page has no substantive text", () => {
    const html = `
      <html><head><title>Empty Shell</title></head>
      <body><script>doStuff();</script><nav>menu</nav></body></html>
    `;
    const result = extractPageEvidence(html);
    expect(result.snippet).toBeNull();
  });
});

describe("crawlEvidence", () => {
  const originalFetch = global.fetch;
  let cacheDir: string;

  beforeEach(async () => {
    cacheDir = await mkdtemp(path.join(tmpdir(), "scoutreach-evidence-"));
  });

  afterEach(async () => {
    global.fetch = originalFetch;
    vi.restoreAllMocks();
    await rm(cacheDir, { recursive: true, force: true });
  });

  it("skips paths that 404 without throwing", async () => {
    global.fetch = vi.fn(async (input: RequestInfo | URL) => {
      const url = input.toString();
      if (url.endsWith("/blog")) {
        return new Response(
          "<html><head><title>Blog</title></head><body><p>Real content here about our product roadmap and plans.</p></body></html>",
          { status: 200 },
        );
      }
      return new Response("not found", { status: 404 });
    }) as typeof fetch;

    const rows = await crawlEvidence(
      { companyId: "company-1", websiteUrl: "https://example.test" },
      { minIntervalMs: 0, cacheDir },
    );

    expect(rows).toHaveLength(1);
    expect(rows[0]).toMatchObject({
      companyId: "company-1",
      kind: "blog",
      url: "https://example.test/blog",
    });
  });

  it("includes the GitHub org as a repo row when provided", async () => {
    global.fetch = vi.fn(async (input: RequestInfo | URL) => {
      const url = input.toString();
      if (url === "https://github.com/example-co") {
        return new Response(
          "<html><head><title>example-co</title></head><body><p>Open source repositories for the example-co engineering team.</p></body></html>",
          { status: 200 },
        );
      }
      return new Response("not found", { status: 404 });
    }) as typeof fetch;

    const rows = await crawlEvidence(
      {
        companyId: "company-1",
        websiteUrl: "https://example.test",
        githubOrgUrl: "https://github.com/example-co",
      },
      { minIntervalMs: 0, cacheDir },
    );

    expect(rows).toHaveLength(1);
    expect(rows[0].kind).toBe("repo");
  });
});

describe("evidenceStatusFor", () => {
  it("flags a company with zero evidence rows as needs_evidence", () => {
    expect(evidenceStatusFor([])).toBe("needs_evidence");
  });

  it("marks a company with at least one row as new", () => {
    expect(
      evidenceStatusFor([
        {
          id: "1",
          companyId: "c1",
          kind: "blog",
          url: "https://example.test/blog",
          title: "Blog",
          snippet: "Some real content.",
          retrievedAt: new Date().toISOString(),
        },
      ]),
    ).toBe("new");
  });
});

describe("crawlEvidenceForCompanies", () => {
  let cacheDir: string;

  beforeEach(async () => {
    cacheDir = await mkdtemp(path.join(tmpdir(), "scoutreach-evidence-batch-"));
  });

  afterEach(async () => {
    vi.restoreAllMocks();
    await rm(cacheDir, { recursive: true, force: true });
  });

  it("a company whose fetch throws (DNS/connection failure) doesn't stop the batch — later companies still get processed", async () => {
    global.fetch = vi.fn(async (input: RequestInfo | URL) => {
      const url = input.toString();
      if (url.startsWith("https://unreachable.invalid")) {
        throw new Error("getaddrinfo ENOTFOUND unreachable.invalid");
      }
      if (url === "https://reachable.test/blog") {
        return new Response(
          "<html><head><title>OK</title></head><body><p>This company's blog loaded fine and has real content.</p></body></html>",
          { status: 200 },
        );
      }
      return new Response("not found", { status: 404 });
    }) as typeof fetch;

    const results = await crawlEvidenceForCompanies(
      [
        { companyId: "unreachable-co", websiteUrl: "https://unreachable.invalid" },
        { companyId: "reachable-co", websiteUrl: "https://reachable.test" },
      ],
      { minIntervalMs: 0, cacheDir },
    );

    expect(results).toHaveLength(2);

    const unreachable = results.find((r) => r.companyId === "unreachable-co");
    expect(unreachable?.status).toBe("needs_evidence");
    expect(unreachable?.rows).toHaveLength(0);

    const reachable = results.find((r) => r.companyId === "reachable-co");
    expect(reachable?.status).toBe("new");
    expect(reachable?.rows.length).toBeGreaterThan(0);
  });
});
