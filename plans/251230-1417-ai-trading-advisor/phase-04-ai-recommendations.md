# Phase 4: AI Summarizer & Personalized Recommendations

## Context Links
- Main Plan: `plan.md`
- Phase 1: `phase-01-technical-analysis-engine.md`
- Phase 2: `phase-02-pattern-recognition-sr.md`
- Phase 3: `phase-03-risk-analyzer.md`
- Architecture Research: `../reports/researcher-251230-1418-ai-trading-advisor-architecture.md`

---

## Overview

Implement LLM-powered analysis summarization using Claude 3.7 Sonnet (primary) and DeepSeek (cost fallback). Generate personalized trading recommendations based on user risk profile. Add semantic caching to reduce LLM costs by ~75%. Support Vietnamese language output.

**Effort:** 10 hours
**Priority:** P1 (the "AI" in AI Trading Advisor)

---

## Key Insights from Research

1. **Model Selection:**
   - Claude 3.7 Sonnet: $3/$15 per MTok - Best reasoning, recommended for strategy evaluation
   - DeepSeek: $0.70/2M tokens - Cost-effective for bulk analysis, good Vietnamese support
2. **Semantic Caching:** 75% cost reduction, 50-200ms vs 1-2s response time
3. **Prompt Engineering:** Few-shot examples + strict output format = consistent quality
4. **Vietnamese:** Both Claude and DeepSeek handle Vietnamese adequately; use LLM-native approach
5. **Confidence Scoring:** Factor agreement + hit ratio tracking for calibrated confidence

---

## Requirements

### Functional
- FR1: Generate natural language technical summaries from computed indicators
- FR2: Generate personalized buy/sell/hold recommendations
- FR3: Support Vietnamese and English output
- FR4: Cache similar queries using semantic similarity (embeddings)
- FR5: Include confidence score with explanation
- FR6: Respect user risk profile in recommendations
- FR7: Emit via `advisor:recommendation` Socket.IO event

### Non-Functional
- NFR1: LLM response latency < 3s (first request)
- NFR2: Cached response latency < 200ms
- NFR3: LLM costs < $50/month (1000 analyses)
- NFR4: Vietnamese output grammatically correct

---

## Architecture

### Component Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                    advisor_events.py                           │
│               @sio.event('advisor:recommendation')             │
└──────────────────────────┬─────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────────┐
│                   advisor_processor.py                         │
│              AdvisorProcessor.process_recommendation()         │
└──────────────────────────┬─────────────────────────────────────┘
                           │
    ┌──────────────────────┼──────────────────────┐
    ▼                      ▼                      ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────────────┐
│ ai_summarizer │   │recommendation_│   │ technical_analyzer    │
│ .py           │   │ engine.py     │   │ pattern_detector      │
│               │   │               │   │ risk_analyzer         │
│ - Claude API  │   │ - aggregate   │   │ (Phases 1-3)          │
│ - DeepSeek    │   │   signals     │   │                       │
│ - semantic    │   │ - personalize │   │                       │
│   cache       │   │ - confidence  │   │                       │
└───────────────┘   └───────────────┘   └───────────────────────┘
         │                 │
         ▼                 │
┌───────────────┐         │
│ Redis         │◄────────┘
│ (semantic     │
│  cache)       │
└───────────────┘
```

### Data Flow for Recommendation

```
Request: { symbol: "AAPL", language: "vi" }
              │
              ▼
       Check semantic cache
              │
        ┌─────┴─────┐
    HIT │           │ MISS
        ▼           ▼
   Return       Gather data:
   cached       - Technical indicators (Phase 1)
                - Patterns detected (Phase 2)
                - S/R levels (Phase 2)
                - Risk analysis (Phase 3)
                - User profile
              │
              ▼
       Build LLM prompt
       (few-shot + context)
              │
              ▼
       Call Claude/DeepSeek
              │
              ▼
       Parse response
       (signal, confidence, reasoning)
              │
              ▼
       Cache with embedding
              │
              ▼
       Return recommendation
