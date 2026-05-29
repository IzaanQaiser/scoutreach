import type { Company, CompanyStatus } from "./types";

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

function getAuthToken(): string {
  return process.env.NEXT_PUBLIC_DEV_AUTH_TOKEN ?? "local-dev-token";
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${getAuthToken()}`,
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

export async function getRunCompanies(params: {
  runId: string;
  status?: CompanyStatus;
  limit?: number;
  offset?: number;
}): Promise<Company[]> {
  const query = new URLSearchParams();
  if (params.status) {
    query.set("status", params.status);
  }
  query.set("limit", String(params.limit ?? 50));
  query.set("offset", String(params.offset ?? 0));

  const data = await requestJson<{ companies: Company[] }>(
    `/runs/${params.runId}/companies?${query.toString()}`,
  );
  return data.companies;
}

export async function updateCompanyStatus(params: {
  companyId: string;
  status: "accepted" | "rejected" | "pending_review";
}): Promise<{ company_id: string; status: string; message: string }> {
  return requestJson(`/companies/${params.companyId}`, {
    method: "PATCH",
    body: JSON.stringify({ status: params.status }),
  });
}

export async function getPendingCount(params: { runId: string }): Promise<number> {
  const data = await requestJson<{ run_id: string; pending_count: number }>(
    `/runs/${params.runId}/companies/pending-count`,
  );
  return data.pending_count;
}
