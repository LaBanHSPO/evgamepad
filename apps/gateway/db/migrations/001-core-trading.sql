-- Phase 2 core: everything the order path and the journal need on day one, and nothing a later
-- phase owns. Later phases add their own versioned migrations rather than editing this one.

-- The idempotency ledger. A cid is reserved UNIQUE *before* the order is sent, so a retry, a
-- reconnect replay, or a double-fire lands on the same row instead of a second position.
CREATE TABLE cid_reservation (
    cid          TEXT PRIMARY KEY,
    intent       TEXT NOT NULL,               -- open | close | modify | panic
    symbol       TEXT,
    state        TEXT NOT NULL DEFAULT 'pending',  -- pending | acked | rejected
    reason       TEXT,
    order_id     INTEGER,
    position_id  INTEGER,
    created_at   INTEGER NOT NULL,
    updated_at   INTEGER NOT NULL
);
CREATE INDEX idx_cid_state ON cid_reservation (state, created_at);

-- One row per evening. Balance and equity come from the cTrader account at open and close;
-- money is never re-derived from summed fills.
CREATE TABLE session_equity (
    session_id     TEXT PRIMARY KEY,
    timezone       TEXT NOT NULL,
    opened_at      INTEGER NOT NULL,
    closed_at      INTEGER,
    balance_open   REAL,
    equity_open    REAL,
    balance_close  REAL,
    equity_close   REAL
);

-- The plan as it stood at FIRE, including R and the conversion that produced it.
CREATE TABLE trade_plan (
    cid             TEXT PRIMARY KEY REFERENCES cid_reservation (cid),
    session_id      TEXT REFERENCES session_equity (session_id),
    symbol          TEXT NOT NULL,
    side            TEXT NOT NULL,             -- buy | sell
    timeframe       TEXT,
    market_session  TEXT,                      -- asia | london | ny, resolved in the session tz
    playbook_id     TEXT,
    lots            REAL NOT NULL,
    volume          INTEGER NOT NULL,
    planned_entry   REAL,
    relative_sl     INTEGER,                   -- 1/100000 distance, as sent to the broker
    relative_tp     INTEGER,
    planned_sl      REAL,                      -- absolute, for the journal and the deck
    planned_tp      REAL,
    planned_rr      REAL,
    r_usd           REAL NOT NULL,
    r_method        TEXT NOT NULL,             -- stop | fallback
    r_units         REAL NOT NULL,
    r_stop_distance REAL,
    r_rate          REAL,
    r_rate_chain    TEXT,
    r_rate_source   TEXT,
    r_rate_ts       INTEGER,
    armed_at        INTEGER,
    created_at      INTEGER NOT NULL
);
CREATE INDEX idx_trade_plan_session ON trade_plan (session_id, created_at);

-- Append-only. Fills, SL/TP amendments, and closes are recorded as they happen; nothing here is
-- ever updated in place, so the trade's history survives a disagreement with the broker.
CREATE TABLE position_event (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    cid          TEXT,
    position_id  INTEGER,
    kind         TEXT NOT NULL,                -- fill | amend | close | reject
    payload      TEXT NOT NULL,                -- JSON, as received
    ts           INTEGER NOT NULL
);
CREATE INDEX idx_position_event_position ON position_event (position_id, ts);
CREATE INDEX idx_position_event_cid ON position_event (cid, ts);

-- One row per full close. r_multiple is non-null for every closed trade, with or without a stop.
CREATE TABLE trade_closed (
    cid           TEXT PRIMARY KEY REFERENCES trade_plan (cid),
    session_id    TEXT REFERENCES session_equity (session_id),
    position_id   INTEGER NOT NULL,
    symbol        TEXT NOT NULL,
    side          TEXT NOT NULL,
    lots          REAL NOT NULL,
    volume        INTEGER NOT NULL,
    entry_price   REAL,
    exit_price    REAL,
    opened_at     INTEGER,
    closed_at     INTEGER NOT NULL,
    gross_pnl     REAL,
    commission    REAL,
    swap          REAL,
    net_pnl_usd   REAL,
    r_usd         REAL NOT NULL,
    r_multiple    REAL NOT NULL,
    mfe           REAL,
    mae           REAL,
    adherence     REAL
);
CREATE INDEX idx_trade_closed_session ON trade_closed (session_id, closed_at);

-- One row per traded window, written after the post-roll settles. A zero-trade evening writes
-- nothing here at all.
CREATE TABLE trade_tape (
    cid          TEXT PRIMARY KEY REFERENCES trade_plan (cid),
    position_id  INTEGER,
    symbol       TEXT NOT NULL,
    from_ts      INTEGER NOT NULL,
    to_ts        INTEGER NOT NULL,
    dt_s         INTEGER NOT NULL,
    bars         BLOB NOT NULL,                -- gzipped columnar bid/ask OHLC
    events       TEXT NOT NULL,                -- denormalised JSON of the position's events
    mfe          REAL,
    mae          REAL,
    created_at   INTEGER NOT NULL
);
