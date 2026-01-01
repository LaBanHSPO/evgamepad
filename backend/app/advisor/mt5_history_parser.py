"""
MT5 trade history parser for automatic outcome detection.
Matches closed positions to advisor recommendations.

Phase 5.2: Accuracy Tracking System - MT5 Auto-Detection
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from uuid import UUID
import asyncio

logger = logging.getLogger(__name__)


class MT5HistoryParser:
    """Parse MT5 trade history and match to recommendations."""

    def __init__(self, mt5_manager, accuracy_tracker, db_pool):
        """
        Initialize MT5 history parser.

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
            Sync statistics: total_deals_fetched, matched, new_outcomes, unmatched_deals
        """
        logger.info(f"Starting MT5 history sync (last {days_back} days)")

        # Fetch closed deals from MT5
        closed_deals = await self._fetch_mt5_history(days_back)
        logger.debug(f"Fetched {len(closed_deals)} closed deals from MT5")

        # Fetch recent recommendations from database
        recommendations = await self._fetch_recent_recommendations(days_back)
        logger.debug(f"Fetched {len(recommendations)} recommendations from database")

        # Match deals to recommendations
        matches = self._match_deals_to_recommendations(closed_deals, recommendations)
        logger.info(f"Matched {len(matches)}/{len(closed_deals)} deals to recommendations")

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

        result = {
            "total_deals_fetched": len(closed_deals),
            "total_recommendations": len(recommendations),
            "matched": len(matches),
            "new_outcomes": new_outcomes,
            "unmatched_deals": len(closed_deals) - len(matches)
        }

        logger.info(f"MT5 sync completed: {result}")
        return result

    async def _fetch_mt5_history(
        self,
        days_back: int
    ) -> List[Dict[str, Any]]:
        """
        Fetch closed deals from MT5 terminal.

        Uses: mt5.history_deals_get()

        Args:
            days_back: Number of days to fetch history for

        Returns:
            List of closed position dictionaries
        """
        try:
            import MetaTrader5 as mt5
        except ImportError:
            logger.error("MetaTrader5 module not available")
            return []

        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)

        # Fetch deals in thread (blocking call)
        def _fetch():
            try:
                # Initialize MT5 if not already
                if not mt5.initialize():
                    logger.error(f"MT5 initialize failed: {mt5.last_error()}")
                    return []

                # Fetch deal history
                deals = mt5.history_deals_get(start_date, end_date)
                if deals is None:
                    logger.warning(f"No deals returned from MT5: {mt5.last_error()}")
                    return []

                return list(deals)
            except Exception as e:
                logger.exception(f"Error fetching MT5 history: {e}")
                return []

        deals = await asyncio.to_thread(_fetch)

        # Convert to dict format
        closed_positions = []
        for deal in deals:
            # Only process exit deals (type = DEAL_TYPE_OUT = 1)
            # Entry deals are type = DEAL_TYPE_IN = 0
            if deal.type == 1:  # DEAL_TYPE_OUT (exit)
                closed_positions.append({
                    "deal_id": deal.ticket,
                    "symbol": deal.symbol,
                    "entry_price": deal.price,  # Exit price for OUT deal
                    "exit_price": deal.price,
                    "volume": deal.volume,
                    "profit": deal.profit,
                    "entry_at": datetime.fromtimestamp(deal.time),
                    "exit_at": datetime.fromtimestamp(deal.time),
                    "comment": deal.comment if hasattr(deal, 'comment') else ""
                })

        logger.debug(f"Processed {len(closed_positions)} closed positions from {len(deals)} total deals")
        return closed_positions

    async def _fetch_recent_recommendations(
        self,
        days_back: int
    ) -> List[Dict[str, Any]]:
        """
        Fetch recommendations from database within date range.

        Args:
            days_back: Number of days to fetch

        Returns:
            List of recommendation dictionaries
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)

        query = """
            SELECT id, symbol, timeframe, signal, confidence,
                   entry_price, stop_loss, take_profit, created_at
            FROM recommendations
            WHERE created_at >= $1
            ORDER BY created_at DESC
        """

        try:
            async with self.db.acquire() as conn:
                rows = await conn.fetch(query, cutoff_date)
            return [dict(row) for row in rows]
        except Exception as e:
            logger.exception(f"Error fetching recommendations: {e}")
            return []

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

        Args:
            deals: List of MT5 closed deals
            recommendations: List of advisor recommendations

        Returns:
            List of matched deal-recommendation pairs
        """
        matches = []

        for deal in deals:
            best_match = None
            best_score = 0

            for rec in recommendations:
                score = self._calculate_match_score(deal, rec)
                if score > best_score and score >= 0.8:  # Minimum 80% match confidence
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

        logger.debug(f"Match details: {len(matches)} successful matches from {len(deals)} deals")
        return matches

    def _calculate_match_score(
        self,
        deal: Dict[str, Any],
        rec: Dict[str, Any]
    ) -> float:
        """
        Calculate match confidence score (0.0-1.0).

        Scoring factors:
        - Symbol match: 40% (must match exactly)
        - Price match: 40% (within tolerance)
        - Time match: 20% (within window)

        Args:
            deal: MT5 deal dictionary
            rec: Recommendation dictionary

        Returns:
            Match score from 0.0 to 1.0
        """
        score = 0.0

        # Symbol match (exact) - required
        if deal["symbol"] == rec["symbol"]:
            score += 0.4
        else:
            return 0.0  # No match if symbol differs

        # Price match (within ±0.1% tolerance)
        price_tolerance = 0.001  # 0.1%
        if rec.get("entry_price"):
            price_diff = abs(deal["entry_price"] - rec["entry_price"]) / rec["entry_price"]
            if price_diff <= price_tolerance:
                score += 0.4  # Perfect price match
            elif price_diff <= price_tolerance * 5:  # Within 0.5%
                score += 0.2  # Partial price match

        # Time match (within ±5min window)
        if rec.get("created_at"):
            time_diff = abs((deal["entry_at"] - rec["created_at"]).total_seconds())
            if time_diff <= 300:  # Within 5 minutes
                score += 0.2
            elif time_diff <= 900:  # Within 15 minutes
                score += 0.1

        return score

    def _determine_exit_reason(
        self,
        deal: Dict[str, Any],
        rec: Dict[str, Any]
    ) -> str:
        """
        Determine why trade was exited.

        Checks:
        1. Take profit hit (price within 0.1% of TP)
        2. Stop loss hit (price within 0.1% of SL)
        3. Manual close (from comment)
        4. Unknown

        Args:
            deal: MT5 deal dictionary
            rec: Recommendation dictionary

        Returns:
            Exit reason string: take_profit, stop_loss, manual, or unknown
        """
        exit_price = deal["exit_price"]

        # Check if TP hit
        if rec.get("take_profit"):
            tp_tolerance = abs(exit_price - rec["take_profit"]) / rec["take_profit"]
            if tp_tolerance < 0.001:  # Within 0.1%
                return "take_profit"

        # Check if SL hit
        if rec.get("stop_loss"):
            sl_tolerance = abs(exit_price - rec["stop_loss"]) / rec["stop_loss"]
            if sl_tolerance < 0.001:  # Within 0.1%
                return "stop_loss"

        # Check comment for manual close indicators
        comment = deal.get("comment", "").lower()
        if "manual" in comment or "closed" in comment or "user" in comment:
            return "manual"

        return "unknown"
