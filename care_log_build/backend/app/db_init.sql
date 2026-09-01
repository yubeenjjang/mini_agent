CREATE TABLE IF NOT EXISTS care_logs (
  id BIGSERIAL PRIMARY KEY,
  baby_id TEXT NOT NULL,
  log_type TEXT NOT NULL CHECK (log_type IN ('feeding','sleep','diaper','growth')),
  recorded_at TIMESTAMPTZ NOT NULL,
  details JSONB NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS idx_care_logs_baby_date ON care_logs (baby_id, recorded_at DESC);
