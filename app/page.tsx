import Link from "next/link";

export default function Home() {
  return (
    <main className="page">
      <section className="panel">
        <h1>ScoutReach</h1>
        <p>v0.1 in progress — see docs/scoutreach-new.md.</p>
        <Link className="button-link" href="/companies">
          View companies
        </Link>
      </section>
    </main>
  );
}
