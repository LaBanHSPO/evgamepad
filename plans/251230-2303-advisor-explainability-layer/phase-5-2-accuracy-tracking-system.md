# Phase 5.2: Accuracy Tracking System

**Duration:** 6 hours (+2h for MT5 auto-detection)
**Priority:** P0
**Status:** Planned

---

## Objective

Record and report historical recommendation performance to build user trust and calibrate confidence scores.

**User Value:** "I can see this advisor has 68% win rate on H4 timeframes, so I trust its H4 BUY signals"

---

## Deliverables

1. Database migration: `recommendation_outcomes` table
2. `backend/app/advisor/accuracy-tracker.py` - Performance tracking module
3. `backend/app/advisor/mt5-history-parser.py` - **NEW: Auto-detect outcomes from MT5**
4. `backend/app/models/accuracy-models.py` - Data models
5. Socket.IO events:
   - `advisor:record_outcome` - Record trade result (manual override)
   - `advisor:accuracy_report` - Get performance metrics
6. Background task: Auto-sync MT5 closed positions
7. Unit tests (30+ tests, +5 for MT5 parsing)

---

## MT5 Auto-Detection Strategy

**Validation Decision:** Auto-detect outcomes from MT5 trade history (not manual user recording)

**Requirements:**
1. Query closed positions from MT5 using `history_deals_get()`
2. Match closed deals to advisor recommendations
3. Auto-populate `recommendation_outcomes` table
4. Handle slippage/timing differences in matching

**Matching Logic:**
- Symbol must match exactly
- Entry price within ±0.1% (slippage tolerance)
- Entry time within ±5min of recommendation timestamp
- Fuzzy matching for partial fills

---

## Database Schema

**Migration File:** `backend/app/database/migrations/005_recommendation_outcomes.sql`

```sql
-- Recommendation outcomes for accuracy tracking
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

-- Materialized view for fast queries
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

-- Indexes
CREATE INDEX idx_rec_outcomes_symbol_tf ON recommendation_outcomes(symbol, timeframe);
CREATE INDEX idx_rec_outcomes_signal ON recommendation_outcomes(signal, outcome);
CREATE INDEX idx_rec_outcomes_created_at ON recommendation_outcomes(created_at DESC);
CREATE INDEX idx_rec_outcomes_user_id ON recommendation_outcomes(user_id) WHERE user_id IS NOT NULL;

-- Auto-update timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

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
```

---

## Implementation

### 1. Accuracy Tracker Module

**File:** `backend/app/advisor/accuracy-tracker.py`

