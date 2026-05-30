"use client";

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { useOnboardingGuard } from "../../../components/onboarding-guard";
import {
  completeOnboarding,
  generateOnboardingExamples,
  submitOnboardingFeedback,
} from "../../../lib/api";
import type { OnboardingExample } from "../../../lib/types";

type Decision = "accepted" | "rejected";

export default function OnboardingCalibrationPage() {
  const router = useRouter();
  const { token, isReady, onboardingState } = useOnboardingGuard("calibration");

  const [loopIndex, setLoopIndex] = useState(0);
  const [examples, setExamples] = useState<OnboardingExample[]>([]);
  const [cursor, setCursor] = useState(0);
  const [decisions, setDecisions] = useState<Record<string, Decision>>({});
  const [phase, setPhase] = useState<"loading" | "swipe" | "feedback">("loading");

  const [positionFeedback, setPositionFeedback] = useState("");
  const [subjectFeedback, setSubjectFeedback] = useState("");
  const [bodyFeedback, setBodyFeedback] = useState("");

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const current = examples[cursor] ?? null;

  const rejectedExamples = useMemo(
    () => examples.filter((example) => decisions[example.example_id] === "rejected"),
    [decisions, examples],
  );

  useEffect(() => {
    let cancelled = false;

    async function loadExamples() {
      if (!isReady) {
        return;
      }

      setBusy(true);
      setError(null);

      try {
        const initialLoop = onboardingState?.calibration_loop_count ?? 0;
        const generated = await generateOnboardingExamples(token, initialLoop);
        if (cancelled) {
          return;
        }

        setLoopIndex(generated.loop_index);
        setExamples(generated.examples);
        setCursor(0);
        setDecisions({});
        setPhase("swipe");
      } catch (caught) {
        if (!cancelled) {
          setError(caught instanceof Error ? caught.message : "Failed to generate calibration examples.");
          setPhase("loading");
        }
      } finally {
        if (!cancelled) {
          setBusy(false);
        }
      }
    }

    void loadExamples();

    return () => {
      cancelled = true;
    };
  }, [isReady, onboardingState?.calibration_loop_count, token]);

  function swipe(decision: Decision) {
    if (!current || busy) {
      return;
    }

    setDecisions((previous) => ({
      ...previous,
      [current.example_id]: decision,
    }));

    const nextCursor = cursor + 1;
    if (nextCursor >= examples.length) {
      const updatedDecisions = {
        ...decisions,
        [current.example_id]: decision,
      };
      const rejectedCount = examples.filter((example) => updatedDecisions[example.example_id] === "rejected").length;
      if (rejectedCount === 0) {
        void submitDecisions([]);
        return;
      }
      setPhase("feedback");
      return;
    }

    setCursor(nextCursor);
  }

  async function submitDecisions(
    rejectedPayload: Array<{
      example_id?: string;
      position_industry_feedback?: string;
      subject_feedback?: string;
      body_feedback?: string;
    }>,
  ) {
    setBusy(true);
    setError(null);

    try {
      const response = await submitOnboardingFeedback(token, {
        loop_index: loopIndex,
        rejected_examples: rejectedPayload,
      });

      if ("onboarding_complete" in response && response.onboarding_complete) {
        router.replace("/dashboard");
        return;
      }

      if (!("examples" in response)) {
        throw new Error("Unexpected calibration response payload.");
      }

      setLoopIndex(response.loop_index);
      setExamples(response.examples);
      setCursor(0);
      setDecisions({});
      setPhase("swipe");
      setPositionFeedback("");
      setSubjectFeedback("");
      setBodyFeedback("");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Failed to submit calibration feedback.");
    } finally {
      setBusy(false);
    }
  }

  async function onSubmitFeedback(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const payload = rejectedExamples.map((item) => ({
      example_id: item.example_id,
      position_industry_feedback: positionFeedback.trim(),
      subject_feedback: subjectFeedback.trim(),
      body_feedback: bodyFeedback.trim(),
    }));

    await submitDecisions(payload);
  }

  async function onSkip() {
    setBusy(true);
    setError(null);

    try {
      await completeOnboarding(token, "skipped_calibration");
      router.replace("/dashboard");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Failed to skip calibration.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="page">
      <section className="panel">
        <h1>Calibrate message style</h1>
        <p>Swipe through sample outreach drafts so ScoutReach can learn your preferences.</p>

        {phase === "loading" ? <p>Generating example messages...</p> : null}

        {phase === "swipe" && current ? (
          <article className="panel calibration-card" data-testid="calibration-card">
            <p>
              Example {cursor + 1} / {examples.length}
            </p>
            <h2>{current.subject}</h2>
            <p>
              Founder: <strong>{current.founder_name}</strong> at <strong>{current.company_name}</strong>
            </p>
            <p>
              Context: {current.target_role_context} | {current.industry_context}
            </p>
            <p>{current.message_content}</p>

            <div className="actions">
              <button type="button" className="secondary" onClick={() => swipe("rejected")} disabled={busy}>
                Reject
              </button>
              <button type="button" onClick={() => swipe("accepted")} disabled={busy}>
                Accept
              </button>
            </div>
          </article>
        ) : null}

        {phase === "feedback" ? (
          <form onSubmit={onSubmitFeedback} className="stacked-form panel">
            <h2>Tell us what to change</h2>
            <p>You rejected {rejectedExamples.length} example(s). Add feedback and we’ll regenerate.</p>

            <label>
              Position/industry feedback
              <textarea value={positionFeedback} onChange={(event) => setPositionFeedback(event.target.value)} rows={3} />
            </label>

            <label>
              Subject/header feedback
              <textarea value={subjectFeedback} onChange={(event) => setSubjectFeedback(event.target.value)} rows={3} />
            </label>

            <label>
              Body feedback
              <textarea value={bodyFeedback} onChange={(event) => setBodyFeedback(event.target.value)} rows={3} />
            </label>

            <div className="actions">
              <button type="submit" disabled={busy}>
                {busy ? "Regenerating..." : "Regenerate Examples"}
              </button>
            </div>
          </form>
        ) : null}

        <div className="actions">
          <button type="button" className="secondary" onClick={onSkip} disabled={busy}>
            Skip calibration
          </button>
        </div>

        {error ? <p className="error">{error}</p> : null}
      </section>
    </main>
  );
}
