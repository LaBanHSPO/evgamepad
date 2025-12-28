# Phase 3: Voice Interaction (Vietnamese)

**Duration**: Week 3
**Goal**: Vietnamese voice conversation (Whisper API + VieNeu-TTS)
**Prerequisites**: Phase 1-2 complete
**Status**: Not Started

---

## OVERVIEW

Implement voice interaction allowing users to speak Vietnamese commands and receive Vietnamese audio responses. Uses OpenAI Whisper for STT (Speech-to-Text) and VieNeu-TTS server for TTS (Text-to-Speech).

### Dependencies
- OpenAI Whisper API ($0.006/min)
- VieNeu-TTS server (self-hosted)
- `httpx`, `aiohttp` libraries

---

## TASK BREAKDOWN

### Task 3.1: Install Dependencies
**Estimated Effort**: 15 minutes

**Update** `backend/requirements.txt`:
```txt
# Add
httpx==0.28.1  # Whisper API client
aiohttp==3.10.11  # VieNeu-TTS client (already added in Phase 2)
```

**Install**:
```bash
pip install httpx aiohttp
```

---

### Task 3.2: Create Voice Service
**Estimated Effort**: 4-5 hours

**File**: `backend/app/capital_companion/voice_service.py`

```python
"""
Voice processing service: Whisper STT + VieNeu TTS
"""
import httpx
import aiohttp
import logging
from typing import Optional
from io import BytesIO
from app.config import capital_config

logger = logging.getLogger(__name__)

class VoiceService:
    """Voice transcription and synthesis service"""

    def __init__(self, openai_api_key: str, vieneu_tts_url: str):
        self.openai_api_key = openai_api_key
        self.vieneu_tts_url = vieneu_tts_url

    async def transcribe(self, audio_buffer: bytes) -> Optional[str]:
        """
        Transcribe audio using Whisper API

        Args:
            audio_buffer: Audio file bytes (webm, mp3, wav, etc.)

        Returns:
            Transcribed text in Vietnamese
        """
        url = "https://api.openai.com/v1/audio/transcriptions"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                files = {
                    'file': ('audio.webm', BytesIO(audio_buffer), 'audio/webm')
                }
                data = {
                    'model': 'whisper-1',
                    'language': 'vi',  # Vietnamese
                    'response_format': 'text'
                }
                headers = {
                    'Authorization': f'Bearer {self.openai_api_key}'
                }

                response = await client.post(url, files=files, data=data, headers=headers)

                if response.status_code == 200:
                    transcription = response.text.strip()
                    logger.info(f"Transcription: {transcription}")
                    return transcription
                else:
                    logger.error(f"Whisper API error: {response.status_code} - {response.text}")
                    return None

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return None

    async def synthesize(self, text: str, voice: str = 'vi-VN-female') -> Optional[bytes]:
        """
        Synthesize speech using VieNeu TTS

        Args:
            text: Vietnamese text to synthesize
            voice: Voice name

        Returns:
            Audio bytes (mp3/wav)
        """
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    'text': text,
                    'voice': voice,
                    'speed': 1.0
                }

                async with session.post(
                    f"{self.vieneu_tts_url}/synthesize",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        audio_data = await response.read()
                        logger.info(f"Synthesized {len(audio_data)} bytes")
                        return audio_data
                    else:
                        error_text = await response.text()
                        logger.error(f"VieNeu TTS error: {response.status} - {error_text}")
                        return None

        except Exception as e:
            logger.error(f"Speech synthesis failed: {e}")
            return None

# Singleton
_voice_service: Optional[VoiceService] = None

def get_voice_service() -> VoiceService:
    global _voice_service
    if _voice_service is None:
        raise RuntimeError("Voice service not initialized")
    return _voice_service

def init_voice_service(openai_api_key: str, vieneu_tts_url: str) -> VoiceService:
    global _voice_service
    _voice_service = VoiceService(openai_api_key, vieneu_tts_url)
    return _voice_service
```

---

### Task 3.3: Create Intent Processor
**Estimated Effort**: 3-4 hours