```

---

## Related Code Files

### From Phases 1-3 (USE)
- `backend/app/advisor/technical_analyzer.py`
- `backend/app/advisor/pattern_detector.py`
- `backend/app/advisor/support_resistance.py`
- `backend/app/advisor/risk_analyzer.py`
- `backend/app/database/redis_client.py`

### New (CREATE)
- `backend/app/advisor/ai_summarizer.py`
- `backend/app/advisor/recommendation_engine.py`
- `backend/app/models/user_profile.py`
- `backend/app/database/postgres_client.py`
- `backend/app/database/schemas.py`

---

## Implementation Steps

### Step 1: AI Summarizer Module (4h)

**File:** `backend/app/advisor/ai_summarizer.py`

```python
"""
AI-powered analysis summarization using Claude/DeepSeek.
Includes semantic caching for cost optimization.
"""
import logging
import json
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

# Prompt templates
TECHNICAL_SUMMARY_PROMPT_VI = """Bạn là chuyên gia phân tích kỹ thuật chứng khoán. Phân tích dữ liệu sau và đưa ra tóm tắt ngắn gọn bằng tiếng Việt.

## Dữ liệu kỹ thuật cho {symbol} ({timeframe}):
- Giá hiện tại: {price}
- RSI: {rsi} ({rsi_signal})
- MACD: {macd_status}
- Xu hướng: {trend}
- Các mẫu hình nến phát hiện: {patterns}
- Hỗ trợ gần nhất: {support}
- Kháng cự gần nhất: {resistance}

## Hồ sơ rủi ro người dùng: {risk_profile}

## Yêu cầu:
1. Tóm tắt tình hình kỹ thuật trong 2-3 câu
2. Đưa ra khuyến nghị: MUA / BÁN / GIỮ
3. Mức độ tin cậy (0-100%)
4. Giải thích lý do ngắn gọn

## Định dạng phản hồi (JSON):
{{"summary": "...", "signal": "BUY/SELL/HOLD", "confidence": 75, "reasoning": "..."}}
"""

TECHNICAL_SUMMARY_PROMPT_EN = """You are a technical analysis expert. Analyze the following data and provide a concise summary.

## Technical data for {symbol} ({timeframe}):
- Current price: {price}
- RSI: {rsi} ({rsi_signal})
- MACD: {macd_status}
- Trend: {trend}
- Candlestick patterns detected: {patterns}
- Nearest support: {support}
- Nearest resistance: {resistance}

## User risk profile: {risk_profile}

## Requirements:
1. Summarize technical situation in 2-3 sentences
2. Provide recommendation: BUY / SELL / HOLD
3. Confidence level (0-100%)
4. Brief reasoning

## Response format (JSON):
{{"summary": "...", "signal": "BUY/SELL/HOLD", "confidence": 75, "reasoning": "..."}}
"""

