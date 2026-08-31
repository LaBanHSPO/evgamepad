-- Phase 6: the deck reads what phases 2 and 3 already own. It creates no core table.
--
-- Two additive columns and a set of indices. `session_equity`, `trade_closed`, and
-- `session_process` keep their original owners; taking them over here would mean two phases
-- believing they define the same row.

-- The method tag that was on the chart at entry (phase 4 supplies it; nullable before that).
ALTER TABLE trade_closed ADD COLUMN setup_tag TEXT;

-- Which rules the fire actually satisfied, as JSON, so the deck can show *why* a score is what
-- it is rather than just the fraction.
ALTER TABLE trade_closed ADD COLUMN adherence_detail TEXT;

-- The player's own one-line note. Never written by the desk.
ALTER TABLE session_process ADD COLUMN note TEXT;

-- Cached per-session adherence, recomputed on write; the deck never re-derives it per request.
ALTER TABLE session_process ADD COLUMN adherence_score REAL;

-- The evening's opportunity quality, averaged from the sentinel. A dead tape is a fact about the
-- night, not about the player.
ALTER TABLE session_process ADD COLUMN opportunity_quality REAL;

-- The adherence inputs that only exist at the moment of the fire. Reconstructing them later from
-- config would score the trade against tonight's rules rather than the ones it was taken under.
ALTER TABLE trade_plan ADD COLUMN inside_window INTEGER;
ALTER TABLE trade_plan ADD COLUMN positions_at_fire INTEGER;
ALTER TABLE trade_plan ADD COLUMN seconds_to_high_impact REAL;
ALTER TABLE trade_plan ADD COLUMN max_lots_at_fire REAL;
ALTER TABLE trade_plan ADD COLUMN max_positions_at_fire INTEGER;
ALTER TABLE trade_plan ADD COLUMN setup_tag TEXT;

CREATE INDEX idx_trade_closed_setup ON trade_closed (setup_tag, closed_at);
CREATE INDEX idx_session_equity_opened ON session_equity (opened_at);