**File**: `backend/app/processors/intent_processor.py`

```python
"""
Voice intent classifier for Vietnamese commands
"""
import re
import logging
from typing import Dict, Optional, Any
from app.capital_companion.market_data_service import get_market_data_service

logger = logging.getLogger(__name__)

class IntentProcessor:
    """Classify Vietnamese voice commands"""

    # Intent patterns (Vietnamese)
    PATTERNS = {
        'query_price': [
            r'giá (vàng|bitcoin|btc|eth|ethereum)',
            r'(vàng|bitcoin|btc|eth) giá bao nhiêu',
            r'giá hiện tại'
        ],
        'analyze_chart': [
            r'phân tích (vàng|bitcoin|btc|eth)',
            r'(vàng|bitcoin) có nên mua không',
            r'xu hướng (vàng|bitcoin)'
        ],
        'get_alerts': [
            r'có cảnh báo (gì|nào|không)',
            r'thông báo',
            r'tin tức'
        ],
        'greeting': [
            r'^(xin chào|chào|hello)',
            r'^(chào buổi sáng|chào buổi chiều)'
        ],
        'thanks': [
            r'(cảm ơn|cám ơn|thanks)',
            r'được rồi'
        ]
    }

    # Symbol mapping
    SYMBOL_MAP = {
        'vàng': 'XAUUSD',
        'gold': 'XAUUSD',
        'bitcoin': 'BTCUSD',
        'btc': 'BTCUSD',
        'ethereum': 'ETHUSD',
        'eth': 'ETHUSD'
    }

    def classify(self, text: str) -> Dict[str, Any]:
        """
        Classify intent from Vietnamese text

        Returns:
            {
                'intent': 'query_price',
                'symbol': 'BTCUSD',
                'confidence': 0.9
            }
        """
        text_lower = text.lower()

        # Check each intent pattern
        for intent, patterns in self.PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    # Extract symbol if present
                    symbol = self._extract_symbol(text_lower)

                    return {
                        'intent': intent,
                        'symbol': symbol,
                        'confidence': 0.9,
                        'original_text': text
                    }

        # Unknown intent
        return {
            'intent': 'unknown',
            'symbol': None,
            'confidence': 0.0,
            'original_text': text
        }

    def _extract_symbol(self, text: str) -> Optional[str]:
        """Extract trading symbol from text"""
        for keyword, symbol in self.SYMBOL_MAP.items():
            if keyword in text:
                return symbol
        return None

    async def process(self, intent_data: Dict[str, Any]) -> str:
        """
        Process intent and generate Vietnamese response

        Returns:
            Vietnamese response text
        """
        intent = intent_data['intent']
        symbol = intent_data['symbol']

        if intent == 'query_price':
            return await self._handle_price_query(symbol)

        elif intent == 'analyze_chart':
            return await self._handle_chart_analysis(symbol)

        elif intent == 'get_alerts':
            return await self._handle_get_alerts()

        elif intent == 'greeting':
            return "Xin chào! Tôi là Atlas, trợ lý giao dịch của bạn. Tôi có thể giúp gì cho bạn?"

        elif intent == 'thanks':
            return "Không có gì! Hãy hỏi tôi bất cứ lúc nào bạn cần."

        else:
            return "Xin lỗi, tôi không hiểu câu hỏi của bạn. Bạn có thể hỏi về giá vàng, Bitcoin, hoặc phân tích thị trường."

    async def _handle_price_query(self, symbol: Optional[str]) -> str:
        """Handle price query intent"""
        if not symbol:
            return "Bạn muốn biết giá của tài sản nào? Vàng, Bitcoin, hay Ethereum?"

        try:
            market_service = get_market_data_service()
            price_data = await market_service.get_cached_price(symbol)

            if price_data:
                price = price_data['price']

                # Symbol name in Vietnamese
                symbol_name = {
                    'XAUUSD': 'vàng',
                    'BTCUSD': 'Bitcoin',
                    'ETHUSD': 'Ethereum'
                }.get(symbol, symbol)

                return f"Giá {symbol_name} hiện tại là ${price:,.2f}."
            else:
                return f"Xin lỗi, tôi không thể lấy giá {symbol} lúc này."

        except Exception as e:
            logger.error(f"Error handling price query: {e}")
            return "Đã xảy ra lỗi khi lấy giá. Vui lòng thử lại."

    async def _handle_chart_analysis(self, symbol: Optional[str]) -> str:
        """Handle chart analysis intent (placeholder)"""
        if not symbol:
            return "Bạn muốn phân tích tài sản nào?"

        # TODO: Integrate with pattern analyzer (Phase 4)
        return f"Tính năng phân tích {symbol} sẽ được cập nhật sau. Hiện tại bạn có thể hỏi về giá."

    async def _handle_get_alerts(self) -> str:
        """Handle get alerts intent (placeholder)"""
        # TODO: Integrate with alert system (Phase 7)
        return "Hiện tại không có cảnh báo mới. Tôi sẽ thông báo khi có cơ hội giao dịch tốt."

# Singleton
_intent_processor: Optional[IntentProcessor] = None

def get_intent_processor() -> IntentProcessor:
    global _intent_processor
    if _intent_processor is None:
        _intent_processor = IntentProcessor()
    return _intent_processor
```

