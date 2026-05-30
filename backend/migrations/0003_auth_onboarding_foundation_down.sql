BEGIN;

DROP INDEX IF EXISTS idx_onboarding_calibration_events_event_type;
DROP INDEX IF EXISTS idx_onboarding_calibration_events_user_created_at;
DROP TABLE IF EXISTS onboarding_calibration_events;

ALTER TABLE users DROP CONSTRAINT IF EXISTS chk_users_onboarding_step;
ALTER TABLE users DROP CONSTRAINT IF EXISTS chk_users_onboarding_status;

ALTER TABLE users
  DROP COLUMN IF EXISTS calibration_last_result,
  DROP COLUMN IF EXISTS calibration_loop_count,
  DROP COLUMN IF EXISTS onboarding_completed_at,
  DROP COLUMN IF EXISTS onboarding_step,
  DROP COLUMN IF EXISTS onboarding_status,
  DROP COLUMN IF EXISTS last_name,
  DROP COLUMN IF EXISTS first_name;

COMMIT;
