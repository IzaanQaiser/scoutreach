"use client";

import React from "react";
import { useMemo, useState } from "react";

import { getPendingCount, getRunCompanies, updateCompanyStatus } from "../lib/api";
import type { Company } from "../lib/types";

function companySubtitle(company: Company): string {
  const parts = [company.batch, company.domain].filter(Boolean);
  return parts.join(" | ");
}

export function ReviewDashboard() {
  const [runIdInput, setRunIdInput] = useState("");
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [pendingCount, setPendingCount] = useState<number>(0);
  const [queue, setQueue] = useState<Company[]>([]);
  const [busy, setBusy] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const current = queue[0] ?? null;

  const hasCompletedReview = useMemo(() => {
    return activeRunId !== null && pendingCount === 0 && queue.length === 0;
  }, [activeRunId, pendingCount, queue.length]);

  async function loadReviewQueue() {
    const runId = runIdInput.trim();
    if (!runId) {
      setErrorMessage("Enter a run ID first.");
      return;
    }

    setBusy(true);
    setErrorMessage(null);

    try {
      const [companies, count] = await Promise.all([
        getRunCompanies({ runId, status: "pending_review", limit: 100, offset: 0 }),
        getPendingCount({ runId }),
      ]);

      setActiveRunId(runId);
      setQueue(companies);
      setPendingCount(count);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Failed to load review queue.");
    } finally {
      setBusy(false);
    }
  }

  async function swipe(status: "accepted" | "rejected") {
    if (!current) {
      return;
    }

    setBusy(true);
    setErrorMessage(null);

    try {
      await updateCompanyStatus({ companyId: current.id, status });
      setQueue((previous) => previous.slice(1));
      setPendingCount((previous) => Math.max(0, previous - 1));
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Failed to update company status.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="page">
      <section className="panel">
        <h1>Evaluate Matches</h1>
        <p>Load pending companies for a run, then swipe right (accept) or left (reject).</p>

        <div className="controls">
          <input
            aria-label="Run ID"
            value={runIdInput}
            onChange={(event) => setRunIdInput(event.target.value)}
            placeholder="Run ID"
          />
          <button type="button" onClick={loadReviewQueue} disabled={busy}>
            {busy ? "Loading..." : "Load Queue"}
          </button>
        </div>

        {activeRunId ? (
          <p className="meta">
            Active run: <strong>{activeRunId}</strong> | Pending: <strong>{pendingCount}</strong>
          </p>
        ) : null}

        {errorMessage ? <p className="error">{errorMessage}</p> : null}
      </section>

      <section className="panel review">
        {current ? (
          <article data-testid="company-card">
            <h2>{current.name}</h2>
            <p>{companySubtitle(current) || "No batch/domain"}</p>

            <div className="actions">
              <button type="button" onClick={() => swipe("rejected")} disabled={busy}>
                Reject
              </button>
              <button type="button" onClick={() => swipe("accepted")} disabled={busy}>
                Accept
              </button>
            </div>
          </article>
        ) : (
          <p data-testid="empty-state">No pending companies loaded.</p>
        )}

        {hasCompletedReview ? (
          <p data-testid="generate-ready">Pending count is 0. You can now generate messages.</p>
        ) : null}
      </section>
    </main>
  );
}
