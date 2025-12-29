# Phase 3: AI Trading Advisor with Multi-Source Analysis

**Duration**: Week 3-5 (3 weeks - expanded from original Phase 3)
**Goal**: Vietnamese voice trading advisor with comprehensive market analysis
**Prerequisites**: Phase 1-2 complete
**Status**: Not Started
**Supersedes**: `phase-03-voice-interaction-llm.md` (simple function-calling)

---

## WHAT CHANGED FROM PHASE 3 LLM

| Component | Phase 3 LLM (Old) | Phase 3 AI Advisor (New) |
|-----------|-------------------|-------------------------|
| **Purpose** | Intent extraction only | Comprehensive analysis + recommendation |
| **LLM Role** | Function-calling classifier | Analytical reasoner with RAG context |
| **Data Sources** | None (market data only) | Sentiment, news, indicators, KOL, patterns |
| **Memory** | Single-turn | Multi-turn conversation context |
| **Response** | Static templates | Streaming + Chain-of-Thought |
| **Legal** | None | Mandatory disclaimers + audit trail |
| **Cost** | $8-35/month | $5-150/month (depends on model mix) |
| **Latency** | 165ms | 2-5s (acceptable for advisory) |

**Why Change?**
- User wants AI to be a **trading advisor**, not just a command executor
- Must aggregate: sentiment, trends, news, indicators, KOL signals, patterns
- Needs analytical reasoning ("Why should I buy gold?"), not just "Buy executed"

---

## ARCHITECTURE OVERVIEW

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                        AI TRADING ADVISOR FLOW                                 │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  User: "Toi nen mua vang khong?" (Should I buy gold?)                        │
│       │                                                                       │
│       ▼                                                                       │
│  ┌─────────────┐                                                              │
│  │ Whisper STT │ (150-300ms)                                                  │
│  └──────┬──────┘                                                              │
│         │                                                                     │
│         ▼                                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐         │
│  │              DATA AGGREGATION LAYER (Parallel)                   │         │
│  ├─────────────────────────────────────────────────────────────────┤         │
│  │  ┌───────────┐ ┌──────────┐ ┌─────────┐ ┌──────────┐ ┌────────┐│         │
│  │  │ Sentiment │ │ Trends   │ │ NEWS    │ │ KOL      │ │ Patterns││         │
│  │  │ Service   │ │ M5-D1    │ │ Service │ │ Signals  │ │ Service ││         │
│  │  └─────┬─────┘ └────┬─────┘ └────┬────┘ └────┬─────┘ └────┬────┘│         │
│  │        └─────────────┼───────────┼───────────┼────────────┘     │         │
│  │                      ▼                                          │         │
│  │              [Aggregated Context JSON]                          │         │
│  └──────────────────────┬──────────────────────────────────────────┘         │
│                         │ (~500-1000ms parallel)                             │
│                         ▼                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐         │
│  │                    CONTEXT MANAGER (RAG)                         │         │
│  ├─────────────────────────────────────────────────────────────────┤         │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │         │
│  │  │ Conversation    │  │ Market Context  │  │ User Context    │  │         │
│  │  │ History (5 msg) │  │ (aggregated)    │  │ (preferences)   │  │         │
│  │  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  │         │
│  │           └───────────────────┬───────────────────┬─┘           │         │
│  │                               ▼                                  │         │
│  │                    [Combined RAG Context]                        │         │
│  └──────────────────────┬──────────────────────────────────────────┘         │
│                         │                                                     │
│                         ▼                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐         │
│  │                    LLM REASONING CHAIN                           │         │
│  ├─────────────────────────────────────────────────────────────────┤         │
│  │  System Prompt + RAG Context + User Query                        │         │
│  │       │                                                          │         │
│  │       ▼                                                          │         │
│  │  ┌─────────────────────────────────────────────────────────────┐│         │
│  │  │ LiteLLM Streaming (GPT-4o / Claude 3.5 / DeepSeek R1)       ││         │
│  │  │ Chain-of-Thought Reasoning                                   ││         │
│  │  └──────────────────────────┬──────────────────────────────────┘│         │
│  │                             │ (1-3s streaming)                   │         │
│  │                             ▼                                    │         │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │         │
│  │  │ Analysis    │  │ Reasoning   │  │ Recommend-  │              │         │
│  │  │ Summary     │  │ Explanation │  │ ation       │              │         │
│  │  └─────────────┘  └─────────────┘  └─────────────┘              │         │
│  └──────────────────────┬──────────────────────────────────────────┘         │
│                         │                                                     │
│                         ▼                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐         │
│  │                    RESPONSE HANDLER                              │         │
│  ├─────────────────────────────────────────────────────────────────┤         │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │         │
│  │  │ Stream      │  │ Append      │  │ Save Audit  │              │         │
│  │  │ to Socket   │  │ Disclaimer  │  │ Trail       │              │         │
│  │  └─────────────┘  └─────────────┘  └─────────────┘              │         │
│  └──────────────────────┬──────────────────────────────────────────┘         │
│                         │                                                     │
│                         ▼                                                     │
│  ┌─────────────┐                                                              │
│  │ VieNeu TTS  │ (100-200ms)                                                  │
│  └──────┬──────┘                                                              │
│         │                                                                     │
│         ▼                                                                     │
│  User hears comprehensive analysis + recommendation                           │
│                                                                               │
│  TOTAL LATENCY: 2-5 seconds (advisory mode, acceptable)                       │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## DATA AGGREGATION LAYER

### 3.1 Data Sources Overview

| Source | API/Method | Update Freq | Cache TTL | Cost |
|--------|-----------|-------------|-----------|------|
| **Sentiment** | Fear & Greed API | 1h | 30min | Free |
| **Trends** | TwelveData (existing) | Real-time | 5s | $79/mo (existing) |
| **News** | NewsAPI | 1h | 30min | Free tier |
| **KOL Signals** | Zalo/Telegram groups | Manual/15min | 10min | $0 (free) |
| **Patterns** | `ta` library (existing Phase 4) | 5min | 5min | Free |
| **Multi-TF** | TwelveData REST | On-demand | 1min | Included |

### 3.2 Sentiment Service

**File**: `backend/app/capital_companion/sentiment_service.py`

```python
"""
Aggregates market sentiment from multiple sources
Sources: Fear & Greed Index, social sentiment, news sentiment
"""
from dataclasses import dataclass
from typing import Optional
import httpx
from datetime import datetime

@dataclass
class SentimentData:
    overall: str  # "fear", "neutral", "greed"
    score: float  # -1.0 to 1.0
    fear_greed_index: int  # 0-100
    social_sentiment: Optional[float]  # Twitter/Reddit score
    news_sentiment: Optional[float]  # VADER on recent news
    last_updated: datetime
    sources_count: int

class SentimentService:
    """Aggregates sentiment from multiple sources"""

    FEAR_GREED_API = "https://api.alternative.me/fng/"

    async def get_sentiment(self, symbol: str) -> SentimentData:
        """Get aggregated sentiment for symbol"""
        # Fetch in parallel
        tasks = [
            self._fetch_fear_greed(symbol),
            self._fetch_news_sentiment(symbol),
            self._fetch_social_sentiment(symbol)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Aggregate
        return self._aggregate_sentiment(results)

    async def _fetch_fear_greed(self, symbol: str) -> dict:
        """Fetch Fear & Greed Index (crypto/general market)"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(self.FEAR_GREED_API)
            data = resp.json()
            return {
                "index": int(data["data"][0]["value"]),
                "classification": data["data"][0]["value_classification"]
            }

    async def _fetch_news_sentiment(self, symbol: str) -> float:
        """Analyze recent news headlines with VADER"""
        # Reuse Phase 5 sentiment_analyzer.py
        from app.capital_companion.sentiment_analyzer import SentimentAnalyzer
        analyzer = SentimentAnalyzer()
        return await analyzer.analyze(symbol)

    async def _fetch_social_sentiment(self, symbol: str) -> Optional[float]:
        """Fetch Twitter/social sentiment for symbol"""
        # KOL service handles this
        kol_service = get_kol_service()
        signals = await kol_service.get_signals(symbol, limit=10)
        if not signals:
            return None
        return sum(s.sentiment for s in signals) / len(signals)

    def _aggregate_sentiment(self, results: list) -> SentimentData:
        """Combine all sentiment sources into single score"""
        fear_greed = results[0] if not isinstance(results[0], Exception) else None
        news = results[1] if not isinstance(results[1], Exception) else None
        social = results[2] if not isinstance(results[2], Exception) else None

        # Weighted average
        weights = {"fear_greed": 0.4, "news": 0.35, "social": 0.25}
        total_weight = 0
        weighted_score = 0

        if fear_greed:
            # Normalize 0-100 to -1 to 1
            normalized = (fear_greed["index"] - 50) / 50
            weighted_score += normalized * weights["fear_greed"]
            total_weight += weights["fear_greed"]

        if news is not None:
            weighted_score += news * weights["news"]
            total_weight += weights["news"]

        if social is not None:
            weighted_score += social * weights["social"]
            total_weight += weights["social"]

        final_score = weighted_score / total_weight if total_weight > 0 else 0

        # Classify
        if final_score > 0.3:
            overall = "greed"
        elif final_score < -0.3:
            overall = "fear"
        else:
            overall = "neutral"

        return SentimentData(
            overall=overall,
            score=final_score,
            fear_greed_index=fear_greed["index"] if fear_greed else 50,
            social_sentiment=social,
            news_sentiment=news,
            last_updated=datetime.utcnow(),
            sources_count=sum(1 for r in results if not isinstance(r, Exception))
        )
```

