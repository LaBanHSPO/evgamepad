-- Migration 006: Create MT5 Account Pool Table
-- Purpose: Manage pool of 10 pre-provisioned MT5 demo accounts
-- Phase: 02 - MT5 Integration Service

CREATE TABLE IF NOT EXISTS mt5_account_pool (
    account_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_number BIGINT NOT NULL UNIQUE,
    broker_server VARCHAR(100) NOT NULL,
    encrypted_password TEXT NOT NULL, -- Encrypted using cryptography.fernet
    status VARCHAR(20) DEFAULT 'available' CHECK (status IN ('available', 'in_use', 'error', 'expired')),
    allocated_to_user_id VARCHAR(100), -- Current user using this account
    allocated_at TIMESTAMP,
    last_health_check TIMESTAMP,
    health_status VARCHAR(20) DEFAULT 'healthy' CHECK (health_status IN ('healthy', 'unhealthy', 'disconnected')),
    expiry_date DATE, -- Demo account expiry date (manual tracking)
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index for fast allocation queries (FOR UPDATE SKIP LOCKED)
CREATE INDEX IF NOT EXISTS idx_account_pool_status ON mt5_account_pool(status) WHERE status = 'available';

-- Index for health check queries
CREATE INDEX IF NOT EXISTS idx_account_pool_health ON mt5_account_pool(last_health_check);

-- Index for user lookup
CREATE INDEX IF NOT EXISTS idx_account_pool_user ON mt5_account_pool(allocated_to_user_id) WHERE allocated_to_user_id IS NOT NULL;

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_mt5_account_pool_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER mt5_account_pool_updated_at
    BEFORE UPDATE ON mt5_account_pool
    FOR EACH ROW
    EXECUTE FUNCTION update_mt5_account_pool_updated_at();
