-- Phase 7: playbooks, their rules, and the grade of every fire.

-- A named setup with a narrative the player wrote. Retiring one hides it from selection but
-- keeps it resolvable, so last month's deck numbers do not vanish when the book changes.
CREATE TABLE playbook (
    id            TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    slug          TEXT NOT NULL UNIQUE,
    method        TEXT NOT NULL DEFAULT 'volman_m5',   -- volman_m5 | custom
    symbols       TEXT NOT NULL DEFAULT '[]',          -- JSON array; empty means any
    detector_tag  TEXT,                                -- the phase 4 tag this setup expects
    narrative     TEXT,                                -- player prose, rendered as text
    active        INTEGER NOT NULL DEFAULT 1,
    created_at    INTEGER NOT NULL,
    retired_at    INTEGER
);

-- One rule of a playbook. `code` references the registry; `params` parameterises it.
-- `required` decides whether it counts toward `clean`.
CREATE TABLE playbook_rule (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    playbook_id  TEXT NOT NULL REFERENCES playbook (id) ON DELETE CASCADE,
    ord          INTEGER NOT NULL,
    kind         TEXT NOT NULL,                        -- auto | manual
    code         TEXT NOT NULL,
    params       TEXT NOT NULL DEFAULT '{}',
    label        TEXT,
    required     INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX idx_playbook_rule_book ON playbook_rule (playbook_id, ord);

-- Keyed on the cid — one *fire*, not one closed position. A declined arm and a rejected intent
-- are gradeable too, and the deck's declined count depends on that being true.
CREATE TABLE trade_grade (
    cid             TEXT PRIMARY KEY,
    playbook_id     TEXT,                              -- null for the implicit __unplanned__ book
    stage           TEXT NOT NULL DEFAULT 'arm',       -- arm | fire
    evaluated_at    INTEGER NOT NULL,
    results         TEXT NOT NULL,                     -- JSON per-rule verdicts
    required_pass   INTEGER NOT NULL,
    required_total  INTEGER NOT NULL,
    clean           INTEGER NOT NULL
);
CREATE INDEX idx_trade_grade_playbook ON trade_grade (playbook_id, evaluated_at);
