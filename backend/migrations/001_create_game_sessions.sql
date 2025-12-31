-- Migration 001: Create game_sessions table
-- Description: Game session management for multi-player trading
-- Created: 2025-12-31

CREATE TABLE IF NOT EXISTS game_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) UNIQUE NOT NULL,
    creator_id VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'waiting',  -- waiting, active, completed
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    max_team_size INT DEFAULT 6,
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT valid_status CHECK (status IN ('waiting', 'active', 'completed'))
);

CREATE INDEX idx_game_sessions_status ON game_sessions(status);
CREATE INDEX idx_game_sessions_name ON game_sessions(name);

COMMENT ON TABLE game_sessions IS 'Game sessions for multi-player trading competitions';
COMMENT ON COLUMN game_sessions.status IS 'Session status: waiting (lobby), active (in progress), completed (finished)';
