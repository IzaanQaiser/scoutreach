"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuth } from "../../components/auth-provider";
import { getOnboardingState } from "../../lib/api";
import { onboardingStepToRoute } from "../../lib/onboarding-routing";

export default function OnboardingIndexPage() {
  const router = useRouter();
  const { token, isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    let cancelled = false;

    async function redirectToCurrentStep() {
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
          router.replace("/auth");
        }
      }
    }

    void redirectToCurrentStep();

    return () => {
      cancelled = true;
    };
  }, [isAuthenticated, isLoading, router, token]);

  return (
    <main className="page">
      <section className="panel">
        <h1>Loading onboarding...</h1>
      </section>
    </main>
  );
}
