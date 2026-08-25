// v0.1 entrypoint — spec §12: scraper -> DB -> evidence crawl -> contact
// search + rank -> export CSV. Run with `npm run pipeline`.
//
// Chains: scrapeCompanies -> crawlEvidence (per company) -> fetchContacts
// (per company, via HunterContactProvider) -> rankContacts (per company)
// -> persist to SQLite -> exportSelectedContactsCsv. Every stage it would
// call is implemented (see ../pipeline/*.ts) — this orchestrator itself
// is still a stub. Wiring it up needs a real run's config (industries,
// filter slices) and DB persistence glue, not just calling the stages.

async function main() {
  throw new Error(
    "not implemented — wire scrapeCompanies -> crawlEvidence -> fetchContacts -> rankContacts -> db writes -> exportSelectedContactsCsv (spec §12 v0.1)",
  );
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
