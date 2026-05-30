BEGIN;

CREATE TABLE IF NOT EXISTS outreach_regeneration_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  run_id UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
  outreach_id UUID NOT NULL REFERENCES outreach(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_outreach_regen_events_user_created_at
  ON outreach_regeneration_events(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_outreach_regen_events_outreach_id
  ON outreach_regeneration_events(outreach_id);

COMMIT;
