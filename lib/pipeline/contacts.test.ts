import { describe, expect, it } from "vitest";

import type { ContactProvider, ContactSearchResult } from "../providers/contact-provider";
import { fetchContacts, TARGET_TITLES } from "./contacts";

function fakeProvider(results: ContactSearchResult[]): ContactProvider {
  return {
    name: "fake",
    search: async () => results,
    enrich: async () => {
      throw new Error("enrich should not be called from fetchContacts (stage [5] only)");
    },
  };
}

describe("fetchContacts", () => {
  it("maps search results into contact rows with enrichment fields left null", async () => {
    const provider = fakeProvider([
      {
        apolloId: "abc123",
        first: "Jordan",
        lastObfuscated: "Sm**h",
        title: "VP of Engineering",
        organizationName: "Example Co",
      },
    ]);

    const rows = await fetchContacts(provider, "company-1", "example.com");

    expect(rows).toHaveLength(1);
    expect(rows[0]).toMatchObject({
      companyId: "company-1",
      apolloId: "abc123",
      first: "Jordan",
      last: null,
      title: "VP of Engineering",
      seniority: null,
      department: null,
      linkedin: null,
      tenureMonths: null,
      email: null,
      emailStatus: "not_fetched",
      selected: false,
    });
  });

  it("passes the engineering/leadership/talent title set to search", async () => {
    let capturedTitles: string[] = [];
    const provider: ContactProvider = {
      name: "fake",
      search: async (_domain, titles) => {
        capturedTitles = titles;
        return [];
      },
      enrich: async () => {
        throw new Error("not used");
      },
    };

    await fetchContacts(provider, "company-1", "example.com");
    expect(capturedTitles).toEqual(TARGET_TITLES);
  });

  it("returns an empty array when a company has no matching contacts", async () => {
    const rows = await fetchContacts(fakeProvider([]), "company-1", "example.com");
    expect(rows).toEqual([]);
  });
});
