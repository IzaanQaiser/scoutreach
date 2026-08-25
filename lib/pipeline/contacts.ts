// Stage [5] — spec §9 / §9.1.
//
// Apollo People Search only (`ContactProvider.search`, see ../providers/contact-provider.ts).
// 0 credits — safe to pull 10-25 per company without worrying about quota.
// Do NOT call enrichment here; that's stage [7], after ranking (§0.3, §6).
//
// Filter person_titles on engineering + leadership + talent per spec §9.1.
// Free-tier limits (600/day) are not a constraint at this volume (~115 companies).

import type { InferInsertModel } from "drizzle-orm";

import type { contacts } from "../db/schema";
import type { ContactProvider } from "../providers/contact-provider";

export type ContactRow = InferInsertModel<typeof contacts>;

export async function fetchContacts(
  provider: ContactProvider,
  companyId: string,
  companyDomain: string,
): Promise<ContactRow[]> {
  throw new Error(
    `not implemented — see spec §9.1 stage [5] (company ${companyId}, ${companyDomain}, provider ${provider.name})`,
  );
}