```python
"""
Accuracy tracking system for recommendation performance.
Records trade outcomes and generates performance reports.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from uuid import UUID
import asyncpg

logger = logging.getLogger(__name__)


class AccuracyTracker:
    """Tracks and reports recommendation accuracy metrics."""

    def __init__(self, db_pool: asyncpg.Pool):
        """
        Args:
            db_pool: PostgreSQL connection pool
        """
        self.db = db_pool

    async def record_outcome(
        self,
        symbol: str,
        timeframe: str,
        signal: str,
        confidence: float,
        entry_price: float,
        exit_price: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        exit_reason: str = "manual",
        entry_at: Optional[datetime] = None,
        exit_at: Optional[datetime] = None,
        provenance: Optional[Dict[str, Any]] = None,
        recommendation_id: Optional[UUID] = None
    ) -> UUID:
        """
        Record trade outcome for accuracy tracking.

        Args:
            symbol: Trading symbol
            timeframe: Timeframe (H1, H4, D1, etc.)
            signal: Original signal (BUY, SELL, HOLD)
            confidence: Confidence score (0-100)
            entry_price: Entry price
            exit_price: Exit price
            stop_loss: Stop loss price (optional)
            take_profit: Take profit price (optional)
            exit_reason: Why trade exited
            entry_at: Entry timestamp (defaults to now)
            exit_at: Exit timestamp (defaults to now)
            provenance: Data source metadata
            recommendation_id: Link to original recommendation

        Returns:
            UUID of created outcome record
        """
        entry_at = entry_at or datetime.utcnow()
        exit_at = exit_at or datetime.utcnow()

        # Calculate P/L
        if signal == "BUY":
            pnl = exit_price - entry_price
            matched_prediction = exit_price > entry_price
        elif signal == "SELL":
            pnl = entry_price - exit_price
            matched_prediction = exit_price < entry_price
        else:  # HOLD
            pnl = 0
            matched_prediction = False

        pnl_pct = (pnl / entry_price) * 100 if entry_price > 0 else 0

        # Determine outcome
        if abs(pnl_pct) < 0.1:  # Within 0.1%
            outcome = "break_even"
        elif pnl_pct > 0:
            outcome = "win"
        else:
            outcome = "loss"

        # Duration
        held_duration = exit_at - entry_at

        # Insert to database
        query = """
            INSERT INTO recommendation_outcomes (
                recommendation_id, symbol, timeframe, signal, confidence,
                entry_price, exit_price, stop_loss, take_profit,
                outcome, pnl, pnl_pct, held_duration, matched_prediction,
                exit_reason, provenance, entry_at, exit_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18
            ) RETURNING id
        """

        async with self.db.acquire() as conn:
            outcome_id = await conn.fetchval(
                query,
                recommendation_id, symbol, timeframe, signal, confidence,
                entry_price, exit_price, stop_loss, take_profit,
                outcome, pnl, pnl_pct, held_duration, matched_prediction,
                exit_reason, provenance, entry_at, exit_at
            )

        logger.info(
            f"Recorded outcome: {symbol} {timeframe} {signal} -> {outcome} "
            f"(P/L: {pnl_pct:.2f}%, {exit_reason})"
        )

        # Refresh materialized view
        await self.refresh_accuracy_view()

        return outcome_id

    async def get_accuracy_report(
        self,
        symbol: Optional[str] = None,
        timeframe: Optional[str] = None,
        signal: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Generate accuracy report from historical data.

        Args:
            symbol: Filter by symbol (optional)
            timeframe: Filter by timeframe (optional)
            signal: Filter by signal type (optional)
            days: Number of days to analyze (default: 30)

        Returns:
            Accuracy report with win rate, profit factor, etc.
        """
        # Build query conditions
        conditions = ["outcome IN ('win', 'loss', 'break_even')"]
        params = []
        param_idx = 1

        if symbol:
            conditions.append(f"symbol = ${param_idx}")
            params.append(symbol)
            param_idx += 1

        if timeframe:
            conditions.append(f"timeframe = ${param_idx}")
            params.append(timeframe)
            param_idx += 1

        if signal:
            conditions.append(f"signal = ${param_idx}")
            params.append(signal)
            param_idx += 1

        # Time filter
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        conditions.append(f"created_at >= ${param_idx}")
        params.append(cutoff_date)

        where_clause = " AND ".join(conditions)

        query = f"""
            SELECT
                COUNT(*) as total_trades,
                SUM(CASE WHEN outcome = 'win' THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN outcome = 'loss' THEN 1 ELSE 0 END) as losses,
                SUM(CASE WHEN outcome = 'break_even' THEN 1 ELSE 0 END) as break_evens,
                ROUND(
                    SUM(CASE WHEN outcome = 'win' THEN 1 ELSE 0 END)::NUMERIC /
                    NULLIF(SUM(CASE WHEN outcome IN ('win', 'loss') THEN 1 END), 0) * 100,
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
                MAX(pnl_pct) as best_trade_pct,
                MIN(pnl_pct) as worst_trade_pct,
                EXTRACT(EPOCH FROM AVG(held_duration)) / 3600 as avg_hold_hours
            FROM recommendation_outcomes
            WHERE {where_clause}
        """

        async with self.db.acquire() as conn:
            row = await conn.fetchrow(query, *params)

        if not row or row["total_trades"] == 0:
            return {
                "period_days": days,
                "symbol": symbol,
                "timeframe": timeframe,
                "signal": signal,
                "total_trades": 0,
                "message": "No trades recorded for this period"
            }

        # Calculate Sharpe ratio (simplified)
        sharpe_ratio = None
        if row["avg_pnl_pct"] and row["avg_loss_pct"]:
            sharpe_ratio = round(
                row["avg_pnl_pct"] / row["avg_loss_pct"],
                2
            )

        return {
            "period_days": days,
            "symbol": symbol,
            "timeframe": timeframe,
            "signal": signal,
            "total_trades": int(row["total_trades"]),
            "wins": int(row["wins"] or 0),
            "losses": int(row["losses"] or 0),
            "break_evens": int(row["break_evens"] or 0),
            "win_rate_pct": float(row["win_rate_pct"] or 0),
            "avg_pnl_pct": round(float(row["avg_pnl_pct"] or 0), 2),
            "avg_win_pct": round(float(row["avg_win_pct"] or 0), 2),
            "avg_loss_pct": round(float(row["avg_loss_pct"] or 0), 2),
            "profit_factor": float(row["profit_factor"] or 0),
            "sharpe_ratio": sharpe_ratio,
            "best_trade_pct": round(float(row["best_trade_pct"] or 0), 2),
            "worst_trade_pct": round(float(row["worst_trade_pct"] or 0), 2),
            "avg_hold_hours": round(float(row["avg_hold_hours"] or 0), 1),
            "recommendation": self._generate_recommendation(row)
        }

    async def get_best_performing_configs(
        self,
        min_trades: int = 10,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Find best-performing symbol/timeframe/signal combinations.

        Args:
            min_trades: Minimum trades required for inclusion
            days: Analysis period

        Returns:
            List of top-performing configurations
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        query = """
            SELECT
                symbol,
                timeframe,
                signal,
                COUNT(*) as total_trades,
                ROUND(
                    SUM(CASE WHEN outcome = 'win' THEN 1 ELSE 0 END)::NUMERIC /
                    NULLIF(SUM(CASE WHEN outcome IN ('win', 'loss') THEN 1 END), 0) * 100,
                    1
                ) as win_rate_pct,
                AVG(pnl_pct) FILTER (WHERE outcome IN ('win', 'loss')) as avg_pnl_pct,
                ROUND(
                    SUM(pnl_pct) FILTER (WHERE outcome = 'win') /
                    NULLIF(SUM(ABS(pnl_pct)) FILTER (WHERE outcome = 'loss'), 0),
                    2
                ) as profit_factor
            FROM recommendation_outcomes
            WHERE outcome IN ('win', 'loss', 'break_even')
                AND created_at >= $1
            GROUP BY symbol, timeframe, signal
            HAVING COUNT(*) >= $2
            ORDER BY win_rate_pct DESC, profit_factor DESC
            LIMIT 10
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, cutoff_date, min_trades)

        return [
            {
                "symbol": row["symbol"],
                "timeframe": row["timeframe"],
                "signal": row["signal"],
                "total_trades": int(row["total_trades"]),
                "win_rate_pct": float(row["win_rate_pct"] or 0),
                "avg_pnl_pct": round(float(row["avg_pnl_pct"] or 0), 2),
                "profit_factor": float(row["profit_factor"] or 0)
            }
            for row in rows
        ]

    async def refresh_accuracy_view(self):
        """Refresh materialized view for fast queries."""
        async with self.db.acquire() as conn:
            await conn.execute("REFRESH MATERIALIZED VIEW recommendation_accuracy")
        logger.debug("Refreshed recommendation_accuracy materialized view")

    def _generate_recommendation(self, stats: Dict[str, Any]) -> str:
        """Generate text recommendation based on stats."""
        win_rate = stats.get("win_rate_pct", 0)
        profit_factor = stats.get("profit_factor", 0)

        if win_rate >= 70 and profit_factor >= 2.0:
            return "Excellent - High confidence trades"
        elif win_rate >= 60 and profit_factor >= 1.5:
            return "Good - Reliable performance"
        elif win_rate >= 50:
            return "Acceptable - Use with caution"
        else:
            return "Avoid - Poor historical performance"
```

