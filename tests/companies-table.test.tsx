import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { CompaniesTable, type CompanyRow } from "../app/companies/companies-table";

const ROWS: CompanyRow[] = [
  { id: "1", name: "Zephyr AI", domain: "zephyr.ai", tier: "B", headcount: 40, status: "new" },
  { id: "2", name: "Avoca", domain: "avoca.ai", tier: "A", headcount: 25, status: "new" },
  { id: "3", name: "Midway", domain: null, tier: "C", headcount: 150, status: "needs_evidence" },
];

function rowOrder(): string[] {
  return screen.getAllByRole("row").slice(1).map((row) => row.textContent ?? "");
}

describe("CompaniesTable", () => {
  it("renders every company row", () => {
    render(<CompaniesTable companies={ROWS} />);
    expect(screen.getByText("Zephyr AI")).toBeInTheDocument();
    expect(screen.getByText("Avoca")).toBeInTheDocument();
    expect(screen.getByText("Midway")).toBeInTheDocument();
  });

  it("shows an empty-state message instead of a table when there are no companies", () => {
    render(<CompaniesTable companies={[]} />);
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
    expect(screen.getByText(/no companies yet/i)).toBeInTheDocument();
  });

  it("sorts ascending by name by default", () => {
    render(<CompaniesTable companies={ROWS} />);
    const [first, second, third] = rowOrder();
    expect(first).toContain("Avoca");
    expect(second).toContain("Midway");
    expect(third).toContain("Zephyr AI");
  });

  it("toggles sort direction when the same header is clicked twice", () => {
    render(<CompaniesTable companies={ROWS} />);
    const nameHeader = screen.getByRole("button", { name: /company/i });

    fireEvent.click(nameHeader); // name asc -> desc (default was already asc)
    expect(rowOrder()[0]).toContain("Zephyr AI");

    fireEvent.click(nameHeader); // desc -> asc
    expect(rowOrder()[0]).toContain("Avoca");
  });

  it("sorts numerically by headcount, not lexicographically", () => {
    render(<CompaniesTable companies={ROWS} />);
    fireEvent.click(screen.getByRole("button", { name: /headcount/i }));

    const order = rowOrder();
    expect(order[0]).toContain("Avoca"); // 25
    expect(order[1]).toContain("Zephyr AI"); // 40
    expect(order[2]).toContain("Midway"); // 150
  });

  it("sorts null values (e.g. missing domain) to the end without throwing", () => {
    render(<CompaniesTable companies={ROWS} />);
    expect(() => fireEvent.click(screen.getByRole("button", { name: /domain/i }))).not.toThrow();
    expect(rowOrder()[2]).toContain("Midway"); // null domain sorts last
  });
});
