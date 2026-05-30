"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useAuth } from "./auth-provider";
import { getOnboardingState } from "../lib/api";
import { onboardingStepIndex, onboardingStepToRoute } from "../lib/onboarding-routing";
import type { OnboardingState, OnboardingStep } from "../lib/types";

export function useOnboardingGuard(expectedStep: OnboardingStep): {
  token: string | null;
  isReady: boolean;
  onboardingState: OnboardingState | null;
} {
  const router = useRouter();
  const { token, isLoading, isAuthenticated } = useAuth();
  const [onboardingState, setOnboardingState] = useState<OnboardingState | null>(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function validateState() {
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

        setOnboardingState(state);

        if (state.onboarding_complete) {
          router.replace("/dashboard");
          return;
        }

        if (onboardingStepIndex(state.step) < onboardingStepIndex(expectedStep)) {
          router.replace(onboardingStepToRoute(state.step));
          return;
        }

        setIsReady(true);
      } catch {
        if (!cancelled) {
          router.replace("/auth");
        }
      }
    }

    void validateState();

    return () => {
      cancelled = true;
    };
  }, [expectedStep, isAuthenticated, isLoading, router, token]);

  return { token, isReady, onboardingState };
}
