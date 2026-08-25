import { describe, expect, it } from "vitest";

import type { companies, contacts } from "../db/schema";
import { exportSelectedContactsCsv } from "./export";

type Company = typeof companies.$inferSelect;
type Contact = typeof contacts.$inferSelect;

function company(overrides: Partial<Company> & { id: string; name: string }): Company {
  return {
    domain: null,
    url: null,
    stage: null,
    sizeBand: null,
    headcount: null,
    location: null,
    industry: null,
    description: null,
    lastFundingDate: null,
    investors: null,
    source: "topstartups.io",
    tier: null,
    status: "new",
    whyThem: null,
    canHireMe: null,
    rawJson: null,
    scrapedAt: new Date().toISOString(),
    ...overrides,
  };
}

function contact(overrides: Partial<Contact> & { id: string; companyId: string }): Contact {
  return {
    apolloId: null,
    first: null,
    last: null,
    title: null,
    seniority: null,
    department: null,
    linkedin: null,
    tenureMonths: null,
    email: null,
    emailStatus: "not_fetched",
    emailSource: null,
    rankScore: null,
    selected: false,
    skipReason: null,
    createdAt: new Date().toISOString(),
    ...overrides,
  };
}

describe("exportSelectedContactsCsv", () => {
  it("includes exactly one row per selected contact, skipping unselected ones", () => {
    const companiesById = new Map([
      ["c1", company({ id: "c1", name: "Example Co", domain: "example.com", tier: "B", headcount: 40 })],
    ]);
    const allContacts = [
      contact({ id: "1", companyId: "c1", title: "CTO", selected: true, rankScore: 100 }),
      contact({ id: "2", companyId: "c1", title: "Junior Engineer", selected: false }),
    ];

    const csv = exportSelectedContactsCsv(companiesById, allContacts);
    const lines = csv.split("\n");

    expect(lines).toHaveLength(2); // header + 1 selected row
    expect(lines[0]).toBe(
      "company_name,company_domain,company_tier,company_headcount,contact_first,contact_last,contact_title,contact_email,contact_email_status,contact_rank_score",
    );
    expect(lines[1]).toContain("Example Co");
    expect(lines[1]).toContain("CTO");
    expect(csv).not.toContain("Junior Engineer");
  });

  it("CSV row count equals selected contact count across multiple companies", () => {
    const companiesById = new Map([
      ["c1", company({ id: "c1", name: "Alpha" })],
      ["c2", company({ id: "c2", name: "Beta" })],
    ]);
    const allContacts = [
      contact({ id: "1", companyId: "c1", selected: true }),
      contact({ id: "2", companyId: "c1", selected: true }),
      contact({ id: "3", companyId: "c1", selected: false }),
      contact({ id: "4", companyId: "c2", selected: true }),
    ];

    const csv = exportSelectedContactsCsv(companiesById, allContacts);
    const dataRows = csv.split("\n").slice(1);
    expect(dataRows).toHaveLength(3);
  });

  it("escapes values containing commas or quotes", () => {
    const companiesById = new Map([
      ["c1", company({ id: "c1", name: 'Example, "The" Co' })],
    ]);
    const allContacts = [contact({ id: "1", companyId: "c1", selected: true })];

    const csv = exportSelectedContactsCsv(companiesById, allContacts);
    expect(csv).toContain('"Example, ""The"" Co"');
  });

  it("returns just the header row when nothing is selected", () => {
    const csv = exportSelectedContactsCsv(new Map(), []);
    expect(csv.split("\n")).toHaveLength(1);
  });
});
