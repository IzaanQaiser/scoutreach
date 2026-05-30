"use client";

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { useAuth } from "../../components/auth-provider";
import { getOnboardingState } from "../../lib/api";
import { onboardingStepToRoute } from "../../lib/onboarding-routing";

export default function AuthPage() {
  const router = useRouter();
  const { token, isLoading, isAuthenticated, signInWithPassword, signUpWithPassword, signInWithGoogle } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submitLabel = useMemo(() => (mode === "login" ? "Log In" : "Sign Up"), [mode]);

  useEffect(() => {
    let cancelled = false;

    async function maybeRouteAuthenticatedUser() {
      if (!isAuthenticated || isLoading) {
        return;
      }

      try {
        const state = await getOnboardingState(token);
        if (cancelled) {
          return;
        }

        if (state.onboarding_complete) {
          router.replace("/dashboard");
          return;
        }

        router.replace(onboardingStepToRoute(state.step));
      } catch {
        if (!cancelled) {
          router.replace("/onboarding/name");
        }
      }
    }

    void maybeRouteAuthenticatedUser();

    return () => {
      cancelled = true;
    };
  }, [isAuthenticated, isLoading, router, token]);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);

    try {
      if (mode === "login") {
        await signInWithPassword(email.trim(), password);
      } else {
        await signUpWithPassword(email.trim(), password);
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Authentication failed.");
    } finally {
      setBusy(false);
    }
  }

  async function onGoogle() {
    setBusy(true);
    setError(null);

    try {
      await signInWithGoogle();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Google sign-in failed.");
      setBusy(false);
    }
  }

  return (
    <main className="page">
      <section className="panel auth-panel">
        <h1>{mode === "login" ? "Welcome back" : "Create your account"}</h1>
        <p>Sign in to continue to onboarding and your outreach dashboard.</p>

        <form onSubmit={onSubmit} className="auth-form">
          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
              autoComplete="email"
            />
          </label>

          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
              autoComplete={mode === "login" ? "current-password" : "new-password"}
            />
          </label>

          <button type="submit" disabled={busy}>
            {busy ? "Working..." : submitLabel}
          </button>
        </form>

        <button type="button" disabled={busy} onClick={onGoogle} className="secondary">
          Continue with Google
        </button>

        <button
          type="button"
          disabled={busy}
          onClick={() => setMode((previous) => (previous === "login" ? "signup" : "login"))}
          className="secondary"
        >
          {mode === "login" ? "Need an account? Sign up" : "Already have an account? Log in"}
        </button>

        {error ? <p className="error">{error}</p> : null}
      </section>
    </main>
  );
}
