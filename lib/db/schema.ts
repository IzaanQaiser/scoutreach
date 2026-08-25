// Drizzle schema for v0.1 — spec docs/scoutreach-new.md §10.
// Only the tables v0.1 actually touches (scrape -> evidence -> contacts -> rank).
// drafts / sends / followups / replies / me_profile / projects land in v0.2
// once the draft engine exists — see §12 build order.

import { sql } from "drizzle-orm";
import {
  integer,
  real,
  sqliteTable,
  text,
} from "drizzle-orm/sqlite-core";

export const companies = sqliteTable("companies", {
  id: text("id").primaryKey(),
  name: text("name").notNull(),
  domain: text("domain"),
  url: text("url"),
  stage: text("stage"),
  sizeBand: text("size_band"),
  headcount: integer("headcount"),
  location: text("location"),
  industry: text("industry"),
  description: text("description"),
  lastFundingDate: text("last_funding_date"),
  investors: text("investors", { mode: "json" }).$type<string[]>(),
  source: text("source").notNull(),
  // spec §4: A / B / C
  tier: text("tier"),
  status: text("status").notNull().default("new"),
  whyThem: text("why_them"),
  canHireMe: integer("can_hire_me", { mode: "boolean" }),
  rawJson: text("raw_json", { mode: "json" }),
  scrapedAt: text("scraped_at").notNull().default(sql`(current_timestamp)`),
});

export const companyEvidence = sqliteTable("company_evidence", {
  id: text("id").primaryKey(),
  companyId: text("company_id")
    .notNull()
    .references(() => companies.id, { onDelete: "cascade" }),
  // blog | changelog | docs | repo | posting | news — spec §10
  kind: text("kind").notNull(),
  url: text("url").notNull(),
  title: text("title"),
  // exact snippet, not a paraphrase — every draft claim must trace back here (§0.4, §9.1)
  snippet: text("snippet").notNull(),
  retrievedAt: text("retrieved_at").notNull().default(sql`(current_timestamp)`),
});

export const contacts = sqliteTable("contacts", {
  id: text("id").primaryKey(),
  companyId: text("company_id")
    .notNull()
    .references(() => companies.id, { onDelete: "cascade" }),
  apolloId: text("apollo_id"),
  first: text("first"),
  last: text("last"),
  title: text("title"),
  seniority: text("seniority"),
  department: text("department"),
  linkedin: text("linkedin"),
  tenureMonths: integer("tenure_months"),
  email: text("email"),
  // unknown | valid | risky | invalid | not_fetched — set once enrichment (stage 7) runs
  emailStatus: text("email_status").notNull().default("not_fetched"),
  emailSource: text("email_source"),
  rankScore: real("rank_score"),
  selected: integer("selected", { mode: "boolean" }).notNull().default(false),
  skipReason: text("skip_reason"),
  createdAt: text("created_at").notNull().default(sql`(current_timestamp)`),
});

// Append-only audit log — spec §10. Cheap, and it's how you reconstruct
// what happened when the numbers look wrong later.
export const events = sqliteTable("events", {
  id: text("id").primaryKey(),
  entity: text("entity").notNull(),
  entityId: text("entity_id").notNull(),
  type: text("type").notNull(),
  payload: text("payload", { mode: "json" }),
  at: text("at").notNull().default(sql`(current_timestamp)`),
});
