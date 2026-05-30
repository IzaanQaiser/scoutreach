import type {
  CandidateProfile,
  Company,
  CompanyStatus,
  MeResponse,
  OnboardingExample,
  OnboardingState,
  SettingsPayload,
} from "./types";

type ApiSuccess<T> = {
  success: true;
  data: T;
};

type ApiFailure = {
  success: false;
  error: {
    code: string;
    message: string;
  };
};

type ApiResponse<T> = ApiSuccess<T> | ApiFailure;

const DEFAULT_API_BASE = "http://127.0.0.1:8000";

function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_API_BASE;
}

function resolveToken(token: string | null | undefined): string {
  if (token && token.trim()) {
    return token;
  }
  const devToken = process.env.NEXT_PUBLIC_DEV_AUTH_TOKEN;
  if (devToken && devToken.trim()) {
    return devToken.trim();
  }
  throw new Error("Missing access token. Please authenticate.");
}

async function requestJson<T>(path: string, token: string | null | undefined, init?: RequestInit): Promise<T> {
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${resolveToken(token)}`,
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  const payload = (await response.json()) as ApiResponse<T>;
  if (!payload.success) {
    throw new Error(payload.error.message);
  }

  return payload.data;
}

export async function getMe(token: string | null | undefined): Promise<MeResponse> {
  return requestJson<MeResponse>("/me", token);
}

export async function patchMe(
  token: string | null | undefined,
  payload: { first_name?: string; last_name?: string },
): Promise<{ message: string; onboarding_step?: string }> {
  return requestJson("/me", token, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function getCandidateProfile(token: string | null | undefined): Promise<CandidateProfile> {
  return requestJson<CandidateProfile>("/candidate-profile", token);
}

export async function putCandidateProfile(
  token: string | null | undefined,
  payload: {
    resume?: string;
    github_url?: string;
    linkedin_url?: string;
    portfolio_url?: string;
    bio?: string;
    extra_context?: string;
    target_roles?: string[];
    job_preferences?: Record<string, unknown>;
    skills?: Record<string, unknown>;
  },
): Promise<{ message: string }> {
  return requestJson("/candidate-profile", token, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function getSettings(token: string | null | undefined): Promise<SettingsPayload> {
  return requestJson<SettingsPayload>("/settings", token);
}

export async function patchSettings(
  token: string | null | undefined,
  payload: { auto_send_enabled?: boolean; message_preferences?: Record<string, unknown> },
): Promise<{ message: string }> {
  return requestJson("/settings", token, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function getOnboardingState(token: string | null | undefined): Promise<OnboardingState> {
  return requestJson<OnboardingState>("/onboarding/state", token);
}

export async function generateOnboardingExamples(
  token: string | null | undefined,
  loopIndex: number,
): Promise<{ loop_index: number; examples: OnboardingExample[]; max_loops: number }> {
  return requestJson("/onboarding/example-messages", token, {
    method: "POST",
    body: JSON.stringify({ loop_index: loopIndex }),
  });
}

export async function submitOnboardingFeedback(
  token: string | null | undefined,
  payload: {
    loop_index: number;
    rejected_examples: Array<{
      example_id?: string;
      position_industry_feedback?: string;
      subject_feedback?: string;
      body_feedback?: string;
    }>;
  },
): Promise<
  | {
      loop_index: number;
      examples: OnboardingExample[];
      max_loops: number;
      message?: string;
    }
  | {
      message: string;
      status: string;
      step: string;
      onboarding_complete: boolean;
    }
> {
  return requestJson("/onboarding/example-feedback", token, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function completeOnboarding(
  token: string | null | undefined,
  completionMode: "completed" | "completed_after_cap" | "skipped_calibration",
): Promise<{ message: string; status: string; step: string; onboarding_complete: boolean }> {
  return requestJson("/onboarding/complete", token, {
    method: "POST",
    body: JSON.stringify({ completion_mode: completionMode }),
  });
}

export async function getRunCompanies(
  token: string | null | undefined,
  params: {
    runId: string;
    status?: CompanyStatus;
    limit?: number;
    offset?: number;
  },
): Promise<Company[]> {
  const query = new URLSearchParams();
  if (params.status) {
    query.set("status", params.status);
  }
  query.set("limit", String(params.limit ?? 50));
  query.set("offset", String(params.offset ?? 0));

  const data = await requestJson<{ companies: Company[] }>(
    `/runs/${params.runId}/companies?${query.toString()}`,
    token,
  );
  return data.companies;
}

export async function updateCompanyStatus(
  token: string | null | undefined,
  params: {
    companyId: string;
    status: "accepted" | "rejected" | "pending_review";
  },
): Promise<{ company_id: string; status: string; message: string }> {
  return requestJson(`/companies/${params.companyId}`, token, {
    method: "PATCH",
    body: JSON.stringify({ status: params.status }),
  });
}

export async function getPendingCount(token: string | null | undefined, params: { runId: string }): Promise<number> {
  const data = await requestJson<{ run_id: string; pending_count: number }>(
    `/runs/${params.runId}/companies/pending-count`,
    token,
  );
  return data.pending_count;
}
