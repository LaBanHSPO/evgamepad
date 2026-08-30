-- Phase 2 core: cid reservation, sessions + equity, trade plan, position events,
-- closed trades, and frozen tape. Later phases own their own migrations; nothing
-- here belongs to playbook, voice, tilt, replay, or score.

-- cid reservation. Written PENDING before the order leaves the process, so a
-- duplicate or a retry after a reboot collides on the primary key instead of
-- opening a second position.
CREATE TABLE cid_ledger (
    cid          TEXT PRIMARY KEY,
    kind         TEXT NOT NULL CHECK (kind IN ('open','close','modify','panic')),
    state        TEXT NOT NULL CHECK (state IN ('pending','sent','acked','rejected')),
    sym          TEXT,
    reserved_at  INTEGER NOT NULL,
    resolved_at  INTEGER,
    order_id     INTEGER,
    position_id  INTEGER,
    reject_reason TEXT
);
CREATE INDEX cid_ledger_state ON cid_ledger (state, reserved_at);

-- One evening. Equity comes from cTrader at open and close; balance is never
-- re-derived from summed fills.
CREATE TABLE session (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    trading_day    TEXT NOT NULL UNIQUE,   -- YYYY-MM-DD in the configured IANA zone
    tz             TEXT NOT NULL,
    opened_at      INTEGER NOT NULL,
    closed_at      INTEGER,
    equity_open    REAL,
    equity_close   REAL,
    balance_open   REAL,
    balance_close  REAL,
    currency       TEXT NOT NULL DEFAULT 'USD'
);

-- Equity series through the evening, for phase 6's deck.
CREATE TABLE session_equity (
    session_id  INTEGER NOT NULL REFERENCES session(id) ON DELETE CASCADE,
    ts          INTEGER NOT NULL,
    equity      REAL NOT NULL,
    balance     REAL NOT NULL,
    open_pnl    REAL NOT NULL DEFAULT 0,
    PRIMARY KEY (session_id, ts)
);

-- Snapshot at FIRE: what was intended, before the market answered. Immutable.
-- The r_usd columns record the conversion inputs so the number stays auditable
-- long after the rate moved -- see apps/gateway/risk/r.py.
CREATE TABLE trade_plan (
    cid                TEXT PRIMARY KEY REFERENCES cid_ledger(cid),
    session_id         INTEGER REFERENCES session(id) ON DELETE SET NULL,
    created_at         INTEGER NOT NULL,
    sym                TEXT NOT NULL,
    side               TEXT NOT NULL CHECK (side IN ('buy','sell')),
    timeframe          TEXT,
    market_session     TEXT,
    playbook_id        TEXT,
    setup              TEXT,
    lots               REAL NOT NULL,
    protocol_volume    INTEGER NOT NULL,
    planned_entry      REAL,
    relative_sl        INTEGER,
    relative_tp        INTEGER,
    planned_sl         REAL,
    planned_tp         REAL,
    planned_rr         REAL,
    r_usd              REAL,
    r_source           TEXT NOT NULL CHECK (r_source IN ('stop','r_unit_fallback')),
    r_rate             REAL,
    r_rate_chain       TEXT,
    r_rate_ts          INTEGER,
    armed_at           INTEGER,
    time_to_fire_ms    INTEGER
);
CREATE INDEX trade_plan_session ON trade_plan (session_id, created_at);

-- Append-only. Every broker fact about a position, in the order it arrived.
CREATE TABLE position_event (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    position_id  INTEGER NOT NULL,
    cid          TEXT REFERENCES cid_ledger(cid),
    ts           INTEGER NOT NULL,
    kind         TEXT NOT NULL CHECK (kind IN ('fill','amend','sl_hit','tp_hit','close','reject')),
    price        REAL,
    lots         REAL,
    sl           REAL,
    tp           REAL,
    detail       TEXT
);
CREATE INDEX position_event_pos ON position_event (position_id, ts);

-- One row per full close. Actual vs plan lives here; phase 6 reads it and never
-- recomputes money from fills.
CREATE TABLE trade_closed (
    position_id      INTEGER PRIMARY KEY,
    cid              TEXT REFERENCES cid_ledger(cid),
    session_id       INTEGER REFERENCES session(id) ON DELETE SET NULL,
    sym              TEXT NOT NULL,
    side             TEXT NOT NULL CHECK (side IN ('buy','sell')),
    lots             REAL NOT NULL,
    opened_at        INTEGER NOT NULL,
    closed_at        INTEGER NOT NULL,
    entry            REAL NOT NULL,
    exit             REAL NOT NULL,
    sl_at_entry      REAL,
    tp_at_entry      REAL,
    sl_at_close      REAL,
    tp_at_close      REAL,
    gross_pnl        REAL NOT NULL,
    commission       REAL NOT NULL DEFAULT 0,
    swap             REAL NOT NULL DEFAULT 0,
    net_pnl          REAL NOT NULL,
    r_usd            REAL NOT NULL,
    r_multiple       REAL NOT NULL,
    mfe              REAL,
    mae              REAL,
    mfe_r            REAL,
    mae_r            REAL,
    exit_reason      TEXT CHECK (exit_reason IN ('manual','sl','tp','panic','broker')),
    adherence        REAL
);
CREATE INDEX trade_closed_session ON trade_closed (session_id, closed_at);
CREATE INDEX trade_closed_sym ON trade_closed (sym, closed_at);

-- One frozen window per trade: [opened_at - pre_roll, closed_at + post_roll].
-- Gzipped columnar 1 Hz bid+ask bars plus denormalised events. A zero-trade
-- evening writes no rows at all.
CREATE TABLE trade_tape (
    position_id  INTEGER PRIMARY KEY,
    cid          TEXT REFERENCES cid_ledger(cid),
    sym          TEXT NOT NULL,
    from_ts      INTEGER NOT NULL,
    to_ts        INTEGER NOT NULL,
    dt_s         INTEGER NOT NULL,
    n            INTEGER NOT NULL,
    digits       INTEGER NOT NULL,
    bars_gz      BLOB NOT NULL,
    events_json  TEXT NOT NULL DEFAULT '[]',
    frozen_at    INTEGER NOT NULL
);
