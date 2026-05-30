"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useOnboardingGuard } from "../../../components/onboarding-guard";
import { getCandidateProfile, putCandidateProfile } from "../../../lib/api";

export default function OnboardingProfileSourcesPage() {
  const router = useRouter();
  const { token, isReady } = useOnboardingGuard("profile_sources");

  const [resume, setResume] = useState("");
  const [githubUrl, setGithubUrl] = useState("");
  const [linkedinUrl, setLinkedinUrl] = useState("");
  const [portfolioUrl, setPortfolioUrl] = useState("");
  const [bio, setBio] = useState("");
  const [extraContext, setExtraContext] = useState("");
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

        setResume((profile.resume ?? "") as string);
        setGithubUrl((profile.github_url ?? "") as string);
        setLinkedinUrl((profile.linkedin_url ?? "") as string);
        setPortfolioUrl((profile.portfolio_url ?? "") as string);
        setBio((profile.bio ?? "") as string);
        setExtraContext((profile.extra_context ?? "") as string);
      } catch {
        if (!cancelled) {
          setError("Failed to load candidate profile.");
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
      await putCandidateProfile(token, {
        resume: resume.trim() || undefined,
        github_url: githubUrl.trim() || undefined,
        linkedin_url: linkedinUrl.trim() || undefined,
        portfolio_url: portfolioUrl.trim() || undefined,
        bio: bio.trim() || undefined,
        extra_context: extraContext.trim() || undefined,
      });
      router.push("/onboarding/targets");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Failed to save profile sources.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="page">
      <section className="panel">
        <h1>Add your profile sources</h1>
        <p>Share the context ScoutReach should use for personalization.</p>

        <form onSubmit={onNext} className="stacked-form">
          <label>
            Resume text
            <textarea value={resume} onChange={(event) => setResume(event.target.value)} rows={6} />
          </label>

          <label>
            GitHub URL
            <input value={githubUrl} onChange={(event) => setGithubUrl(event.target.value)} placeholder="https://github.com/you" />
          </label>

          <label>
            LinkedIn URL
            <input
              value={linkedinUrl}
              onChange={(event) => setLinkedinUrl(event.target.value)}
              placeholder="https://linkedin.com/in/you"
            />
          </label>

          <label>
            Portfolio URL
            <input
              value={portfolioUrl}
              onChange={(event) => setPortfolioUrl(event.target.value)}
              placeholder="https://yourportfolio.com"
            />
          </label>

          <label>
            Short bio
            <textarea value={bio} onChange={(event) => setBio(event.target.value)} rows={3} />
          </label>

          <label>
            Extra context
            <textarea value={extraContext} onChange={(event) => setExtraContext(event.target.value)} rows={3} />
          </label>

          <div className="actions">
            <button type="button" className="secondary" onClick={() => router.push("/onboarding/name")} disabled={busy}>
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
