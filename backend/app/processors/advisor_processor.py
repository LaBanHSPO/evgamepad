"""
Advisor command processor.
Routes Socket.IO events to technical analysis components.
"""
import logging
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