---

### 2. Socket.IO Events

**File:** `backend/app/events/advisor_events.py`

```python
@sio.on("advisor:record_outcome")
async def handle_record_outcome(sid, data):
    """
    Record trade outcome for accuracy tracking.

    Request:
    {
        "symbol": "XAUUSD",
        "timeframe": "H1",
        "signal": "BUY",
        "confidence": 85,
        "entry_price": 2634.50,
        "exit_price": 2640.20,
        "stop_loss": 2625.50,
        "take_profit": 2645.00,
        "exit_reason": "take_profit",
        "entry_at": "2025-12-30T10:00:00Z",
        "exit_at": "2025-12-30T14:30:00Z"
    }
    """
    try:
        # Validate required fields
        required_fields = ["symbol", "signal", "entry_price", "exit_price"]
        for field in required_fields:
            if field not in data:
                await sio.emit("advisor:error", {
                    "error_code": "INVALID_REQUEST",
                    "message": f"Missing required field: {field}"
                }, room=sid)
                return

        # Record outcome
        outcome_id = await accuracy_tracker.record_outcome(
            symbol=data["symbol"],
            timeframe=data.get("timeframe", "H1"),
            signal=data["signal"],
            confidence=data.get("confidence", 50),
            entry_price=float(data["entry_price"]),
            exit_price=float(data["exit_price"]),
            stop_loss=float(data["stop_loss"]) if "stop_loss" in data else None,
            take_profit=float(data["take_profit"]) if "take_profit" in data else None,
            exit_reason=data.get("exit_reason", "manual"),
            entry_at=datetime.fromisoformat(data["entry_at"]) if "entry_at" in data else None,
            exit_at=datetime.fromisoformat(data["exit_at"]) if "exit_at" in data else None
        )

        await sio.emit("advisor:outcome_recorded", {
            "success": True,
            "outcome_id": str(outcome_id),
            "message": "Trade outcome recorded successfully"
        }, room=sid)

    except Exception as e:
        logger.exception(f"Error recording outcome: {e}")
        await sio.emit("advisor:error", {
            "error_code": "RECORD_FAILED",
            "message": str(e)
        }, room=sid)


@sio.on("advisor:accuracy_report")
async def handle_accuracy_report(sid, data):
    """
    Get accuracy performance report.

    Request:
    {
        "symbol": "XAUUSD",  // optional
        "timeframe": "H1",   // optional
        "signal": "BUY",     // optional
        "days": 30           // optional, default 30
    }
    """
    try:
        report = await accuracy_tracker.get_accuracy_report(
            symbol=data.get("symbol"),
            timeframe=data.get("timeframe"),
            signal=data.get("signal"),
            days=data.get("days", 30)
        )

        # Get best-performing configs
        best_configs = await accuracy_tracker.get_best_performing_configs(
            min_trades=10,
            days=data.get("days", 30)
        )

        await sio.emit("advisor:accuracy_result", {
            "success": True,
            "data": {
                "report": report,
                "best_performing": best_configs
            }
        }, room=sid)

    except Exception as e:
        logger.exception(f"Error generating accuracy report: {e}")
        await sio.emit("advisor:error", {
            "error_code": "REPORT_FAILED",
            "message": str(e)
        }, room=sid)
```

