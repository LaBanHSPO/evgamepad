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
TECHNICAL_SUMMARY_PROMPT_VI = """Bạn là chuyên gia phân tích kỹ thuật vàng (XAUUSD). Phân tích dữ liệu sau và đưa ra tóm tắt ngắn gọn bằng tiếng Việt.

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
