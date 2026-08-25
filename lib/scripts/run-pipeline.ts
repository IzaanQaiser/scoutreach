// v0.1 entrypoint — spec §12: scraper -> DB -> evidence crawl -> Apollo
// search + rank -> export CSV. Run with `npm run pipeline`.
//
// Chains: scrapeCompanies -> crawlEvidence (per company) -> fetchContacts
// (per company) -> rankContacts (per company) -> write companies.csv.
// Not implemented yet — each stage it calls is still a stub (see
// ../pipeline/*.ts). This file exists so the wiring/order is decided now,
// not re-derived later.

async function main() {
  throw new Error(
    "not implemented — wire scrapeCompanies -> crawlEvidence -> fetchContacts -> rankContacts once those stages are built (spec §12 v0.1)",
  );
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
