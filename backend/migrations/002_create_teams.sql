-- Migration 002: Create teams table
-- Description: Team management within game sessions
-- Created: 2025-12-31

CREATE TABLE IF NOT EXISTS teams (
    team_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES game_sessions(session_id) ON DELETE CASCADE,
    team_name VARCHAR(50) NOT NULL,
    total_pnl DECIMAL(15,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT unique_team_per_session UNIQUE(session_id, team_name)
);

CREATE INDEX idx_teams_session ON teams(session_id);
CREATE INDEX idx_teams_pnl ON teams(session_id, total_pnl DESC);

COMMENT ON TABLE teams IS 'Teams within game sessions';
COMMENT ON COLUMN teams.total_pnl IS 'Aggregated P&L for all team members';
