// Swappable enrichment source — spec §11 / §0.3.
//
// Apollo is the default implementation, but §0.3/§14 flags an open question:
// whether API enrichment draws from the *email credit* pool (10,000/mo free)
// or the *export credit* pool (120/YEAR free). That must be verified in the
// Apollo billing page before `search`/`enrich` are implemented for real —
// if it's export credits, the fallback is pattern inference
// (firstname@domain) confirmed against one known-good address per domain,
// which is why this sits behind an interface instead of being called directly
// from the pipeline stages.

export interface ContactSearchResult {
  apolloId: string;
  first: string;
  last: string;
  title: string;
  seniority: string | null;
  department: string | null;
  linkedin: string | null;
  tenureMonths: number | null;
}

export interface ContactEnrichmentResult {
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
