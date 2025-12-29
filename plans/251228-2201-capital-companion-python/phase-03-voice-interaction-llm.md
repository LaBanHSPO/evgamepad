# Phase 3: Voice Interaction with LLM Intent Classification

**Duration**: Week 3-4
**Goal**: Vietnamese voice conversation using LLM function-calling (replaces regex-based intent)
**Prerequisites**: Phase 1-2 complete
**Status**: Not Started
**Replaces**: `phase-03-voice-interaction.md` (original regex approach)

---

## WHAT CHANGED FROM ORIGINAL PHASE 3

| Component | Original (Regex) | Updated (LLM) |
|-----------|------------------|---------------|
| **Intent Detection** | Hardcoded regex patterns | LLM function-calling |
| **Language Model** | None | GPT-4o, Claude 3.5, DeepSeek V3 |
| **Flexibility** | Add new patterns manually | LLM generalizes to new intents |
| **Cost** | $0 | $8-35/month (1000 users) |
| **Accuracy** | ~70-80% (Vietnamese variability) | 95-98% (LLM understands context) |
| **Latency** | ~10ms | ~165ms (acceptable, <3s budget) |
| **Maintainability** | Edit regex patterns | Edit function schemas |

**Why Change?**
- Regex cannot handle Vietnamese variation ("giá vàng", "vàng giá bao nhiêu", "cho tui xem giá vàng đi")
- LLM function-calling extracts structured intents reliably
- Research shows 8.8/10 rating for LiteLLM + Function-Calling hybrid

---

## ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Voice Interaction Flow                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  User Speaks (Vietnamese)                                           │
│       │                                                             │
│       ▼                                                             │
│  ┌─────────────┐                                                    │
│  │ Whisper STT │ (150-300ms) - OpenAI API                          │
│  └──────┬──────┘                                                    │
│         │ "giá vàng bao nhiêu rồi"                                 │
│         ▼                                                           │
│  ┌─────────────┐                                                    │
│  │ LiteLLM     │ ← Single API for GPT-4o/Claude/DeepSeek           │
│  │ Proxy       │                                                    │
│  └──────┬──────┘                                                    │
│         │                                                           │
│         ▼                                                           │
│  ┌─────────────────────────────────────────────────┐                │
│  │ Function-Calling Request                        │                │
│  │ tools: [get_price, buy_gold, sell_gold, ...]   │                │
│  │ model: gpt-4o (fallback: claude, deepseek)      │                │
│  └──────┬──────────────────────────────────────────┘                │
│         │                                                           │
│         ▼ (165ms p95)                                               │
│  ┌─────────────────────────────────────────────────┐                │
│  │ Function Call Response                          │                │
│  │ {function: "get_price", args: {symbol: "gold"}} │                │
│  └──────┬──────────────────────────────────────────┘                │
│         │                                                           │
│         ▼                                                           │
│  ┌─────────────┐                                                    │
│  │ Intent      │ ← Deterministic execution (if-else)                │
│  │ Executor    │   No hallucination risk                           │
│  └──────┬──────┘                                                    │
│         │                                                           │
│         ▼                                                           │
│  ┌─────────────┐                                                    │
│  │ Market/     │ ← Fetch real data                                 │
│  │ Trading Svc │                                                    │
│  └──────┬──────┘                                                    │
│         │                                                           │
│         ▼                                                           │
│  ┌─────────────┐                                                    │
│  │ Response    │ ← Generate Vietnamese text                        │
│  │ Generator   │                                                    │
│  └──────┬──────┘                                                    │
│         │ "Giá vàng hiện tại là $2,650.50"                         │
│         ▼                                                           │
│  ┌─────────────┐                                                    │
│  │ VieNeu TTS  │ (100-200ms) - Self-hosted                         │
│  └──────┬──────┘                                                    │
│         │                                                           │
│         ▼                                                           │
│  User Hears Response                                                │
│                                                                     │
│  TOTAL LATENCY: 465-765ms (well under 3s budget)                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## TASK BREAKDOWN

