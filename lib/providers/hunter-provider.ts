// Hunter.io implementation of ContactProvider (spec §0.3 fallback,
// §9.1 stage [5]/[7]).
//
// Endpoints, auth, and field shapes verified against Hunter's own V2 API
// docs (2026-08-25), not assumed — a first fetch accidentally landed on
// stale V1 docs that claimed no name/title/department fields exist;
// re-checked against the actual V2 reference before writing this:
// - search: GET https://api.hunter.io/v2/domain-search
//   Free plan, real API access included (no card, no paid-plan gate —
//   unlike Apollo). Supports department/seniority filters natively and
//   returns first_name/last_name/position/seniority/department/linkedin/
//   email/confidence all in one call — no separate enrichment step.
// - verify: GET https://api.hunter.io/v2/email-verifier
//   Only call for ranked/selected contacts (stage [6] first, always).
// - auth: api_key query param (also accepts header/bearer; query param
//   is simplest and matches Hunter's own documented examples)
//
// Requires HUNTER_API_KEY in the environment. Both calls go through
// cachedJsonCall so a rerun never repeats a call against the monthly
// credit cap (free plan: 50 credits/month, shared across searches and
// verifications).

import { cachedJsonCall } from "../pipeline/http-cache";
import type {
  ContactProvider,
  ContactSearchResult,
  EmailVerificationResult,
} from "./contact-provider";

const SEARCH_URL = "https://api.hunter.io/v2/domain-search";
const VERIFY_URL = "https://api.hunter.io/v2/email-verifier";

interface HunterDomainSearchEmail {
  value: string;
  confidence: number;
  first_name: string | null;
  last_name: string | null;
  position: string | null;
  seniority: string | null;
  department: string | null;
  linkedin: string | null;
}

interface HunterDomainSearchResponse {
  data: {
    organization: string | null;
    emails: HunterDomainSearchEmail[];
  };
}

interface HunterVerifyResponse {
  data: {
    email: string;
    status: string;
    score: number | null;
  };
}

// Hunter's "status" values (spec verified) map onto our shared
// valid/risky/invalid/unknown vocabulary.
function mapStatus(status: string): EmailVerificationResult["status"] {
  if (status === "valid") return "valid";
  if (status === "accept_all" || status === "webmail") return "risky";
  if (status === "invalid" || status === "disposable") return "invalid";
  return "unknown"; // includes Hunter's own "unknown" plus anything unrecognized
}

export interface HunterProviderOptions {
  apiKey?: string;
  cacheDir?: string;
  minIntervalMs?: number;
}

export class HunterContactProvider implements ContactProvider {
  readonly name = "hunter";

  private readonly apiKey: string;
  private readonly cacheDir?: string;
  private readonly minIntervalMs: number;

  constructor(options: HunterProviderOptions = {}) {
    const apiKey = options.apiKey ?? process.env.HUNTER_API_KEY;
    if (!apiKey) {
      throw new Error("HUNTER_API_KEY is required to use HunterContactProvider");
    }
    this.apiKey = apiKey;
    this.cacheDir = options.cacheDir;
    // Free plan: 15 req/sec, 500 req/min for search — well above what a
    // one-time ~115-company run needs; a small floor is still polite.
    this.minIntervalMs = options.minIntervalMs ?? 200;
  }

  async search(companyDomain: string, titles: string[]): Promise<ContactSearchResult[]> {
    const params = new URLSearchParams({
      domain: companyDomain,
      api_key: this.apiKey,
      limit: "25",
    });
    const url = `${SEARCH_URL}?${params.toString()}`;
    // Cache key must not include the API key (would bust cache on key
    // rotation for no reason, and keeps the key out of cache filenames).
    const cacheKey = `${SEARCH_URL}?domain=${companyDomain}&limit=25`;

    const response = await cachedJsonCall<HunterDomainSearchResponse>(
      cacheKey,
      { namespace: "hunter-search", minIntervalMs: this.minIntervalMs, cacheDir: this.cacheDir },
      async () => {
        const res = await fetch(url);
        if (!res.ok) {
          throw new Error(`Hunter domain search failed: ${res.status} ${res.statusText}`);
        }
        return (await res.json()) as HunterDomainSearchResponse;
      },
    );

    const titleSet = new Set(titles.map((t) => t.toLowerCase()));
    const emails = response.data.emails ?? [];

    // Hunter's domain-search doesn't take a title filter in one shot the
    // way our TARGET_TITLES list is shaped — filter client-side on
    // whichever position strings are present (a page position is a
    // substring match against our target list, not an exact one, since
    // real job titles vary in phrasing).
    const matching = titleSet.size
      ? emails.filter((e) => {
          const position = (e.position ?? "").toLowerCase();
          return position && Array.from(titleSet).some((t) => position.includes(t) || t.includes(position));
        })
      : emails;

    const results = matching.length > 0 ? matching : emails;

    return results.map((e) => ({
      providerId: null,
      first: e.first_name,
      last: e.last_name,
      title: e.position,
      seniority: e.seniority,
      department: e.department,
      linkedin: e.linkedin,
      email: e.value,
      emailConfidence: e.confidence,
      organizationName: response.data.organization,
    }));
  }

  async verifyEmail(email: string): Promise<EmailVerificationResult> {
    const params = new URLSearchParams({ email, api_key: this.apiKey });
    const url = `${VERIFY_URL}?${params.toString()}`;
    const cacheKey = `${VERIFY_URL}?email=${email}`;

    const response = await cachedJsonCall<HunterVerifyResponse>(
      cacheKey,
      { namespace: "hunter-verify", minIntervalMs: this.minIntervalMs, cacheDir: this.cacheDir },
      async () => {
        const res = await fetch(url);
        if (!res.ok) {
          throw new Error(`Hunter email verify failed: ${res.status} ${res.statusText}`);
        }
        return (await res.json()) as HunterVerifyResponse;
      },
    );

    return {
      email: response.data.email,
      status: mapStatus(response.data.status),
      score: response.data.score,
    };
  }
}
