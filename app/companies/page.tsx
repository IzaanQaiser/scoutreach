// v0.1 UI target — spec §12: "no UI beyond a sortable table."
// Wire this up to `db.select().from(companies)` (../../lib/db/client.ts,
// ../../lib/db/schema.ts) once the scrape/evidence/contact/rank pipeline
// stages are implemented and there's data to show.

export default function CompaniesPage() {
  return (
    <main className="page">
      <section className="panel">
        <h1>Companies</h1>
        <p>No data yet — run the pipeline once stages [1]-[6] are implemented.</p>
      </section>
    </main>
  );
}