### Task 3.1: Install Dependencies
**Estimated Effort**: 15 minutes

**Update** `backend/requirements.txt`:
```txt
# Voice Processing
httpx==0.28.1              # Whisper API client
aiohttp==3.10.11           # VieNeu-TTS client

# LLM Integration
litellm==1.55.0            # Unified LLM API (GPT-4o, Claude, DeepSeek)
```

**Install**:
```bash
pip install httpx aiohttp litellm
```

**Environment Variables** (add to `.env`):
```env
# LLM Configuration
OPENAI_API_KEY=sk-...           # Required for GPT-4o and Whisper
ANTHROPIC_API_KEY=sk-ant-...    # Optional: Claude fallback
DEEPSEEK_API_KEY=sk-...         # Optional: DeepSeek V3 (cost savings)

# Model Selection
LLM_MODEL=gpt-4o                # Default model (or claude-3.5-sonnet, deepseek-chat)
LLM_FALLBACK_MODEL=deepseek-chat # Fallback if primary fails

# Voice Services
VIENEU_TTS_URL=http://localhost:5001  # VieNeu TTS server
```

---

### Task 3.2: Create LLM Configuration
**Estimated Effort**: 30 minutes

**File**: `backend/app/capital_companion/llm_config.py`

```python
"""
LLM configuration for Capital Companion voice trading
Supports: GPT-4o, Claude 3.5 Sonnet, DeepSeek V3
"""
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class LLMConfig:
    """LLM configuration loaded from environment"""

    # API Keys
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    deepseek_api_key: str = ""

    # Model Selection
    primary_model: str = "gpt-4o"
    fallback_model: str = "deepseek-chat"

    # Performance
    timeout_seconds: float = 10.0
    max_retries: int = 2

    # Cost Tracking
    track_costs: bool = True

    @classmethod
    def from_env(cls) -> "LLMConfig":
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", ""),
            primary_model=os.getenv("LLM_MODEL", "gpt-4o"),
            fallback_model=os.getenv("LLM_FALLBACK_MODEL", "deepseek-chat"),
            timeout_seconds=float(os.getenv("LLM_TIMEOUT", "10.0")),
            max_retries=int(os.getenv("LLM_MAX_RETRIES", "2")),
            track_costs=os.getenv("LLM_TRACK_COSTS", "true").lower() == "true"
        )

    def validate(self) -> bool:
        """Ensure at least one API key is configured"""
        return bool(self.openai_api_key or self.anthropic_api_key or self.deepseek_api_key)


# Singleton
_llm_config: Optional[LLMConfig] = None

def get_llm_config() -> LLMConfig:
    global _llm_config
    if _llm_config is None:
        _llm_config = LLMConfig.from_env()
    return _llm_config
```

---

### Task 3.3: Define Trading Functions Schema
**Estimated Effort**: 1 hour

**File**: `backend/app/capital_companion/trading_functions.py`

