-- Phase 7: the playbook and the grade. Nothing here belongs to a later phase.

-- A named way of trading. `method` distinguishes a seeded Volman book from one
-- the player wrote.
CREATE TABLE playbook (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    slug          TEXT NOT NULL UNIQUE,
    name          TEXT NOT NULL,
    method        TEXT NOT NULL CHECK (method IN ('volman_m5','custom')),
    symbols_json  TEXT NOT NULL DEFAULT '[]',
    detector_tag  TEXT,
    narrative     TEXT NOT NULL DEFAULT '',
    active        INTEGER NOT NULL DEFAULT 1,
    created_at    INTEGER NOT NULL,
    -- Retiring hides a playbook from selection without deleting it: historical
    -- grades keep resolving, so the deck never loses a month.
    retired_at    INTEGER
);

CREATE TABLE playbook_rule (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    playbook_id  INTEGER NOT NULL REFERENCES playbook(id) ON DELETE CASCADE,
    ord          INTEGER NOT NULL,
    kind         TEXT NOT NULL CHECK (kind IN ('auto','manual')),
    code         TEXT NOT NULL,          -- references method/rules.py REGISTRY
    params_json  TEXT NOT NULL DEFAULT '{}',
    label        TEXT NOT NULL,
    -- Only required rules gate `clean`. An optional rule that fails is
    -- information, not a verdict.
    required     INTEGER NOT NULL DEFAULT 1,
    UNIQUE (playbook_id, code)
);
CREATE INDEX playbook_rule_book ON playbook_rule (playbook_id, ord);

-- Keyed on the cid -- one fire -- not on a closed position. A rejected or
-- declined fire is gradeable too, and phase 6's declined count depends on it.
CREATE TABLE trade_grade (
    cid             TEXT PRIMARY KEY,
    playbook_id     INTEGER REFERENCES playbook(id) ON DELETE SET NULL,
    session_id      INTEGER REFERENCES session(id) ON DELETE SET NULL,
    evaluated_at    INTEGER NOT NULL,
    phase           TEXT NOT NULL CHECK (phase IN ('arm','fire','settled')),
    results_json    TEXT NOT NULL DEFAULT '[]',
    required_pass   INTEGER NOT NULL DEFAULT 0,
    required_total  INTEGER NOT NULL DEFAULT 0,
    clean           INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX trade_grade_session ON trade_grade (session_id, evaluated_at);

-- The active playbook is part of session state.
ALTER TABLE session_process ADD COLUMN playbook_id INTEGER REFERENCES playbook(id);