### 3.3 KOL Signals Service (Zalo/Telegram Integration)

**File**: `backend/app/capital_companion/kol_service.py`

**User Decision**: No Twitter API needed ($100/mo saved). User has access to Zalo/Telegram groups with KOL signals. Start with manual entry, add API integration later if available.

```python
"""
Key Opinion Leader signals aggregation
Sources: Zalo groups, Telegram groups (manual entry initially, API later)
"""
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
from enum import Enum
import json

class SignalSource(str, Enum):
    ZALO = "zalo"
    TELEGRAM = "telegram"
    MANUAL = "manual"

@dataclass
class KOLSignal:
    author: str
    platform: str  # "zalo", "telegram", "manual"
    content: str
    sentiment: float  # -1.0 to 1.0
    signal_type: str  # "buy", "sell", "hold", "info"
    symbol: str
    timestamp: datetime
    confidence: float  # 0-1, user-assigned or derived
    metadata: dict  # Extra info (group name, etc)

class KOLService:
    """
    Aggregates signals from Key Opinion Leaders

    Phase 1 (MVP): Manual signal entry via API/UI
    Phase 2 (Future): Telegram Bot API integration
    Phase 3 (Future): Zalo webhook integration (if available)
    """

    def __init__(self):
        self.redis = get_redis_client()
        self.postgres = get_postgres_client()

    async def get_signals(self, symbol: str, limit: int = 10) -> List[KOLSignal]:
        """Get recent KOL signals for symbol"""
        # Check cache first
        cached = await self.redis.get(f"kol:{symbol}")
        if cached:
            data = json.loads(cached)
            return [KOLSignal(**s) for s in data]

        # Fetch from database
        signals = await self._fetch_stored_signals(symbol, limit)

        # Cache for 10 minutes
        if signals:
            await self.redis.set(
                f"kol:{symbol}",
                json.dumps([s.__dict__ for s in signals], default=str),
                ex=600
            )

        return signals

    async def add_signal(
        self,
        author: str,
        content: str,
        symbol: str,
        signal_type: str,  # "buy", "sell", "hold"
        platform: str = "manual",
        confidence: float = 0.7,
        metadata: Optional[dict] = None
    ) -> KOLSignal:
        """
        Add KOL signal manually (MVP flow)
        Called via API endpoint or admin UI
        """
        sentiment = self._derive_sentiment(signal_type, content)

        signal = KOLSignal(
            author=author,
            platform=platform,
            content=content[:500],  # Limit content length
            sentiment=sentiment,
            signal_type=signal_type,
            symbol=symbol.upper(),
            timestamp=datetime.utcnow(),
            confidence=confidence,
            metadata=metadata or {}
        )

        # Store in database
        await self._store_signal(signal)

        # Invalidate cache
        await self.redis.delete(f"kol:{symbol}")

        return signal

    async def _fetch_stored_signals(self, symbol: str, limit: int) -> List[KOLSignal]:
        """Fetch signals from PostgreSQL"""
        rows = await self.postgres.fetch("""
            SELECT author, platform, content, sentiment, signal_type,
                   symbol, timestamp, confidence, metadata
            FROM kol_signals
            WHERE symbol = $1
            AND timestamp > NOW() - INTERVAL '24 hours'
            ORDER BY timestamp DESC
            LIMIT $2
        """, symbol, limit)

        return [
            KOLSignal(
                author=r["author"],
                platform=r["platform"],
                content=r["content"],
                sentiment=r["sentiment"],
                signal_type=r["signal_type"],
                symbol=r["symbol"],
                timestamp=r["timestamp"],
                confidence=r["confidence"],
                metadata=r["metadata"] or {}
            )
            for r in rows
        ]

    async def _store_signal(self, signal: KOLSignal):
        """Store signal in PostgreSQL"""
        await self.postgres.execute("""
            INSERT INTO kol_signals (
                author, platform, content, sentiment, signal_type,
                symbol, timestamp, confidence, metadata
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """,
            signal.author, signal.platform, signal.content,
            signal.sentiment, signal.signal_type, signal.symbol,
            signal.timestamp, signal.confidence, json.dumps(signal.metadata)
        )

    def _derive_sentiment(self, signal_type: str, content: str) -> float:
        """Derive sentiment score from signal type and content"""
        base_sentiment = {
            "buy": 0.7,
            "sell": -0.7,
            "hold": 0.0,
            "info": 0.0
        }.get(signal_type.lower(), 0.0)

        # Adjust based on content keywords (Vietnamese + English)
        bullish_words = ["mua", "long", "tăng", "buy", "bullish", "breakout", "hỗ trợ"]
        bearish_words = ["bán", "short", "giảm", "sell", "bearish", "breakdown", "kháng cự"]

        content_lower = content.lower()
        bullish_count = sum(1 for w in bullish_words if w in content_lower)
        bearish_count = sum(1 for w in bearish_words if w in content_lower)

        # Modify base sentiment by content analysis
        content_modifier = (bullish_count - bearish_count) * 0.1
        return max(-1.0, min(1.0, base_sentiment + content_modifier))

    def _analyze_signal_sentiment(self, text: str) -> float:
        """Quick sentiment analysis of signal text"""
        bullish_words = ["mua", "long", "tăng", "buy", "bullish", "breakout", "moon"]
        bearish_words = ["bán", "short", "giảm", "sell", "bearish", "crash", "dump"]

        text_lower = text.lower()
        bullish_count = sum(1 for w in bullish_words if w in text_lower)
        bearish_count = sum(1 for w in bearish_words if w in text_lower)

        if bullish_count > bearish_count:
            return 0.5
        elif bearish_count > bullish_count:
            return -0.5
        return 0.0


# --- Future: Telegram Bot Integration (Phase 2) ---
#
# class TelegramKOLBot:
#     """
#     Telegram bot to capture signals from groups
#     User adds bot to group, bot captures messages with trading keywords
#     """
#     def __init__(self, bot_token: str):
#         self.bot_token = bot_token
#         self.kol_service = KOLService()
#
#     async def handle_message(self, update: dict):
#         message = update.get("message", {})
#         text = message.get("text", "")
#
#         if self._is_trading_signal(text):
#             await self.kol_service.add_signal(
#                 author=message.get("from", {}).get("username", "unknown"),
#                 content=text,
#                 symbol=self._extract_symbol(text),
#                 signal_type=self._extract_signal_type(text),
#                 platform="telegram",
#                 metadata={"chat_id": message.get("chat", {}).get("id")}
#             )
```

### 3.4 Multi-Timeframe Analysis Service

**File**: `backend/app/capital_companion/multiframe_service.py`

