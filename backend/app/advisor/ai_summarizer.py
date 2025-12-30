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
2. Give recommendation: BUY / SELL / HOLD
3. Confidence level (0-100%)
4. Brief reasoning

## Response format (JSON):
{{"summary": "...", "signal": "BUY/SELL/HOLD", "confidence": 75, "reasoning": "..."}}
"""

PORTFOLIO_ADVICE_PROMPT_VI = """Bạn là cố vấn rủi ro bảo thủ, tập trung vào BẢO VỆ VỐN.

## Trạng thái danh mục đầu tư:
- Số dư tài khoản: ${account_balance}
- Tổng rủi ro hiện tại: {risk_exposure}% (Mục tiêu: <2%)
- Mức sụt giảm hiện tại: {drawdown}%
- Điểm sức khỏe danh mục: {health_score}/100 ({health_status})

## Các vị thế đang mở:
{positions_summary}

## Hồ sơ rủi ro người dùng: {risk_profile}

## Nhiệm vụ của bạn:
1. Đánh giá rủi ro tổng thể của danh mục
2. Xác định vị thế nào cần hành động ngay
3. Đưa ra khuyến nghị cụ thể để BẢO VỆ VỐN
4. Giải thích lý do tập trung vào việc giữ vốn gốc

## Nguyên tắc:
- BẢO VỆ VỐN TRƯỚC, LỢI NHUẬN SAU
- Mất 50% cần tăng 100% để hòa vốn
- Khuyến nghị giảm/đóng vị thế khi rủi ro cao
- Đưa ra hành động ưu tiên cụ thể

## Định dạng phản hồi (JSON):
{{
  "summary": "Tóm tắt tình trạng danh mục trong 2-3 câu",
  "overall_risk": "LOW/MODERATE/HIGH",
  "priority_actions": [
    "Hành động 1: Đóng vị thế XAUUSD để bảo vệ vốn",
    "Hành động 2: Giảm exposure xuống 2%"
  ],
  "reasoning": "Giải thích tại sao cần bảo vệ vốn",
  "confidence": 85
}}
"""

PORTFOLIO_ADVICE_PROMPT_EN = """You are a conservative risk advisor focused on CAPITAL PRESERVATION.

## Portfolio Status:
- Account Balance: ${account_balance}
- Total Risk Exposure: {risk_exposure}% (Target: <2%)
- Current Drawdown: {drawdown}%
- Portfolio Health Score: {health_score}/100 ({health_status})

## Open Positions:
{positions_summary}

## User Risk Profile: {risk_profile}

## Your Task:
1. Assess overall portfolio risk
2. Identify positions requiring immediate action
3. Provide specific recommendations to PROTECT CAPITAL
4. Explain reasoning focused on preserving principle

## Principles:
- PROTECT CAPITAL FIRST, PROFITS SECOND
- 50% loss requires 100% gain just to break even
- Recommend reducing/closing positions when risk high
- Provide specific priority actions

