import type { OnboardingStep } from "./types";

const ORDER: OnboardingStep[] = [
  "auth",
  "name",
  "profile_sources",
  "targets",
  "message_preferences",
  "calibration",
  "done",
];

export function onboardingStepToRoute(step: OnboardingStep): string {
  switch (step) {
    case "name":
      return "/onboarding/name";
    case "profile_sources":
      return "/onboarding/profile-sources";
    case "targets":
      return "/onboarding/targets";
    case "message_preferences":
      return "/onboarding/message-preferences";
    case "calibration":
      return "/onboarding/calibration";
    case "done":
      return "/dashboard";
    case "auth":
    default:
      return "/auth";
  }
}

export function onboardingStepIndex(step: OnboardingStep): number {
  return ORDER.indexOf(step);
}

export function routeSegmentToOnboardingStep(segment: string): OnboardingStep {
  switch (segment) {
    case "name":
      return "name";
    case "profile-sources":
      return "profile_sources";
    case "targets":
      return "targets";
    case "message-preferences":
      return "message_preferences";
    case "calibration":
      return "calibration";
    default:
      return "auth";
  }
}
