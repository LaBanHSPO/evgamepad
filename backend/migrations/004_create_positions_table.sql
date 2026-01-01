-- Migration 004: Create positions table
-- Description: Trading positions tracking for P&L calculation
-- Created: 2025-12-31

CREATE TABLE IF NOT EXISTS positions (
    position_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES game_sessions(session_id) ON DELETE CASCADE,
    user_id VARCHAR(100) NOT NULL,
    ticket BIGINT NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    type VARCHAR(10) NOT NULL,  -- buy, sell
    volume DECIMAL(10,2) NOT NULL,
    open_price DECIMAL(15,5) NOT NULL,
    close_price DECIMAL(15,5),
    sl DECIMAL(15,5),
    tp DECIMAL(15,5),
    pnl DECIMAL(15,2) DEFAULT 0,
    opened_at TIMESTAMP DEFAULT NOW(),
    closed_at TIMESTAMP,

    CONSTRAINT unique_ticket_per_session UNIQUE(session_id, ticket)
);

CREATE INDEX idx_positions_session_user ON positions(session_id, user_id);
CREATE INDEX idx_positions_open ON positions(session_id, closed_at) WHERE closed_at IS NULL;
CREATE INDEX idx_positions_ticket ON positions(ticket);

COMMENT ON TABLE positions IS 'Trading positions for leaderboard P&L calculation';
COMMENT ON COLUMN positions.pnl IS 'Profit/Loss for this position (updated on close or sync)';
COMMENT ON COLUMN positions.closed_at IS 'NULL for open positions, timestamp for closed positions';
