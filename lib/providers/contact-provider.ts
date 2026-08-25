// Swappable contact-data source — spec §11 / §0.3.
//
// Apollo was the original default per the spec, but its free plan
// doesn't include API access at all (confirmed directly in-account,
// 2026-08-25) — Basic/Free are UI-only, raw API access needs a paid
// plan. Hunter.io is the real default now: free plan includes genuine
// API access (no card required), and its Domain Search endpoint
// (verified against Hunter's own V2 docs) returns name/title/seniority/
// department/linkedin/email/confidence all in ONE call — richer than
// Apollo's free tier would have given even with a paid enrichment step.
//
// Kept behind this interface anyway (not just a HunterContactProvider
// used directly) so a different/better source can be swapped in later
// without touching the pipeline stages that consume it.

export interface ContactSearchResult {
  // Not every provider has a stable person ID (Hunter doesn't) — null
  // when there isn't one; email is the durable cross-provider key.
  providerId: string | null;
  first: string | null;
  last: string | null;
  title: string | null;
  seniority: string | null;
  department: string | null;
  linkedin: string | null;
  // Populated at search time by providers that give it upfront (Hunter);
  // left null for providers where it needs a separate paid step.
  email: string | null;
  // 0-100, the provider's own estimate. Null if unknown/unavailable.
  emailConfidence: number | null;
  organizationName: string | null;
}

export interface EmailVerificationResult {
  email: string;
  status: "valid" | "risky" | "invalid" | "unknown";
  score: number | null;
}

export interface ContactProvider {
  readonly name: string;

  // Stage [5] — must stay free/0-cost.
  search(companyDomain: string, titles: string[]): Promise<ContactSearchResult[]>;

  // Stage [7] "email + verify" — only call for ranked/selected contacts
  // (stage [6] must run first, never before).
  verifyEmail(email: string): Promise<EmailVerificationResult>;
}
