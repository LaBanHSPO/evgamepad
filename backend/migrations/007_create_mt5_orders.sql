-- Migration 007: Create MT5 Orders Table
-- Purpose: Track all MT5 order executions for audit and debugging
-- Phase: 02 - MT5 Integration Service

CREATE TABLE IF NOT EXISTS mt5_orders (
    order_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES game_sessions(session_id) ON DELETE CASCADE,
    user_id VARCHAR(100) NOT NULL,
    account_number BIGINT NOT NULL, -- MT5 account used
    ticket BIGINT, -- MT5 order ticket (null if order failed)
    symbol VARCHAR(20) NOT NULL,
    order_type VARCHAR(10) NOT NULL CHECK (order_type IN ('BUY', 'SELL')),
    volume DECIMAL(10, 2) NOT NULL,
    price DECIMAL(15, 5),
    sl DECIMAL(15, 5),
    tp DECIMAL(15, 5),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'executed', 'failed', 'cancelled')),
    retcode INT, -- MT5 return code
    comment TEXT, -- MT5 response comment
    executed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index for user order history
CREATE INDEX IF NOT EXISTS idx_mt5_orders_user ON mt5_orders(user_id, created_at DESC);

-- Index for session orders
CREATE INDEX IF NOT EXISTS idx_mt5_orders_session ON mt5_orders(session_id, created_at DESC);

-- Index for ticket lookup (for position matching)
CREATE INDEX IF NOT EXISTS idx_mt5_orders_ticket ON mt5_orders(ticket) WHERE ticket IS NOT NULL;

-- Index for account tracking
CREATE INDEX IF NOT EXISTS idx_mt5_orders_account ON mt5_orders(account_number, created_at DESC);
