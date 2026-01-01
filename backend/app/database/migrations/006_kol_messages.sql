-- Migration: KOL Messages Table for Real-time Trading Signals
-- Feature: KOL Updates MVP
-- Created: 2025-12-31

-- KOL messages table with deduplication
CREATE TABLE IF NOT EXISTS kol_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kol_id VARCHAR(100) NOT NULL,           -- KOL identifier (e.g., "trader_pro_vn")
    kol_name VARCHAR(200) NOT NULL,         -- Display name (e.g., "Trader Pro VN")
    message_text TEXT NOT NULL,             -- Raw message content
    message_hash VARCHAR(32) NOT NULL UNIQUE, -- MD5 hash for deduplication
    zalo_message_id VARCHAR(255),           -- Zalo's message ID (if provided)
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB                          -- Additional fields (zalo user ID, source, etc.)
);

-- Indexes for performance
CREATE INDEX idx_kol_messages_received_at ON kol_messages(received_at DESC);
CREATE INDEX idx_kol_messages_kol_id ON kol_messages(kol_id, received_at DESC);
CREATE INDEX idx_kol_messages_hash ON kol_messages(message_hash);

-- Auto-update timestamp trigger (reuse existing function)
CREATE TRIGGER update_kol_messages_updated_at
    BEFORE UPDATE ON kol_messages
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE kol_messages IS 'Stores KOL trading signals received via Zalo webhook with deduplication';
COMMENT ON COLUMN kol_messages.message_hash IS 'MD5 hash of kol_id|timestamp|message for deduplication';
COMMENT ON COLUMN kol_messages.metadata IS 'JSONB metadata containing Zalo user ID, source, and other webhook data';
