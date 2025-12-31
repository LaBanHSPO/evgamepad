"""
Accuracy tracking system for recommendation performance.
Records trade outcomes and generates performance reports.

Phase 5.2: Accuracy Tracking System
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
        Initialize accuracy tracker.

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
        recommendation_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None
    ) -> UUID:
        """
        Record trade outcome for accuracy tracking.

        Args:
            symbol: Trading symbol (e.g., XAUUSD)
            timeframe: Timeframe (H1, H4, D1, etc.)
            signal: Original signal (BUY, SELL, HOLD)
            confidence: Confidence score (0-100)
            entry_price: Entry price
            exit_price: Exit price
            stop_loss: Stop loss price (optional)
            take_profit: Take profit price (optional)
            exit_reason: Why trade exited (take_profit, stop_loss, manual, timeout)
            entry_at: Entry timestamp (defaults to now)
            exit_at: Exit timestamp (defaults to now)
            provenance: Data source metadata from recommendation
            recommendation_id: Link to original recommendation
            user_id: User ID for per-user tracking

        Returns:
            UUID of created outcome record
        """
        entry_at = entry_at or datetime.utcnow()
        exit_at = exit_at or datetime.utcnow()

        # Calculate P/L based on signal direction
        if signal == "BUY":
            pnl = exit_price - entry_price
            matched_prediction = exit_price > entry_price
        elif signal == "SELL":
            pnl = entry_price - exit_price
            matched_prediction = exit_price < entry_price
        else:  # HOLD
            pnl = 0
            matched_prediction = False

        # Calculate P/L percentage
        pnl_pct = (pnl / entry_price) * 100 if entry_price > 0 else 0

        # Determine outcome
        if abs(pnl_pct) < 0.1:  # Within 0.1% is break-even
            outcome = "break_even"
        elif pnl_pct > 0:
            outcome = "win"
        else:
            outcome = "loss"

        # Calculate held duration
        held_duration = exit_at - entry_at

        # Insert to database
        query = """
            INSERT INTO recommendation_outcomes (
                recommendation_id, user_id, symbol, timeframe, signal, confidence,
                entry_price, exit_price, stop_loss, take_profit,
                outcome, pnl, pnl_pct, held_duration, matched_prediction,
                exit_reason, provenance, entry_at, exit_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19
            ) RETURNING id
        """

        async with self.db.acquire() as conn:
            outcome_id = await conn.fetchval(
                query,
                recommendation_id, user_id, symbol, timeframe, signal, confidence,
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
        days: int = 30,
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Generate accuracy report from historical data.

        Args:
            symbol: Filter by symbol (optional)
            timeframe: Filter by timeframe (optional)
            signal: Filter by signal type (optional)
            days: Number of days to analyze (default: 30)
            user_id: Filter by user ID (optional)

        Returns:
            Accuracy report with win rate, profit factor, statistics
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

        if user_id:
            conditions.append(f"user_id = ${param_idx}")
            params.append(user_id)
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
        days: int = 30,
        user_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """
        Find best-performing symbol/timeframe/signal combinations.

        Args:
            min_trades: Minimum trades required for inclusion
            days: Analysis period in days
            user_id: Filter by user ID (optional)

        Returns:
            List of top-performing configurations ranked by win rate and profit factor
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Build user filter
        user_filter = ""
        params = [cutoff_date, min_trades]
        if user_id:
            user_filter = "AND user_id = $3"
            params.append(user_id)

        query = f"""
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
                {user_filter}
            GROUP BY symbol, timeframe, signal
            HAVING COUNT(*) >= $2
            ORDER BY win_rate_pct DESC, profit_factor DESC
            LIMIT 10
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, *params)

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
        """
        Generate text recommendation based on statistics.

        Args:
            stats: Dictionary containing win_rate_pct and profit_factor

        Returns:
            Human-readable recommendation string
        """
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
