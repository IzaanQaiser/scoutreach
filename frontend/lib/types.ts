export type CompanyStatus =
  | "pending_review"
  | "accepted"
  | "rejected"
  | "dossier_failed"
  | "scrape_failed"
  | "email_lookup_failed";

export type Founder = {
  name?: string;
  linkedin_url?: string;
  email?: string | null;
  email_confidence?: number | null;
  email_lookup_status?: "success" | "empty" | "failed";
};

export type Company = {
  id: string;
  run_id: string;
  name: string;
  yc_url?: string;
  website_url?: string;
  domain?: string;
  batch?: string;
  founders: Founder[];
  tags?: string[];
  dossier?: Record<string, unknown>;
  status: CompanyStatus;
  fit_score?: number | null;
};

export type OnboardingStep =
  | "auth"
  | "name"
  | "profile_sources"
  | "targets"
  | "message_preferences"
  | "calibration"
  | "done";

export type OnboardingStatus =
  | "not_started"
  | "in_progress"
  | "completed"
  | "completed_after_cap"
  | "skipped_calibration";

export type MeUser = {
  id: string;
  email: string;
  premium_status: boolean;
  tokens_used: number;
  auto_send_enabled: boolean;
  message_preferences: Record<string, unknown>;
  first_name?: string | null;
  last_name?: string | null;
  onboarding_status: OnboardingStatus;
  onboarding_step: OnboardingStep;
  onboarding_completed_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type MeResponse = {
  user: MeUser;
  has_candidate_profile: boolean;
  onboarding_complete: boolean;
};

export type CandidateProfile = {
  user_id: string;
  resume?: string | null;
  skills: Record<string, unknown>;
  github_url?: string | null;
  github_content: Record<string, unknown>;
  linkedin_url?: string | null;
  linkedin_content: Record<string, unknown>;
  portfolio_url?: string | null;
  portfolio_content: Record<string, unknown>;
  bio?: string | null;
  extra_context?: string | null;
  target_roles: string[];
  job_preferences: Record<string, unknown>;
};

export type SettingsPayload = {
  auto_send_enabled: boolean;
  message_preferences: Record<string, unknown>;
};

export type OnboardingState = {
  status: OnboardingStatus;
  step: OnboardingStep;
  onboarding_complete: boolean;
  calibration_loop_count: number;
  calibration_last_result?: string | null;
};

export type OnboardingExample = {
  example_id: string;
  founder_name: string;
  company_name: string;
  target_role_context: string;
  industry_context: string;
  subject: string;
  message_content: string;
};
