"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useOnboardingGuard } from "../../../components/onboarding-guard";
import { getMe, patchMe } from "../../../lib/api";

export default function OnboardingNamePage() {
  const router = useRouter();
  const { token, isReady } = useOnboardingGuard("name");

  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadExisting() {
      if (!isReady) {
        return;
      }

      try {
        const me = await getMe(token);
        if (cancelled) {
          return;
        }
        setFirstName((me.user.first_name ?? "") as string);
        setLastName((me.user.last_name ?? "") as string);
      } catch {
        if (!cancelled) {
          setError("Failed to load current profile info.");
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

    try {
      await patchMe(token, {
        first_name: firstName.trim(),
        last_name: lastName.trim(),
      });
      router.push("/onboarding/profile-sources");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Failed to save your name.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="page">
      <section className="panel">
        <h1>Tell us your name</h1>
        <p>We’ll use this to personalize your outreach flow.</p>

        <form onSubmit={onNext} className="stacked-form">
          <label>
            First name
            <input value={firstName} onChange={(event) => setFirstName(event.target.value)} required />
          </label>

          <label>
            Last name
            <input value={lastName} onChange={(event) => setLastName(event.target.value)} required />
          </label>

          <div className="actions">
            <button type="button" className="secondary" onClick={() => router.push("/auth")} disabled={busy}>
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
