// Stage [1] — spec §9 / §9.1.
//
// Source: topstartups.io. Investigated directly (2026-08-25): it's a
// Django app with server-rendered HTML, not the Airtable/JSON backend the
// spec speculated. Its own robots.txt disallows `/*?page=` — the exact
// mechanism its infinite-scroll listing uses past the first 20 results —
// so pagination is off-limits. The workaround: its filter GET params
// (company_size, funding_round, industries, hq_location — all
// combinable, AND logic) reliably narrow result sets under 20 on page 1
// alone. buildFilterSlices() below slices spec §2's target buckets finely
// enough to stay compliant; scrapeCompanies() logs a warning (not an
// error — the human decides how to narrow further) if any single slice
// still returns a full page, since that means results are being missed.
//
// Secondary sources (YC Work at a Startup, topstartups.io/jobs,
// recent-raise lists, fund portfolio pages — spec §2) are out of scope
// for this module; they need their own scrapers with their own markup.

import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

import { parse } from "node-html-parser";
import type { InferInsertModel } from "drizzle-orm";

import type { companies } from "../db/schema";
import { cachedFetch } from "./http-cache";

export type ScrapedCompany = InferInsertModel<typeof companies>;

export interface ScrapeFilters {
  // Native topstartups.io company_size option values, e.g.
  // ["11-50 employees", "51-100 employees", "101-200 employees"]
  sizeBands: string[];
  // Native funding_round option values, e.g. ["Seed", "Series A", "Series B"]
  fundingRounds: string[];
  // Metro/region labels — expanded to city search terms via LOCATION_CITY_MAP
  locations: string[];
  // Native industries option values (spec §14: user picks 4-6 they can
  // speak to credibly — not hardcoded here)
  industries: string[];
}

// Translates the spec's target metro/region labels (§2) into the literal
// city strings topstartups.io's free-text hq_location search matches
// against. Extend as needed; this is a mechanical lookup, not a scope
// decision.
export const LOCATION_CITY_MAP: Record<string, string[]> = {
  "SF Bay": [
    "San Francisco",
    "Palo Alto",
    "Mountain View",
    "San Mateo",
    "Oakland",
    "Berkeley",
    "Menlo Park",
    "Redwood City",
    "San Jose",
  ],
  NYC: ["New York"],
  Toronto: ["Toronto"],
  Remote: ["Remote"],
};

const BASE_URL = "https://topstartups.io/";
const PAGE_SIZE = 20; // confirmed by direct inspection

interface FilterSlice {
  sizeBand: string;
  fundingRound: string;
  location: string;
  industry: string;
}

export function buildFilterSlices(filters: ScrapeFilters): FilterSlice[] {
  const slices: FilterSlice[] = [];
  for (const sizeBand of filters.sizeBands) {
    for (const fundingRound of filters.fundingRounds) {
      for (const location of filters.locations) {
        const cities = LOCATION_CITY_MAP[location] ?? [location];
        for (const city of cities) {
          for (const industry of filters.industries) {
            slices.push({ sizeBand, fundingRound, location: city, industry });
          }
        }
      }
    }
  }
  return slices;
}

function buildSliceUrl(slice: FilterSlice): string {
  const params = new URLSearchParams({
    company_size: slice.sizeBand,
    funding_round: slice.fundingRound,
    hq_location: slice.location,
    industries: slice.industry,
  });
  return `${BASE_URL}?${params.toString()}`;
}

function stripUtmSource(url: string): string {
  try {
    const parsed = new URL(url);
    parsed.searchParams.delete("utm_source");
    return parsed.toString();
  } catch {
    return url;
  }
}

function domainFromUrl(url: string): string | null {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return null;
  }
}

