BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT NOT NULL UNIQUE,
  premium_status BOOLEAN NOT NULL DEFAULT FALSE,
  tokens_used INTEGER NOT NULL DEFAULT 0,
  auto_send_enabled BOOLEAN NOT NULL DEFAULT FALSE,
  message_preferences JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS candidate_profile (
  user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  resume TEXT,
  skills JSONB NOT NULL DEFAULT '{}'::jsonb,
  github_url TEXT,
  github_content JSONB NOT NULL DEFAULT '{}'::jsonb,
  linkedin_url TEXT,
  linkedin_content JSONB NOT NULL DEFAULT '{}'::jsonb,
  portfolio_url TEXT,
  portfolio_content JSONB NOT NULL DEFAULT '{}'::jsonb,
  bio TEXT,
  extra_context TEXT,
  target_roles JSONB NOT NULL DEFAULT '[]'::jsonb,
  job_preferences JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  selected_batches JSONB NOT NULL DEFAULT '[]'::jsonb,
  status TEXT NOT NULL CHECK (
    status IN (
      'queued',
      'running',
      'scraping',
      'enriching',
      'dossier_generating',
      'completed',
      'completed_with_errors',
      'failed',
      'messages_generating',
      'messages_generated',
      'sending'
    )
  ),
  progress INTEGER NOT NULL DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
  profile_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
  error_message TEXT,
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS companies (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  yc_url TEXT,
  website_url TEXT,
  domain TEXT,
  batch TEXT,
  founders JSONB NOT NULL DEFAULT '[]'::jsonb,
  raw_scraped_data JSONB NOT NULL DEFAULT '{}'::jsonb,
  website_content JSONB NOT NULL DEFAULT '{}'::jsonb,
  tags JSONB NOT NULL DEFAULT '[]'::jsonb,
  dossier JSONB NOT NULL DEFAULT '{}'::jsonb,
  status TEXT NOT NULL DEFAULT 'pending_review' CHECK (
    status IN (
      'pending_review',
      'accepted',
      'rejected',
      'dossier_failed',
      'scrape_failed',
      'email_lookup_failed'
    )
  ),
  fit_score DOUBLE PRECISION,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS outreach (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  run_id UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
  company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  founder_name TEXT,
  founder_email TEXT,
  subject TEXT,
  message_content TEXT,
  status TEXT NOT NULL DEFAULT 'draft' CHECK (
    status IN (
      'draft',
      'approved',
      'needs_review',
      'rejected',
      'generation_failed',
      'sending',
      'sent',
      'failed'
    )
  ),
  review_notes TEXT,
  error_message TEXT,
  sent_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_runs_user_id ON runs(user_id);
CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status);
CREATE INDEX IF NOT EXISTS idx_companies_run_id ON companies(run_id);
CREATE INDEX IF NOT EXISTS idx_companies_status ON companies(status);
CREATE INDEX IF NOT EXISTS idx_outreach_user_id ON outreach(user_id);
CREATE INDEX IF NOT EXISTS idx_outreach_run_id ON outreach(run_id);
CREATE INDEX IF NOT EXISTS idx_outreach_company_id ON outreach(company_id);
CREATE INDEX IF NOT EXISTS idx_outreach_status ON outreach(status);

DROP TRIGGER IF EXISTS trg_users_updated_at ON users;
CREATE TRIGGER trg_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_candidate_profile_updated_at ON candidate_profile;
CREATE TRIGGER trg_candidate_profile_updated_at
BEFORE UPDATE ON candidate_profile
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_runs_updated_at ON runs;
CREATE TRIGGER trg_runs_updated_at
BEFORE UPDATE ON runs
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_companies_updated_at ON companies;
CREATE TRIGGER trg_companies_updated_at
BEFORE UPDATE ON companies
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_outreach_updated_at ON outreach;
CREATE TRIGGER trg_outreach_updated_at
BEFORE UPDATE ON outreach
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

COMMIT;
