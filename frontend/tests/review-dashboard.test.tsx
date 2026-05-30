import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ReviewDashboard } from "../components/review-dashboard";
import type { Company } from "../lib/types";

const getRunCompanies = vi.fn();
const getPendingCount = vi.fn();
const updateCompanyStatus = vi.fn();

vi.mock("../lib/api", () => ({
  getRunCompanies: (...args: unknown[]) => getRunCompanies(...args),
  getPendingCount: (...args: unknown[]) => getPendingCount(...args),
  updateCompanyStatus: (...args: unknown[]) => updateCompanyStatus(...args),
}));

function makeCompany(overrides: Partial<Company>): Company {
  return {
    id: "company-1",
    run_id: "run-1",
    name: "Example Labs",
    founders: [],
    status: "pending_review",
    ...overrides,
  };
}

describe("ReviewDashboard", () => {
  const token = "test-token";
  const onSignOut = vi.fn();

  beforeEach(() => {
    getRunCompanies.mockReset();
    getPendingCount.mockReset();
    updateCompanyStatus.mockReset();
    onSignOut.mockReset();
  });

  it("loads pending queue and pending count for a run", async () => {
    getRunCompanies.mockResolvedValue([
      makeCompany({ id: "company-1", name: "Alpha Co", domain: "alpha.co", batch: "W25" }),
    ]);
    getPendingCount.mockResolvedValue(1);

    render(<ReviewDashboard token={token} onSignOut={onSignOut} />);

    await userEvent.type(screen.getByLabelText("Run ID"), "run-123");
    await userEvent.click(screen.getByRole("button", { name: "Load Queue" }));

    await waitFor(() => {
      expect(getRunCompanies).toHaveBeenCalledWith(token, {
        runId: "run-123",
        status: "pending_review",
        limit: 100,
        offset: 0,
      });
      expect(getPendingCount).toHaveBeenCalledWith(token, { runId: "run-123" });
    });

    expect(await screen.findByText("Alpha Co")).toBeInTheDocument();
    expect(screen.getByText(/Pending:/)).toHaveTextContent("Pending: 1");
  });

  it("accept swipe calls API and updates local state", async () => {
    getRunCompanies.mockResolvedValue([
      makeCompany({ id: "company-1", name: "Alpha Co", domain: "alpha.co", batch: "W25" }),
    ]);
    getPendingCount.mockResolvedValue(1);
    updateCompanyStatus.mockResolvedValue({
      company_id: "company-1",
      status: "accepted",
      message: "Company status updated successfully",
    });

    render(<ReviewDashboard token={token} onSignOut={onSignOut} />);

    await userEvent.type(screen.getByLabelText("Run ID"), "run-123");
    await userEvent.click(screen.getByRole("button", { name: "Load Queue" }));

    expect(await screen.findByText("Alpha Co")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Accept" }));

    await waitFor(() => {
      expect(updateCompanyStatus).toHaveBeenCalledWith(token, {
        companyId: "company-1",
        status: "accepted",
      });
    });

    expect(screen.getByTestId("empty-state")).toBeInTheDocument();
    expect(screen.getByTestId("generate-ready")).toBeInTheDocument();
    expect(screen.getByText(/Pending:/)).toHaveTextContent("Pending: 0");
  });

  it("reject swipe calls API with rejected status", async () => {
    getRunCompanies.mockResolvedValue([
      makeCompany({ id: "company-2", name: "Beta Co", domain: "beta.co", batch: "S24" }),
    ]);
    getPendingCount.mockResolvedValue(1);
    updateCompanyStatus.mockResolvedValue({
      company_id: "company-2",
      status: "rejected",
      message: "Company status updated successfully",
    });

    render(<ReviewDashboard token={token} onSignOut={onSignOut} />);

    await userEvent.type(screen.getByLabelText("Run ID"), "run-555");
    await userEvent.click(screen.getByRole("button", { name: "Load Queue" }));

    expect(await screen.findByText("Beta Co")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Reject" }));

    await waitFor(() => {
      expect(updateCompanyStatus).toHaveBeenCalledWith(token, {
        companyId: "company-2",
        status: "rejected",
      });
    });

    expect(screen.getByTestId("generate-ready")).toBeInTheDocument();
  });
});