```python
"""
Multi-timeframe trend analysis
Timeframes: M5, M15, H1, H4, D1
"""
from dataclasses import dataclass
from typing import Dict, List
from datetime import datetime

@dataclass
class TimeframeTrend:
    timeframe: str
    trend: str  # "bullish", "bearish", "neutral"
    strength: float  # 0-1
    last_close: float
    sma_20: float
    rsi: float
    support: float
    resistance: float

@dataclass
class MultiFrameAnalysis:
    symbol: str
    timeframes: Dict[str, TimeframeTrend]
    consensus: str  # overall trend direction
    alignment_score: float  # how aligned are all timeframes
    timestamp: datetime

class MultiFrameService:
    """Analyzes trends across multiple timeframes"""

    TIMEFRAMES = ["5min", "15min", "1h", "4h", "1day"]
    TF_DISPLAY = {"5min": "M5", "15min": "M15", "1h": "H1", "4h": "H4", "1day": "D1"}

    def __init__(self):
        self.market_service = get_market_data_service()
        self.pattern_analyzer = get_pattern_analyzer()

    async def analyze(self, symbol: str) -> MultiFrameAnalysis:
        """Analyze symbol across all timeframes"""
        timeframes = {}

        # Fetch and analyze each timeframe in parallel
        tasks = [
            self._analyze_timeframe(symbol, tf)
            for tf in self.TIMEFRAMES
        ]
        results = await asyncio.gather(*tasks)

        for tf, result in zip(self.TIMEFRAMES, results):
            timeframes[self.TF_DISPLAY[tf]] = result

        # Calculate consensus
        consensus, alignment = self._calculate_consensus(timeframes)

        return MultiFrameAnalysis(
            symbol=symbol,
            timeframes=timeframes,
            consensus=consensus,
            alignment_score=alignment,
            timestamp=datetime.utcnow()
        )

    async def _analyze_timeframe(self, symbol: str, timeframe: str) -> TimeframeTrend:
        """Analyze single timeframe"""
        # Fetch historical data
        df = await self.market_service.get_historical(
            symbol=symbol,
            interval=timeframe,
            outputsize=100
        )

        # Calculate indicators (reuse from Phase 4)
        from ta.trend import SMAIndicator
        from ta.momentum import RSIIndicator

        sma_20 = SMAIndicator(df['close'], window=20).sma_indicator().iloc[-1]
        rsi = RSIIndicator(df['close'], window=14).rsi().iloc[-1]

        # Determine trend
        last_close = df['close'].iloc[-1]
        if last_close > sma_20 and rsi > 50:
            trend = "bullish"
            strength = min((rsi - 50) / 30, 1.0)
        elif last_close < sma_20 and rsi < 50:
            trend = "bearish"
            strength = min((50 - rsi) / 30, 1.0)
        else:
            trend = "neutral"
            strength = 0.5

        # Calculate support/resistance (simplified)
        support = df['low'].rolling(20).min().iloc[-1]
        resistance = df['high'].rolling(20).max().iloc[-1]

        return TimeframeTrend(
            timeframe=self.TF_DISPLAY[timeframe],
            trend=trend,
            strength=strength,
            last_close=last_close,
            sma_20=sma_20,
            rsi=rsi,
            support=support,
            resistance=resistance
        )

    def _calculate_consensus(self, timeframes: Dict[str, TimeframeTrend]) -> tuple:
        """Calculate overall consensus from all timeframes"""
        bullish_count = sum(1 for tf in timeframes.values() if tf.trend == "bullish")
        bearish_count = sum(1 for tf in timeframes.values() if tf.trend == "bearish")
        total = len(timeframes)

        if bullish_count >= 4:
            consensus = "strong_bullish"
        elif bullish_count >= 3:
            consensus = "bullish"
        elif bearish_count >= 4:
            consensus = "strong_bearish"
        elif bearish_count >= 3:
            consensus = "bearish"
        else:
            consensus = "mixed"

        # Alignment score: how many timeframes agree
        max_alignment = max(bullish_count, bearish_count)
        alignment = max_alignment / total

        return consensus, alignment
```

### 3.5 Data Aggregator (Main Service)

**File**: `backend/app/capital_companion/data_aggregator.py`

```python
"""
Main data aggregation service
Combines all sources into unified context for LLM
"""
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio
import json

@dataclass
class AggregatedContext:
    """All market data aggregated for LLM context"""
    symbol: str
    current_price: float
    price_change_24h: float
    sentiment: Dict[str, Any]
    multiframe: Dict[str, Any]
    patterns: Dict[str, Any]
    kol_signals: list
    news_headlines: list
    timestamp: datetime

    def to_llm_context(self) -> str:
        """Format as text for LLM prompt"""
        return f"""
## Market Context for {self.symbol}

### Current Price
- Price: ${self.current_price:,.2f}
- 24h Change: {self.price_change_24h:+.2f}%

### Market Sentiment
- Overall: {self.sentiment.get('overall', 'unknown').upper()}
- Fear & Greed Index: {self.sentiment.get('fear_greed_index', 50)}/100
- News Sentiment: {self.sentiment.get('news_sentiment', 0):.2f}

### Multi-Timeframe Trends
{self._format_multiframe()}

### Technical Patterns
{self._format_patterns()}

### KOL Signals (Top 5)
{self._format_kol_signals()}

### Recent News
{self._format_news()}
"""

    def _format_multiframe(self) -> str:
        lines = []
        for tf, data in self.multiframe.get('timeframes', {}).items():
            trend = data.get('trend', 'unknown')
            rsi = data.get('rsi', 50)
            lines.append(f"- {tf}: {trend.upper()} (RSI: {rsi:.0f})")
        lines.append(f"- Consensus: {self.multiframe.get('consensus', 'unknown')}")
        lines.append(f"- Alignment: {self.multiframe.get('alignment_score', 0):.0%}")
        return "\n".join(lines)

    def _format_patterns(self) -> str:
        patterns = self.patterns.get('patterns', [])
        if not patterns:
            return "- No significant patterns detected"
        return "\n".join(f"- {p['type']}: {p.get('description', '')} (confidence: {p.get('confidence', 0):.0%})" for p in patterns[:3])

    def _format_kol_signals(self) -> str:
        if not self.kol_signals:
            return "- No recent KOL signals"
        lines = []
        for s in self.kol_signals[:5]:
            sentiment = "Bullish" if s.get('sentiment', 0) > 0 else "Bearish" if s.get('sentiment', 0) < 0 else "Neutral"
            lines.append(f"- @{s.get('author', 'unknown')}: {sentiment} - \"{s.get('content', '')[:80]}...\"")
        return "\n".join(lines)

    def _format_news(self) -> str:
        if not self.news_headlines:
            return "- No recent news"
        return "\n".join(f"- {h[:100]}" for h in self.news_headlines[:5])


class DataAggregator:
    """Aggregates all data sources for LLM context"""

    def __init__(self):
        self.sentiment_service = get_sentiment_service()
        self.multiframe_service = get_multiframe_service()
        self.pattern_analyzer = get_pattern_analyzer()
        self.kol_service = get_kol_service()
        self.news_service = get_news_service()
        self.market_service = get_market_data_service()
        self.redis = get_redis_client()

    async def aggregate(self, symbol: str) -> AggregatedContext:
        """Aggregate all data sources for symbol"""
        cache_key = f"context:{symbol}"

        # Check cache (30s TTL for real-time feel)
        cached = await self.redis.get(cache_key)
        if cached:
            return AggregatedContext(**json.loads(cached))

        # Fetch all sources in parallel
        results = await asyncio.gather(
            self.market_service.get_cached_price(symbol),
            self.sentiment_service.get_sentiment(symbol),
            self.multiframe_service.analyze(symbol),
            self.pattern_analyzer.analyze(symbol, "H4"),
            self.kol_service.get_signals(symbol, limit=5),
            self.news_service.get_headlines(symbol, limit=5),
            return_exceptions=True
        )

        price_data, sentiment, multiframe, patterns, kol_signals, news = results

        # Build context
        context = AggregatedContext(
            symbol=symbol,
            current_price=price_data.get("price", 0) if isinstance(price_data, dict) else 0,
            price_change_24h=price_data.get("change_percent", 0) if isinstance(price_data, dict) else 0,
            sentiment=asdict(sentiment) if not isinstance(sentiment, Exception) else {},
            multiframe=asdict(multiframe) if not isinstance(multiframe, Exception) else {},
            patterns=patterns if not isinstance(patterns, Exception) else {},
            kol_signals=[asdict(s) for s in kol_signals] if not isinstance(kol_signals, Exception) else [],
            news_headlines=news if not isinstance(news, Exception) else [],
            timestamp=datetime.utcnow()
        )

        # Cache for 30 seconds
        await self.redis.set(cache_key, json.dumps(asdict(context), default=str), ex=30)

        return context
```

