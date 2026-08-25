// Swappable enrichment source — spec §11 / §0.3.
//
// Apollo is the default implementation, but §0.3/§14 flags an open question:
// whether API enrichment draws from the *email credit* pool (10,000/mo free)
// or the *export credit* pool (120/YEAR free). That must be verified in the
// Apollo billing page before `enrich` is actually CALLED in the pipeline —
// if it's export credits, the fallback is pattern inference
// (firstname@domain) confirmed against one known-good address per domain,
// which is why this sits behind an interface instead of being called directly
// from the pipeline stages. `search` has no such blocker (0 credits always)
// and is implemented for real.
//
// Field shapes verified directly against Apollo's published API schema
// (2026-08-25), not assumed: the free /mixed_people/api_search endpoint
// returns far less than a first read of the spec implies — no seniority,
// department, linkedin, or tenure, and only an OBFUSCATED last name. Those
// only come back from /people/match (enrichment, costs credits). rank.ts's
// scoring formula was adjusted accordingly (title-text-only, see that file).

export interface ContactSearchResult {
  apolloId: string;
  first: string;
  // e.g. "Sm**h" — Apollo redacts this in search results. Not usable for
  // outreach; a real last name only comes from enrich().
  lastObfuscated: string | null;
  title: string;
  organizationName: string | null;
}

export interface ContactEnrichmentResult {
  first: string | null;
  last: string | null;
  title: string | null;
  seniority: string | null;
  department: string | null;
  linkedin: string | null;
  tenureMonths: number | null;
  email: string | null;
  emailStatus: "valid" | "risky" | "invalid" | "unknown";
  emailSource: string;
}

export interface ContactProvider {
  readonly name: string;

  // People Search equivalent — must stay free/0-cost per company (spec §0.3).
  search(companyDomain: string, titles: string[]): Promise<ContactSearchResult[]>;

  // Enrichment equivalent — costs credits. Only call for ranked/selected
  // contacts (stage [6] must run before this, never before).
  enrich(apolloId: string): Promise<ContactEnrichmentResult>;
}
