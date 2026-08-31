-- Phase 11: the Process Score, and the evidence the Review axis credits.
--
-- The row stores the axis **inputs**, not just the total. A weight change then recomputes every
-- historical evening from what was actually measured, instead of leaving last month's scores
-- computed under a weighting nobody can reconstruct.
--
-- Note what is deliberately absent: there is no streak column, no level, no "days since", and no
-- table keyed by anything but a single session. The schema has nowhere to accumulate, which is the
-- structural version of the promise that this score never becomes a thing to defend.

CREATE TABLE session_score (
    session_id      TEXT PRIMARY KEY REFERENCES session_equity (session_id),
    computed_at     INTEGER NOT NULL,
    weights_version INTEGER NOT NULL,

    -- The five axes. NULL is a *vacuous* axis — no evidence — and is not the same as 0.
    adherence       REAL,
    selectivity     REAL,
    risk_discipline REAL,
    preparation     REAL,
    review          REAL,

    na_axes         TEXT NOT NULL DEFAULT '[]',   -- JSON: which axes had no denominator
    oq_mean         REAL,                          -- the evening's mean opportunity quality
    n_fires         INTEGER NOT NULL DEFAULT 0,
    total           REAL NOT NULL,                 -- unrounded; the deck rounds for display
    inputs          TEXT NOT NULL                  -- JSON: everything score_session() read
);

-- Opening a replay is review, and review is part of the process being scored. One row per open,
-- so a session that reviewed three trades reads differently from one that opened the same trade
-- three times.
CREATE TABLE review_event (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT REFERENCES session_equity (session_id),
    kind        TEXT NOT NULL,                     -- replay_open
    cid         TEXT,                              -- the trade reviewed, when there is one
    ts          INTEGER NOT NULL
);
CREATE INDEX idx_review_event_session ON review_event (session_id, ts);
