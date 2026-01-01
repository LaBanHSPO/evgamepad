-- Migration: Recommendation Outcomes for Accuracy Tracking
-- Phase 5.2: Accuracy Tracking System
-- Created: 2025-12-31

-- Recommendation outcomes table
CREATE TABLE IF NOT EXISTS recommendation_outcomes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recommendation_id UUID,  -- Link to recommendations table (optional)
    user_id UUID,  -- Track per-user accuracy (future)

    -- Trade details
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    signal TEXT NOT NULL CHECK (signal IN ('BUY', 'SELL', 'HOLD')),
    confidence NUMERIC(5,2) CHECK (confidence >= 0 AND confidence <= 100),

    -- Prices
    entry_price NUMERIC(20,8) NOT NULL,
    exit_price NUMERIC(20,8),
    stop_loss NUMERIC(20,8),
    take_profit NUMERIC(20,8),

    -- Outcome
    outcome TEXT CHECK (outcome IN ('win', 'loss', 'break_even', 'pending')),
    pnl NUMERIC(20,8),  -- Profit/loss in units
    pnl_pct NUMERIC(6,2),  -- P/L as percentage
    held_duration INTERVAL,
    matched_prediction BOOLEAN,  -- Did price move as predicted?
    exit_reason TEXT CHECK (exit_reason IN ('take_profit', 'stop_loss', 'manual', 'timeout', 'pending')),

    -- Metadata
    provenance JSONB,  -- Data source metadata from recommendation
    notes TEXT,  -- User notes (future)

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    entry_at TIMESTAMPTZ,
    exit_at TIMESTAMPTZ
);

-- Materialized view for fast accuracy queries
CREATE MATERIALIZED VIEW recommendation_accuracy AS
SELECT
    symbol,
    timeframe,
    signal,
    COUNT(*) as total_trades,
    SUM(CASE WHEN outcome = 'win' THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN outcome = 'loss' THEN 1 ELSE 0 END) as losses,
    SUM(CASE WHEN outcome = 'break_even' THEN 1 ELSE 0 END) as break_evens,
    ROUND(
        SUM(CASE WHEN outcome = 'win' THEN 1 ELSE 0 END)::NUMERIC /
        NULLIF(COUNT(CASE WHEN outcome IN ('win', 'loss') THEN 1 END), 0) * 100,
        1
    ) as win_rate_pct,
    AVG(pnl_pct) FILTER (WHERE outcome IN ('win', 'loss')) as avg_pnl_pct,
    AVG(pnl_pct) FILTER (WHERE outcome = 'win') as avg_win_pct,
    AVG(ABS(pnl_pct)) FILTER (WHERE outcome = 'loss') as avg_loss_pct,
    ROUND(
        SUM(pnl_pct) FILTER (WHERE outcome = 'win') /
        NULLIF(SUM(ABS(pnl_pct)) FILTER (WHERE outcome = 'loss'), 0),
        2
    ) as profit_factor,
    EXTRACT(EPOCH FROM AVG(held_duration)) / 3600 as avg_hold_hours,
    MAX(updated_at) as last_updated
FROM recommendation_outcomes
WHERE outcome IN ('win', 'loss', 'break_even')
GROUP BY symbol, timeframe, signal;

-- Indexes for performance
CREATE INDEX idx_rec_outcomes_symbol_tf ON recommendation_outcomes(symbol, timeframe);
CREATE INDEX idx_rec_outcomes_signal ON recommendation_outcomes(signal, outcome);
CREATE INDEX idx_rec_outcomes_created_at ON recommendation_outcomes(created_at DESC);
CREATE INDEX idx_rec_outcomes_user_id ON recommendation_outcomes(user_id) WHERE user_id IS NOT NULL;

-- Auto-update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_recommendation_outcomes_updated_at
    BEFORE UPDATE ON recommendation_outcomes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Refresh function for materialized view
CREATE OR REPLACE FUNCTION refresh_recommendation_accuracy()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW recommendation_accuracy;
END;
$$ LANGUAGE plpgsql;

-- Comments for documentation
COMMENT ON TABLE recommendation_outcomes IS 'Stores trade outcomes for accuracy tracking and performance analysis';
COMMENT ON COLUMN recommendation_outcomes.matched_prediction IS 'Boolean indicating if price moved in predicted direction';
COMMENT ON COLUMN recommendation_outcomes.provenance IS 'JSON metadata containing data source information from original recommendation';
COMMENT ON MATERIALIZED VIEW recommendation_accuracy IS 'Pre-aggregated accuracy metrics by symbol, timeframe, and signal type';
