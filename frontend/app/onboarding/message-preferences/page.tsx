"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useOnboardingGuard } from "../../../components/onboarding-guard";
import { getSettings, patchSettings } from "../../../lib/api";

export default function OnboardingMessagePreferencesPage() {
  const router = useRouter();
  const { token, isReady } = useOnboardingGuard("message_preferences");

  const [tone, setTone] = useState("casual");
  const [length, setLength] = useState("short");
  const [personalizationLevel, setPersonalizationLevel] = useState("high");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadSettings() {
      if (!isReady) {
        return;
      }

      try {
        const settings = await getSettings(token);
        if (cancelled) {
          return;
        }

        const prefs = (settings.message_preferences ?? {}) as Record<string, unknown>;
        const toneValue = prefs["tone"];
        const lengthValue = prefs["length"];
        const personalizationValue = prefs["personalization_level"];

        if (typeof toneValue === "string") {
          setTone(toneValue);
        }
        if (typeof lengthValue === "string") {
          setLength(lengthValue);
        }
        if (typeof personalizationValue === "string") {
          setPersonalizationLevel(personalizationValue);
        }
      } catch {
        if (!cancelled) {
          setError("Failed to load message preferences.");
        }
      }
    }

    void loadSettings();

    return () => {
      cancelled = true;
    };
  }, [isReady, token]);

  async function onNext(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);

    try {
      await patchSettings(token, {
        message_preferences: {
          tone,
          length,
          personalization_level: personalizationLevel,
        },
      });
      router.push("/onboarding/calibration");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Failed to save message preferences.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="page">
      <section className="panel">
        <h1>Message preferences</h1>
        <p>Set your baseline style before calibration.</p>

        <form onSubmit={onNext} className="stacked-form">
          <label>
            Tone
            <input value={tone} onChange={(event) => setTone(event.target.value)} required />
          </label>

          <label>
            Length
            <input value={length} onChange={(event) => setLength(event.target.value)} required />
          </label>

          <label>
            Personalization level
            <input
              value={personalizationLevel}
              onChange={(event) => setPersonalizationLevel(event.target.value)}
              required
            />
          </label>

          <div className="actions">
            <button type="button" className="secondary" onClick={() => router.push("/onboarding/targets")} disabled={busy}>
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