```python
"""
Function schemas for LLM function-calling
Each function maps to a deterministic backend action
"""
from typing import List, Dict, Any

# Trading function definitions (OpenAI Tools format)
TRADING_FUNCTIONS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_price",
            "description": "Lấy giá hiện tại của tài sản (vàng, Bitcoin, Ethereum)",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "enum": ["gold", "bitcoin", "ethereum"],
                        "description": "Tài sản cần xem giá"
                    }
                },
                "required": ["symbol"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_trend",
            "description": "Phân tích xu hướng giá của tài sản",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "enum": ["gold", "bitcoin", "ethereum"],
                        "description": "Tài sản cần phân tích"
                    },
                    "timeframe": {
                        "type": "string",
                        "enum": ["1h", "4h", "1d", "1w"],
                        "description": "Khung thời gian phân tích",
                        "default": "1d"
                    }
                },
                "required": ["symbol"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_alerts",
            "description": "Lấy danh sách cảnh báo và thông báo giao dịch",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Số lượng cảnh báo tối đa",
                        "default": 5
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "greeting",
            "description": "Chào hỏi người dùng",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "thanks",
            "description": "Phản hồi khi người dùng cảm ơn",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "unknown",
            "description": "Khi không hiểu câu hỏi của người dùng",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_message": {
                        "type": "string",
                        "description": "Tin nhắn gốc của người dùng"
                    }
                },
                "required": []
            }
        }
    }
]

# Symbol mapping (Vietnamese → internal)
SYMBOL_MAP = {
    "gold": "XAUUSD",
    "vang": "XAUUSD",
    "bitcoin": "BTCUSD",
    "btc": "BTCUSD",
    "ethereum": "ETHUSD",
    "eth": "ETHUSD"
}

def get_internal_symbol(symbol: str) -> str:
    """Convert user symbol to internal symbol"""
    return SYMBOL_MAP.get(symbol.lower(), symbol.upper())
```

---

### Task 3.4: Create LLM Intent Processor
**Estimated Effort**: 3-4 hours

**File**: `backend/app/processors/llm_intent_processor.py`

```python
"""
LLM-based intent processor using function-calling
Replaces regex-based intent_processor.py
"""
import json
import logging
from typing import Dict, Any, Optional
from litellm import acompletion
from litellm.exceptions import (
    RateLimitError,
    APIConnectionError,
    Timeout
)

from app.capital_companion.llm_config import get_llm_config
from app.capital_companion.trading_functions import (
    TRADING_FUNCTIONS,
    get_internal_symbol
)

logger = logging.getLogger(__name__)


class LLMIntentProcessor:
    """
    Process Vietnamese voice commands using LLM function-calling

    Architecture:
    1. Receive transcribed Vietnamese text
    2. Send to LLM with function schemas
    3. LLM returns function call (intent + params)
    4. Execute function deterministically (no hallucination)
    """

    SYSTEM_PROMPT = """Bạn là Atlas, trợ lý giao dịch vàng và crypto.
Nhiệm vụ: Phân tích câu hỏi tiếng Việt và gọi function phù hợp.

Quy tắc:
- Luôn gọi function, không trả lời trực tiếp
- Nếu không hiểu, gọi function "unknown"
- Với câu hỏi về giá, dùng "get_price"
- Với câu hỏi phân tích, dùng "analyze_trend"
- Với lời chào, dùng "greeting"
- Với lời cảm ơn, dùng "thanks"
"""

    def __init__(self):
        self.config = get_llm_config()
        self._validate_config()

    def _validate_config(self):
        if not self.config.validate():
            raise RuntimeError("No LLM API key configured. Set OPENAI_API_KEY or ANTHROPIC_API_KEY or DEEPSEEK_API_KEY")

    async def classify(self, text: str) -> Dict[str, Any]:
        """
        Classify Vietnamese voice intent via LLM function-calling

        Args:
            text: Transcribed Vietnamese text from Whisper

        Returns:
            {
                "intent": "get_price",
                "params": {"symbol": "gold"},
                "confidence": 0.95,
                "original_text": "giá vàng bao nhiêu"
            }
        """
        try:
            response = await self._call_llm(text)
            return self._parse_response(response, text)

        except (RateLimitError, Timeout) as e:
            logger.warning(f"Primary LLM failed ({e}), trying fallback")
            return await self._call_fallback(text)

        except APIConnectionError as e:
            logger.error(f"LLM connection failed: {e}")
            return self._unknown_intent(text)

        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
            return self._unknown_intent(text)

    async def _call_llm(self, text: str, use_fallback: bool = False) -> Any:
        """Call LLM with function-calling"""
        model = self.config.fallback_model if use_fallback else self.config.primary_model

        logger.info(f"Calling LLM ({model}) for intent: {text[:50]}...")

        response = await acompletion(
            model=model,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": text}
            ],
            tools=TRADING_FUNCTIONS,
            tool_choice="required",  # Force function call
            timeout=self.config.timeout_seconds
        )

        return response

    async def _call_fallback(self, text: str) -> Dict[str, Any]:
        """Try fallback model"""
        try:
            response = await self._call_llm(text, use_fallback=True)
            return self._parse_response(response, text)
        except Exception as e:
            logger.error(f"Fallback LLM also failed: {e}")
            return self._unknown_intent(text)

    def _parse_response(self, response: Any, original_text: str) -> Dict[str, Any]:
        """Parse LLM function-calling response"""
        try:
            message = response.choices[0].message

            if not message.tool_calls:
                logger.warning("LLM returned no function call")
                return self._unknown_intent(original_text)

            tool_call = message.tool_calls[0]
            function_name = tool_call.function.name

            # Parse arguments
            try:
                arguments = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                arguments = {}

            # Convert symbol if present
            if "symbol" in arguments:
                arguments["internal_symbol"] = get_internal_symbol(arguments["symbol"])

            logger.info(f"Intent classified: {function_name} with {arguments}")

            return {
                "intent": function_name,
                "params": arguments,
                "confidence": 0.95,  # LiteLLM doesn't expose confidence, use fixed high value
                "original_text": original_text
            }

        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return self._unknown_intent(original_text)

    def _unknown_intent(self, text: str) -> Dict[str, Any]:
        """Return unknown intent for fallback"""
        return {
            "intent": "unknown",
            "params": {"user_message": text},
            "confidence": 0.0,
            "original_text": text
        }


# Singleton
_llm_intent_processor: Optional[LLMIntentProcessor] = None

def get_llm_intent_processor() -> LLMIntentProcessor:
    global _llm_intent_processor
    if _llm_intent_processor is None:
        _llm_intent_processor = LLMIntentProcessor()
    return _llm_intent_processor
```