---

## CONTEXT MANAGEMENT (MEMORY)

### 3.6 Conversation Memory

**File**: `backend/app/capital_companion/memory_manager.py`

```python
"""
Conversation and context memory management
Stores: conversation history, user preferences, market context
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

@dataclass
class Message:
    role: str  # "user", "assistant"
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ConversationContext:
    session_id: str
    user_id: str
    messages: List[Message]
    current_symbol: Optional[str]
    user_preferences: Dict[str, Any]
    market_context: Optional[str]  # Last aggregated context

class MemoryManager:
    """Manages conversation memory and context"""

    MAX_MESSAGES = 10  # Keep last 10 messages
    CONTEXT_TTL = 1800  # 30 minutes

    def __init__(self):
        self.redis = get_redis_client()

    async def get_context(self, session_id: str, user_id: str) -> ConversationContext:
        """Get or create conversation context"""
        cache_key = f"conv:{session_id}"

        cached = await self.redis.get(cache_key)
        if cached:
            data = json.loads(cached)
            return ConversationContext(
                session_id=session_id,
                user_id=user_id,
                messages=[Message(**m) for m in data.get("messages", [])],
                current_symbol=data.get("current_symbol"),
                user_preferences=data.get("user_preferences", {}),
                market_context=data.get("market_context")
            )

        # Load user preferences from database
        preferences = await self._load_user_preferences(user_id)

        return ConversationContext(
            session_id=session_id,
            user_id=user_id,
            messages=[],
            current_symbol=None,
            user_preferences=preferences,
            market_context=None
        )

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ):
        """Add message to conversation history"""
        context = await self.get_context(session_id, "")

        message = Message(
            role=role,
            content=content,
            timestamp=datetime.utcnow(),
            metadata=metadata or {}
        )

        context.messages.append(message)

        # Keep only last N messages
        if len(context.messages) > self.MAX_MESSAGES:
            context.messages = context.messages[-self.MAX_MESSAGES:]

        await self._save_context(context)

    async def update_market_context(self, session_id: str, market_context: str):
        """Update current market context"""
        context = await self.get_context(session_id, "")
        context.market_context = market_context
        await self._save_context(context)

    async def set_current_symbol(self, session_id: str, symbol: str):
        """Set the symbol user is discussing"""
        context = await self.get_context(session_id, "")
        context.current_symbol = symbol
        await self._save_context(context)

    async def _save_context(self, context: ConversationContext):
        """Save context to Redis"""
        cache_key = f"conv:{context.session_id}"
        data = {
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp.isoformat(),
                    "metadata": m.metadata
                }
                for m in context.messages
            ],
            "current_symbol": context.current_symbol,
            "user_preferences": context.user_preferences,
            "market_context": context.market_context
        }
        await self.redis.set(cache_key, json.dumps(data), ex=self.CONTEXT_TTL)

    async def _load_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Load user preferences from database"""
        if not user_id:
            return {}

        postgres = get_postgres_client()
        profile = await postgres.get_user_profile(user_id)

        return {
            "risk_tolerance": profile.get("risk_tolerance", "moderate"),
            "preferred_timeframes": profile.get("preferred_timeframes", ["H4", "D1"]),
            "watchlist": profile.get("watchlist", ["XAUUSD", "BTCUSD"]),
            "language": profile.get("language", "vi")
        }

    def format_for_llm(self, context: ConversationContext) -> str:
        """Format conversation context for LLM prompt"""
        parts = []

        # User preferences
        prefs = context.user_preferences
        parts.append(f"""## User Profile
- Risk Tolerance: {prefs.get('risk_tolerance', 'moderate')}
- Preferred Timeframes: {', '.join(prefs.get('preferred_timeframes', []))}
- Watchlist: {', '.join(prefs.get('watchlist', []))}
""")

        # Conversation history
        if context.messages:
            parts.append("## Conversation History")
            for msg in context.messages[-5:]:  # Last 5 messages
                role_label = "User" if msg.role == "user" else "Atlas"
                parts.append(f"{role_label}: {msg.content}")

        # Market context
        if context.market_context:
            parts.append(context.market_context)

        return "\n\n".join(parts)
```

---

## LLM REASONING CHAIN

### 3.7 AI Advisor Service (Core)

**File**: `backend/app/capital_companion/ai_advisor_service.py`

