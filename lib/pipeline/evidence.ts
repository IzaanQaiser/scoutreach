// Stage [2] — spec §9 / §9.1.
//
// For each company: fetch /blog, /changelog, /docs, /careers,
// /engineering off its own domain, plus its GitHub org if known. Store
// URL + title + exact snippet + retrieved_at per item — a paraphrase is
// not acceptable, the whole evidence-gate design (§0.4) depends on being
// able to point at the literal source text later. Target 3-8 rows per
// company; most companies won't have all 5 paths (verified against a
// real site while building this: 3 of 5 resolved).
//
// "Recent news" (the 6th source in §9.1) is not implemented here — it
// needs a search provider (e.g. a news API or Google News RSS), not a
// direct fetch like the rest of this stage, and picking one is a
// separate decision. TODO before this stage can reliably hit its own
// 3-8-rows target for companies with a thin owned-content footprint.
//
// Verified directly against a real site (2026-08-25): modern startup
// sites are frequently Next.js/React SPAs. The first few hundred bytes
// of <body> can be a hydration placeholder, but the actual page content
// is still present as server-rendered text further into the HTML — a
// plain fetch + strip-script/style + read visible text works. No
// headless browser needed for this stage.

import type { InferInsertModel } from "drizzle-orm";
import { parse } from "node-html-parser";

import type { companyEvidence } from "../db/schema";
import { cachedFetch } from "./http-cache";

export type EvidenceRow = InferInsertModel<typeof companyEvidence>;
type EvidenceKind = EvidenceRow["kind"];

// spec §10 only defines these kinds; /careers and /engineering don't
// have exact matches so they're mapped to the closest fit.
const DIRECT_PATHS: { path: string; kind: EvidenceKind }[] = [
  { path: "/blog", kind: "blog" },
  { path: "/changelog", kind: "changelog" },
  { path: "/docs", kind: "docs" },
  { path: "/careers", kind: "posting" },
  { path: "/engineering", kind: "blog" },
];

const NOISE_TAGS = ["script", "style", "noscript", "nav", "footer", "header", "svg"];
const MIN_SNIPPET_LENGTH = 40;
const SNIPPET_LENGTH = 320;

export interface ExtractedPage {
  title: string | null;
  snippet: string | null;
}

// Exact-substring extraction, not a paraphrase or summary — this stage
// runs before any AI model is involved (spec §0.4).
export function extractPageEvidence(html: string): ExtractedPage {
  const root = parse(html);
  for (const tag of NOISE_TAGS) {
    root.querySelectorAll(tag).forEach((el) => el.remove());
  }

  const title =
    root.querySelector("title")?.text.trim() || root.querySelector("h1")?.text.trim() || null;

  const paragraphs = root
    .querySelectorAll("p, li, h2, h3")
    .map((el) => el.text.replace(/\s+/g, " ").trim())
    .filter((text) => text.length >= MIN_SNIPPET_LENGTH);

  const snippet = paragraphs[0]
    ? paragraphs[0].slice(0, SNIPPET_LENGTH).trim()
    : null;

  return { title, snippet };
}

async function fetchOptional(
  url: string,
  minIntervalMs: number,
  cacheDir: string | undefined,
): Promise<string | null> {
  try {
    return await cachedFetch(url, { namespace: "evidence", minIntervalMs, cacheDir });
  } catch {
    // 404s and unreachable pages are the expected common case (most
    // companies don't have all 5 paths) — skip, don't fail the company.
    return null;
  }
}

export interface EvidenceSource {
  companyId: string;
  websiteUrl: string;
  githubOrgUrl?: string | null;
}

export interface CrawlEvidenceOptions {
  // spec §9.1: ~1 req/2s. Configurable so tests don't pay real wall-clock
  // time for a rate limit that only matters against the live site.
  minIntervalMs?: number;
  // Passed straight through to cachedFetch; unset means its own default
  // (SCOUTREACH_CACHE_DIR env var, or .cache).
  cacheDir?: string;
}

export async function crawlEvidence(
  source: EvidenceSource,
  { minIntervalMs = 2000, cacheDir }: CrawlEvidenceOptions = {},
): Promise<EvidenceRow[]> {
  const base = new URL(source.websiteUrl);
  const rows: EvidenceRow[] = [];

  const targets: { url: string; kind: EvidenceKind }[] = [
    ...DIRECT_PATHS.map(({ path, kind }) => ({ url: new URL(path, base).toString(), kind })),
    ...(source.githubOrgUrl ? [{ url: source.githubOrgUrl, kind: "repo" as EvidenceKind }] : []),
  ];

  for (const { url, kind } of targets) {
    const html = await fetchOptional(url, minIntervalMs, cacheDir);
    if (!html) continue;

    const { title, snippet } = extractPageEvidence(html);
    if (!snippet) continue; // page loaded but had no usable content — skip, don't store empty evidence

    rows.push({
      id: crypto.randomUUID(),
      companyId: source.companyId,
      kind,
      url,
      title,
      snippet,
      retrievedAt: new Date().toISOString(),
    });
  }

  return rows;
}

export type EvidenceStatus = "new" | "needs_evidence";

// spec §2 rule 4: no evidence rows -> flag for review, never silently drop.
export function evidenceStatusFor(rows: EvidenceRow[]): EvidenceStatus {
  return rows.length === 0 ? "needs_evidence" : "new";
}

export interface EvidenceCrawlResult {
  companyId: string;
  rows: EvidenceRow[];
  status: EvidenceStatus;
}

// One unreachable/broken company must not stop the batch — each
// company's crawl is isolated and always produces a result (possibly
// empty + flagged), never an unhandled rejection.
export async function crawlEvidenceForCompanies(
  sources: EvidenceSource[],
  options: CrawlEvidenceOptions = {},
): Promise<EvidenceCrawlResult[]> {
  const results: EvidenceCrawlResult[] = [];
  for (const source of sources) {
    let rows: EvidenceRow[] = [];
    try {
      rows = await crawlEvidence(source, options);
    } catch {
      rows = [];
    }
    results.push({ companyId: source.companyId, rows, status: evidenceStatusFor(rows) });
  }
  return results;
}