## Response Format (JSON):
{{
  "summary": "Portfolio status summary in 2-3 sentences",
  "overall_risk": "LOW/MODERATE/HIGH",
  "priority_actions": [
    "Action 1: Close XAUUSD position to preserve capital",
    "Action 2: Reduce exposure to 2%"
  ],
  "reasoning": "Explanation of why capital preservation needed",
  "confidence": 85
}}
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
        model: Optional[str] = None,
        temperature: float = 0.5
    ) -> Dict[str, Any]:
        """
        Generate AI summary from technical analysis data.

        Args:
            analysis_data: Dict containing technical indicators, patterns, S/R
            language: "vi" for Vietnamese, "en" for English
            use_cache: Whether to use semantic cache
            model: Override default model ("claude" or "deepseek")
            temperature: Sampling temperature 0.0-1.0 (default: 0.5 for balanced output)

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
                response = await self._call_anthropic(prompt, max_tokens=500, temperature=temperature)
            else:
                response = await self._call_deepseek(prompt, max_tokens=500, temperature=temperature)

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

    async def _call_deepseek(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
        """Call DeepSeek API (OpenAI-compatible) with configurable parameters.

        Args:
            prompt: The prompt to send to DeepSeek
            max_tokens: Maximum tokens in response (default: 500)
            temperature: Sampling temperature 0.0-2.0 (default: 0.7)
        """
        client = self._get_openai_client()
        if client is None:
            raise RuntimeError("OpenAI/DeepSeek client not available")

        def _sync_call():
            response = client.chat.completions.create(
                model="deepseek-chat",
                max_tokens=max_tokens,
                temperature=temperature,
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

    async def generate_portfolio_advice(
        self,
        positions: List[Dict[str, Any]],
        portfolio_health: Dict[str, Any],
        account_balance: float,
        risk_profile: str = "conservative",
        language: str = "vi",
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Generate LLM-powered portfolio analysis with capital preservation focus.

        Args:
            positions: List of analyzed positions
            portfolio_health: Portfolio health metrics
            account_balance: Total account balance
            risk_profile: User risk tolerance
            language: Output language
            use_cache: Whether to use semantic caching

        Returns:
            AI advice with summary, actions, reasoning
        """
        # Build positions summary text with sanitization
        def sanitize_text(text: str) -> str:
            """Sanitize text to prevent prompt injection."""
            return str(text).replace('\n', ' ').replace('\r', '')[:100]

        positions_summary = "\n".join([
            f"- {sanitize_text(p['symbol'])}: Entry {p['entry_price']}, Current {p['current_price']}, "
            f"P&L {p['pnl_pct']}%, R-Multiple {p['r_multiple']}, "
            f"Status: {sanitize_text(p['risk_status'])}, Tech Signal: {sanitize_text(p['technical_signal'])}"
            for p in positions
        ])

        # Prepare prompt data
        prompt_data = {
            "account_balance": account_balance,
            "risk_exposure": portfolio_health["total_risk_exposure"],
            "drawdown": portfolio_health["current_drawdown"],
            "health_score": portfolio_health["score"],
            "health_status": portfolio_health["status"],
            "positions_summary": positions_summary,
            "risk_profile": risk_profile
        }

        # Generate cache key
        cache_key = None
        if use_cache and self.redis:
            cache_key = self._generate_portfolio_advice_cache_key(prompt_data)
            cached = await self._check_cache(cache_key)
            if cached:
                logger.debug("Portfolio advice cache hit")
                cached["cached"] = True
                return cached

        # Select prompt template
        prompt_template = (
            PORTFOLIO_ADVICE_PROMPT_VI if language == "vi"
            else PORTFOLIO_ADVICE_PROMPT_EN
        )
        prompt = prompt_template.format(**prompt_data)

        # Call LLM
        try:
            # Try Claude first
            client = self._get_anthropic_client()
            if client:
                response_text = await self._call_anthropic(prompt, max_tokens=1024, temperature=0.3)
            # Fallback to DeepSeek
            else:
                client = self._get_openai_client()
                if not client:
                    raise ValueError("No LLM client available")
                response_text = await self._call_deepseek(prompt, max_tokens=1024, temperature=0.3)

            # Parse JSON response
            try:
                advice = json.loads(response_text)
            except json.JSONDecodeError:
                # Fallback parsing with truncation
                logger.warning("Failed to parse LLM JSON, attempting fallback")
                advice = {
                    "summary": response_text[:500],  # Limit to 500 chars
                    "overall_risk": "MODERATE",
                    "priority_actions": [],
                    "reasoning": "Unable to parse structured response",
                    "confidence": 50,
                    "raw_response_truncated": response_text[:2000]  # Store more for debugging
                }

            # Add metadata
            advice["model"] = "claude" if self._anthropic_client else "deepseek"
            advice["language"] = language
            advice["cached"] = False
            advice["generated_at"] = datetime.utcnow().isoformat()

            # Cache result
            if use_cache and cache_key:
                await self._save_to_cache(cache_key, advice, ttl=300)

            return advice

        except Exception as e:
            logger.exception(f"Portfolio advice generation failed: {e}")
            # Return fallback advice
            return {
                "error": str(e),
                "summary": "Unable to generate AI advice due to API error",
                "overall_risk": "MODERATE",
                "priority_actions": [
                    "Review portfolio manually",
                    "Consider reducing high-risk positions"
                ],
                "reasoning": "AI service temporarily unavailable",
                "confidence": 0,
                "model": "fallback",
                "language": language,
                "cached": False
            }

    def _generate_portfolio_advice_cache_key(self, prompt_data: Dict[str, Any]) -> str:
        """Generate cache key for portfolio advice."""
        key_data = {
            "risk_exposure_bucket": round(prompt_data["risk_exposure"], 0),
            "drawdown_bucket": round(prompt_data["drawdown"], 0),
            "health_score_bucket": round(prompt_data["health_score"] / 10) * 10,
            "risk_profile": prompt_data["risk_profile"],
            # Hash positions summary for deterministic key
            "positions_hash": hashlib.md5(
                prompt_data["positions_summary"].encode()
            ).hexdigest()[:8]
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return f"portfolio_advice:{hashlib.md5(key_str.encode()).hexdigest()}"

    async def _call_anthropic(self, prompt: str, max_tokens: int = 1024, temperature: float = 0.7) -> str:
        """Call Claude API with configurable parameters.

        Args:
            prompt: The prompt to send to Claude
            max_tokens: Maximum tokens in response (default: 1024)
            temperature: Sampling temperature 0.0-1.0 (default: 0.7)
        """
        def _sync_call():
            response = self._get_anthropic_client().messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text

        return await asyncio.to_thread(_sync_call)