```python
"""
AI Trading Advisor - Core reasoning service
Uses LLM with RAG context for comprehensive analysis
"""
import logging
from typing import AsyncGenerator, Dict, Any, Optional
from litellm import acompletion
from datetime import datetime

from app.capital_companion.data_aggregator import DataAggregator, AggregatedContext
from app.capital_companion.memory_manager import MemoryManager, ConversationContext
from app.capital_companion.legal_compliance import LegalCompliance

logger = logging.getLogger(__name__)

class AIAdvisorService:
    """
    AI Trading Advisor with multi-source analysis

    Flow:
    1. Extract symbol from user query
    2. Aggregate market data (parallel)
    3. Build RAG context (memory + market + user)
    4. Stream LLM reasoning
    5. Conditionally append legal disclaimer (only on trade recommendations)
    6. Save audit trail

    Supports: GPT-4o and DeepSeek for A/B testing
    """

    # Supported models for A/B testing
    SUPPORTED_MODELS = {
        "gpt-4o": {
            "name": "gpt-4o",
            "provider": "openai",
            "cost_per_1k_input": 0.0025,
            "cost_per_1k_output": 0.01
        },
        "deepseek": {
            "name": "deepseek/deepseek-chat",  # LiteLLM format
            "provider": "deepseek",
            "cost_per_1k_input": 0.00014,
            "cost_per_1k_output": 0.00028
        }
    }

    SYSTEM_PROMPT = """Bạn là Atlas, trợ lý giao dịch tài chính chuyên nghiệp.

Nhiệm vụ: Phân tích thị trường và đưa ra khuyến nghị giao dịch dựa trên dữ liệu được cung cấp.

Quy tắc:
1. LUÔN dựa vào dữ liệu thực tế được cung cấp, KHÔNG bịa đặt
2. Giải thích logic phân tích rõ ràng (Chain-of-Thought)
3. Đưa ra khuyến nghị cụ thể: MUA, BÁN, hoặc CHỜ
4. Nêu rõ mức độ tin cậy và rủi ro
5. Trả lời bằng tiếng Việt tự nhiên, ngắn gọn

Cấu trúc trả lời:
1. **Tóm tắt thị trường** (2-3 câu)
2. **Phân tích** (các yếu tố quan trọng)
3. **Khuyến nghị** (hành động + lý do)
4. **Cảnh báo rủi ro** (nếu có)

Bạn KHÔNG được:
- Bịa số liệu
- Đưa ra lời khuyên tài chính mà không có disclaimer
- Khẳng định chắc chắn về giá tương lai"""

    def __init__(self, model: str = "gpt-4o"):
        """
        Initialize AI Advisor with model selection

        Args:
            model: "gpt-4o" or "deepseek" - can be changed per-request
        """
        self.default_model = model
        self.data_aggregator = DataAggregator()
        self.memory_manager = MemoryManager()
        self.legal = LegalCompliance()

    def get_model_name(self, model_key: str) -> str:
        """Get LiteLLM model name from key"""
        model_config = self.SUPPORTED_MODELS.get(model_key, self.SUPPORTED_MODELS["gpt-4o"])
        return model_config["name"]

    async def analyze(
        self,
        query: str,
        session_id: str,
        user_id: str,
        model: Optional[str] = None  # Override model per-request
    ) -> AsyncGenerator[str, None]:
        """
        Analyze user query and stream response

        Args:
            query: User's question in Vietnamese
            session_id: Conversation session ID
            user_id: User identifier
            model: Optional model override ("gpt-4o" or "deepseek")

        Yields:
            str: Chunks of response text (for streaming)
        """
        # Select model (per-request override or default)
        selected_model = model or self.default_model
        model_name = self.get_model_name(selected_model)

        try:
            # Step 1: Extract symbol from query
            symbol = await self._extract_symbol(query)
            if not symbol:
                yield "Xin lỗi, bạn muốn phân tích tài sản nào? (Vàng, Bitcoin, Ethereum)"
                return

            # Step 2: Get conversation context
            conv_context = await self.memory_manager.get_context(session_id, user_id)
            await self.memory_manager.set_current_symbol(session_id, symbol)

            # Step 3: Aggregate market data
            yield "Đang thu thập dữ liệu thị trường... "
            market_context = await self.data_aggregator.aggregate(symbol)

            # Step 4: Build RAG context
            rag_context = self._build_rag_context(conv_context, market_context, query)

            # Step 5: Stream LLM response
            full_response = ""
            async for chunk in self._stream_llm_response(rag_context, model_name):
                full_response += chunk
                yield chunk

            # Step 6: Conditionally append legal disclaimer
            # Only append if response contains trade recommendation (buy/sell/hold)
            if self.legal.contains_recommendation(full_response):
                disclaimer = self.legal.get_disclaimer("vi")
                yield f"\n\n---\n{disclaimer}"

            # Step 7: Save to memory and audit
            await self.memory_manager.add_message(session_id, "user", query)
            await self.memory_manager.add_message(
                session_id,
                "assistant",
                full_response,
                metadata={
                    "symbol": symbol,
                    "model": selected_model,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

            # Save audit trail (only if recommendation was made)
            if self.legal.contains_recommendation(full_response):
                await self.legal.save_audit(
                    user_id=user_id,
                    session_id=session_id,
                    query=query,
                    response=full_response,
                    symbol=symbol,
                    model=selected_model,
                    context_snapshot=market_context.to_llm_context()
                )

        except Exception as e:
            logger.error(f"AI Advisor error: {e}")
            yield f"Xin lỗi, đã xảy ra lỗi khi phân tích. Vui lòng thử lại."

    async def _extract_symbol(self, query: str) -> Optional[str]:
        """Extract symbol from Vietnamese query"""
        # Simple keyword matching first (fast)
        query_lower = query.lower()

        if any(w in query_lower for w in ["vàng", "vang", "gold", "xau"]):
            return "XAUUSD"
        elif any(w in query_lower for w in ["bitcoin", "btc"]):
            return "BTCUSD"
        elif any(w in query_lower for w in ["ethereum", "eth"]):
            return "ETHUSD"

        # If not found, use LLM for extraction
        response = await acompletion(
            model="gpt-4o-mini",  # Cheap model for extraction
            messages=[
                {"role": "system", "content": "Extract the financial symbol from the query. Return ONLY: XAUUSD, BTCUSD, ETHUSD, or NONE"},
                {"role": "user", "content": query}
            ],
            max_tokens=10
        )

        symbol = response.choices[0].message.content.strip().upper()
        return symbol if symbol in ["XAUUSD", "BTCUSD", "ETHUSD"] else None

    def _build_rag_context(
        self,
        conv_context: ConversationContext,
        market_context: AggregatedContext,
        query: str
    ) -> str:
        """Build full RAG context for LLM"""
        parts = [
            self.memory_manager.format_for_llm(conv_context),
            market_context.to_llm_context(),
            f"\n## Current Query\nUser: {query}"
        ]
        return "\n\n".join(parts)

    async def _stream_llm_response(self, rag_context: str, model_name: str) -> AsyncGenerator[str, None]:
        """Stream LLM response with Chain-of-Thought"""
        response = await acompletion(
            model=model_name,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": rag_context}
            ],
            stream=True,
            max_tokens=1000,
            temperature=0.7
        )

        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
```

---

## LEGAL COMPLIANCE

### 3.8 Legal Compliance Service (Conditional Disclaimer)

**File**: `backend/app/capital_companion/legal_compliance.py`

**User Decision**: Disclaimers should ONLY appear on trade recommendations (buy/sell/hold), NOT on informational queries like "What's the gold price?". Auto-detect recommendation presence.

```python
"""
Legal compliance for trading recommendations
- Conditional disclaimers (only on trade recommendations)
- Audit trail for recommendations only
"""
from datetime import datetime
from typing import Optional
import json
import re

class LegalCompliance:
    """
    Handles legal disclaimers and audit trail

    Disclaimer Logic:
    - ONLY append disclaimer if response contains buy/sell/hold recommendation
    - Informational responses (price queries, explanations) = NO disclaimer
    """

    DISCLAIMERS = {
        "vi": """⚠️ **CẢNH BÁO RỦI RO**: Đây chỉ là phân tích tham khảo, KHÔNG phải lời khuyên đầu tư.
Giao dịch tài chính có rủi ro cao. Bạn có thể mất một phần hoặc toàn bộ vốn.
Luôn tự nghiên cứu và cân nhắc khả năng tài chính trước khi giao dịch.""",

        "en": """⚠️ **RISK WARNING**: This is for informational purposes only, NOT financial advice.
Trading carries high risk. You may lose some or all of your capital.
Always do your own research and consider your financial situation before trading."""
    }

    # Keywords that indicate a trade recommendation
    RECOMMENDATION_KEYWORDS_VI = [
        "nên mua", "nên bán", "khuyến nghị mua", "khuyến nghị bán",
        "mua vào", "bán ra", "vào lệnh", "đóng lệnh",
        "long", "short", "take profit", "stop loss",
        "điểm vào", "điểm ra", "entry", "exit"
    ]

    RECOMMENDATION_KEYWORDS_EN = [
        "should buy", "should sell", "recommend buy", "recommend sell",
        "buy now", "sell now", "go long", "go short",
        "take profit", "stop loss", "entry point", "exit point"
    ]

    # Action keywords (single words that indicate recommendation)
    ACTION_KEYWORDS = [
        "mua", "bán", "buy", "sell", "hold", "chờ", "giữ"
    ]

    def get_disclaimer(self, language: str = "vi") -> str:
        """Get localized disclaimer"""
        return self.DISCLAIMERS.get(language, self.DISCLAIMERS["vi"])

    def contains_recommendation(self, text: str) -> bool:
        """
        Check if text contains trading recommendation

        Returns True if response has buy/sell/hold advice
        Returns False for pure information (price, news, explanations)

        Examples:
        - "Giá vàng hiện tại là $2650" -> False (informational)
        - "Tôi khuyến nghị MUA vàng" -> True (recommendation)
        - "RSI đang ở mức 65" -> False (informational)
        - "Nên chờ đợi, không vào lệnh" -> True (recommendation to hold)
        """
        text_lower = text.lower()

        # Check Vietnamese phrase patterns
        for phrase in self.RECOMMENDATION_KEYWORDS_VI:
            if phrase in text_lower:
                return True

        # Check English phrase patterns
        for phrase in self.RECOMMENDATION_KEYWORDS_EN:
            if phrase in text_lower:
                return True

        # Check for action keywords in recommendation context
        # Pattern: "khuyến nghị" + action OR "nên" + action
        recommendation_patterns = [
            r"khuyến nghị\s+\w*\s*(mua|bán|chờ|giữ)",
            r"nên\s+\w*\s*(mua|bán|chờ|giữ|đợi)",
            r"(recommend|should)\s+\w*\s*(buy|sell|hold|wait)",
            r"(buy|sell|hold)\s+(recommendation|signal)",
        ]

        for pattern in recommendation_patterns:
            if re.search(pattern, text_lower):
                return True

        # Check section headers that indicate recommendation
        recommendation_headers = [
            "khuyến nghị", "recommendation", "kết luận", "conclusion",
            "hành động", "action", "tín hiệu", "signal"
        ]

        for header in recommendation_headers:
            # Look for header followed by buy/sell/hold within 50 chars
            header_pos = text_lower.find(header)
            if header_pos != -1:
                context = text_lower[header_pos:header_pos+100]
                if any(action in context for action in self.ACTION_KEYWORDS):
                    return True

        return False

    async def save_audit(
        self,
        user_id: str,
        session_id: str,
        query: str,
        response: str,
        symbol: str,
        model: str,
        context_snapshot: str
    ):
        """Save recommendation to audit trail (called only for recommendations)"""
        postgres = get_postgres_client()

        await postgres.execute("""
            INSERT INTO recommendation_audit (
                user_id, session_id, query, response,
                symbol, model, context_snapshot, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """,
            user_id, session_id, query, response,
            symbol, model, context_snapshot, datetime.utcnow()
        )
```

