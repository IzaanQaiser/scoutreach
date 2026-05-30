"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuth } from "../../../components/auth-provider";
import { getOnboardingState } from "../../../lib/api";
import { onboardingStepToRoute } from "../../../lib/onboarding-routing";

export default function AuthCallbackPage() {
  const router = useRouter();
  const { token, isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    let cancelled = false;

    async function completeAuthRedirect() {
      if (isLoading) {
        return;
      }

      if (!isAuthenticated) {
        router.replace("/auth");
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

    void completeAuthRedirect();

    return () => {
      cancelled = true;
    };
  }, [isAuthenticated, isLoading, router, token]);

  return (
    <main className="page">
      <section className="panel">
        <h1>Finishing sign in...</h1>
        <p>Redirecting you to ScoutReach.</p>
      </section>
    </main>
  );
}
