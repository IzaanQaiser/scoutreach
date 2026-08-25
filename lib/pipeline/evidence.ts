// Stage [2] — spec §9 / §9.1.
//
// For each company, fetch /blog, /changelog, /docs, /careers, /engineering,
// the GitHub org, and recent news. This table is the campaign's spine: no
// evidence, no draft (§0.4, §9.1). Target 3-8 rows per company.
//
// Store URL + title + exact snippet + retrieved_at per row — a paraphrase
// is not acceptable here, the whole evidence-gate design depends on being
// able to point at the literal source text later.

import type { InferInsertModel } from "drizzle-orm";

import type { companyEvidence } from "../db/schema";

export type EvidenceRow = InferInsertModel<typeof companyEvidence>;

export async function crawlEvidence(companyId: string, url: string): Promise<EvidenceRow[]> {
  throw new Error(`not implemented — see spec §9.1 stage [2] (company ${companyId}, ${url})`);
}
