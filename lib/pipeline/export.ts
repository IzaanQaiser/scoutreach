// v0.1 output — spec §12: "export CSV. No UI beyond a sortable table."
// One row per SELECTED contact (stage [6] output), joined with its
// company. Most contact fields (last name, email) are null at this
// stage — they only get filled in once enrichment (stage [7]) runs on
// the selected set, which is a separate, credit-costing step.

import type { companies, contacts } from "../db/schema";

type Company = typeof companies.$inferSelect;
type Contact = typeof contacts.$inferSelect;

const CSV_HEADERS = [
  "company_name",
  "company_domain",
  "company_tier",
  "company_headcount",
  "contact_first",
  "contact_last",
  "contact_title",
  "contact_email",
  "contact_email_status",
  "contact_rank_score",
];

function csvEscape(value: string | number | null | undefined): string {
  if (value === null || value === undefined) return "";
  const str = String(value);
  if (/[",\n]/.test(str)) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return str;
}

export function exportSelectedContactsCsv(
  companiesById: Map<string, Company>,
  allContacts: Contact[],
): string {
  const selectedRows = allContacts
    .filter((c) => c.selected)
    .map((contact) => {
      const company = companiesById.get(contact.companyId);
      return [
        company?.name,
        company?.domain,
        company?.tier,
        company?.headcount,
        contact.first,
        contact.last,
        contact.title,
        contact.email,
        contact.emailStatus,
        contact.rankScore,
      ]
        .map(csvEscape)
        .join(",");
    });

  return [CSV_HEADERS.join(","), ...selectedRows].join("\n");
}