---

### Task 3.4: Create Vietnamese Response Templates
**Estimated Effort**: 2 hours

**File**: `backend/app/utils/vietnamese_responses.py`

```python
"""
Vietnamese response templates
"""
from typing import Dict, Any

class VietnameseResponses:
    """Template responses in Vietnamese"""

    GREETINGS = [
        "Xin chào! Tôi là Atlas, trợ lý giao dịch của bạn.",
        "Chào buổi sáng! Tôi đã phân tích thị trường cho bạn.",
        "Chào bạn! Có gì tôi có thể giúp không?"
    ]

    PRICE_RESPONSES = {
        'up': "Giá {symbol} đang tăng {change}% hôm nay. Hiện tại là ${price:,.2f}.",
        'down': "Giá {symbol} đang giảm {change}% hôm nay. Hiện tại là ${price:,.2f}.",
        'stable': "Giá {symbol} hiện tại là ${price:,.2f}, ổn định so với hôm qua."
    }

    ALERTS = {
        'breakout': "{symbol} đang phá vỡ mức kháng cự ${level:,.2f}!",
        'support': "{symbol} đang tiếp cận hỗ trợ tại ${level:,.2f}.",
        'rsi_overbought': "{symbol} RSI đang quá mua (>70). Cẩn thận với điều chỉnh.",
        'rsi_oversold': "{symbol} RSI đang quá bán (<30). Có thể là cơ hội mua."
    }

    ERRORS = {
        'no_data': "Xin lỗi, tôi không thể lấy dữ liệu lúc này.",
        'unknown': "Tôi không hiểu câu hỏi. Bạn có thể hỏi lại được không?",
        'connection': "Mất kết nối. Đang kết nối lại..."
    }

    @staticmethod
    def format_price_response(symbol: str, price: float, change_percent: float) -> str:
        """Format price response with change"""
        symbol_name = {
            'XAUUSD': 'vàng',
            'BTCUSD': 'Bitcoin',
            'ETHUSD': 'Ethereum'
        }.get(symbol, symbol)

        if change_percent > 0.5:
            return VietnameseResponses.PRICE_RESPONSES['up'].format(
                symbol=symbol_name,
                price=price,
                change=abs(change_percent)
            )
        elif change_percent < -0.5:
            return VietnameseResponses.PRICE_RESPONSES['down'].format(
                symbol=symbol_name,
                price=price,
                change=abs(change_percent)
            )
        else:
            return VietnameseResponses.PRICE_RESPONSES['stable'].format(
                symbol=symbol_name,
                price=price
            )
```

---

### Task 3.5: Create Voice Event Handlers
**Estimated Effort**: 4-5 hours

**File**: `backend/app/events/voice_events.py`

