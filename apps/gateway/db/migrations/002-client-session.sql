-- Phase 3 core: what the client agent produces. Nothing here is on the order path.

-- Pad telemetry, batched at 1 Hz by the client. Phase 9 is the only reader; it is captured from
-- day one because there is no way to reconstruct it after the fact.
CREATE TABLE pad_event (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id     TEXT REFERENCES session_equity (session_id),
    ts             INTEGER NOT NULL,
    from_phase     TEXT NOT NULL,
    to_phase       TEXT NOT NULL,
    reason         TEXT,
    symbol         TEXT,
    lots           REAL,
    clutch_ms      INTEGER NOT NULL DEFAULT 0,
    arm_ms         INTEGER NOT NULL DEFAULT 0,
    clutch_cycles  INTEGER NOT NULL DEFAULT 0,
    arm_flips      INTEGER NOT NULL DEFAULT 0,
    btn_rate_hz    REAL NOT NULL DEFAULT 0,
    lot_steps      INTEGER NOT NULL DEFAULT 0,
    ttf_ms         INTEGER
);
CREATE INDEX idx_pad_event_session ON pad_event (session_id, ts);

-- The pre/post check-in and the stood-down count. Both are skippable: a null rating means the
-- player declined, which is different from a rating of 1 and must stay distinguishable.
CREATE TABLE session_process (
    session_id       TEXT PRIMARY KEY REFERENCES session_equity (session_id),
    pre_rating       INTEGER,
    pre_at           INTEGER,
    post_rating      INTEGER,
    post_at          INTEGER,
    stood_down_count INTEGER NOT NULL DEFAULT 0
);
