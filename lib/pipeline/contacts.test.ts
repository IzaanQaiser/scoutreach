import { describe, expect, it } from "vitest";

import type { ContactProvider, ContactSearchResult } from "../providers/contact-provider";
import { fetchContacts, TARGET_TITLES } from "./contacts";

function fakeProvider(results: ContactSearchResult[]): ContactProvider {
  return {
    name: "fake",
    search: async () => results,
    verifyEmail: async () => {
      throw new Error("verifyEmail should not be called from fetchContacts (stage [5] only)");
    },
  };
}

describe("fetchContacts", () => {
  it("maps a full search result (Hunter-shaped) straight through, no deferred fields", async () => {
    const provider = fakeProvider([
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

    const rows = await fetchContacts(provider, "company-1", "example.com");

    expect(rows).toHaveLength(1);
    expect(rows[0]).toMatchObject({
      companyId: "company-1",
      first: "Jordan",
      last: "Smith",
      title: "VP of Engineering",
      seniority: "executive",
      department: "engineering",
      linkedin: "https://linkedin.com/in/jordansmith",
      email: "jordan@example.com",
      emailStatus: "valid", // confidence 91 -> valid
      emailSource: "fake",
      selected: false,
    });
  });

  it("maps confidence to emailStatus at the documented thresholds", async () => {
    const provider = fakeProvider([
      { providerId: null, first: "A", last: null, title: null, seniority: null, department: null, linkedin: null, email: "a@x.com", emailConfidence: 90, organizationName: null },
      { providerId: null, first: "B", last: null, title: null, seniority: null, department: null, linkedin: null, email: "b@x.com", emailConfidence: 60, organizationName: null },
      { providerId: null, first: "C", last: null, title: null, seniority: null, department: null, linkedin: null, email: "c@x.com", emailConfidence: 10, organizationName: null },
    ]);

    const rows = await fetchContacts(provider, "company-1", "example.com");
    expect(rows.map((r) => r.emailStatus)).toEqual(["valid", "risky", "invalid"]);
  });

  it("leaves emailStatus not_fetched when a provider gives no email at search time", async () => {
    const provider = fakeProvider([
      { providerId: "abc", first: "Jordan", last: null, title: "VP of Engineering", seniority: null, department: null, linkedin: null, email: null, emailConfidence: null, organizationName: null },
    ]);

    const rows = await fetchContacts(provider, "company-1", "example.com");
    expect(rows[0].emailStatus).toBe("not_fetched");
    expect(rows[0].emailSource).toBeNull();
  });

  it("passes the engineering/leadership/talent title set to search", async () => {
    let capturedTitles: string[] = [];
    const provider: ContactProvider = {
      name: "fake",
      search: async (_domain, titles) => {
        capturedTitles = titles;
        return [];
      },
      verifyEmail: async () => {
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