---

### Task 3.5: Create Intent Executor
**Estimated Effort**: 2 hours

**File**: `backend/app/processors/intent_executor.py`

```python
"""
Deterministic intent executor
Receives classified intent from LLM, executes corresponding action
Zero hallucination risk - LLM only classifies, backend executes
"""
import logging
from typing import Dict, Any, Optional
from app.capital_companion.market_data_service import get_market_data_service
from app.utils.vietnamese_responses import VietnameseResponses

logger = logging.getLogger(__name__)


class IntentExecutor:
    """
    Execute trading intents deterministically

    Flow: LLM Intent → Executor → Market Service → Response
    """

    async def execute(self, intent_data: Dict[str, Any]) -> str:
        """
        Execute intent and generate Vietnamese response

        Args:
            intent_data: {
                "intent": "get_price",
                "params": {"symbol": "gold", "internal_symbol": "XAUUSD"},
                "confidence": 0.95
            }

        Returns:
            Vietnamese response text
        """
        intent = intent_data.get("intent", "unknown")
        params = intent_data.get("params", {})

        logger.info(f"Executing intent: {intent} with params: {params}")

        # Dispatch to handler
        handlers = {
            "get_price": self._handle_get_price,
            "analyze_trend": self._handle_analyze_trend,
            "get_alerts": self._handle_get_alerts,
            "greeting": self._handle_greeting,
            "thanks": self._handle_thanks,
            "unknown": self._handle_unknown
        }

        handler = handlers.get(intent, self._handle_unknown)
        return await handler(params)

    async def _handle_get_price(self, params: Dict[str, Any]) -> str:
        """Handle price query"""
        symbol = params.get("internal_symbol")
        user_symbol = params.get("symbol", "")

        if not symbol:
            return "Bạn muốn biết giá của tài sản nào? Vàng, Bitcoin, hay Ethereum?"

        try:
            market_service = get_market_data_service()
            price_data = await market_service.get_cached_price(symbol)

            if price_data:
                price = price_data["price"]
                change = price_data.get("change_percent", 0)

                return VietnameseResponses.format_price_response(
                    symbol=symbol,
                    price=price,
                    change_percent=change
                )
            else:
                return f"Xin lỗi, tôi không thể lấy giá {user_symbol} lúc này."

        except Exception as e:
            logger.error(f"Error in get_price: {e}")
            return VietnameseResponses.ERRORS["no_data"]

    async def _handle_analyze_trend(self, params: Dict[str, Any]) -> str:
        """Handle trend analysis (placeholder for Phase 4)"""
        symbol = params.get("internal_symbol")
        timeframe = params.get("timeframe", "1d")

        if not symbol:
            return "Bạn muốn phân tích tài sản nào?"

        # TODO: Integrate with pattern analyzer in Phase 4
        symbol_name = self._get_symbol_name(symbol)
        return f"Tính năng phân tích {symbol_name} ({timeframe}) sẽ được cập nhật sau."

    async def _handle_get_alerts(self, params: Dict[str, Any]) -> str:
        """Handle get alerts (placeholder for Phase 7)"""
        # TODO: Integrate with alert system in Phase 7
        return "Hiện tại không có cảnh báo mới. Tôi sẽ thông báo khi có cơ hội giao dịch tốt."

    async def _handle_greeting(self, params: Dict[str, Any]) -> str:
        """Handle greeting"""
        return "Xin chào! Tôi là Atlas, trợ lý giao dịch của bạn. Tôi có thể giúp gì cho bạn?"

    async def _handle_thanks(self, params: Dict[str, Any]) -> str:
        """Handle thanks"""
        return "Không có gì! Hãy hỏi tôi bất cứ lúc nào bạn cần."

    async def _handle_unknown(self, params: Dict[str, Any]) -> str:
        """Handle unknown intent"""
        user_msg = params.get("user_message", "")
        logger.warning(f"Unknown intent for: {user_msg}")
        return VietnameseResponses.ERRORS["unknown"]

    def _get_symbol_name(self, symbol: str) -> str:
        """Get Vietnamese name for symbol"""
        names = {
            "XAUUSD": "vàng",
            "BTCUSD": "Bitcoin",
            "ETHUSD": "Ethereum"
        }
        return names.get(symbol, symbol)


# Singleton
_intent_executor: Optional[IntentExecutor] = None

def get_intent_executor() -> IntentExecutor:
    global _intent_executor
    if _intent_executor is None:
        _intent_executor = IntentExecutor()
    return _intent_executor
```

