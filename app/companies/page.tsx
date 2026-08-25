import { db } from "../../lib/db/client";
import { companies } from "../../lib/db/schema";
import { CompaniesTable } from "./companies-table";

// This is a local-only tool reading a live SQLite file that may not
// exist yet at build time (before migrations run) — never prerender it.
export const dynamic = "force-dynamic";

export default async function CompaniesPage() {
  const rows = await db
    .select({
      id: companies.id,
      name: companies.name,
      domain: companies.domain,
      tier: companies.tier,
      headcount: companies.headcount,
      status: companies.status,
    })
    .from(companies);

  return (
    <main className="page">
      <section className="panel">
        <h1>Companies</h1>
        <CompaniesTable companies={rows} />
      </section>
    </main>
  );
}
