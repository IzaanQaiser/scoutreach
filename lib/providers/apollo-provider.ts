// Apollo implementation of ContactProvider (spec §0.3, §9.1 stage [5]/[7]).
//
// Endpoints, auth, and field shapes below were verified against Apollo's
// published API docs (2026-08-25), not assumed:
// - search: POST https://api.apollo.io/api/v1/mixed_people/api_search
//   (0 credits, but only returns id/first_name/last_name_obfuscated/title/
//   organization.name — no seniority/department/linkedin/tenure)
// - enrich: POST https://api.apollo.io/api/v1/people/match
//   (costs credits with reveal_personal_emails=true; returns the full
//   profile including real last name, seniority, departments,
//   linkedin_url, and employment_history)
// - auth: x-api-key header
//
// Requires APOLLO_API_KEY in the environment. Both calls go through
// cachedJsonCall so a rerun never re-spends credits on the same request.

import { cachedJsonCall } from "../pipeline/http-cache";
import type {
  ContactEnrichmentResult,
  ContactProvider,
  ContactSearchResult,
} from "./contact-provider";

const SEARCH_URL = "https://api.apollo.io/api/v1/mixed_people/api_search";
const MATCH_URL = "https://api.apollo.io/api/v1/people/match";
const PAGE_SIZE = 25;

interface ApolloSearchPerson {
  id: string;
  first_name: string | null;
  last_name_obfuscated: string | null;
  title: string | null;
  organization: { name: string | null } | null;
}

interface ApolloSearchResponse {
  people: ApolloSearchPerson[];
  total_entries: number;
}

interface ApolloEmploymentHistoryEntry {
  current: boolean;
  start_date: string | null;
}

interface ApolloMatchResponse {
  person: {
    first_name: string | null;
    last_name: string | null;
    title: string | null;
    seniority: string | null;
    departments: string[] | null;
    linkedin_url: string | null;
    email: string | null;
    email_status: string | null;
    employment_history: ApolloEmploymentHistoryEntry[] | null;
  } | null;
}

function monthsSince(dateStr: string): number {
  const start = new Date(dateStr);
  const now = new Date();
  return (
    (now.getFullYear() - start.getFullYear()) * 12 + (now.getMonth() - start.getMonth())
  );
}

function currentTenureMonths(
  history: ApolloEmploymentHistoryEntry[] | null,
): number | null {
  const current = history?.find((entry) => entry.current && entry.start_date);
  return current?.start_date ? monthsSince(current.start_date) : null;
}

function mapEmailStatus(status: string | null): ContactEnrichmentResult["emailStatus"] {
  if (status === "verified") return "valid";
  if (status === "guessed" || status === "unavailable") return "risky";
  if (status === "invalid") return "invalid";
  return "unknown";
}

export interface ApolloProviderOptions {
  apiKey?: string;
  cacheDir?: string;
  minIntervalMs?: number;
}

export class ApolloContactProvider implements ContactProvider {
  readonly name = "apollo";

  private readonly apiKey: string;
  private readonly cacheDir?: string;
  private readonly minIntervalMs: number;

  constructor(options: ApolloProviderOptions = {}) {
    const apiKey = options.apiKey ?? process.env.APOLLO_API_KEY;
    if (!apiKey) {
      throw new Error("APOLLO_API_KEY is required to use ApolloContactProvider");
    }
    this.apiKey = apiKey;
    this.cacheDir = options.cacheDir;
    this.minIntervalMs = options.minIntervalMs ?? 150; // free-tier cap: 50/min
  }

  private headers(): Record<string, string> {
    return {
      "Content-Type": "application/json",
      "Cache-Control": "no-cache",
      accept: "application/json",
      "x-api-key": this.apiKey,
    };
  }

  async search(companyDomain: string, titles: string[]): Promise<ContactSearchResult[]> {
    const body = {
      q_organization_domains_list: [companyDomain],
      person_titles: titles,
      per_page: PAGE_SIZE,
      page: 1,
    };
    const cacheKey = JSON.stringify(body);

    const response = await cachedJsonCall<ApolloSearchResponse>(
      cacheKey,
      { namespace: "apollo-search", minIntervalMs: this.minIntervalMs, cacheDir: this.cacheDir },
      async () => {
        const res = await fetch(SEARCH_URL, {
          method: "POST",
          headers: this.headers(),
          body: JSON.stringify(body),
        });
        if (!res.ok) {
          throw new Error(`Apollo search failed: ${res.status} ${res.statusText}`);
        }
        return (await res.json()) as ApolloSearchResponse;
      },
    );

    return response.people.map((person) => ({
      apolloId: person.id,
      first: person.first_name ?? "",
      lastObfuscated: person.last_name_obfuscated,
      title: person.title ?? "",
      organizationName: person.organization?.name ?? null,
    }));
  }

  async enrich(apolloId: string): Promise<ContactEnrichmentResult> {
    const params = new URLSearchParams({
      id: apolloId,
      reveal_personal_emails: "true",
    });
    const url = `${MATCH_URL}?${params.toString()}`;

    const response = await cachedJsonCall<ApolloMatchResponse>(
      url,
      { namespace: "apollo-enrich", minIntervalMs: this.minIntervalMs, cacheDir: this.cacheDir },
      async () => {
        const res = await fetch(url, {
          method: "POST",
          headers: this.headers(),
        });
        if (!res.ok) {
          throw new Error(`Apollo enrich failed: ${res.status} ${res.statusText}`);
        }
        return (await res.json()) as ApolloMatchResponse;
      },
    );

    const person = response.person;
    return {
      first: person?.first_name ?? null,
      last: person?.last_name ?? null,
      title: person?.title ?? null,
      seniority: person?.seniority ?? null,
      department: person?.departments?.[0] ?? null,
      linkedin: person?.linkedin_url ?? null,
      tenureMonths: currentTenureMonths(person?.employment_history ?? null),
      email: person?.email ?? null,
      emailStatus: mapEmailStatus(person?.email_status ?? null),
      emailSource: "apollo",
    };
  }
}
