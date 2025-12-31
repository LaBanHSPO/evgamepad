-- Migration 008: Add MT5 Metadata to Positions Table
-- Purpose: Link positions table to MT5 accounts and enhance position tracking
-- Phase: 02 - MT5 Integration Service

-- Add MT5 account reference
ALTER TABLE positions
ADD COLUMN IF NOT EXISTS account_number BIGINT;

-- Add position type (BUY/SELL)
ALTER TABLE positions
ADD COLUMN IF NOT EXISTS position_type VARCHAR(10) CHECK (position_type IN ('BUY', 'SELL'));

-- Add volume for position sizing
ALTER TABLE positions
ADD COLUMN IF NOT EXISTS volume DECIMAL(10, 2);

-- Add open price for P&L calculation
ALTER TABLE positions
ADD COLUMN IF NOT EXISTS open_price DECIMAL(15, 5);

-- Add close price for realized P&L
ALTER TABLE positions
ADD COLUMN IF NOT EXISTS close_price DECIMAL(15, 5);

-- Add status to track position lifecycle
ALTER TABLE positions
ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'closed'));

-- Index for account-based position queries
CREATE INDEX IF NOT EXISTS idx_positions_account ON positions(account_number) WHERE account_number IS NOT NULL;

-- Index for open positions (5s sync task)
CREATE INDEX IF NOT EXISTS idx_positions_open ON positions(status, session_id) WHERE status = 'open';

-- Index for ticket + session (fast position lookup during sync)
CREATE INDEX IF NOT EXISTS idx_positions_ticket_session ON positions(ticket, session_id) WHERE status = 'open';

-- Update materialized view to include new fields (refresh will pick up schema changes)
COMMENT ON MATERIALIZED VIEW team_leaderboard IS 'Phase 01 materialized view - refreshed every 30s by leaderboard_refresh_task. Phase 02: Enhanced with MT5 position data.';
