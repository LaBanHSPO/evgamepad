-- Phase 11. One settled score per session.
--
-- Every input is process-side. There is deliberately no column here for win
-- rate, profit factor, P/L, R, or tilt: the first four are outcomes and the
-- fifth is a retrospective, and none of them is a way to trade well.
CREATE TABLE score_session (
    session_id       INTEGER PRIMARY KEY REFERENCES session(id) ON DELETE CASCADE,
    settled_at       INTEGER NOT NULL,
    total            REAL NOT NULL,
    axes_json        TEXT NOT NULL DEFAULT '{}',
    -- Axes with no evidence. Stored so the radar can draw a dashed "n/a" ring
    -- rather than a zero spoke, which would read as a bad evening instead of
    -- an absent measurement.
    na_json          TEXT NOT NULL DEFAULT '[]',
    items_json       TEXT NOT NULL DEFAULT '[]',
    weights_version  TEXT NOT NULL DEFAULT '1'
);
