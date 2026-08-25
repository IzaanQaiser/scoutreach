"use client";

// v0.1 UI — spec §12: "no UI beyond a sortable table." Client component
// so column-header clicks can sort in place; data fetching stays in the
// server component (page.tsx) that renders this.

import { useMemo, useState } from "react";

export interface CompanyRow {
  id: string;
  name: string;
  domain: string | null;
  tier: string | null;
  headcount: number | null;
  status: string;
}

type SortKey = "name" | "domain" | "tier" | "headcount" | "status";
type SortDirection = "asc" | "desc";

const COLUMNS: { key: SortKey; label: string }[] = [
  { key: "name", label: "Company" },
  { key: "domain", label: "Domain" },
  { key: "tier", label: "Tier" },
  { key: "headcount", label: "Headcount" },
  { key: "status", label: "Status" },
];

function compare(a: CompanyRow, b: CompanyRow, key: SortKey): number {
  const av = a[key];
  const bv = b[key];
  if (av === null && bv === null) return 0;
  if (av === null) return 1;
  if (bv === null) return -1;
  if (typeof av === "number" && typeof bv === "number") return av - bv;
  return String(av).localeCompare(String(bv));
}

export function CompaniesTable({ companies }: { companies: CompanyRow[] }) {
  const [sortKey, setSortKey] = useState<SortKey>("name");
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");

  const sorted = useMemo(() => {
    const rows = [...companies].sort((a, b) => compare(a, b, sortKey));
    return sortDirection === "asc" ? rows : rows.reverse();
  }, [companies, sortKey, sortDirection]);

  function handleSort(key: SortKey) {
    if (key === sortKey) {
      setSortDirection((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDirection("asc");
    }
  }

  if (companies.length === 0) {
    return <p>No companies yet — run the pipeline once stages [1]-[6] are implemented.</p>;
  }

  return (
    <table>
      <thead>
        <tr>
          {COLUMNS.map(({ key, label }) => (
            <th key={key}>
              <button type="button" onClick={() => handleSort(key)}>
                {label}
                {sortKey === key ? (sortDirection === "asc" ? " ▲" : " ▼") : ""}
              </button>
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {sorted.map((company) => (
          <tr key={company.id}>
            <td>{company.name}</td>
            <td>{company.domain ?? ""}</td>
            <td>{company.tier ?? ""}</td>
            <td>{company.headcount ?? ""}</td>
            <td>{company.status}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