---

### Task 3.6: Keep Vietnamese Response Templates
**Estimated Effort**: 30 minutes (update existing)

Keep `backend/app/utils/vietnamese_responses.py` from original Phase 3.
This serves as fallback templates and standardizes response format.

---

### Task 3.7: Update Voice Event Handlers
**Estimated Effort**: 2 hours

**File**: `backend/app/events/voice_events.py`

```python
"""
Socket.IO events for voice interaction (LLM-based)
"""
import logging
import time
from socketio import AsyncServer
from app.sio import sio
from app.capital_companion.voice_service import get_voice_service
from app.processors.llm_intent_processor import get_llm_intent_processor
from app.processors.intent_executor import get_intent_executor

logger = logging.getLogger(__name__)

# Session storage for voice buffers
voice_sessions = {}


@sio.event
async def voice_start(sid):
    """Start voice recording session"""
    try:
        voice_sessions[sid] = {
            "audio_chunks": [],
            "start_time": time.time()
        }
        logger.info(f"Voice session started: {sid}")
        await sio.emit("voice:listening", room=sid)
    except Exception as e:
        logger.error(f"voice_start error: {e}")
        await sio.emit("error", {"message": "Không thể bắt đầu ghi âm"}, room=sid)


@sio.event
async def voice_audio(sid, data):
    """Receive audio chunk from client"""
    try:
        if sid in voice_sessions:
            voice_sessions[sid]["audio_chunks"].append(data)
    except Exception as e:
        logger.error(f"voice_audio error: {e}")


@sio.event
async def voice_stop(sid):
    """Stop voice recording and process via LLM"""
    try:
        if sid not in voice_sessions:
            return

        session = voice_sessions[sid]
        audio_chunks = session["audio_chunks"]
        start_time = session["start_time"]

        # Concatenate audio chunks
        audio_buffer = b"".join(audio_chunks)
        duration_ms = int((time.time() - start_time) * 1000)

        logger.info(f"Processing voice: {len(audio_buffer)} bytes, {duration_ms}ms")

        # Step 1: Transcribe via Whisper
        voice_service = get_voice_service()
        transcription = await voice_service.transcribe(audio_buffer)

        if not transcription:
            await sio.emit("voice:error", {
                "message": "Không thể nghe rõ. Vui lòng nói lại."
            }, room=sid)
            del voice_sessions[sid]
            return

        # Send transcription to client
        await sio.emit("voice:transcription", {"text": transcription}, room=sid)

        # Step 2: Classify intent via LLM
        llm_processor = get_llm_intent_processor()
        intent_data = await llm_processor.classify(transcription)

        logger.info(f"LLM Intent: {intent_data}")

        # Step 3: Execute intent deterministically
        executor = get_intent_executor()
        response_text = await executor.execute(intent_data)

        # Step 4: Synthesize response via VieNeu TTS
        audio_response = await voice_service.synthesize(response_text)

        if audio_response:
            await sio.emit("voice:audio_response", audio_response, room=sid)

        # Send text response
        await sio.emit("voice:text_response", {
            "text": response_text,
            "intent": intent_data["intent"],
            "confidence": intent_data["confidence"]
        }, room=sid)

        await sio.emit("voice:complete", room=sid)

        # Cleanup
        del voice_sessions[sid]

    except Exception as e:
        logger.error(f"voice_stop error: {e}")
        await sio.emit("voice:error", {
            "message": "Đã xảy ra lỗi. Vui lòng thử lại."
        }, room=sid)

        if sid in voice_sessions:
            del voice_sessions[sid]
```

