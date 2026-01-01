-- Migration 003: Create team_members table
-- Description: Team membership tracking
-- Created: 2025-12-31

CREATE TABLE IF NOT EXISTS team_members (
    member_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(team_id) ON DELETE CASCADE,
    user_id VARCHAR(100) NOT NULL,
    username VARCHAR(50) NOT NULL,
    joined_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT unique_user_per_team UNIQUE(team_id, user_id)
);

CREATE INDEX idx_team_members_team ON team_members(team_id);
CREATE INDEX idx_team_members_user ON team_members(user_id);

COMMENT ON TABLE team_members IS 'Members belonging to teams';
COMMENT ON COLUMN team_members.user_id IS 'User identifier (e.g., Discord ID or session ID)';