### 3.9 Database Schema Update

**File**: `db/migrations/002_ai_advisor_schema.sql`

```sql
-- Conversation sessions
CREATE TABLE conversation_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT UNIQUE NOT NULL,
    user_id UUID REFERENCES user_profiles(id),
    current_symbol TEXT,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    last_activity TIMESTAMPTZ DEFAULT NOW()
);

-- Recommendation audit trail (legal requirement)
CREATE TABLE recommendation_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES user_profiles(id),
    session_id TEXT NOT NULL,
    query TEXT NOT NULL,
    response TEXT NOT NULL,
    symbol TEXT NOT NULL,
    model TEXT NOT NULL,
    context_snapshot TEXT,  -- Full market context at time of recommendation
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for audit queries
CREATE INDEX idx_recommendation_audit_user_id ON recommendation_audit(user_id);
CREATE INDEX idx_recommendation_audit_created_at ON recommendation_audit(created_at DESC);
CREATE INDEX idx_recommendation_audit_symbol ON recommendation_audit(symbol);
CREATE INDEX idx_conversation_sessions_session_id ON conversation_sessions(session_id);

-- KOL signals (Zalo/Telegram - manual entry + future API)
CREATE TABLE kol_signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    author TEXT NOT NULL,
    platform TEXT NOT NULL,  -- 'zalo', 'telegram', 'manual'
    content TEXT NOT NULL,
    sentiment NUMERIC(3,2),
    signal_type TEXT NOT NULL,  -- 'buy', 'sell', 'hold', 'info'
    symbol TEXT NOT NULL,
    confidence NUMERIC(3,2) DEFAULT 0.7,
    metadata JSONB,  -- Extra info (group name, etc)
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_kol_signals_symbol ON kol_signals(symbol);
CREATE INDEX idx_kol_signals_timestamp ON kol_signals(timestamp DESC);
CREATE INDEX idx_kol_signals_signal_type ON kol_signals(signal_type);
```

---

## STREAMING RESPONSES

### 3.10 Socket.IO Streaming Events

**File**: `backend/app/events/advisor_events.py`

```python
"""
Socket.IO events for AI Trading Advisor
Streams LLM responses in real-time
"""
import logging
from app.sio import sio
from app.capital_companion.ai_advisor_service import AIAdvisorService
from app.capital_companion.voice_service import get_voice_service

logger = logging.getLogger(__name__)

# Advisor service instance
advisor = AIAdvisorService(model="gpt-4o")


@sio.event
async def advisor_query(sid, data):
    """
    Handle text query to AI advisor

    Input: {
        query: "Tôi nên mua vàng không?",
        session_id: "xxx",
        user_id: "yyy",
        model: "gpt-4o" | "deepseek" (optional, for per-request override)
    }
    Output: Streams response chunks via advisor:chunk events
    """
    try:
        query = data.get("query", "")
        session_id = data.get("session_id", sid)
        user_id = data.get("user_id", "")
        model = data.get("model")  # Optional per-request model override

        if not query:
            await sio.emit("advisor:error", {"message": "Query is required"}, room=sid)
            return

        logger.info(f"Advisor query from {sid}: {query[:50]}... (model: {model or 'default'})")

        # Emit start event with model info
        await sio.emit("advisor:start", {"query": query, "model": model or "default"}, room=sid)

        # Stream response (pass model override)
        full_response = ""
        async for chunk in advisor.analyze(query, session_id, user_id, model=model):
            full_response += chunk
            await sio.emit("advisor:chunk", {"text": chunk}, room=sid)

        # Emit complete event
        await sio.emit("advisor:complete", {
            "full_response": full_response,
            "query": query,
            "model": model or advisor.default_model
        }, room=sid)

    except Exception as e:
        logger.error(f"Advisor query error: {e}")
        await sio.emit("advisor:error", {"message": str(e)}, room=sid)


@sio.event
async def advisor_voice_query(sid, data):
    """
    Handle voice query to AI advisor

    Input: {audio: bytes, session_id: "xxx", user_id: "yyy"}
    Output: Streams text + synthesizes audio response
    """
    try:
        audio_buffer = data.get("audio")
        session_id = data.get("session_id", sid)
        user_id = data.get("user_id", "")

        if not audio_buffer:
            await sio.emit("advisor:error", {"message": "Audio is required"}, room=sid)
            return

        # Step 1: Transcribe
        voice_service = get_voice_service()
        transcription = await voice_service.transcribe(audio_buffer)

        if not transcription:
            await sio.emit("advisor:error", {
                "message": "Không thể nghe rõ. Vui lòng nói lại."
            }, room=sid)
            return

        await sio.emit("advisor:transcription", {"text": transcription}, room=sid)

        # Step 2: Get AI analysis (streaming)
        full_response = ""
        async for chunk in advisor.analyze(transcription, session_id, user_id):
            full_response += chunk
            await sio.emit("advisor:chunk", {"text": chunk}, room=sid)

        # Step 3: Synthesize audio response
        # Only speak the main analysis, not disclaimer
        speakable = full_response.split("---")[0].strip()
        audio_response = await voice_service.synthesize(speakable)

        if audio_response:
            await sio.emit("advisor:audio", audio_response, room=sid)

        await sio.emit("advisor:complete", {
            "full_response": full_response,
            "transcription": transcription
        }, room=sid)

    except Exception as e:
        logger.error(f"Advisor voice query error: {e}")
        await sio.emit("advisor:error", {"message": str(e)}, room=sid)
```

---

## COST ANALYSIS

### Monthly Cost Breakdown (Updated per User Decisions)

**Key Changes**:
- Twitter API removed ($100/mo saved) - using Zalo/Telegram instead
- Both GPT-4o and DeepSeek supported for A/B testing

| Service | Usage | Cost/Unit | Monthly Cost |
|---------|-------|-----------|--------------|
| **LLM (Analysis)** | | | |
| GPT-4o (main) | 10k queries x 1.5k tokens | $10/1M output | $150 |
| GPT-4o-mini (extraction) | 10k queries x 50 tokens | $0.60/1M | $0.30 |
| DeepSeek (alternative) | 10k queries x 1.5k tokens | $0.28/1M | $4.20 |
| **Data Sources** | | | |
| KOL Signals (Zalo/Telegram) | Manual/Bot | Free | **$0** |
| Fear & Greed API | unlimited | Free | $0 |
| NewsAPI | 100 req/day | Free tier | $0 |
| TwelveData | existing | $79/mo | (already budgeted) |
| **Infrastructure** | | | |
| Redis (memory) | 2GB | Included | $0 |
| PostgreSQL | 10GB | Included | $0 |
| **TOTAL (GPT-4o only)** | | | **~$150/mo** |
| **TOTAL (DeepSeek only)** | | | **~$5/mo** |
| **TOTAL (50/50 A/B mix)** | | | **~$77/mo** |

### Cost Comparison: Before vs After User Decisions

| Scenario | Before (Twitter) | After (Zalo/Telegram) | Savings |
|----------|------------------|----------------------|---------|
| GPT-4o only | $250/mo | $150/mo | **$100/mo** |
| DeepSeek only | $133/mo | $5/mo | **$128/mo** |
| Mixed A/B | $190/mo | $77/mo | **$113/mo** |

### Cost Optimization Path

1. **Week 3-4**: Start with GPT-4o (~$150/mo) - proven, reliable baseline
2. **Week 4-5**: Enable A/B testing, route 20% traffic to DeepSeek
3. **Week 5-6**: Compare accuracy/user satisfaction between models
4. **Week 6+**: Adjust ratio based on quality metrics (target: 50/50 or better)

### Token Budget Per Query

| Component | Input Tokens | Output Tokens |
|-----------|-------------|---------------|
| System prompt | ~300 | - |
| Conversation (5 msg) | ~500 | - |
| Market context | ~800 | - |
| User query | ~50 | - |
| **Total Input** | **~1650** | - |
| Analysis response | - | ~500-1000 |
| **Cost per query (GPT-4o)** | $0.004 | $0.010 |
| **Cost per query (DeepSeek)** | $0.0002 | $0.0004 |

