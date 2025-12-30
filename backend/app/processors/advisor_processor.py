"""
Advisor command processor.
Routes Socket.IO events to technical analysis components.
"""
import logging
import asyncio
import hashlib
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.advisor.technical_analyzer import TechnicalAnalyzer
from app.advisor.data_fetcher import DataFetcher
from app.advisor.pattern_detector import PatternDetector
from app.advisor.support_resistance import SupportResistanceCalculator
from app.advisor.risk_analyzer import RiskAnalyzer
from app.advisor.ai_summarizer import AISummarizer
from app.advisor.recommendation_engine import RecommendationEngine
from app.database.redis_client import RedisClient
from app.models.responses import success_response, error_response, ErrorCode
from app.models.advisor_models import PositionInput
from app.config import config

logger = logging.getLogger(__name__)

class AdvisorProcessor:
    """
    Central processor for advisor commands.
    Handles caching, data fetching, and analysis coordination.
    """

    def __init__(
        self,
        mt5_manager,
        redis_client: Optional[RedisClient] = None
    ):
        self.data_fetcher = DataFetcher(mt5_manager)
        self.analyzer = TechnicalAnalyzer()
        self.pattern_detector = PatternDetector()
        self.sr_calculator = SupportResistanceCalculator()
        self.risk_analyzer = RiskAnalyzer()
        self.redis_client = redis_client

        # AI components for Phase 04
        self.ai_summarizer = AISummarizer(
            anthropic_api_key=config.ANTHROPIC_API_KEY,
            deepseek_api_key=config.DEEPSEEK_API_KEY,
            default_model=config.DEFAULT_LLM_MODEL,
            redis_client=redis_client
        )
        self.recommendation_engine = RecommendationEngine(self.ai_summarizer)

    async def process_technical_summary(
        self,
        sid: str,
        symbol: str,
        timeframe: str,
        indicators: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Process technical summary request with caching.
        """
        logger.info(f"[{sid}] Processing technical summary: {symbol} {timeframe}")

        # Check cache first
        if self.redis_client:
            cached = await self.redis_client.get_indicators(symbol, timeframe)
            if cached:
                logger.debug(f"[{sid}] Cache hit for {symbol} {timeframe}")
                cached['cached'] = True
                return success_response(cached)

        # Fetch OHLCV data
        df = await self.data_fetcher.fetch_ohlcv(symbol, timeframe, count=100)
        if df is None:
            return error_response(
                ErrorCode.MT5_ERROR,
                f"Failed to fetch data for {symbol} {timeframe}"
            )

        # Calculate indicators
        result = self.analyzer.calculate_indicators(df, indicators)
        if "error" in result:
            return error_response(ErrorCode.INTERNAL_ERROR, result["error"])

        # Add metadata
        result["symbol"] = symbol
        result["timeframe"] = timeframe
        result["overall"] = self.analyzer.get_overall_signal(result)
        result["cached"] = False
        result["computed_at"] = datetime.utcnow().isoformat()

        # Cache result
        if self.redis_client:
            await self.redis_client.set_indicators(symbol, timeframe, result, ttl=60)

        return success_response(result)

    async def process_multi_timeframe(
        self,
        sid: str,
        symbol: str,
        timeframes: List[str]
    ) -> Dict[str, Any]:
        """
        Process multi-timeframe analysis.
        Returns analysis for each timeframe + alignment summary.
        """
        logger.info(f"[{sid}] Processing multi-timeframe: {symbol} {timeframes}")

        results = {}
        signals = []

        for tf in timeframes:
            # Process each timeframe
            tf_result = await self.process_technical_summary(sid, symbol, tf, None)
            if tf_result.get('success'):
                results[tf] = tf_result.get('data', {})
                overall = results[tf].get('overall', {})
                signals.append({
                    "timeframe": tf,
                    "signal": overall.get('signal', 'neutral'),
                    "confidence": overall.get('confidence', 0),
                })
            else:
                results[tf] = {"error": tf_result.get('message', 'Failed')}

        # Calculate alignment
        bullish_count = sum(1 for s in signals if s['signal'] == 'bullish')
        bearish_count = sum(1 for s in signals if s['signal'] == 'bearish')
        total = len(signals)

        if bullish_count == total:
            alignment = "strong_bullish"
        elif bearish_count == total:
            alignment = "strong_bearish"
        elif bullish_count > bearish_count:
            alignment = "bullish_bias"
        elif bearish_count > bullish_count:
            alignment = "bearish_bias"
        else:
            alignment = "mixed"

        return success_response({
            "symbol": symbol,
            "timeframes": results,
            "alignment": {
                "status": alignment,
                "bullish_count": bullish_count,
                "bearish_count": bearish_count,
                "signals": signals,
            },
            "power_zone": alignment in ["strong_bullish", "strong_bearish"],
            "computed_at": datetime.utcnow().isoformat(),
        })

    async def process_pattern_scan(
        self,
        sid: str,
        symbol: str,
        timeframe: str,
        include_sr: bool = True
    ) -> Dict[str, Any]:
        """
        Process pattern scan request.
        """
        logger.info(f"[{sid}] Processing pattern scan: {symbol} {timeframe}")

        # Check cache
        cache_key = f"patterns:{symbol}:{timeframe}"
        if self.redis_client:
            cached = await self.redis_client._client.get(cache_key)
            if cached:
                import json
                data = json.loads(cached)
                data['cached'] = True
                return success_response(data)

        # Fetch OHLCV data (need more candles for patterns)
        df = await self.data_fetcher.fetch_ohlcv(symbol, timeframe, count=200)
        if df is None:
            return error_response(
                ErrorCode.MT5_ERROR,
                f"Failed to fetch data for {symbol} {timeframe}"
            )

        result = {
            "symbol": symbol,
            "timeframe": timeframe,
            "last_price": float(df['close'].iloc[-1]),
        }

        # Detect candlestick patterns
        candlestick = self.pattern_detector.detect_candlestick_patterns(df)
        result["candlestick_patterns"] = candlestick

        # Detect chart patterns
        chart_patterns = self.pattern_detector.detect_chart_patterns(df)
        result["chart_patterns"] = chart_patterns

        # Calculate S/R levels
        if include_sr:
            sr_levels = self.sr_calculator.calculate_all(df)
            result["support_resistance"] = sr_levels

        result["cached"] = False
        result["computed_at"] = datetime.utcnow().isoformat()

        # Cache result
        if self.redis_client:
            import json
            await self.redis_client._client.setex(
                cache_key,
                300,  # 5 min TTL
                json.dumps(result, default=str)
            )

        return success_response(result)

    async def process_risk_analysis(
        self,
        sid: str,
        symbol: str,
        account_balance: float,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        risk_profile: str = "moderate",
        timeframe: str = "H1"
    ) -> Dict[str, Any]:
        """
        Process complete risk analysis request.
        Fetches ATR if symbol provided.
        """
        logger.info(f"[{sid}] Processing risk analysis for {symbol}")

        # Get ATR if symbol provided
        atr = None
        if symbol:
            # Try to get from cache first
            cached = await self.redis_client.get_indicators(symbol, timeframe) if self.redis_client else None
            if cached and "atr" in cached.get("indicators", {}):
                atr = cached["indicators"]["atr"]
            else:
                # Calculate fresh
                df = await self.data_fetcher.fetch_ohlcv(symbol, timeframe, count=50)
                if df is not None:
                    indicators = self.analyzer.calculate_indicators(df, ["atr"])
                    atr = indicators.get("indicators", {}).get("atr")

        # Run full risk analysis
        result = self.risk_analyzer.analyze_full_risk(
            account_balance=account_balance,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_profile=risk_profile,
            atr=atr,
        )

        result["symbol"] = symbol
        result["computed_at"] = datetime.utcnow().isoformat()

        return success_response(result)

    async def process_recommendation(
        self,
        sid: str,
        symbol: str,
        timeframe: str,
        language: str = "vi",
        risk_profile: str = "moderate"
    ) -> Dict[str, Any]:
        """
        Process complete recommendation request.
        Combines technical analysis, patterns, S/R, and AI summary.
        """
        logger.info(f"[{sid}] Processing recommendation for {symbol} {timeframe}")

        # 1. Get technical analysis
        tech_result = await self.process_technical_summary(sid, symbol, timeframe)
        if not tech_result.get("success"):
            return tech_result

        technical_data = tech_result.get("data", {})

        # 2. Get pattern analysis
        pattern_result = await self.process_pattern_scan(sid, symbol, timeframe, include_sr=True)
        pattern_data = pattern_result.get("data", {}) if pattern_result.get("success") else {}

        # 3. Extract S/R data
        sr_data = pattern_data.get("support_resistance", {})

        # 4. Build user profile
        user_profile = {
            "risk_tolerance": risk_profile,
            "preferred_timeframe": timeframe,
        }

        # 5. Generate recommendation
        recommendation = await self.recommendation_engine.generate_recommendation(
            symbol=symbol,
            technical_data=technical_data,
            pattern_data=pattern_data,
            sr_data=sr_data,
            user_profile=user_profile,
            language=language
        )

        recommendation["timeframe"] = timeframe
        recommendation["language"] = language

        return success_response(recommendation)

    async def process_portfolio_analysis(
        self,
        sid: str,
        positions: List[PositionInput],
        account_balance: float,
        risk_profile: str,
        language: str
    ) -> Dict[str, Any]:
        """
        Process comprehensive portfolio analysis with LLM advice.

        Args:
            sid: Socket session ID
            positions: List of user positions
            account_balance: Total account balance
            risk_profile: User risk tolerance
            language: Output language (vi/en)

        Returns:
            PortfolioAnalysisResponse as dict
        """
        logger.info(f"[{sid}] Processing portfolio: {len(positions)} positions, balance={account_balance}")

        # Generate cache key from positions
        cache_key = self._generate_portfolio_cache_key(positions, account_balance, risk_profile)

        # Check cache first
        if self.redis_client:
            try:
                cached = await self.redis_client.get_portfolio_analysis(cache_key)
                if cached:
                    logger.debug(f"[{sid}] Portfolio cache hit")
                    cached['cached'] = True
                    return success_response(cached)
            except Exception as e:
                logger.warning(f"[{sid}] Cache read failed, continuing without cache: {e}")

        # Step 1: Analyze each position in parallel
        position_tasks = [
            self._analyze_single_position(pos, account_balance, risk_profile)
            for pos in positions
        ]
        position_results = await asyncio.gather(*position_tasks, return_exceptions=True)

        # Filter out failures
        valid_results = []
        for i, result in enumerate(position_results):
            if isinstance(result, Exception):
                logger.warning(f"[{sid}] Position {positions[i].symbol} analysis failed: {result}")
            else:
                valid_results.append(result)

        if not valid_results:
            return error_response(
                ErrorCode.INTERNAL_ERROR,
                "All position analyses failed"
            )

        # Step 2: Calculate portfolio-wide metrics
        portfolio_health = self._calculate_portfolio_health(
            valid_results, account_balance
        )

        # Step 3: Generate LLM capital preservation advice
        ai_advice = await self.ai_summarizer.generate_portfolio_advice(
            positions=valid_results,
            portfolio_health=portfolio_health,
            account_balance=account_balance,
            risk_profile=risk_profile,
            language=language,
            use_cache=True
        )

        # Step 4: Build response
        response = {
            "success": True,
            "portfolio_health": portfolio_health,
            "position_analysis": valid_results,
            "ai_advice": ai_advice,
            "cached": False,
            "computed_at": datetime.utcnow().isoformat()
        }

        # Cache result
        if self.redis_client:
            await self.redis_client.set_portfolio_analysis(cache_key, response, ttl=300)

        return success_response(response)

    async def _analyze_single_position(
        self,
        position: PositionInput,
        account_balance: float,
        risk_profile: str
    ) -> Dict[str, Any]:
        """
        Analyze single position: technical + risk metrics.
        """
        # Fetch current price if not provided
        current_price = position.current_price
        if current_price is None:
            df = await self.data_fetcher.fetch_ohlcv(
                position.symbol, position.timeframe, count=1
            )
            if df is not None and len(df) > 0:
                current_price = df['close'].iloc[-1]
            else:
                raise ValueError(f"Failed to fetch current price for {position.symbol}")

        # Get technical analysis
        tech_result = await self.process_technical_summary(
            sid="internal",
            symbol=position.symbol,
            timeframe=position.timeframe
        )
        technical_data = tech_result.get("data", {})

        # Calculate risk metrics
        entry = position.entry_price
        if not position.stop_loss:
            logger.warning(f"No stop-loss for {position.symbol}, using 2% default")
        stop = position.stop_loss or (entry * 0.98)  # Default 2% stop if not provided

        # Calculate unrealized P&L
        pnl_pct = ((current_price - entry) / entry) * 100
        pnl_amount = (current_price - entry) * position.position_size

        # Calculate R-Multiple
        risk_per_unit = abs(entry - stop)
        reward_per_unit = abs(current_price - entry)
        r_multiple = reward_per_unit / risk_per_unit if risk_per_unit > 0 else 0

        # Distance to stop-loss
        distance_to_stop_pct = abs((current_price - stop) / current_price) * 100

        # Risk status assessment
        if distance_to_stop_pct <= 1:
            risk_status = "danger"
            recommendation = "CLOSE"
        elif distance_to_stop_pct <= 3:
            risk_status = "approaching_stop"
            recommendation = "REDUCE"
        elif technical_data.get("overall", {}).get("signal") == "bearish" and pnl_pct < 0:
            risk_status = "caution"
            recommendation = "REDUCE"
        else:
            risk_status = "safe"
            recommendation = "HOLD"

        return {
            "symbol": position.symbol,
            "entry_price": entry,
            "current_price": current_price,
            "position_size": position.position_size,
            "stop_loss": stop,
            "pnl_pct": round(pnl_pct, 2),
            "pnl_amount": round(pnl_amount, 2),
            "r_multiple": round(r_multiple, 2),
            "distance_to_stop_pct": round(distance_to_stop_pct, 2),
            "risk_status": risk_status,
            "recommendation": recommendation,
            "technical_signal": technical_data.get("overall", {}).get("signal", "neutral"),
            "technical_confidence": technical_data.get("overall", {}).get("confidence", 0)
        }

    def _calculate_portfolio_health(
        self,
        position_results: List[Dict[str, Any]],
        account_balance: float
    ) -> Dict[str, Any]:
        """
        Calculate portfolio-wide health metrics.
        """
        total_risk_amount = 0
        positions_at_risk = 0
        max_drawdown = 0

        for pos in position_results:
            # Calculate risk exposure for this position
            risk_per_position = abs(pos["entry_price"] - pos["stop_loss"]) * pos["position_size"]
            total_risk_amount += risk_per_position

            # Count positions at risk
            if pos["risk_status"] in ["approaching_stop", "danger"]:
                positions_at_risk += 1

            # Track max drawdown
            if pos["pnl_pct"] < max_drawdown:
                max_drawdown = pos["pnl_pct"]

        # Calculate metrics
        total_risk_exposure = (total_risk_amount / account_balance) * 100 if account_balance > 0 else 0
        current_drawdown = abs(max_drawdown)

        # Calculate health score (0-100)
        score = 100
        score -= min(total_risk_exposure * 10, 50)  # Penalty for high risk exposure
        score -= min(current_drawdown * 5, 30)  # Penalty for drawdown
        score -= min(positions_at_risk * 10, 20)  # Penalty for risky positions
        score = max(0, min(100, int(score)))

        # Determine status
        if score >= 70:
            status = "HEALTHY"
        elif score >= 40:
            status = "CAUTION"
        else:
            status = "DANGER"

        return {
            "score": score,
            "status": status,
            "total_risk_exposure": round(total_risk_exposure, 2),
            "current_drawdown": round(current_drawdown, 2),
            "positions_at_risk": positions_at_risk
        }

    def _generate_portfolio_cache_key(
        self,
        positions: List[PositionInput],
        account_balance: float,
        risk_profile: str
    ) -> str:
        """Generate cache key for portfolio analysis."""
        # Create deterministic key from positions + risk profile
        key_data = {
            "positions": [
                {
                    "symbol": p.symbol,
                    "entry": round(p.entry_price, -1),  # Round to nearest 10
                    "size": p.position_size
                }
                for p in sorted(positions, key=lambda x: x.symbol)
            ],
            "balance_bucket": round(account_balance, -3),  # Round to nearest 1000
            "risk_profile": risk_profile
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return f"portfolio_analysis:{hashlib.md5(key_str.encode()).hexdigest()}"
