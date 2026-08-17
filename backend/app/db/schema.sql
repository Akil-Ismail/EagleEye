CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    role TEXT NULL,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    enrolled_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes TEXT NULL
);

CREATE TABLE IF NOT EXISTS media_uploads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type TEXT NOT NULL CHECK (source_type IN ('camera', 'upload_image', 'upload_video')),
    original_filename TEXT NULL,
    file_path TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP NULL
);

CREATE TABLE IF NOT EXISTS access_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NULL,
    media_upload_id INTEGER NULL,
    camera_id TEXT NULL,
    frame_timestamp_ms INTEGER NULL,
    event_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    confidence_score REAL NOT NULL,
    liveness_passed BOOLEAN NULL,
    decision TEXT NOT NULL CHECK (decision IN ('authorized', 'unknown', 'spoof_suspected')),
    snapshot_path TEXT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL,
    FOREIGN KEY (media_upload_id) REFERENCES media_uploads (id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_access_logs_event_timestamp ON access_logs (event_timestamp);
CREATE INDEX IF NOT EXISTS idx_access_logs_decision ON access_logs (decision);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    log_id INTEGER NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('unauthorized_access', 'spoof_attempt', 'repeated_unknown')),
    resolved BOOLEAN NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    FOREIGN KEY (log_id) REFERENCES access_logs (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_alerts_resolved ON alerts (resolved);

CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    summary_text TEXT NOT NULL,
    log_ids_included TEXT NOT NULL,
    generated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
