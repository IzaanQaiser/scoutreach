// Stage [5] — spec §9 / §9.1.
//
// ContactProvider.search (see ../providers/contact-provider.ts and
// ../providers/hunter-provider.ts) — must stay free/0-cost. Hunter's
// domain-search returns the full profile (name/title/seniority/
// department/linkedin/email/confidence) in this one call, so unlike the
// Apollo-shaped design this used to have, most fields are populated
// immediately rather than deferred to a separate enrichment step.
// verifyEmail (stage [7]) still only runs on the ranked/selected set —
// its job now is confirming deliverability, not fetching the profile.
//
// Filter person_titles on engineering + leadership + talent per spec
// §9.1. Free-tier limits (Hunter: 50 credits/month, shared across
// search+verify) are the real constraint at ~115 companies — pace
// accordingly, this isn't a "run once" free-for-all like Apollo's
// (unusable) free search would have been.

import type { InferInsertModel } from "drizzle-orm";

import type { contacts } from "../db/schema";
import type { ContactProvider } from "../providers/contact-provider";

export type ContactRow = InferInsertModel<typeof contacts>;

// Engineering + leadership + talent, per spec §9.1. Kept here (not in a
// provider) since it's a pipeline-stage decision, not a provider detail.
export const TARGET_TITLES = [
  "Chief Technology Officer",
  "Co-Founder",
  "VP of Engineering",
  "Head of Engineering",
  "Director of Engineering",
  "Engineering Manager",
  "Staff Engineer",
  "Principal Engineer",
  "Senior Engineer",
  "Technical Recruiter",
  "Head of Talent",
];

// Provider-reported confidence -> our emailStatus vocabulary, only used
// when a provider gives an email at search time (Hunter) rather than
// waiting for a separate verify step.
function statusFromConfidence(confidence: number | null): ContactRow["emailStatus"] {
  if (confidence === null) return "not_fetched";
  if (confidence >= 80) return "valid";
  if (confidence >= 50) return "risky";
  return "invalid";
}

export async function fetchContacts(
  provider: ContactProvider,
  companyId: string,
  companyDomain: string,
): Promise<ContactRow[]> {
  const results = await provider.search(companyDomain, TARGET_TITLES);

  return results.map((result) => ({
    id: crypto.randomUUID(),
    companyId,
    providerId: result.providerId,
    first: result.first,
    last: result.last,
    title: result.title,
    seniority: result.seniority,
    department: result.department,
    linkedin: result.linkedin,
    tenureMonths: null, // no provider in scope supplies this; dropped from rank.ts too
    email: result.email,
    emailStatus: result.email ? statusFromConfidence(result.emailConfidence) : "not_fetched",
    emailSource: result.email ? provider.name : null,
    rankScore: null,
    selected: false,
    skipReason: null,
    createdAt: new Date().toISOString(),
  }));
}
