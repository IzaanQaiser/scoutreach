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