---

## MODEL A/B TESTING

### Overview

Support both GPT-4o and DeepSeek simultaneously for:
- A/B testing to compare accuracy and user satisfaction
- Cost optimization (DeepSeek is ~35x cheaper)
- Model switching per-request or per-session

### Model Selection Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| **Per-Request** | Client specifies model in each query | Testing, power users |
| **Per-Session** | Model set at session start, persists | Consistent experience |
| **A/B Random** | Server randomly assigns model | Statistical comparison |
| **User Preference** | User sets default in profile | Personalization |

### A/B Testing Configuration

**File**: `backend/app/capital_companion/ab_testing.py`

```python
"""
A/B Testing for LLM model comparison
Tracks: accuracy, latency, cost, user satisfaction
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime
import random

@dataclass
class ABTestConfig:
    """A/B test configuration"""
    test_name: str = "gpt4o_vs_deepseek"
    gpt4o_weight: float = 0.5  # 50% traffic
    deepseek_weight: float = 0.5  # 50% traffic
    enabled: bool = True

@dataclass
class ABTestResult:
    """Result of a single A/B test query"""
    session_id: str
    model: str
    query: str
    response_time_ms: int
    token_count: int
    cost_usd: float
    user_rating: Optional[int]  # 1-5 if user rates
    timestamp: datetime

class ABTestManager:
    """Manages A/B testing for model comparison"""

    def __init__(self, config: ABTestConfig = None):
        self.config = config or ABTestConfig()
        self.redis = get_redis_client()
        self.postgres = get_postgres_client()

    def select_model(
        self,
        session_id: str,
        user_preference: Optional[str] = None,
        request_model: Optional[str] = None
    ) -> str:
        """
        Select model for query based on priority:
        1. Explicit request model (highest)
        2. User preference (if set)
        3. A/B random assignment (default)
        """
        # Priority 1: Explicit request
        if request_model in ["gpt-4o", "deepseek"]:
            return request_model

        # Priority 2: User preference
        if user_preference in ["gpt-4o", "deepseek"]:
            return user_preference

        # Priority 3: A/B random (but sticky per session)
        return self._get_session_model(session_id)

    def _get_session_model(self, session_id: str) -> str:
        """Get or assign model for session (sticky)"""
        cache_key = f"ab:model:{session_id}"

        # Check if already assigned
        cached = self.redis.get(cache_key)
        if cached:
            return cached.decode()

        # Assign based on weights
        if not self.config.enabled:
            model = "gpt-4o"  # Default when A/B disabled
        else:
            rand = random.random()
            if rand < self.config.gpt4o_weight:
                model = "gpt-4o"
            else:
                model = "deepseek"

        # Store assignment (24h TTL)
        self.redis.set(cache_key, model, ex=86400)
        return model

    async def record_result(self, result: ABTestResult):
        """Record A/B test result for analysis"""
        await self.postgres.execute("""
            INSERT INTO ab_test_results (
                test_name, session_id, model, query,
                response_time_ms, token_count, cost_usd,
                user_rating, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """,
            self.config.test_name,
            result.session_id,
            result.model,
            result.query[:200],
            result.response_time_ms,
            result.token_count,
            result.cost_usd,
            result.user_rating,
            result.timestamp
        )

    async def get_comparison_stats(self) -> dict:
        """Get aggregate stats for model comparison"""
        rows = await self.postgres.fetch("""
            SELECT
                model,
                COUNT(*) as query_count,
                AVG(response_time_ms) as avg_latency,
                AVG(token_count) as avg_tokens,
                SUM(cost_usd) as total_cost,
                AVG(user_rating) as avg_rating,
                COUNT(user_rating) as rated_count
            FROM ab_test_results
            WHERE test_name = $1
            AND created_at > NOW() - INTERVAL '7 days'
            GROUP BY model
        """, self.config.test_name)

        return {
            row["model"]: {
                "queries": row["query_count"],
                "avg_latency_ms": round(row["avg_latency"], 0),
                "avg_tokens": round(row["avg_tokens"], 0),
                "total_cost": round(row["total_cost"], 2),
                "avg_rating": round(row["avg_rating"], 2) if row["avg_rating"] else None,
                "rated_count": row["rated_count"]
            }
            for row in rows
        }
```

### Database Schema for A/B Testing

```sql
-- Add to 002_ai_advisor_schema.sql

-- A/B test results
CREATE TABLE ab_test_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_name TEXT NOT NULL,
    session_id TEXT NOT NULL,
    model TEXT NOT NULL,
    query TEXT NOT NULL,
    response_time_ms INTEGER,
    token_count INTEGER,
    cost_usd NUMERIC(10, 6),
    user_rating INTEGER CHECK (user_rating BETWEEN 1 AND 5),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_ab_test_results_test_name ON ab_test_results(test_name);
CREATE INDEX idx_ab_test_results_model ON ab_test_results(model);
CREATE INDEX idx_ab_test_results_created_at ON ab_test_results(created_at DESC);
```

### User Rating API

```python
# Add to advisor_events.py

@sio.event
async def advisor_rate(sid, data):
    """
    User rates response quality (1-5 stars)
    Used for A/B test comparison

    Input: {session_id: "xxx", rating: 4}
    """
    session_id = data.get("session_id", sid)
    rating = data.get("rating")

    if not rating or rating < 1 or rating > 5:
        await sio.emit("advisor:error", {"message": "Rating must be 1-5"}, room=sid)
        return

    ab_manager = ABTestManager()
    await ab_manager.update_last_rating(session_id, rating)

    await sio.emit("advisor:rated", {"rating": rating}, room=sid)
```

---

## LATENCY BUDGET

### Target: 2-5 seconds (Advisory Mode)

| Step | Time | Notes |
|------|------|-------|
| Whisper STT | 150-300ms | Existing |
| Data Aggregation | 500-1000ms | **Parallel** fetch all sources |
| Context Building | 50ms | CPU only |
| LLM Streaming | 1000-3000ms | First token ~200ms, full ~3s |
| Disclaimer Append | <10ms | Static text |
| VieNeu TTS | 100-200ms | Optional, shortened text |
| **TOTAL** | **2-5s** | Acceptable for advisory |

### Latency Optimization

1. **Parallel Data Fetch**: All sources fetched simultaneously
2. **Aggressive Caching**: 30s cache on aggregated context
3. **Streaming Response**: User sees text as it generates
4. **Shortened TTS**: Speak summary only, not full analysis

---

## INTEGRATION WITH OTHER PHASES

### Dependencies

| This Phase | Depends On | Notes |
|------------|-----------|-------|
| Phase 3 | Phase 1 (DB) | PostgreSQL for audit, Redis for cache |
| Phase 3 | Phase 2 (Market) | Real-time prices, historical data |
| Phase 4 | Phase 3 | Pattern analyzer reused |
| Phase 5 | Phase 3 | Sentiment analyzer reused |
| Phase 7 | Phase 3 | Alert generator uses AI advisor |

### What Moves Forward

- **Phase 4 (Patterns)**: Integrated into Data Aggregator
- **Phase 5 (Sentiment)**: Integrated into Sentiment Service
- **Phase 7 (Alerts)**: Can now include AI-generated reasoning

---

## TASK BREAKDOWN

### Sub-Phase 3A: Data Aggregation Layer (Week 3)

| Task | Est | Files |
|------|-----|-------|
| 3A.1 Create SentimentService | 2h | `sentiment_service.py` |
| 3A.2 Create KOLService (Zalo/Telegram) | 2h | `kol_service.py` |
| 3A.3 Create MultiFrameService | 2h | `multiframe_service.py` |
| 3A.4 Create DataAggregator | 2h | `data_aggregator.py` |
| 3A.5 Add KOL signal entry API | 1h | `routes/kol.py` |
| 3A.6 Test data aggregation | 1h | Manual testing |
| **Subtotal** | **10h** | |

### Sub-Phase 3B: Memory & Context (Week 4)