```python
"""
Socket.IO events for voice interaction
"""
import logging
import time
from socketio import AsyncServer
from app.sio import sio
from app.capital_companion.voice_service import get_voice_service
from app.processors.intent_processor import get_intent_processor
from app.database.postgres_client import get_postgres_client

logger = logging.getLogger(__name__)

# Session storage for voice buffers
voice_sessions = {}

@sio.event
async def voice_start(sid):
    """
    Start voice recording session

    Event: voice:start
    """
    try:
        # Initialize voice buffer for this session
        voice_sessions[sid] = {
            'audio_chunks': [],
            'start_time': time.time()
        }

        logger.info(f"Voice session started for {sid}")
        await sio.emit('voice:listening', room=sid)

    except Exception as e:
        logger.error(f"Error in voice_start: {e}")
        await sio.emit('error', {'message': 'Không thể bắt đầu ghi âm'}, room=sid)

@sio.event
async def voice_audio(sid, data):
    """
    Receive audio chunk from client

    Event: voice:audio
    Payload: Binary audio data
    """
    try:
        if sid in voice_sessions:
            voice_sessions[sid]['audio_chunks'].append(data)
            logger.debug(f"Received audio chunk from {sid}: {len(data)} bytes")
        else:
            logger.warning(f"Audio received for unknown session: {sid}")

    except Exception as e:
        logger.error(f"Error in voice_audio: {e}")

@sio.event
async def voice_stop(sid):
    """
    Stop voice recording and process

    Event: voice:stop
    """
    try:
        if sid not in voice_sessions:
            logger.warning(f"voice_stop called for unknown session: {sid}")
            return

        session = voice_sessions[sid]
        audio_chunks = session['audio_chunks']
        start_time = session['start_time']

        # Concatenate audio chunks
        audio_buffer = b''.join(audio_chunks)
        duration_ms = int((time.time() - start_time) * 1000)

        logger.info(f"Processing voice: {len(audio_buffer)} bytes, {duration_ms}ms")

        # Transcribe via Whisper
        voice_service = get_voice_service()
        transcription = await voice_service.transcribe(audio_buffer)

        if not transcription:
            await sio.emit('voice:error', {
                'message': 'Không thể nghe rõ. Vui lòng nói lại.'
            }, room=sid)
            del voice_sessions[sid]
            return

        # Send transcription to client
        await sio.emit('voice:transcription', {
            'text': transcription
        }, room=sid)

        # Classify intent
        intent_processor = get_intent_processor()
        intent_data = intent_processor.classify(transcription)

        logger.info(f"Intent: {intent_data}")

        # Process intent and generate response
        response_text = await intent_processor.process(intent_data)

        # Synthesize response via VieNeu TTS
        audio_response = await voice_service.synthesize(response_text)

        if audio_response:
            # Send audio response to client
            await sio.emit('voice:audio_response', audio_response, room=sid)

        # Send text response as well
        await sio.emit('voice:text_response', {
            'text': response_text
        }, room=sid)

        # Store interaction in database
        try:
            postgres_client = get_postgres_client()
            user_id = 'anonymous'  # TODO: Get from session after auth

            await postgres_client.create_voice_interaction(
                user_id=user_id,
                transcript=transcription,
                response=response_text,
                intent=intent_data['intent'],
                duration_ms=duration_ms
            )
        except Exception as e:
            logger.error(f"Failed to store voice interaction: {e}")

        await sio.emit('voice:complete', room=sid)

        # Cleanup
        del voice_sessions[sid]

    except Exception as e:
        logger.error(f"Error in voice_stop: {e}")
        await sio.emit('voice:error', {
            'message': 'Đã xảy ra lỗi. Vui lòng thử lại.'
        }, room=sid)

        if sid in voice_sessions:
            del voice_sessions[sid]
```

---

### Task 3.6: Create Voice Data Models
**Estimated Effort**: 1 hour

**File**: `backend/app/models/voice.py`

```python
"""
Voice interaction models
"""
from pydantic import BaseModel
from typing import Optional

class VoiceTranscription(BaseModel):
    """Whisper transcription result"""
    text: str
    language: str = 'vi'
    duration_ms: int

class VoiceIntent(BaseModel):
    """Classified intent"""
    intent: str
    symbol: Optional[str] = None
    confidence: float
    original_text: str

class VoiceResponse(BaseModel):
    """Voice response"""
    text: str
    audio: Optional[bytes] = None
    duration_ms: int
```

