// Stage [1] — spec §9 / §9.1.
//
// Source: topstartups.io (primary) + secondary sources (YC Work at a Startup,
// topstartups.io/jobs, recent-raise lists, fund portfolio pages — spec §2).
//
// Before writing a DOM parser: check the network tab. The site is very likely
// Airtable-backed, and calling the JSON endpoint the frontend itself hits is
// far more stable and far less code than scraping rendered HTML. This is an
// open item in spec §14 — confirm the endpoint shape before implementing.
//
// Rules from the spec, not optional:
// - respect robots.txt / ToS, personal use only, no redistribution
// - rate-limit to ~1 request / 2s
// - cache every raw response to disk so re-runs cost nothing
// - store raw_json alongside parsed fields on the `companies` row —
//   the parser will be wrong twice before it's right

import type { InferInsertModel } from "drizzle-orm";

import type { companies } from "../db/schema";

export type ScrapedCompany = InferInsertModel<typeof companies>;

export interface ScrapeFilters {
  sizeBands: string[]; // e.g. ["11-50", "51-200"] — spec §2
  stages: string[]; // e.g. ["seed", "series_a", "series_b"]
  locations: string[];
  industries: string[];
}

export async function scrapeCompanies(
  _filters: ScrapeFilters,
): Promise<ScrapedCompany[]> {
  throw new Error("not implemented — see spec §9.1 stage [1] and §14 open items");
}
