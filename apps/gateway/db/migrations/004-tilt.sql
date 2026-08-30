-- Phase 9. Samples for the deck's retrospective only.
--
-- Tilt is never persisted as a trait: there is no per-player tilt column
-- anywhere, and these rows are scoped to a session. Nobody is "a tilty trader";
-- an evening had a tilt curve.
CREATE TABLE tilt_sample (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      INTEGER REFERENCES session(id) ON DELETE CASCADE,
    ts              INTEGER NOT NULL,
    score           REAL NOT NULL,
    band            TEXT NOT NULL CHECK (band IN ('cool','warm','hot','scorched')),
    -- The named drivers, so the deck can say what happened rather than only
    -- how high the number got.
    top_json        TEXT NOT NULL DEFAULT '[]',
    components_json TEXT NOT NULL DEFAULT '{}',
    cooldown_until  INTEGER
);
CREATE INDEX tilt_sample_session ON tilt_sample (session_id, ts);