---

### Task 3.7: Integrate into Backend
**Estimated Effort**: 1 hour

**Update** `backend/app/main.py`:

```python
from app.capital_companion.voice_service import init_voice_service
from app.events import voice_events

# Add global
voice_service = None

# Update lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    global voice_service
    # ... existing code ...

    # Initialize Voice Service
    try:
        voice_service = init_voice_service(
            openai_api_key=capital_config.OPENAI_API_KEY,
            vieneu_tts_url=capital_config.VIENEU_TTS_URL
        )
        logger.info("Voice service initialized")
    except Exception as e:
        logger.error(f"Voice service initialization failed: {e}")

    app.state.voice_service = voice_service

    yield
    # ... shutdown ...
```

---

### Task 3.8: Update Frontend
**Estimated Effort**: 3-4 hours

**Update** `src/components/CapitalCompanionPanel.tsx`:

```typescript
const handleTalkToggle = async () => {
  if (isTalking) {
    // Stop recording
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
    }
    setIsTalking(false);
  } else {
    // Start recording
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm'
      });

      mediaRecorderRef.current = mediaRecorder;

      // Emit voice:start
      socket.emit('voice:start');

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          // Send audio chunk to backend
          socket.emit('voice:audio', event.data);
        }
      };

      mediaRecorder.onstop = () => {
        // Emit voice:stop
        socket.emit('voice:stop');
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start(100); // Send chunks every 100ms
      setIsTalking(true);

    } catch (err) {
      console.error('Microphone access denied:', err);
    }
  }
};

// Listen for voice events
useEffect(() => {
  socket.on('voice:transcription', (data: { text: string }) => {
    console.log('Transcription:', data.text);
  });

  socket.on('voice:audio_response', (audioData: Blob) => {
    // Play audio response
    const audio = new Audio(URL.createObjectURL(new Blob([audioData])));
    audio.play();
  });

  socket.on('voice:text_response', (data: { text: string }) => {
    // Add AI response to messages
    const newMessage = {
      id: Date.now(),
      text: data.text,
      isAI: true,
      timestamp: new Date().toLocaleTimeString()
    };
    setMessages(prev => [...prev, newMessage]);
  });

  return () => {
    socket.off('voice:transcription');
    socket.off('voice:audio_response');
    socket.off('voice:text_response');
  };
}, [socket]);
```

---

## VERIFICATION STEPS

1. **Test Whisper API**:
   ```bash
   # Manual test
   python
   >>> from app.capital_companion.voice_service import VoiceService
   >>> service = VoiceService('your-api-key', 'http://tts-server')
   >>> with open('test_audio.webm', 'rb') as f:
   ...     result = await service.transcribe(f.read())
   >>> print(result)
   ```

2. **Test Intent Classification**:
   ```python
   >>> from app.processors.intent_processor import IntentProcessor
   >>> processor = IntentProcessor()
   >>> intent = processor.classify("Giá vàng bao nhiêu?")
   >>> print(intent)
   # {'intent': 'query_price', 'symbol': 'XAUUSD', ...}
   ```

3. **Test Full Flow**:
   - Open Monitor 1
   - Click "TALK" button
   - Speak: "Giá Bitcoin bao nhiêu?"
   - Should hear Vietnamese response
   - Check console for transcription

---

## ACCEPTANCE CRITERIA

- [ ] Voice recording works (MediaRecorder API)
- [ ] Audio chunks sent to backend via Socket.IO
- [ ] Whisper transcribes Vietnamese correctly
- [ ] Intent classification works for common queries
- [ ] VieNeu-TTS generates Vietnamese audio
- [ ] Audio response plays in browser
- [ ] Roundtrip latency < 4 seconds
- [ ] Voice interactions stored in database
- [ ] Error handling for microphone access denied

---

## NEXT PHASE

**Phase 4**: AI Pattern Recognition

See `phase-04-pattern-recognition.md`
