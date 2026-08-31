-- Phase 13: safe preferences, and an audit trail for the destructive operations.
--
-- The boundary this migration exists to hold: **a hard safety invariant is never a database row.**
-- Demo mode, the bind address, the broker credentials, the copilot's hot-path ban and tilt's
-- close-gate ban all live in YAML and env, where they are boot-fails. Anything that can be edited
-- from a browser at runtime belongs here, and nothing here can weaken a safety property.
--
-- `user_setting` is a key/value table on purpose: the *validation* lives in `settings/schema.py`
-- as an explicit allowlist, so adding a row is not the same as adding a setting.

CREATE TABLE user_setting (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL,          -- JSON, so a list of symbols and a boolean share one column
    updated_at  INTEGER NOT NULL
);

-- What a destructive operation did, and nothing about what it touched. A backup, a restore and a
-- delete each leave one row: the action, when, and counts. No secrets, no paths, and — critically
-- for delete-all — no trace of the content that was removed. An audit row that quotes a deleted
-- note has not deleted it.
CREATE TABLE data_operation (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    action      TEXT NOT NULL,          -- backup | restore | delete_all | export
    started_at  INTEGER NOT NULL,
    finished_at INTEGER,
    ok          INTEGER,
    counts      TEXT NOT NULL DEFAULT '{}',   -- JSON: row and file counts only
    note        TEXT                    -- a fixed reason string, never player content
);
CREATE INDEX idx_data_operation_action ON data_operation (action, started_at);