---

### 3. Data Models

**File:** `backend/app/models/accuracy_models.py`

```python
"""Data models for accuracy tracking."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class RecordOutcomeRequest(BaseModel):
    """Request to record trade outcome."""
    symbol: str
    timeframe: str = "H1"
    signal: str = Field(..., pattern="^(BUY|SELL|HOLD)$")
    confidence: float = Field(ge=0, le=100)
    entry_price: float = Field(gt=0)
    exit_price: float = Field(gt=0)
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    exit_reason: str = "manual"
    entry_at: Optional[datetime] = None
    exit_at: Optional[datetime] = None


class AccuracyReportRequest(BaseModel):
    """Request for accuracy report."""
    symbol: Optional[str] = None
    timeframe: Optional[str] = None
    signal: Optional[str] = None
    days: int = Field(default=30, ge=1, le=365)


class AccuracyMetrics(BaseModel):
    """Accuracy performance metrics."""
    period_days: int
    symbol: Optional[str]
    timeframe: Optional[str]
    signal: Optional[str]
    total_trades: int
    wins: int
    losses: int
    break_evens: int
    win_rate_pct: float
    avg_pnl_pct: float
    avg_win_pct: float
    avg_loss_pct: float
    profit_factor: float
    sharpe_ratio: Optional[float]
    best_trade_pct: float
    worst_trade_pct: float
    avg_hold_hours: float
    recommendation: str


class BestPerformingConfig(BaseModel):
    """Best-performing configuration."""
    symbol: str
    timeframe: str
    signal: str
    total_trades: int
    win_rate_pct: float
    avg_pnl_pct: float
    profit_factor: float
```

