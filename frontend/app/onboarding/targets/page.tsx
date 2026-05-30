"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useOnboardingGuard } from "../../../components/onboarding-guard";
import { getCandidateProfile, putCandidateProfile } from "../../../lib/api";

function splitCsv(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

export default function OnboardingTargetsPage() {
  const router = useRouter();
  const { token, isReady } = useOnboardingGuard("targets");

  const [targetRoles, setTargetRoles] = useState("");
  const [industries, setIndustries] = useState("");
  const [locations, setLocations] = useState("");
  const [workType, setWorkType] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadExisting() {
      if (!isReady) {
        return;
      }

      try {
        const profile = await getCandidateProfile(token);
        if (cancelled) {
          return;
        }

        const roleList = Array.isArray(profile.target_roles) ? profile.target_roles : [];
        setTargetRoles(roleList.join(", "));

        const preferences = (profile.job_preferences ?? {}) as Record<string, unknown>;
        const industriesValue = preferences["industries"];
        const locationsValue = preferences["locations"];
        const workTypeValue = preferences["work_type"];

        const industryList = Array.isArray(industriesValue)
          ? (industriesValue as string[])
          : [];
        const locationList = Array.isArray(locationsValue)
          ? (locationsValue as string[])
          : [];

        setIndustries(industryList.join(", "));
        setLocations(locationList.join(", "));
        setWorkType(typeof workTypeValue === "string" ? workTypeValue : "");
      } catch {
        if (!cancelled) {
          setError("Failed to load target role preferences.");
        }
      }
    }

    void loadExisting();

    return () => {
      cancelled = true;
    };
  }, [isReady, token]);

  async function onNext(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);

    const normalizedRoles = splitCsv(targetRoles);
    const normalizedIndustries = splitCsv(industries);
    const normalizedLocations = splitCsv(locations);

    if (normalizedRoles.length === 0 || normalizedIndustries.length === 0) {
      setError("Add at least one target role and one industry.");
      setBusy(false);
      return;
    }

    try {
      await putCandidateProfile(token, {
        target_roles: normalizedRoles,
        job_preferences: {
          industries: normalizedIndustries,
          locations: normalizedLocations,
          work_type: workType.trim() || null,
        },
      });
      router.push("/onboarding/message-preferences");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Failed to save target preferences.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="page">
      <section className="panel">
        <h1>Target roles and industries</h1>
        <p>Tell ScoutReach what opportunities you want to focus on.</p>

        <form onSubmit={onNext} className="stacked-form">
          <label>
            Target roles (comma-separated)
            <input value={targetRoles} onChange={(event) => setTargetRoles(event.target.value)} required />
          </label>

          <label>
            Industries (comma-separated)
            <input value={industries} onChange={(event) => setIndustries(event.target.value)} required />
          </label>

          <label>
            Preferred locations (comma-separated)
            <input value={locations} onChange={(event) => setLocations(event.target.value)} />
          </label>

          <label>
            Work type
            <input value={workType} onChange={(event) => setWorkType(event.target.value)} placeholder="internship / full-time / contract" />
          </label>

          <div className="actions">
            <button
              type="button"
              className="secondary"
              onClick={() => router.push("/onboarding/profile-sources")}
              disabled={busy}
            >
              Back
            </button>
            <button type="submit" disabled={busy}>
              {busy ? "Saving..." : "Next"}
            </button>
          </div>
        </form>

        {error ? <p className="error">{error}</p> : null}
      </section>
    </main>
  );
}