---

### Task 3.8: Update Backend Main
**Estimated Effort**: 30 minutes

**Update** `backend/app/main.py`:

```python
# Add imports
from app.capital_companion.voice_service import init_voice_service
from app.capital_companion.llm_config import get_llm_config
from app.events import voice_events  # noqa: F401 - registers events

# Update lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ... existing code ...

    # Initialize LLM Config (validate API keys)
    try:
        llm_config = get_llm_config()
        if llm_config.validate():
            logger.info(f"LLM configured: {llm_config.primary_model}")
        else:
            logger.warning("No LLM API keys configured")
    except Exception as e:
        logger.error(f"LLM config failed: {e}")

    # Initialize Voice Service
    try:
        voice_service = init_voice_service(
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            vieneu_tts_url=os.getenv("VIENEU_TTS_URL", "http://localhost:5001")
        )
        logger.info("Voice service initialized")
    except Exception as e:
        logger.error(f"Voice service failed: {e}")

    yield
    # ... shutdown ...
```

---

## FILE STRUCTURE

### New Files

```
backend/
├── app/
│   ├── capital_companion/
│   │   ├── __init__.py
│   │   ├── llm_config.py           # NEW: LLM configuration
│   │   ├── trading_functions.py    # NEW: Function schemas
│   │   └── voice_service.py        # Same as original Phase 3
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── llm_intent_processor.py # NEW: LLM-based intent
│   │   └── intent_executor.py      # NEW: Deterministic executor
│   ├── events/
│   │   └── voice_events.py         # UPDATED: Use LLM processor
│   └── utils/
│       └── vietnamese_responses.py # Same as original Phase 3
```

### Modified Files

