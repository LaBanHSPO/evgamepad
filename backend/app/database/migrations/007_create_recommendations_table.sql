-- Migration: Create Recommendations Table
-- Phase 5.2: Accuracy Tracking System support
-- Required for MT5 history parser to match trades against recommendations

CREATE TABLE IF NOT EXISTS recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Core Signal Data
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    signal TEXT NOT NULL CHECK (signal IN ('BUY', 'SELL', 'HOLD')),
    confidence NUMERIC(5,2) CHECK (confidence >= 0 AND confidence <= 100),
    
    -- Price Targets
    entry_price NUMERIC(20,8) NOT NULL,
    stop_loss NUMERIC(20,8),
    take_profit NUMERIC(20,8),
    
    -- Metadata
    user_id UUID,  -- Optional link to user who created/requested it
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'expired', 'cancelled', 'completed')),
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_recommendations_created_at ON recommendations(created_at DESC);
CREATE INDEX idx_recommendations_symbol ON recommendations(symbol);
CREATE INDEX idx_recommendations_status ON recommendations(status);

-- Auto-update timestamp trigger
CREATE TRIGGER update_recommendations_updated_at
    BEFORE UPDATE ON recommendations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE recommendations IS 'Stores trading recommendations/signals for execution and tracking';
