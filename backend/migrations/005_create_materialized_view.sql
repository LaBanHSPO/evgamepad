-- Migration 005: Create team_leaderboard materialized view
-- Description: Materialized view for leaderboard Tier 2 caching
-- Created: 2025-12-31

CREATE MATERIALIZED VIEW IF NOT EXISTS team_leaderboard AS
SELECT
    t.session_id,
    t.team_id,
    t.team_name,
    COALESCE(SUM(p.pnl), 0) as total_pnl,
    COUNT(DISTINCT tm.user_id) as team_size,
    NOW() as computed_at
FROM teams t
JOIN team_members tm ON t.team_id = tm.team_id
LEFT JOIN positions p ON tm.user_id = p.user_id
    AND p.session_id = t.session_id
    AND p.closed_at IS NULL  -- Only open positions
GROUP BY t.session_id, t.team_id, t.team_name;

CREATE UNIQUE INDEX idx_team_leaderboard_pk ON team_leaderboard(session_id, team_id);
CREATE INDEX idx_team_leaderboard_pnl ON team_leaderboard(session_id, total_pnl DESC);

COMMENT ON MATERIALIZED VIEW team_leaderboard IS 'Tier 2 cache for leaderboard (refreshed every 30s)';
COMMENT ON COLUMN team_leaderboard.total_pnl IS 'Aggregated P&L from open positions';
