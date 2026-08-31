-- Phase 4: the desk's own durable state. Nothing here is on the order path.

-- One typed plan per session, so phase 6 can ask what the evening intended before it started.
CREATE TABLE session_plan (
    session_id   TEXT PRIMARY KEY REFERENCES session_equity (session_id),
    created_at   INTEGER NOT NULL,
    bias         TEXT,                        -- buy | sell | none, from the M5 detectors
    setup        TEXT,                        -- the method tag in play at session open
    text         TEXT NOT NULL,               -- the desk's plan, or 'coach offline'
    offline      INTEGER NOT NULL DEFAULT 0,  -- 1 when written without a reachable desk
    calendar_state TEXT                       -- live | cached | file | offline
);

-- Signals worth keeping a reference to: what was on screen when a trade was taken.
CREATE TABLE signal_item (
    id          TEXT PRIMARY KEY,
    session_id  TEXT REFERENCES session_equity (session_id),
    kind        TEXT NOT NULL,                -- volman | tv | calendar
    symbol      TEXT,
    side        TEXT,
    text        TEXT NOT NULL,
    url         TEXT,
    ts          INTEGER NOT NULL
);
CREATE INDEX idx_signal_item_session ON signal_item (session_id, ts);