| File | Change |
|------|--------|
| `backend/requirements.txt` | Add `litellm==1.55.0` |
| `backend/app/main.py` | Add LLM config initialization |
| `backend/app/config.py` | Add LLM env vars (optional, use llm_config.py instead) |
| `.env` | Add `OPENAI_API_KEY`, `LLM_MODEL`, etc. |

---

## CONFIGURATION

### Environment Variables

```env
# Required: At least one LLM API key
OPENAI_API_KEY=sk-...                    # For GPT-4o and Whisper STT
ANTHROPIC_API_KEY=sk-ant-...             # Optional: Claude fallback
DEEPSEEK_API_KEY=sk-...                  # Optional: DeepSeek V3 (cost savings)

# Model Selection
LLM_MODEL=gpt-4o                         # Primary model
LLM_FALLBACK_MODEL=deepseek-chat         # Fallback if primary fails
LLM_TIMEOUT=10.0                         # Request timeout (seconds)
LLM_MAX_RETRIES=2                        # Retry attempts
LLM_TRACK_COSTS=true                     # Enable LiteLLM cost tracking

# Voice Services
VIENEU_TTS_URL=http://localhost:5001     # VieNeu TTS server
```

### Model Options

| Model | LiteLLM Name | Cost (input/output) | Vietnamese | Use Case |
|-------|--------------|---------------------|------------|----------|
| GPT-4o | `gpt-4o` | $2.50/$10/1M | Excellent | Phase 1 baseline |
| Claude 3.5 | `claude-3-5-sonnet-20241022` | $3/$15/1M | Excellent | Alternative |
| DeepSeek V3 | `deepseek-chat` | $0.28/$0.42/1M | Excellent | Phase 2 cost optimize |

---

## VERIFICATION STEPS

### Test 1: LLM Configuration
```python
# Run in Python shell
from app.capital_companion.llm_config import get_llm_config
config = get_llm_config()
print(f"Model: {config.primary_model}")
print(f"Valid: {config.validate()}")
```

### Test 2: Function-Calling Intent
```python
import asyncio
from app.processors.llm_intent_processor import get_llm_intent_processor

async def test():
    processor = get_llm_intent_processor()

    # Test Vietnamese commands
    tests = [
        "giá vàng bao nhiêu",
        "cho tui xem giá bitcoin đi",
        "phân tích xu hướng ethereum",
        "xin chào",
        "cảm ơn nha"
    ]

    for text in tests:
        result = await processor.classify(text)
        print(f"{text} → {result['intent']}: {result['params']}")

asyncio.run(test())
```

### Test 3: Intent Execution
```python
import asyncio
from app.processors.intent_executor import get_intent_executor

async def test():
    executor = get_intent_executor()

    intent = {
        "intent": "get_price",
        "params": {"symbol": "gold", "internal_symbol": "XAUUSD"}
    }

    response = await executor.execute(intent)
    print(f"Response: {response}")

asyncio.run(test())
```

### Test 4: Full Voice Flow
1. Open Monitor page in browser
2. Click "TALK" button
3. Speak: "Giá vàng bao nhiêu rồi?"
4. Expected:
   - See transcription: "giá vàng bao nhiêu rồi"
   - Hear response: "Giá vàng hiện tại là $X,XXX.XX"
   - See intent in console: `get_price`
5. Total time should be < 3 seconds

### Test 5: Model Fallback
```bash
# Temporarily set invalid primary key
LLM_MODEL=invalid-model LLM_FALLBACK_MODEL=gpt-4o python -c "
import asyncio
from app.processors.llm_intent_processor import get_llm_intent_processor

async def test():
    processor = get_llm_intent_processor()
    result = await processor.classify('giá vàng')
    print(result)

asyncio.run(test())
"
# Should fallback to GPT-4o and return valid intent
```

---

## ACCEPTANCE CRITERIA

### Functional Requirements