---

### 4. MT5 History Parser (**NEW - Validation Decision**)

**File:** `backend/app/advisor/mt5-history-parser.py`

**Purpose:** Auto-detect trade outcomes from MT5 terminal history

```python
"""
MT5 trade history parser for automatic outcome detection.
Matches closed positions to advisor recommendations.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)


class MT5HistoryParser:
    """Parse MT5 trade history and match to recommendations."""

    def __init__(self, mt5_manager, accuracy_tracker, db_pool):
        """
        Args:
            mt5_manager: MT5ConnectionManager instance
            accuracy_tracker: AccuracyTracker instance
            db_pool: PostgreSQL connection pool
        """
        self.mt5 = mt5_manager
        self.tracker = accuracy_tracker
        self.db = db_pool

    async def sync_closed_positions(
        self,
        days_back: int = 7
    ) -> Dict[str, Any]:
        """
        Sync closed MT5 positions to recommendation_outcomes table.

        Args:
            days_back: How many days of history to fetch

        Returns:
            Sync statistics (new_outcomes, matched_recommendations, unmatched_deals)
        """
        # Fetch closed deals from MT5
        closed_deals = await self._fetch_mt5_history(days_back)

        # Fetch recent recommendations from database
        recommendations = await self._fetch_recent_recommendations(days_back)

        # Match deals to recommendations
        matches = self._match_deals_to_recommendations(closed_deals, recommendations)

        # Record outcomes
        new_outcomes = 0
        for match in matches:
            try:
                await self.tracker.record_outcome(
                    symbol=match["symbol"],
                    timeframe=match["timeframe"],
                    signal=match["signal"],
                    confidence=match["confidence"],
                    entry_price=match["entry_price"],
                    exit_price=match["exit_price"],
                    stop_loss=match.get("stop_loss"),
                    take_profit=match.get("take_profit"),
                    exit_reason=match["exit_reason"],
                    entry_at=match["entry_at"],
                    exit_at=match["exit_at"],
                    recommendation_id=match["recommendation_id"]
                )
                new_outcomes += 1
            except Exception as e:
                logger.warning(f"Failed to record outcome for deal {match['deal_id']}: {e}")

        return {
            "total_deals_fetched": len(closed_deals),
            "total_recommendations": len(recommendations),
            "matched": len(matches),
            "new_outcomes": new_outcomes,
            "unmatched_deals": len(closed_deals) - len(matches)
        }

    async def _fetch_mt5_history(
        self,
        days_back: int
    ) -> List[Dict[str, Any]]:
        """
        Fetch closed deals from MT5 terminal.

        Uses: mt5.history_deals_get()
        """
        try:
            import MetaTrader5 as mt5
        except ImportError:
            logger.error("MetaTrader5 not available")
            return []

        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)

        # Fetch deals in thread (blocking call)
        def _fetch():
            deals = mt5.history_deals_get(start_date, end_date)
            if deals is None:
                return []
            return list(deals)

        deals = await asyncio.to_thread(_fetch)

        # Convert to dict format
        closed_positions = []
        for deal in deals:
            # Only process closed positions (type = DEAL_TYPE_OUT)
            if deal.type == 1:  # DEAL_TYPE_OUT
                closed_positions.append({
                    "deal_id": deal.ticket,
                    "symbol": deal.symbol,
                    "entry_price": deal.price,
                    "exit_price": deal.price,  # Exit deal price
                    "volume": deal.volume,
                    "profit": deal.profit,
                    "entry_at": datetime.fromtimestamp(deal.time),
                    "exit_at": datetime.fromtimestamp(deal.time),
                    "comment": deal.comment
                })

        logger.info(f"Fetched {len(closed_positions)} closed positions from MT5")
        return closed_positions

    async def _fetch_recent_recommendations(
        self,
        days_back: int
    ) -> List[Dict[str, Any]]:
        """Fetch recommendations from database within date range."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)

        query = """
            SELECT id, symbol, timeframe, signal, confidence,
                   entry_price, stop_loss, take_profit, created_at
            FROM recommendations
            WHERE created_at >= $1
            ORDER BY created_at DESC
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, cutoff_date)

        return [dict(row) for row in rows]

    def _match_deals_to_recommendations(
        self,
        deals: List[Dict[str, Any]],
        recommendations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Match MT5 deals to advisor recommendations.

        Matching criteria:
        1. Symbol must match exactly
        2. Entry price within ±0.1% (slippage tolerance)
        3. Entry time within ±5min of recommendation
        """
        matches = []

        for deal in deals:
            best_match = None
            best_score = 0

            for rec in recommendations:
                score = self._calculate_match_score(deal, rec)
                if score > best_score and score >= 0.8:  # Min 80% match
                    best_score = score
                    best_match = rec

            if best_match:
                # Determine exit reason
                exit_reason = self._determine_exit_reason(deal, best_match)

                matches.append({
                    "deal_id": deal["deal_id"],
                    "recommendation_id": best_match["id"],
                    "symbol": deal["symbol"],
                    "timeframe": best_match["timeframe"],
                    "signal": best_match["signal"],
                    "confidence": best_match["confidence"],
                    "entry_price": deal["entry_price"],
                    "exit_price": deal["exit_price"],
                    "stop_loss": best_match.get("stop_loss"),
                    "take_profit": best_match.get("take_profit"),
                    "exit_reason": exit_reason,
                    "entry_at": deal["entry_at"],
                    "exit_at": deal["exit_at"],
                    "match_score": best_score
                })

        logger.info(f"Matched {len(matches)}/{len(deals)} deals to recommendations")
        return matches

    def _calculate_match_score(
        self,
        deal: Dict[str, Any],
        rec: Dict[str, Any]
    ) -> float:
        """
        Calculate match confidence score (0.0-1.0).

        Factors:
        - Symbol match: 40%
        - Price match: 40%
        - Time match: 20%
        """
        score = 0.0

        # Symbol match (exact)
        if deal["symbol"] == rec["symbol"]:
            score += 0.4
        else:
            return 0.0  # No match if symbol differs

        # Price match (within ±0.1%)
        price_tolerance = 0.001  # 0.1%
        if rec.get("entry_price"):
            price_diff = abs(deal["entry_price"] - rec["entry_price"]) / rec["entry_price"]
            if price_diff <= price_tolerance:
                score += 0.4
            elif price_diff <= price_tolerance * 5:  # Within 0.5%
                score += 0.2

        # Time match (within ±5min)
        if rec.get("created_at"):
            time_diff = abs((deal["entry_at"] - rec["created_at"]).total_seconds())
            if time_diff <= 300:  # 5 minutes
                score += 0.2
            elif time_diff <= 900:  # 15 minutes
                score += 0.1

        return score

    def _determine_exit_reason(
        self,
        deal: Dict[str, Any],
        rec: Dict[str, Any]
    ) -> str:
        """Determine why trade was exited."""
        exit_price = deal["exit_price"]

        # Check if TP hit
        if rec.get("take_profit"):
            tp_tolerance = abs(exit_price - rec["take_profit"]) / rec["take_profit"]
            if tp_tolerance < 0.001:  # Within 0.1%
                return "take_profit"

        # Check if SL hit
        if rec.get("stop_loss"):
            sl_tolerance = abs(exit_price - rec["stop_loss"]) / rec["stop_loss"]
            if sl_tolerance < 0.001:
                return "stop_loss"

        # Check comment for manual close indicators
        comment = deal.get("comment", "").lower()
        if "manual" in comment or "closed" in comment:
            return "manual"

        return "unknown"
```