// Card markup confirmed by direct inspection (2026-08-25):
// .infinite-item .card, with id="startup-website-link" for name/url,
// #industry-tags / #company-size-tags / #funding-tags badge spans, and
// a "📍HQ: <text>" line for location.
export function parseCompanyCards(html: string): ScrapedCompany[] {
  const root = parse(html);
  const cards = root.querySelectorAll(".infinite-item .card");

  const results: ScrapedCompany[] = [];
  for (const card of cards) {
    const nameLink = card.querySelector("#startup-website-link");
    if (!nameLink) continue;

    const name = nameLink.text.trim();
    const websiteUrl = stripUtmSource(nameLink.getAttribute("href") ?? "");
    const domain = domainFromUrl(websiteUrl);

    const industryTags = card
      .querySelectorAll("#industry-tags")
      .map((el) => el.text.trim());

    const sizeTags = card.querySelectorAll("#company-size-tags").map((el) => el.text.trim());
    const sizeBand = sizeTags.find((t) => /employees/.test(t)) ?? null;
    const foundedMatch = sizeTags
      .map((t) => t.match(/Founded:\s*(\d{4})/))
      .find(Boolean);
    const foundedYear = foundedMatch ? foundedMatch[1] : null;

    // Funding tags are either an investor name or "[$amount] <Round> in <year>"
    // (the $-amount prefix is optional). Match against known round names
    // rather than "everything before ' in YYYY'" so a raise amount doesn't
    // get swept into the round label.
    const ROUND_NAMES =
      /(Pre-Seed|Seed|Series [A-I]|Post-IPO|Unknown)\s+in\s+(\d{4})$/;
    const fundingTags = card.querySelectorAll("#funding-tags").map((el) => el.text.trim());
    const roundTag = fundingTags.find((t) => ROUND_NAMES.test(t));
    const roundMatch = roundTag?.match(ROUND_NAMES);
    const fundingRound = roundMatch ? roundMatch[1] : null;
    const fundingYear = roundMatch ? roundMatch[2] : null;
    const investors = fundingTags.filter((t) => t !== roundTag);

    const bodyText = card.text;
    const hqMatch = bodyText.match(/HQ:\s*([^\n]+)/);
    const location = hqMatch ? hqMatch[1].trim() : null;

    const descMatch = card.innerHTML.match(
      /What they do:\s*<\/b>\s*<br>\s*([^<]+)/,
    );
    const description = descMatch ? descMatch[1].trim() : null;

    results.push({
      id: crypto.randomUUID(),
      name,
      domain,
      url: websiteUrl || null,
      stage: fundingRound,
      sizeBand,
      headcount: null,
      location,
      industry: industryTags[0] ?? null,
      description,
      lastFundingDate: fundingYear,
      investors,
      source: "topstartups.io",
      tier: null,
      status: "new",
      whyThem: null,
      canHireMe: null,
      rawJson: {
        name,
        websiteUrl,
        industryTags,
        sizeTags,
        foundedYear,
        fundingTags,
        location,
      },
      scrapedAt: new Date().toISOString(),
    });
  }
  return results;
}

async function cacheSliceHtml(url: string): Promise<string> {
  return cachedFetch(url, { namespace: "topstartups" });
}

export async function scrapeCompanies(filters: ScrapeFilters): Promise<ScrapedCompany[]> {
  const slices = buildFilterSlices(filters);
  const byDomain = new Map<string, ScrapedCompany>();

  for (const slice of slices) {
    const url = buildSliceUrl(slice);
    const html = await cacheSliceHtml(url);
    const parsed = parseCompanyCards(html);

    if (parsed.length >= PAGE_SIZE) {
      console.warn(
        `[scrape] slice hit the ${PAGE_SIZE}-result page cap (robots.txt blocks pagination past it) — narrow further: ${JSON.stringify(slice)}`,
      );
    }

    for (const company of parsed) {
      const key = company.domain ?? company.name;
      if (!byDomain.has(key)) {
        byDomain.set(key, company);
      }
    }
  }

  return Array.from(byDomain.values());
}

// Mechanically-checkable slice of spec §2's quality bar. The other two
// criteria (nameable product/buyer, public engineering surface) need a
// human or the Phase 2 evidence crawl and are not decided here — this
// only flags funding recency, since headcount is already guaranteed by
// the slice's own company_size filter.
export function passesFundingRecency(
  fundingYear: string | null,
  now: Date = new Date(),
): boolean {
  if (!fundingYear) return false;
  const yearsSince = now.getFullYear() - Number(fundingYear);
  return yearsSince <= 2;
}