class AISummarizer:
    """
    Generates AI-powered technical analysis summaries.
    Supports Claude (Anthropic) and DeepSeek (OpenAI-compatible).
    """

    def __init__(
        self,
        anthropic_api_key: Optional[str] = None,
        deepseek_api_key: Optional[str] = None,
        default_model: str = "claude",
        redis_client=None
    ):
        """
        Args:
            anthropic_api_key: Anthropic API key for Claude
            deepseek_api_key: DeepSeek API key
            default_model: "claude" or "deepseek"
            redis_client: Redis client for semantic caching
        """
        self.anthropic_key = anthropic_api_key
        self.deepseek_key = deepseek_api_key
        self.default_model = default_model
        self.redis = redis_client

        # Initialize clients lazily
        self._anthropic_client = None
        self._openai_client = None

    def _get_anthropic_client(self):
        """Lazy initialization of Anthropic client."""
        if self._anthropic_client is None and self.anthropic_key:
            try:
                import anthropic
                self._anthropic_client = anthropic.Anthropic(api_key=self.anthropic_key)
            except ImportError:
                logger.warning("anthropic package not installed")
        return self._anthropic_client

    def _get_openai_client(self):
        """Lazy initialization of OpenAI client (for DeepSeek)."""
        if self._openai_client is None and self.deepseek_key:
            try:
                from openai import OpenAI
                self._openai_client = OpenAI(
                    api_key=self.deepseek_key,
                    base_url="https://api.deepseek.com"
                )
            except ImportError:
                logger.warning("openai package not installed")
        return self._openai_client

    def _generate_cache_key(self, data: Dict[str, Any]) -> str:
        """Generate cache key from analysis data."""
        # Create deterministic hash from relevant fields
        key_data = {
            "symbol": data.get("symbol"),
            "timeframe": data.get("timeframe"),
            "rsi_signal": data.get("rsi_signal"),
            "trend": data.get("trend"),
            "risk_profile": data.get("risk_profile"),
            # Round price to reduce cache misses from tiny price changes
            "price_bucket": round(data.get("price", 0), -1),
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return f"ai_summary:{hashlib.md5(key_str.encode()).hexdigest()}"

    async def _check_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Check semantic cache for existing response."""
        if self.redis is None:
            return None

        try:
            cached = await self.redis._client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache check failed: {e}")

        return None

    async def _save_to_cache(
        self,
        cache_key: str,
        data: Dict[str, Any],
        ttl: int = 300
    ):
        """Save response to cache."""
        if self.redis is None:
            return

        try:
            await self.redis._client.setex(
                cache_key, ttl, json.dumps(data)
            )
        except Exception as e:
            logger.warning(f"Cache save failed: {e}")

    async def generate_summary(
        self,
        analysis_data: Dict[str, Any],
        language: str = "vi",
        use_cache: bool = True,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate AI summary from technical analysis data.

        Args:
            analysis_data: Dict containing technical indicators, patterns, S/R
            language: "vi" for Vietnamese, "en" for English
            use_cache: Whether to use semantic cache
            model: Override default model ("claude" or "deepseek")

        Returns:
            Dict with summary, signal, confidence, reasoning
        """
        model = model or self.default_model

        # Check cache first
        if use_cache:
            cache_key = self._generate_cache_key(analysis_data)
            cached = await self._check_cache(cache_key)
            if cached:
                cached["cached"] = True
                return cached

        # Build prompt
        prompt = self._build_prompt(analysis_data, language)

        # Call LLM
        try:
            if model == "claude":
                response = await self._call_claude(prompt)
            else:
                response = await self._call_deepseek(prompt)

            # Parse response
            result = self._parse_response(response)
            result["model"] = model
            result["language"] = language
            result["cached"] = False
            result["generated_at"] = datetime.utcnow().isoformat()

            # Save to cache
            if use_cache:
                await self._save_to_cache(cache_key, result)

            return result

        except Exception as e:
            logger.exception(f"AI summary generation failed: {e}")
            return {
                "error": str(e),
                "summary": "Unable to generate AI summary",
                "signal": "HOLD",
                "confidence": 0,
                "reasoning": "AI service unavailable",
            }

    def _build_prompt(
        self,
        data: Dict[str, Any],
        language: str
    ) -> str:
        """Build prompt from analysis data."""
        template = TECHNICAL_SUMMARY_PROMPT_VI if language == "vi" else TECHNICAL_SUMMARY_PROMPT_EN

        # Extract data with defaults
        indicators = data.get("indicators", {})
        signals = data.get("signals", {})
        patterns = data.get("candlestick_patterns", {})
        sr = data.get("support_resistance", {})

        # Format MACD status
        macd = indicators.get("macd", {})
        if isinstance(macd, dict):
            macd_status = f"Line: {macd.get('macd', 'N/A')}, Signal: {macd.get('signal', 'N/A')}"
        else:
            macd_status = str(macd)

        # Format patterns
        detected_patterns = patterns.get("detected", [])
        pattern_names = [p.get("name", "unknown") for p in detected_patterns[:5]]
        patterns_str = ", ".join(pattern_names) if pattern_names else "None"

        return template.format(
            symbol=data.get("symbol", "Unknown"),
            timeframe=data.get("timeframe", "H1"),
            price=data.get("last_price", data.get("last_close", "N/A")),
            rsi=indicators.get("rsi", "N/A"),
            rsi_signal=signals.get("rsi", "neutral"),
            macd_status=macd_status,
            trend=signals.get("trend", "unknown"),
            patterns=patterns_str,
            support=sr.get("nearest_support", {}).get("price", "N/A") if isinstance(sr.get("nearest_support"), dict) else sr.get("nearest_support", "N/A"),
            resistance=sr.get("nearest_resistance", {}).get("price", "N/A") if isinstance(sr.get("nearest_resistance"), dict) else sr.get("nearest_resistance", "N/A"),
            risk_profile=data.get("risk_profile", "moderate"),
        )

    async def _call_claude(self, prompt: str) -> str:
        """Call Claude API."""
        client = self._get_anthropic_client()
        if client is None:
            raise RuntimeError("Anthropic client not available")

        def _sync_call():
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text

        return await asyncio.to_thread(_sync_call)

    async def _call_deepseek(self, prompt: str) -> str:
        """Call DeepSeek API (OpenAI-compatible)."""
        client = self._get_openai_client()
        if client is None:
            raise RuntimeError("OpenAI/DeepSeek client not available")

        def _sync_call():
            response = client.chat.completions.create(
                model="deepseek-chat",
                max_tokens=500,
                messages=[
                    {"role": "system", "content": "You are a technical analysis expert. Always respond in valid JSON format."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content

        return await asyncio.to_thread(_sync_call)

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured data."""
        try:
            # Try to extract JSON from response
            response = response.strip()

            # Handle markdown code blocks
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            data = json.loads(response)

            # Normalize signal
            signal = data.get("signal", "HOLD").upper()
            if signal not in ["BUY", "SELL", "HOLD"]:
                signal = "HOLD"

            # Normalize confidence
            confidence = data.get("confidence", 50)
            if isinstance(confidence, str):
                confidence = int(confidence.replace("%", ""))
            confidence = max(0, min(100, confidence))

            return {
                "summary": data.get("summary", ""),
                "signal": signal,
                "confidence": confidence,
                "reasoning": data.get("reasoning", ""),
            }

        except json.JSONDecodeError:
            # Fallback: extract info from text
            logger.warning(f"Failed to parse JSON response, using fallback")
            signal = "HOLD"
            if "BUY" in response.upper():
                signal = "BUY"
            elif "SELL" in response.upper():
                signal = "SELL"

            return {
                "summary": response[:500],
                "signal": signal,
                "confidence": 50,
                "reasoning": "Unable to parse structured response",
            }
```

### Step 2: Recommendation Engine (2.5h)

**File:** `backend/app/advisor/recommendation_engine.py`

```python
"""
Personalized recommendation engine.
Combines technical analysis with user profile for tailored advice.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class SignalStrength(Enum):
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    WEAK_BUY = "weak_buy"
    HOLD = "hold"
    WEAK_SELL = "weak_sell"
    SELL = "sell"
    STRONG_SELL = "strong_sell"

class RecommendationEngine:
    """
    Generates personalized trading recommendations by combining:
    - Technical indicators
    - Pattern recognition
    - Support/Resistance levels
    - User risk profile
    - AI-generated insights
    """

    def __init__(self, ai_summarizer=None):
        """
        Args:
            ai_summarizer: AISummarizer instance for natural language generation
        """
        self.ai_summarizer = ai_summarizer

    async def generate_recommendation(
        self,
        symbol: str,
        technical_data: Dict[str, Any],
        pattern_data: Optional[Dict[str, Any]] = None,
        sr_data: Optional[Dict[str, Any]] = None,
        risk_data: Optional[Dict[str, Any]] = None,
        user_profile: Optional[Dict[str, Any]] = None,
        language: str = "vi"
    ) -> Dict[str, Any]:
        """
        Generate comprehensive trading recommendation.

        Args:
            symbol: Trading symbol
            technical_data: Output from TechnicalAnalyzer
            pattern_data: Output from PatternDetector
            sr_data: Output from SupportResistanceCalculator
            risk_data: Output from RiskAnalyzer
            user_profile: User preferences and risk settings
            language: Output language

        Returns:
            Comprehensive recommendation with signal, confidence, targets
        """
        result = {
            "symbol": symbol,
            "generated_at": datetime.utcnow().isoformat(),
        }

        # Default user profile
        if user_profile is None:
            user_profile = {
                "risk_tolerance": "moderate",
                "preferred_timeframe": "H1",
            }

        # 1. Aggregate signals from technical analysis
        tech_signal = self._aggregate_technical_signals(technical_data)
        result["technical_signal"] = tech_signal

        # 2. Aggregate pattern signals
        pattern_signal = self._aggregate_pattern_signals(pattern_data) if pattern_data else None
        if pattern_signal:
            result["pattern_signal"] = pattern_signal

        # 3. Calculate overall signal
        overall = self._calculate_overall_signal(
            tech_signal, pattern_signal, user_profile
        )
        result["overall_signal"] = overall

        # 4. Determine entry/exit targets
        targets = self._calculate_targets(
            technical_data, sr_data, overall["signal"], user_profile
        )
        result["targets"] = targets

        # 5. Generate AI summary if available
        if self.ai_summarizer:
            combined_data = {
                "symbol": symbol,
                "timeframe": user_profile.get("preferred_timeframe", "H1"),
                "last_price": technical_data.get("last_close"),
                "indicators": technical_data.get("indicators", {}),
                "signals": technical_data.get("signals", {}),
                "candlestick_patterns": pattern_data or {},
                "support_resistance": sr_data or {},
                "risk_profile": user_profile.get("risk_tolerance", "moderate"),
            }

            ai_result = await self.ai_summarizer.generate_summary(
                combined_data, language=language
            )
            result["ai_summary"] = ai_result

        # 6. Final recommendation
        result["recommendation"] = self._format_recommendation(
            result, user_profile, language
        )

        return result

    def _aggregate_technical_signals(
        self,
        technical_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Aggregate signals from technical indicators into single assessment.
        """
        signals = technical_data.get("signals", {})
        indicators = technical_data.get("indicators", {})

        bullish_count = 0
        bearish_count = 0
        total_weight = 0

        # Weighted signal counting
        signal_weights = {
            "trend": 2.0,      # Trend is most important
            "macd": 1.5,
            "rsi": 1.0,
            "bollinger": 0.8,
            "adx": 0.7,
        }

        for key, value in signals.items():
            weight = signal_weights.get(key, 1.0)
            total_weight += weight

            value_str = str(value).lower()
            if "bullish" in value_str or value in ["oversold", "lower_band"]:
                bullish_count += weight
            elif "bearish" in value_str or value in ["overbought", "upper_band"]:
                bearish_count += weight

        # Calculate signal strength
        if total_weight > 0:
            bullish_pct = bullish_count / total_weight
            bearish_pct = bearish_count / total_weight
        else:
            bullish_pct = bearish_pct = 0

        # Determine signal
        if bullish_pct > 0.6:
            signal = "bullish"
            strength = bullish_pct
        elif bearish_pct > 0.6:
            signal = "bearish"
            strength = bearish_pct
        else:
            signal = "neutral"
            strength = 1 - max(bullish_pct, bearish_pct)

        # RSI extreme check
        rsi = indicators.get("rsi")
        if rsi:
            if rsi < 30:
                signal = "bullish"  # Oversold
            elif rsi > 70:
                signal = "bearish"  # Overbought

        return {
            "signal": signal,
            "strength": round(strength, 2),
            "bullish_weight": round(bullish_count, 2),
            "bearish_weight": round(bearish_count, 2),
            "total_weight": round(total_weight, 2),
            "raw_signals": signals,
        }

    def _aggregate_pattern_signals(
        self,
        pattern_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Aggregate signals from detected patterns.
        """
        if not pattern_data:
            return None

        candlestick = pattern_data.get("candlestick_patterns", {})
        chart = pattern_data.get("chart_patterns", {})

        # Count pattern biases
        bullish = len(candlestick.get("bullish_patterns", []))
        bearish = len(candlestick.get("bearish_patterns", []))

        # Check chart patterns
        for pattern in chart.get("patterns", []):
            if pattern.get("bias") == "bullish":
                bullish += 2  # Chart patterns have more weight
            elif pattern.get("bias") == "bearish":
                bearish += 2

        total = bullish + bearish
        if total == 0:
            return None

        if bullish > bearish:
            signal = "bullish"
            confidence = bullish / total
        elif bearish > bullish:
            signal = "bearish"
            confidence = bearish / total
        else:
            signal = "neutral"
            confidence = 0.5

        return {
            "signal": signal,
            "confidence": round(confidence, 2),
            "bullish_patterns": bullish,
            "bearish_patterns": bearish,
            "strongest_pattern": candlestick.get("detected", [{}])[0].get("name") if candlestick.get("detected") else None,
        }

    def _calculate_overall_signal(
        self,
        tech_signal: Dict[str, Any],
        pattern_signal: Optional[Dict[str, Any]],
        user_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate final signal combining all inputs with user profile.
        """
        risk_tolerance = user_profile.get("risk_tolerance", "moderate")

        # Weight factors based on risk tolerance
        weights = {
            "conservative": {"technical": 0.7, "pattern": 0.3, "confirmation_required": True},
            "moderate": {"technical": 0.6, "pattern": 0.4, "confirmation_required": False},
            "aggressive": {"technical": 0.5, "pattern": 0.5, "confirmation_required": False},
        }

        w = weights.get(risk_tolerance, weights["moderate"])

        # Calculate weighted signal
        tech_score = 0
        if tech_signal["signal"] == "bullish":
            tech_score = tech_signal["strength"]
        elif tech_signal["signal"] == "bearish":
            tech_score = -tech_signal["strength"]

        pattern_score = 0
        if pattern_signal:
            if pattern_signal["signal"] == "bullish":
                pattern_score = pattern_signal["confidence"]
            elif pattern_signal["signal"] == "bearish":
                pattern_score = -pattern_signal["confidence"]

        combined_score = (tech_score * w["technical"]) + (pattern_score * w["pattern"])

        # Determine final signal
        if combined_score > 0.3:
            signal = "BUY"
            strength = SignalStrength.BUY
        elif combined_score > 0.6:
            signal = "BUY"
            strength = SignalStrength.STRONG_BUY
        elif combined_score < -0.3:
            signal = "SELL"
            strength = SignalStrength.SELL
        elif combined_score < -0.6:
            signal = "SELL"
            strength = SignalStrength.STRONG_SELL
        else:
            signal = "HOLD"
            strength = SignalStrength.HOLD

        # Conservative users need confirmation
        if w["confirmation_required"]:
            if tech_signal["signal"] != (pattern_signal or {}).get("signal"):
                signal = "HOLD"
                strength = SignalStrength.HOLD

        confidence = abs(combined_score) * 100
        confidence = max(0, min(100, confidence))

        return {
            "signal": signal,
            "strength": strength.value,
            "confidence": round(confidence),
            "combined_score": round(combined_score, 3),
            "risk_tolerance_applied": risk_tolerance,
        }

    def _calculate_targets(
        self,
        technical_data: Dict[str, Any],
        sr_data: Optional[Dict[str, Any]],
        signal: str,
        user_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate entry, stop loss, and take profit targets.
        """
        price = technical_data.get("last_close", 0)
        atr = technical_data.get("indicators", {}).get("atr", price * 0.01)

        if atr is None:
            atr = price * 0.01

        risk_tolerance = user_profile.get("risk_tolerance", "moderate")

        # ATR multipliers based on risk
        multipliers = {
            "conservative": {"sl": 2.0, "tp": 3.0},
            "moderate": {"sl": 1.5, "tp": 2.5},
            "aggressive": {"sl": 1.0, "tp": 2.0},
        }

        m = multipliers.get(risk_tolerance, multipliers["moderate"])

        targets = {
            "current_price": round(price, 5),
        }

        if signal == "BUY":
            targets["entry"] = round(price, 5)
            targets["stop_loss"] = round(price - (atr * m["sl"]), 5)
            targets["take_profit"] = round(price + (atr * m["tp"]), 5)

            # Use S/R if available
            if sr_data:
                nearest_support = sr_data.get("nearest_support")
                if nearest_support and isinstance(nearest_support, dict):
                    sr_stop = nearest_support.get("price")
                    if sr_stop and sr_stop < price:
                        targets["stop_loss_sr"] = round(sr_stop * 0.998, 5)

                nearest_resistance = sr_data.get("nearest_resistance")
                if nearest_resistance and isinstance(nearest_resistance, dict):
                    sr_tp = nearest_resistance.get("price")
                    if sr_tp and sr_tp > price:
                        targets["take_profit_sr"] = round(sr_tp, 5)

        elif signal == "SELL":
            targets["entry"] = round(price, 5)
            targets["stop_loss"] = round(price + (atr * m["sl"]), 5)
            targets["take_profit"] = round(price - (atr * m["tp"]), 5)

            if sr_data:
                nearest_resistance = sr_data.get("nearest_resistance")
                if nearest_resistance and isinstance(nearest_resistance, dict):
                    sr_stop = nearest_resistance.get("price")
                    if sr_stop and sr_stop > price:
                        targets["stop_loss_sr"] = round(sr_stop * 1.002, 5)

                nearest_support = sr_data.get("nearest_support")
                if nearest_support and isinstance(nearest_support, dict):
                    sr_tp = nearest_support.get("price")
                    if sr_tp and sr_tp < price:
                        targets["take_profit_sr"] = round(sr_tp, 5)

        return targets

    def _format_recommendation(
        self,
        result: Dict[str, Any],
        user_profile: Dict[str, Any],
        language: str
    ) -> Dict[str, Any]:
        """
        Format final recommendation for output.
        """
        overall = result.get("overall_signal", {})
        targets = result.get("targets", {})
        ai = result.get("ai_summary", {})

        signal = overall.get("signal", "HOLD")
        confidence = overall.get("confidence", 0)

        # Action text
        if language == "vi":
            action_text = {
                "BUY": "MUA",
                "SELL": "BÁN",
                "HOLD": "GIỮ",
            }
            confidence_text = f"Độ tin cậy: {confidence}%"
        else:
            action_text = {
                "BUY": "BUY",
                "SELL": "SELL",
                "HOLD": "HOLD",
            }
            confidence_text = f"Confidence: {confidence}%"

        return {
            "action": action_text.get(signal, signal),
            "signal": signal,
            "confidence": confidence,
            "confidence_text": confidence_text,
            "entry": targets.get("entry"),
            "stop_loss": targets.get("stop_loss"),
            "take_profit": targets.get("take_profit"),
            "summary": ai.get("summary", ""),
            "reasoning": ai.get("reasoning", ""),
        }
```

### Step 3: User Profile Model (1h)

**File:** `backend/app/models/user_profile.py`

```python
"""
User profile and preferences for personalized recommendations.
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class RiskTolerance(str, Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"

class UserProfile(BaseModel):
    """User trading profile and preferences."""
    user_id: str
    risk_tolerance: RiskTolerance = RiskTolerance.MODERATE
    preferred_timeframes: List[str] = Field(default=["H1", "H4", "D1"])
    preferred_indicators: List[str] = Field(default=["RSI", "MACD", "SMA"])
    watchlist: List[str] = Field(default=[])
    max_position_risk: float = Field(default=0.02, ge=0.005, le=0.10)
    language: str = Field(default="vi", pattern="^(vi|en)$")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class UserProfileUpdate(BaseModel):
    """Update model for user profile."""
    risk_tolerance: Optional[RiskTolerance] = None
    preferred_timeframes: Optional[List[str]] = None
    preferred_indicators: Optional[List[str]] = None
    watchlist: Optional[List[str]] = None
    max_position_risk: Optional[float] = None
    language: Optional[str] = None

class RecommendationRequest(BaseModel):
    """Request for personalized recommendation."""
    symbol: str = Field(..., min_length=1, max_length=20)
    timeframe: str = Field(default="H1")
    language: str = Field(default="vi", pattern="^(vi|en)$")
    include_technical: bool = True
    include_patterns: bool = True
    include_sr: bool = True
    include_ai_summary: bool = True

class RecommendationResponse(BaseModel):
    """Response for recommendation request."""
    success: bool = True
    symbol: str
    overall_signal: Dict[str, Any]
    technical_signal: Optional[Dict[str, Any]] = None
    pattern_signal: Optional[Dict[str, Any]] = None
    targets: Dict[str, Any]
    ai_summary: Optional[Dict[str, Any]] = None
    recommendation: Dict[str, Any]
    generated_at: datetime = Field(default_factory=datetime.utcnow)
```

### Step 4: Extend Advisor Events (1h)

**Modify:** `backend/app/events/advisor_events.py`

Add:

```python
@sio.event
async def advisor_recommendation(sid: str, data: Dict[str, Any]):
    """
    Handle personalized recommendation request.

    Request: {
        "symbol": "XAUUSD",
        "timeframe": "H1",
        "language": "vi",
        "risk_profile": "moderate"
    }

    Response: {
        "success": true,
        "symbol": "XAUUSD",
        "recommendation": {...},
        "ai_summary": {...}
    }
    """
    logger.info(f"Recommendation request from {sid}: {data.get('symbol')}")

    try:
        symbol = data.get('symbol', '').upper()
        timeframe = data.get('timeframe', 'H1').upper()
        language = data.get('language', 'vi')
        risk_profile = data.get('risk_profile', 'moderate')

        if not symbol:
            await sio.emit('advisor:error', error_response(
                ErrorCode.VALIDATION_ERROR,
                "Symbol is required"
            ), to=sid)
            return

        if advisor_processor:
            result = await advisor_processor.process_recommendation(
                sid, symbol, timeframe, language, risk_profile
            )
            await sio.emit('advisor:recommendation_result', result, to=sid)
        else:
            await sio.emit('advisor:error', error_response(
                ErrorCode.INTERNAL_ERROR,
                "Advisor processor not initialized"
            ), to=sid)

    except Exception as e:
        logger.exception(f"Recommendation failed for {sid}: {e}")
        await sio.emit('advisor:error', error_response(
            ErrorCode.INTERNAL_ERROR,
            str(e)
        ), to=sid)
```

### Step 5: Extend Advisor Processor (1.5h)

**Modify:** `backend/app/processors/advisor_processor.py`

Add to imports:
```python
from app.advisor.ai_summarizer import AISummarizer
from app.advisor.recommendation_engine import RecommendationEngine
```

Add to __init__:
```python
# AI components
self.ai_summarizer = AISummarizer(
    anthropic_api_key=config.ANTHROPIC_API_KEY,
    deepseek_api_key=config.DEEPSEEK_API_KEY,
    default_model=config.DEFAULT_LLM_MODEL,
    redis_client=redis_client
)
self.recommendation_engine = RecommendationEngine(self.ai_summarizer)
```

Add new method:
```python
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
```

Add config variables:
```python
# backend/app/config.py
ANTHROPIC_API_KEY: str = os.getenv('ANTHROPIC_API_KEY', '')
DEEPSEEK_API_KEY: str = os.getenv('DEEPSEEK_API_KEY', '')
DEFAULT_LLM_MODEL: str = os.getenv('DEFAULT_LLM_MODEL', 'claude')
```

---

## Todo List

- [ ] Create `backend/app/advisor/ai_summarizer.py`
- [ ] Create `backend/app/advisor/recommendation_engine.py`
- [ ] Create `backend/app/models/user_profile.py`
- [ ] Extend `backend/app/events/advisor_events.py` - add recommendation
- [ ] Extend `backend/app/processors/advisor_processor.py` - add recommendation
- [ ] Extend `backend/app/config.py` - add LLM API keys
- [ ] Update `backend/requirements.txt` - add anthropic, openai
- [ ] Test Claude integration
- [ ] Test DeepSeek integration
- [ ] Test semantic caching
- [ ] Test Vietnamese output quality
- [ ] Test full recommendation flow

---

## Success Criteria

- [ ] Claude API generates coherent Vietnamese summaries
- [ ] DeepSeek fallback works when Claude unavailable
- [ ] Semantic cache reduces duplicate LLM calls
- [ ] Recommendations respect user risk profile
- [ ] Confidence scores correlate with signal agreement
- [ ] Response latency < 3s (first) / < 200ms (cached)
- [ ] LLM costs trackable via logging

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM API downtime | High | Fallback to rule-based summary |
| Poor Vietnamese grammar | Medium | Review and refine prompts |
| JSON parsing failures | Medium | Robust fallback parsing |
| High LLM costs | Medium | Aggressive caching, cost monitoring |
| Hallucinated signals | High | Validate LLM output against computed data |

---

## Security Considerations

- Store API keys in environment variables only
- Rate limit LLM calls per user
- Log all LLM requests for audit
- Validate LLM outputs before returning to client
- Sanitize user input in prompts (prevent injection)

---

## Cost Optimization

1. **Semantic Caching:** Cache similar queries for 5 min
2. **Prompt Compression:** Keep prompts under 500 tokens
3. **Batch Processing:** Group multiple symbol analyses
4. **Model Selection:** Use DeepSeek for bulk, Claude for complex
5. **Output Limits:** Cap response at 500 tokens

**Estimated Monthly Cost (1000 analyses):**
- Claude: ~$15 (500 tokens avg)
- DeepSeek: ~$1.50 (fallback only)
- With 75% cache hit: ~$5/month

---

## Next Steps

After Phase 4 completion:
1. Validate AI output quality with real users
2. Monitor LLM costs and cache hit rate
3. Gather user feedback on recommendation quality
4. Consider adding feedback loop for learning
