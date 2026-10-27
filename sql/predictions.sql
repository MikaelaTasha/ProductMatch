-- Separate from the frozen benchmark database. All records are append-only.
CREATE TABLE IF NOT EXISTS model_versions (
    model_id TEXT PRIMARY KEY,
    classifier_version TEXT NOT NULL,
    freeze_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE TABLE IF NOT EXISTS predictions (
    prediction_id TEXT PRIMARY KEY,
    model_id TEXT NOT NULL REFERENCES model_versions(model_id),
    source_database_sha256 TEXT NOT NULL,
    source_split_sha256 TEXT NOT NULL,
    split_name TEXT NOT NULL CHECK (split_name IN ('train','validation')),
    pair_id TEXT NOT NULL,
    input_json TEXT NOT NULL,
    features_json TEXT NOT NULL,
    score REAL NOT NULL CHECK (score >= 0 AND score <= 1),
    decision TEXT NOT NULL CHECK (decision IN ('Match','Different','Review')),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    UNIQUE(model_id,source_database_sha256,split_name,pair_id)
);
CREATE TABLE IF NOT EXISTS review_events (
    event_id TEXT PRIMARY KEY,
    prediction_id TEXT NOT NULL REFERENCES predictions(prediction_id),
    decision TEXT NOT NULL CHECK (decision IN ('Match','Different','Review')),
    reviewer TEXT NOT NULL CHECK (length(trim(reviewer)) > 0),
    note TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE INDEX IF NOT EXISTS review_events_prediction ON review_events(prediction_id);
CREATE TRIGGER IF NOT EXISTS model_versions_no_update BEFORE UPDATE ON model_versions BEGIN SELECT RAISE(ABORT,'model versions are append-only'); END;
CREATE TRIGGER IF NOT EXISTS model_versions_no_delete BEFORE DELETE ON model_versions BEGIN SELECT RAISE(ABORT,'model versions are append-only'); END;
CREATE TRIGGER IF NOT EXISTS predictions_no_update BEFORE UPDATE ON predictions BEGIN SELECT RAISE(ABORT,'predictions are append-only'); END;
CREATE TRIGGER IF NOT EXISTS predictions_no_delete BEFORE DELETE ON predictions BEGIN SELECT RAISE(ABORT,'predictions are append-only'); END;
CREATE TRIGGER IF NOT EXISTS review_events_no_update BEFORE UPDATE ON review_events BEGIN SELECT RAISE(ABORT,'reviews are append-only'); END;
CREATE TRIGGER IF NOT EXISTS review_events_no_delete BEFORE DELETE ON review_events BEGIN SELECT RAISE(ABORT,'reviews are append-only'); END;
