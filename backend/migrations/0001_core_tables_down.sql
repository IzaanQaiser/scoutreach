BEGIN;

DROP TRIGGER IF EXISTS trg_outreach_updated_at ON outreach;
DROP TRIGGER IF EXISTS trg_companies_updated_at ON companies;
DROP TRIGGER IF EXISTS trg_runs_updated_at ON runs;
DROP TRIGGER IF EXISTS trg_candidate_profile_updated_at ON candidate_profile;
DROP TRIGGER IF EXISTS trg_users_updated_at ON users;

DROP TABLE IF EXISTS outreach;
DROP TABLE IF EXISTS companies;
DROP TABLE IF EXISTS runs;
DROP TABLE IF EXISTS candidate_profile;
DROP TABLE IF EXISTS users;

DROP FUNCTION IF EXISTS set_updated_at();

COMMIT;