| Task | Est | Files |
|------|-----|-------|
| 3B.1 Create MemoryManager | 2h | `memory_manager.py` |
| 3B.2 Create DB migration | 1h | `002_ai_advisor_schema.sql` |
| 3B.3 Create LegalCompliance | 1h | `legal_compliance.py` |
| 3B.4 Implement audit trail | 1h | Postgres queries |
| 3B.5 Test memory persistence | 1h | Manual testing |
| **Subtotal** | **6h** | |

### Sub-Phase 3C: AI Advisor Core (Week 4-5)

| Task | Est | Files |
|------|-----|-------|
| 3C.1 Create AIAdvisorService | 4h | `ai_advisor_service.py` |
| 3C.2 Implement streaming | 2h | Socket.IO events |
| 3C.3 Create advisor_events.py | 2h | `events/advisor_events.py` |
| 3C.4 Integrate with voice | 2h | Voice flow update |
| 3C.5 End-to-end testing | 3h | Full flow testing |
| 3C.6 Prompt tuning | 2h | System prompt iteration |
| **Subtotal** | **15h** | |

### Sub-Phase 3D: Production Readiness & A/B Testing

| Task | Est | Files |
|------|-----|-------|
| 3D.1 Error handling | 2h | All services |
| 3D.2 Logging & monitoring | 1h | Logging config |
| 3D.3 Rate limiting | 1h | Redis-based limiter |
| 3D.4 A/B testing infrastructure | 2h | `ab_testing.py` |
| 3D.5 Model comparison dashboard | 2h | Admin UI |
| 3D.6 Load testing | 2h | Locust scripts |
| 3D.7 Documentation | 1h | API docs |
| **Subtotal** | **11h** | |

### Sub-Phase 3E: Fine-tuning (Optional - Future)

**User Decision**: Start without fine-tuning. Open for future implementation.

| Task | Est | Files |
|------|-----|-------|
| 3E.1 Data collection pipeline | 4h | Audit log extraction |
| 3E.2 Fine-tuning dataset prep | 4h | JSONL formatting |
| 3E.3 Fine-tune model (OpenAI/DeepSeek) | 2h | API calls |
| 3E.4 A/B test fine-tuned vs base | 2h | Comparison |
| **Subtotal** | **12h** | Optional |

**TOTAL PHASE 3**: ~42 hours (2-3 weeks) - Core implementation
**OPTIONAL**: +12 hours for fine-tuning (Phase 3E)

---

## FILE STRUCTURE

```
backend/
├── app/
│   ├── capital_companion/
│   │   ├── __init__.py
│   │   ├── ai_advisor_service.py      # NEW: Core AI advisor (GPT-4o + DeepSeek)
│   │   ├── ab_testing.py              # NEW: A/B testing for model comparison
│   │   ├── data_aggregator.py         # NEW: Multi-source aggregation
│   │   ├── sentiment_service.py       # NEW: Sentiment aggregation
│   │   ├── kol_service.py             # NEW: KOL signals (Zalo/Telegram)
│   │   ├── multiframe_service.py      # NEW: Multi-timeframe analysis
│   │   ├── memory_manager.py          # NEW: Conversation memory
│   │   ├── legal_compliance.py        # NEW: Conditional disclaimers + audit
│   │   ├── llm_config.py              # KEEP from Phase 3 LLM
│   │   ├── trading_functions.py       # KEEP (may use for quick commands)
│   │   ├── market_data_service.py     # EXISTING from Phase 2
│   │   ├── voice_service.py           # EXISTING from Phase 3
│   │   ├── pattern_analyzer.py        # MERGE from Phase 4
│   │   └── sentiment_analyzer.py      # MERGE from Phase 5
│   │
│   ├── routes/
│   │   └── kol.py                     # NEW: KOL signal entry API
│   │
│   ├── events/
│   │   ├── advisor_events.py          # NEW: AI advisor Socket.IO
│   │   ├── voice_events.py            # UPDATE: Add voice→advisor flow
│   │   └── market_events.py           # EXISTING
│   │
│   └── ...
│
├── db/
│   └── migrations/
│       ├── 001_initial_schema.sql     # EXISTING
│       └── 002_ai_advisor_schema.sql  # NEW (includes A/B test tables)
```

---

## ACCEPTANCE CRITERIA

### Functional

- [ ] User asks "Tôi nên mua vàng không?" → AI provides comprehensive analysis
- [ ] Response includes: sentiment, trends, patterns, KOL signals, news
- [ ] Response streams in real-time (chunks visible as generated)
- [ ] Legal disclaimer appended to every recommendation
- [ ] Conversation history maintained (user can follow up)
- [ ] Audit trail saved for all recommendations

### Performance

- [ ] Data aggregation completes in <1.5s
- [ ] First LLM token arrives in <500ms
- [ ] Full response completes in <5s
- [ ] Voice response (TTS) completes in <6s total

### Quality

- [ ] Analysis references actual market data (no hallucinations)
- [ ] Recommendations include confidence level
- [ ] Risk warnings included when appropriate
- [ ] Vietnamese language natural and professional

### Reliability

- [ ] Graceful degradation if data source fails
- [ ] Fallback to available data if some sources unavailable
- [ ] Error messages user-friendly
- [ ] No data loss on connection issues

---

## RESOLVED DECISIONS (User Confirmed)

1. **KOL Signals Source**: RESOLVED - Use Zalo/Telegram groups (free), NO Twitter API needed. Manual entry initially, API integration later if available. **Savings: $100/mo**

2. **Model Support**: RESOLVED - Support BOTH GPT-4o AND DeepSeek simultaneously with A/B testing capability. User can switch per-request or per-session.

3. **Disclaimer Frequency**: RESOLVED - Disclaimers ONLY on trade recommendations (buy/sell/hold), NOT on informational queries. Auto-detect recommendation presence.

4. **Fine-tuning**: RESOLVED - Start without. Open for future (Phase 3E optional).

## REMAINING QUESTIONS

1. **Multi-turn Depth**: How many messages to keep in context? Current: 10 messages. (Keep as-is for now)

2. **KOL Source Customization**: Should users customize their trusted KOL sources? (Future enhancement)

3. **Telegram Bot vs Manual**: When to implement Telegram Bot API for automatic signal capture? (After MVP validation)

---

## RISK MITIGATION

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| LLM hallucinates data | Medium | High | RAG context forces real data usage |
| KOL signal staleness | Low | Low | Manual entry ensures fresh signals, TTL 24h |
| High latency (>5s) | Medium | Medium | Streaming masks wait, cache aggressively |
| Legal liability | Low | High | Conditional disclaimer, audit trail on recommendations only |
| Cost overrun | Low | Low | A/B testing allows shift to DeepSeek (35x cheaper) |
| Vietnamese quality | Low | Medium | Test prompts, compare GPT-4o vs DeepSeek |
| Model quality variance | Low | Medium | A/B testing with user ratings measures quality |

---

## REFERENCES

- [LiteLLM Streaming](https://docs.litellm.ai/docs/streaming)
- [DeepSeek API](https://platform.deepseek.com/docs)
- [Fear & Greed Index API](https://alternative.me/crypto/fear-and-greed-index/)
- [RAG Architecture Patterns](https://www.anthropic.com/research/rag)
- [Telegram Bot API](https://core.telegram.org/bots/api) (Future: KOL signal automation)
- Phase 3 LLM Plan: `phase-03-voice-interaction-llm.md`
- Phase 4 Patterns: `SUMMARY.md` (Phase 4 section)
- Phase 5 Sentiment: `SUMMARY.md` (Phase 5 section)

---

**Created**: 2025-12-29
**Updated**: 2025-12-29 (User decisions integrated)
**Status**: Ready for Implementation
**Next Step**: Begin Sub-Phase 3A - Data Aggregation Layer

---

## CHANGE LOG

### 2025-12-29 - User Decisions Update

**Changes Made**:
1. Removed Twitter API ($100/mo) - replaced with Zalo/Telegram integration
2. Added A/B testing for GPT-4o vs DeepSeek model comparison
3. Updated disclaimer logic - only on trade recommendations
4. Added optional fine-tuning phase (3E)
5. Updated cost analysis - now $5-150/mo (was $50-250/mo)
6. Added KOL signal manual entry API
7. Updated database schema for KOL signals
8. Added user rating system for A/B testing
