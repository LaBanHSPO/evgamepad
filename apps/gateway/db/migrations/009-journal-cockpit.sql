-- Phase 12: the daily journal cockpit.
--
-- One boundary governs every table here: **broker facts are immutable, player review is append-on-
-- top.** Nothing in this migration can rewrite a fill, a price, an R conversion input, or an
-- execution event. `trade_review` and `mistake_occurrence` reference a cid; they never shadow one.
--
-- Player text is stored as text and rendered as a text child, never as markup. Attachments store a
-- server-generated id and never a client-supplied path.

-- The five-item readiness check, one row per item so a sixth is a data change rather than a
-- migration. Advisory only: nothing here has ever blocked an unlock or a fire.
CREATE TABLE readiness_check (
    session_id  TEXT NOT NULL REFERENCES session_equity (session_id),
    item        TEXT NOT NULL,          -- sleep | calm | focus | risk_accepted | plan_reviewed
    ok          INTEGER,                -- 1 yes, 0 no, NULL declined — three distinct answers
    note        TEXT,
    ts          INTEGER NOT NULL,
    PRIMARY KEY (session_id, item)
);

-- The evening's written intent. Player-authored: the desk's own plan lives in `session_plan` and
-- the two are shown side by side rather than merged, so a model can never edit what you wrote.
CREATE TABLE daily_analysis (
    session_id   TEXT PRIMARY KEY REFERENCES session_equity (session_id),
    updated_at   INTEGER NOT NULL,
    thesis       TEXT,
    instruments  TEXT,                  -- JSON array of symbols
    key_levels   TEXT,                  -- JSON array of {price, label}
    invalidation TEXT,
    event_risks  TEXT,
    tags         TEXT,                  -- JSON array
    notes        TEXT
);

-- Chart screenshots, attached by hand. No scraping, no unofficial quote API.
CREATE TABLE journal_attachment (
    id          TEXT PRIMARY KEY,       -- server-generated ULID; also the on-disk filename stem
    session_id  TEXT REFERENCES session_equity (session_id),
    cid         TEXT,                   -- set when the attachment belongs to one trade
    mime        TEXT NOT NULL,          -- image/png | image/jpeg | image/webp, from magic bytes
    bytes       INTEGER NOT NULL,
    width       INTEGER,
    height      INTEGER,
    label       TEXT,
    created_at  INTEGER NOT NULL
);
CREATE INDEX idx_attachment_session ON journal_attachment (session_id, created_at);
CREATE INDEX idx_attachment_cid ON journal_attachment (cid);

-- One review per trade. `intent` is the four-group classification; it is only ever `impulsive` or
-- `revenge` when the player said so, because inferring that from a chart is how a clean
-- discretionary trade gets libelled.
CREATE TABLE trade_review (
    cid         TEXT PRIMARY KEY REFERENCES trade_plan (cid),
    updated_at  INTEGER NOT NULL,
    intent      TEXT,                   -- planned | impulsive | revenge | unknown
    intent_by   TEXT,                   -- derived | player
    note        TEXT,
    early_exit  INTEGER                 -- 1 when the player recorded a discretionary early close
);

-- The taxonomy. Built-ins are seeded on first boot; a custom mistake is just a row with
-- `builtin = 0`, so the two are counted and trended by exactly the same code.
CREATE TABLE mistake_definition (
    code        TEXT PRIMARY KEY,
    label       TEXT NOT NULL,
    builtin     INTEGER NOT NULL DEFAULT 0,
    active      INTEGER NOT NULL DEFAULT 1,
    created_at  INTEGER NOT NULL
);

-- What actually happened, per trade. `source` separates evidence the gateway can prove from a
-- judgement the player made; the trend counts both but never conflates them.
CREATE TABLE mistake_occurrence (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    cid         TEXT NOT NULL,
    session_id  TEXT,
    code        TEXT NOT NULL REFERENCES mistake_definition (code),
    source      TEXT NOT NULL,          -- auto | player
    note        TEXT,
    ts          INTEGER NOT NULL,
    UNIQUE (cid, code, source)
);
CREATE INDEX idx_mistake_session ON mistake_occurrence (session_id, ts);
CREATE INDEX idx_mistake_code ON mistake_occurrence (code, ts);

-- The player's own philosophy, and at most one thing they are working on. Deliberately a single
-- row: this is a statement of how you trade, not a log to accumulate.
CREATE TABLE system_principles (
    id           INTEGER PRIMARY KEY CHECK (id = 1),
    updated_at   INTEGER NOT NULL,
    philosophy   TEXT,
    principles   TEXT,                  -- JSON array of strings
    focus_code   TEXT                   -- the one mistake being worked on, or NULL
);
