-- Phase 9: tilt samples and the score frozen onto each fire.
--
-- Note the gap: 006 belongs to phase 8 (voice), which is deferred. The runner tracks each applied
-- migration id rather than a single maximum version, so a gap applies cleanly and 006 slots in
-- whenever phase 8 resumes.

-- Per-session samples for the deck's retrospective. Tilt is **never** persisted as a trait — this
-- is a record of an evening, not a property of the player.
CREATE TABLE tilt_sample (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id   TEXT REFERENCES session_equity (session_id),
    ts           INTEGER NOT NULL,
    score        REAL NOT NULL,
    band         TEXT NOT NULL,
    components   TEXT NOT NULL,          -- JSON: every component, its value and its weight
    missing      TEXT NOT NULL DEFAULT '[]',
    top_driver   TEXT
);
CREATE INDEX idx_tilt_sample_session ON tilt_sample (session_id, ts);

-- What the score was at the moment of the fire. Read by the deck's retrospective; it is not, and
-- must never become, an input to the Process Score.
ALTER TABLE trade_closed ADD COLUMN tilt_at_entry REAL;
