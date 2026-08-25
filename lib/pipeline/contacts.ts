// Stage [5] — spec §9 / §9.1.
//
// Apollo People Search only (`ContactProvider.search`, see
// ../providers/contact-provider.ts and ../providers/apollo-provider.ts).
// 0 credits — safe to pull the full title-target set per company without
// worrying about quota. Do NOT call enrichment here; that's stage [7],
// after ranking (§0.3, §6) — search only returns an obfuscated last name
// and no seniority/department/linkedin/tenure (verified against Apollo's
// API schema; see contact-provider.ts), so persisted rows start with
// those fields null and get filled in only for the ranked/selected
// contacts, later.
//
// Filter person_titles on engineering + leadership + talent per spec
// §9.1. Free-tier limits (600/day) are not a constraint at this volume
// (~115 companies).

import type { InferInsertModel } from "drizzle-orm";

import type { contacts } from "../db/schema";
import type { ContactProvider } from "../providers/contact-provider";

export type ContactRow = InferInsertModel<typeof contacts>;

// Engineering + leadership + talent, per spec §9.1. Kept here (not in the
// provider) since it's a pipeline-stage decision, not an Apollo detail.
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

export async function fetchContacts(
  provider: ContactProvider,
  companyId: string,
  companyDomain: string,
): Promise<ContactRow[]> {
  const results = await provider.search(companyDomain, TARGET_TITLES);

  return results.map((result) => ({
    id: crypto.randomUUID(),
    companyId,
    apolloId: result.apolloId,
    first: result.first || null,
    // last name is obfuscated at search time; real value only exists
    // after enrich() runs on a ranked/selected contact.
    last: null,
    title: result.title || null,
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
  }));
}
