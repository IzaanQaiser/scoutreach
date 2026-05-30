BEGIN;

DROP INDEX IF EXISTS idx_outreach_regen_events_outreach_id;
DROP INDEX IF EXISTS idx_outreach_regen_events_user_created_at;
DROP TABLE IF EXISTS outreach_regeneration_events;

COMMIT;
