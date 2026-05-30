BEGIN;

ALTER TABLE users
  ADD COLUMN IF NOT EXISTS first_name TEXT,
  ADD COLUMN IF NOT EXISTS last_name TEXT,
  ADD COLUMN IF NOT EXISTS onboarding_status TEXT NOT NULL DEFAULT 'not_started',
  ADD COLUMN IF NOT EXISTS onboarding_step TEXT NOT NULL DEFAULT 'auth',
  ADD COLUMN IF NOT EXISTS onboarding_completed_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS calibration_loop_count INTEGER NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS calibration_last_result TEXT;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'chk_users_onboarding_status'
  ) THEN
    ALTER TABLE users
      ADD CONSTRAINT chk_users_onboarding_status
      CHECK (onboarding_status IN (
        'not_started',
        'in_progress',
        'completed',
        'completed_after_cap',
        'skipped_calibration'
      ));
  END IF;
END
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'chk_users_onboarding_step'
  ) THEN
    ALTER TABLE users
      ADD CONSTRAINT chk_users_onboarding_step
      CHECK (onboarding_step IN (
        'auth',
        'name',
        'profile_sources',
        'targets',
        'message_preferences',
        'calibration',
        'done'
      ));
  END IF;
END
$$;

CREATE TABLE IF NOT EXISTS onboarding_calibration_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  event_type TEXT NOT NULL CHECK (event_type IN (
    'examples_generated',
    'feedback_submitted',
    'skipped',
    'completed'
  )),
  loop_index INTEGER NOT NULL DEFAULT 0,
  feedback JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_onboarding_calibration_events_user_created_at
  ON onboarding_calibration_events(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_onboarding_calibration_events_event_type
  ON onboarding_calibration_events(event_type);

COMMIT;
