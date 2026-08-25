import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

import {
  buildFilterSlices,
  parseCompanyCards,
  passesFundingRecency,
} from "./scrape";

const FIXTURE_PATH = "tests/fixtures/topstartups-slice.html";

describe("parseCompanyCards", () => {
  const html = readFileSync(FIXTURE_PATH, "utf-8");
  const results = parseCompanyCards(html);

  it("parses every card in the fixture", () => {
    expect(results).toHaveLength(2);
  });

  it("extracts clean fields, stripping tracking params and amount prefixes", () => {
    const avoca = results.find((c) => c.name === "Avoca");
    expect(avoca).toMatchObject({
      domain: "avoca.ai",
      url: "https://www.avoca.ai/",
      stage: "Seed",
      sizeBand: "11-50 employees",
      location: "New York, New York, USA",
      industry: "Artificial Intelligence",
      description: "Building the AI Workforce for Service Businesses",
      lastFundingDate: "2023",
      investors: ["Y Combinator"],
      source: "topstartups.io",
      status: "new",
    });
  });

  it("strips a leading raise-amount prefix from the funding round", () => {
    // fixture's second card has funding tag "$30M Seed in 2024" — the
    // round must come out as "Seed", not "$30M Seed"
    const slingshot = results.find((c) => c.name === "Slingshot AI");
    expect(slingshot?.stage).toBe("Seed");
    expect(slingshot?.lastFundingDate).toBe("2024");
    expect(slingshot?.investors).toEqual(["Andreessen Horowitz"]);
  });

  it("preserves the raw parsed tags in rawJson for debugging", () => {
    const avoca = results.find((c) => c.name === "Avoca");
    expect(avoca?.rawJson).toMatchObject({
      fundingTags: ["Y Combinator", "Seed in 2023"],
    });
  });
});

describe("buildFilterSlices", () => {
  it("expands a metro location into its constituent cities", () => {
    const slices = buildFilterSlices({
      sizeBands: ["11-50 employees"],
      fundingRounds: ["Seed"],
      locations: ["NYC"],
      industries: ["Artificial Intelligence"],
    });
    expect(slices).toEqual([
      {
        sizeBand: "11-50 employees",
        fundingRound: "Seed",
        location: "New York",
        industry: "Artificial Intelligence",
      },
    ]);
  });

  it("passes through an unmapped location literally", () => {
    const slices = buildFilterSlices({
      sizeBands: ["11-50 employees"],
      fundingRounds: ["Seed"],
      locations: ["Austin"],
      industries: ["FinTech"],
    });
    expect(slices[0].location).toBe("Austin");
  });

  it("takes the cartesian product across all four axes", () => {
    const slices = buildFilterSlices({
      sizeBands: ["11-50 employees", "51-100 employees"],
      fundingRounds: ["Seed", "Series A"],
      locations: ["Toronto"],
      industries: ["FinTech"],
    });
    expect(slices).toHaveLength(4);
  });
});

describe("passesFundingRecency", () => {
  const now = new Date("2026-08-25");

  it("rejects a null funding year", () => {
    expect(passesFundingRecency(null, now)).toBe(false);
  });

  it("accepts funding within the last 2 years", () => {
    expect(passesFundingRecency("2025", now)).toBe(true);
    expect(passesFundingRecency("2024", now)).toBe(true);
  });

  it("rejects funding older than 2 years", () => {
    expect(passesFundingRecency("2023", now)).toBe(false);
    expect(passesFundingRecency("2020", now)).toBe(false);
  });
});