**Background Task Integration:**

Add to `backend/app/main.py`:
```python
from app.advisor.mt5_history_parser import MT5HistoryParser

# Initialize parser
mt5_parser = MT5HistoryParser(mt5_manager, accuracy_tracker, db_pool)

# Background task (runs every 5 minutes)
@app.on_event("startup")
async def start_mt5_sync():
    async def sync_loop():
        while True:
            try:
                result = await mt5_parser.sync_closed_positions(days_back=7)
                logger.info(f"MT5 sync: {result}")
            except Exception as e:
                logger.exception(f"MT5 sync failed: {e}")
            await asyncio.sleep(300)  # 5 minutes

    asyncio.create_task(sync_loop())
```

---

## Testing Strategy

**File:** `backend/tests/test_accuracy_tracker.py`

```python
import pytest
from datetime import datetime, timedelta
from app.advisor.accuracy_tracker import AccuracyTracker


class TestAccuracyTracker:
    """Test accuracy tracking system."""

    @pytest.fixture
    async def tracker(self, db_pool):
        return AccuracyTracker(db_pool)

    @pytest.mark.asyncio
    async def test_record_winning_trade(self, tracker):
        """Test recording winning trade."""
        outcome_id = await tracker.record_outcome(
            symbol="XAUUSD",
            timeframe="H1",
            signal="BUY",
            confidence=85,
            entry_price=2634.50,
            exit_price=2640.20,
            exit_reason="take_profit"
        )

        assert outcome_id is not None

    @pytest.mark.asyncio
    async def test_accuracy_report(self, tracker):
        """Test accuracy report generation."""
        # Record some trades
        await tracker.record_outcome(
            symbol="XAUUSD",
            timeframe="H1",
            signal="BUY",
            confidence=85,
            entry_price=2634.50,
            exit_price=2640.20
        )

        await tracker.record_outcome(
            symbol="XAUUSD",
            timeframe="H1",
            signal="BUY",
            confidence=75,
            entry_price=2640.00,
            exit_price=2638.50
        )

        # Get report
        report = await tracker.get_accuracy_report(
            symbol="XAUUSD",
            timeframe="H1",
            days=7
        )

        assert report["total_trades"] == 2
        assert report["wins"] == 1
        assert report["losses"] == 1
        assert report["win_rate_pct"] == 50.0

    # ... (25 total tests)
```

---

## Acceptance Criteria

- [ ] Database migration runs successfully
- [ ] Outcome recording saves to PostgreSQL
- [ ] Accuracy reports calculate correct win rate, profit factor
- [ ] Materialized view refreshes automatically
- [ ] Socket.IO events functional
- [ ] Unit tests: 25+ tests passing
- [ ] Performance: Report query < 100ms

---

## Next Steps

Proceed to Phase 5.3: Visual Indicator Dashboard