- [ ] LiteLLM correctly routes to configured model
- [ ] Function-calling extracts intent from Vietnamese text
- [ ] All 6 function types work: get_price, analyze_trend, get_alerts, greeting, thanks, unknown
- [ ] Intent executor returns Vietnamese responses
- [ ] Voice flow works end-to-end (speak → transcribe → classify → execute → respond)
- [ ] Audio response plays in browser

### Performance Requirements

- [ ] LLM intent classification < 300ms (p95)
- [ ] Full voice roundtrip < 3 seconds (speak to hear response)
- [ ] No timeout errors under normal load

### Reliability Requirements

- [ ] Fallback to secondary model when primary fails
- [ ] Graceful handling of API errors (rate limit, timeout)
- [ ] Unknown intent returns helpful message

### Security Requirements

- [ ] API keys stored in environment variables only
- [ ] No API keys in logs
- [ ] Deterministic execution prevents hallucinated trades

---

## COST COMPARISON

### Original Phase 3 (Regex)

| Item | Cost/Month |
|------|------------|
| Whisper STT | ~$18 (1000 users x 10 queries x $0.006) |
| Regex Processing | $0 |
| VieNeu TTS | $0 (self-hosted) |
| **Total** | **~$18** |

### Updated Phase 3 (LLM)

| Item | GPT-4o | DeepSeek V3 |
|------|--------|-------------|
| Whisper STT | $18 | $18 |
| LLM Intent | $35 | $8 |
| VieNeu TTS | $0 | $0 |
| **Total** | **~$53** | **~$26** |

**Cost Delta**: +$8-35/month for 98%+ accuracy vs ~75% regex accuracy

---

## MIGRATION PATH

### Phase 1: GPT-4o Baseline (Week 3-4)

1. Install LiteLLM
2. Configure GPT-4o as primary
3. Implement function-calling intent processor
4. Test with 100 Vietnamese commands
5. Measure accuracy (target: 95%+)

### Phase 2: DeepSeek V3 Optimization (Week 5)

1. Add DeepSeek API key
2. Run parallel benchmark: GPT-4o vs DeepSeek V3
3. Compare:
   - Accuracy on Vietnamese trading commands
   - Latency (should be similar)
   - Cost (DeepSeek is 87% cheaper)
4. If DeepSeek accuracy >= 95%, switch to primary
5. Keep GPT-4o as fallback

### Phase 3: Fine-tuning (Optional, Week 6+)

1. Collect 500+ labeled Vietnamese trading commands
2. Fine-tune DeepSeek or Claude
3. Deploy fine-tuned model
4. Target: 99%+ accuracy

---

## RISK MITIGATION

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| LLM returns wrong function | Low | Medium | Schema validation, unit tests |
| LLM hallucinates parameters | Low | High | Strict param schema, backend validation |
| Rate limit exceeded | Medium | Medium | LiteLLM fallback, caching common queries |
| Latency spike (market hours) | Medium | Medium | Timeout + fallback, async queue |
| Vietnamese not understood | Low | Medium | Test with diverse Vietnamese inputs |
| API key leaked | Low | Critical | Env vars only, no logging |

---

## UNRESOLVED QUESTIONS

1. **Multi-turn context**: Does Atlas need conversation memory ("What did I say earlier?")? Current design is single-turn only.

2. **Fine-tuning data source**: Where to get 500+ labeled Vietnamese trading commands? Options: synthetic generation, forum scraping, manual labeling.

3. **Risk disclaimers**: Should LLM add risk warnings to trading-related responses? (Regulatory question)

4. **Streaming responses**: Should we stream LLM response token-by-token for faster perceived latency? LiteLLM supports streaming.

---

## REFERENCES

- [LiteLLM Documentation](https://docs.litellm.ai/)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
- [Research: LLM Integration Approaches](./research/llm-integration-approaches-rating.md)
- [Research: Executive Summary](./research/EXECUTIVE-SUMMARY.md)

---

**Created**: 2025-12-29
**Status**: Ready for Implementation
**Next Step**: Begin Task 3.1 - Install Dependencies
