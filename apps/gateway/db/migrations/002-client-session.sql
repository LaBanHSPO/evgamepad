-- Phase 3 owns these two tables. Nothing here belongs to a later phase.

-- Raw pad telemetry, batched at 1 Hz by the client. Phase 9's tilt meter has no
-- other source, and an evening that was not recorded cannot be replayed -- so it
-- is captured from the first session even though nothing reads it yet.
CREATE TABLE pad_event (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id     INTEGER REFERENCES session(id) ON DELETE CASCADE,
    ts             INTEGER NOT NULL,
    from_state     TEXT,
    to_state       TEXT,
    sym            TEXT,
    lots           REAL,
    reason         TEXT,
    clutch_ms      INTEGER NOT NULL DEFAULT 0,
    arm_ms         INTEGER NOT NULL DEFAULT 0,
    clutch_cycles  INTEGER NOT NULL DEFAULT 0,
    arm_flips      INTEGER NOT NULL DEFAULT 0,
    btn_rate_hz    REAL NOT NULL DEFAULT 0,
    lot_steps      INTEGER NOT NULL DEFAULT 0,
    ttf_ms         INTEGER
);
CREATE INDEX pad_event_session ON pad_event (session_id, ts);

-- The pre/post session check-in, and the stand-down tally the evening earned.
-- Both ratings are nullable because the check-in is skippable by design: it
-- must never stand between the player and the start of a session.
CREATE TABLE session_process (
    session_id       INTEGER PRIMARY KEY REFERENCES session(id) ON DELETE CASCADE,
    pre_rating       INTEGER CHECK (pre_rating BETWEEN 1 AND 5),
    pre_at           INTEGER,
    pre_note         TEXT,
    post_rating      INTEGER CHECK (post_rating BETWEEN 1 AND 5),
    post_at          INTEGER,
    post_note        TEXT,
    stand_downs      INTEGER NOT NULL DEFAULT 0,
    stand_down_json  TEXT NOT NULL DEFAULT '[]'
);
