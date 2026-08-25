import { describe, expect, it } from "vitest";

import type { contacts } from "../db/schema";
import { isRecruiterTitle, rankContacts, scoreContact, targetContactCount } from "./rank";

type ContactCandidate = typeof contacts.$inferSelect;

function candidate(overrides: Partial<ContactCandidate> & { title: string }): ContactCandidate {
  return {
    id: crypto.randomUUID(),
    companyId: "company-1",
    providerId: crypto.randomUUID(),
    first: "Test",
    last: null,
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

describe("scoreContact", () => {
  const HEADCOUNT = 200; // above the recruiter-penalty threshold, isolates title_weight

  it.each([
    ["CTO", 100],
    ["Chief Technology Officer", 100],
    ["Technical Co-Founder", 100],
    ["VP of Engineering", 90],
    ["Head of Engineering", 90],
    ["Director of Engineering", 80],
    ["Engineering Manager", 70],
    ["Staff Engineer", 65],
    ["Principal Engineer", 65],
    ["Senior Engineer", 55],
    ["Technical Recruiter", 40],
    ["Head of Talent", 40],
    ["Software Engineer", 20], // no tier match -> fallback
    ["Intern", 20],
  ])("scores %s as %i (title_weight, headcount above recruiter threshold)", (title, expected) => {
    expect(scoreContact(candidate({ title }), HEADCOUNT)).toBe(expected);
  });

  it("applies the recruiter penalty only when headcount < 120", () => {
    const recruiter = candidate({ title: "Technical Recruiter" });
    expect(scoreContact(recruiter, 119)).toBe(40 - 20); // 20
    expect(scoreContact(recruiter, 120)).toBe(40); // penalty does not apply at exactly 120
  });

  it("applies the department bonus when title text matches a supplied keyword", () => {
    const c = candidate({ title: "VP of Engineering" });
    expect(scoreContact(c, HEADCOUNT, { targetDepartments: ["engineering"] })).toBe(90 + 15);
    expect(scoreContact(c, HEADCOUNT, { targetDepartments: ["sales"] })).toBe(90);
  });

  it("defaults to no department bonus when no keywords are supplied", () => {
    const c = candidate({ title: "VP of Engineering" });
    expect(scoreContact(c, HEADCOUNT)).toBe(90);
  });

  it("prefers the real department field over title text when both are present", () => {
    // Title alone doesn't mention "engineering", but Hunter's real
    // `department` field does — the bonus must still apply.
    const c = candidate({ title: "Head of Talent", department: "engineering" });
    expect(scoreContact(c, HEADCOUNT, { targetDepartments: ["engineering"] })).toBe(40 + 15);
  });
});

describe("isRecruiterTitle", () => {
  it.each([
    ["Technical Recruiter", true],
    ["Senior Recruiter", true],
    ["Talent Acquisition Partner", true],
    ["Head of Talent", false], // "talent" alone doesn't match "talent acquisition"
    ["VP of Engineering", false],
  ])("%s -> %s", (title, expected) => {
    expect(isRecruiterTitle(title)).toBe(expected);
  });
});

describe("targetContactCount", () => {
  it.each([
    [10, 2],
    [50, 2],
    [51, 3],
    [120, 3],
    [121, 4],
    [200, 4],
  ])("headcount %i -> %i contacts", (headcount, expected) => {
    expect(targetContactCount(headcount)).toBe(expected);
  });
});

describe("rankContacts", () => {
  it("selects the top N by score for the headcount band (11-50 -> 2)", () => {
    const pool = [
      candidate({ title: "Senior Engineer" }), // 55
      candidate({ title: "CTO" }), // 100
      candidate({ title: "Software Engineer" }), // 20
    ];
    const selected = rankContacts(pool, 30);
    expect(selected).toHaveLength(2);
    expect(selected.map((c) => c.title)).toEqual(["CTO", "Senior Engineer"]);
  });

  it("never selects more than one recruiter", () => {
    const pool = [
      candidate({ title: "Technical Recruiter", providerId: "r1" }),
      candidate({ title: "Head of Talent", providerId: "r2" }), // both classify as recruiter title text
      candidate({ title: "VP of Engineering", providerId: "v1" }),
    ];
    const selected = rankContacts(pool, 200);
    const recruiterCount = selected.filter((c) => isRecruiterTitle(c.title ?? "")).length;
    expect(recruiterCount).toBeLessThanOrEqual(1);
  });

  it("never selects two contacts with the identical title", () => {
    const pool = [
      candidate({ title: "Senior Engineer", providerId: "1" }),
      candidate({ title: "Senior Engineer", providerId: "2" }),
      candidate({ title: "Senior Engineer", providerId: "3" }),
      candidate({ title: "CTO", providerId: "4" }),
    ];
    const selected = rankContacts(pool, 30);
    const titles = selected.map((c) => c.title);
    expect(new Set(titles).size).toBe(titles.length);
  });

  it("includes the naturally-highest-scoring budget-owner when top-N already contains one", () => {
    const pool = [
      candidate({ title: "Senior Engineer", providerId: "1" }), // 55
      candidate({ title: "Staff Engineer", providerId: "2" }), // 65
      candidate({ title: "Director of Engineering", providerId: "3" }), // 80, budget owner
    ];
    const selected = rankContacts(pool, 30);
    expect(selected.map((c) => c.title)).toEqual(["Director of Engineering", "Staff Engineer"]);
  });

  it("swaps in a budget-owner that scored below the natural cutoff, rather than excluding it", () => {
    // With a department bonus applied unevenly, two ICs can out-score the
    // one budget-owner in the pool on raw score alone — the selection
    // rule still requires >=1 budget-owner, so it must swap one in.
    const pool = [
      candidate({ title: "Senior Engineer", providerId: "1" }), // 55 + 15 = 70
      candidate({ title: "Staff Engineer", providerId: "2" }), // 65 + 15 = 80
      candidate({ title: "Engineering Manager", providerId: "3" }), // 70, budget owner, no keyword match
    ];
    const selected = rankContacts(pool, 30, {
      targetDepartments: ["senior", "staff", "principal"],
    });

    expect(selected).toHaveLength(2);
    expect(selected.map((c) => c.title)).toEqual(["Staff Engineer", "Engineering Manager"]);
  });

  it("degrades gracefully (no throw) when no budget-owner exists in the pool at all", () => {
    const pool = [
      candidate({ title: "Senior Engineer", providerId: "1" }),
      candidate({ title: "Staff Engineer", providerId: "2" }),
    ];
    expect(() => rankContacts(pool, 30)).not.toThrow();
    const selected = rankContacts(pool, 30);
    expect(selected.length).toBeGreaterThan(0);
  });

  it("returns an empty array for an empty pool", () => {
    expect(rankContacts([], 30)).toEqual([]);
  });
});
