# EV GamePad - Code Standards & Guidelines

**Last Updated:** 2026-01-01
**Version:** Phase 1 (Audio System) + Phase 5.4 (Advisor Features)

---

## Table of Contents

1. [Naming Conventions](#naming-conventions)
2. [Code Organization](#code-organization)
3. [Backend Standards](#backend-standards)
4. [Frontend Standards](#frontend-standards)
5. [Type Safety](#type-safety)
6. [Error Handling](#error-handling)
7. [Testing Standards](#testing-standards)
8. [Documentation Standards](#documentation-standards)

---

## Naming Conventions

### Python Backend

**Module/File Names:**
- Use `snake_case` for file names
- Group related modules in directories
- Example: `technical_analyzer.py`, `advisor_processor.py`

**Class Names:**
- Use `PascalCase`
- Descriptive, concrete names
- Examples: `AdvisorProcessor`, `TechnicalAnalyzer`, `RedisClient`

**Function Names:**
- Use `snake_case`
- Verb-based for functions that perform actions
- Examples: `process_technical_summary()`, `calculate_portfolio_health()`, `fetch_ohlcv()`

**Constant Names:**
- Use `UPPER_SNAKE_CASE`
- Group related constants at module top
- Examples: `MT5_TIMEFRAMES`, `CACHE_TTL_SECONDS`, `DEFAULT_RISK_PROFILE`

**Variable Names:**
- Use `snake_case`
- Descriptive, single-letter variables only in loops
- Examples:
  ```python
  # Good
  portfolio_health = {...}
  position_analysis = [...]

  # Avoid
  ph = {...}
  pa = [...]
  ```

**Private Methods/Variables:**
- Prefix with `_` for internal use only
- Example: `_analyze_single_position()`, `_calculate_cache_key()`

**Async Functions:**
- No special prefix/suffix (async is in `async def`)
- Examples: `async def process_portfolio_analysis()`, `async def generate_advice()`

### TypeScript Frontend

**File Names:**
- Use `PascalCase` for components: `PositionInputForm.tsx`, `AIRiskAdvisoryPanel.tsx`
- Use `camelCase` for hooks: `usePortfolioAnalysis.ts`
- Use `snake_case` for utilities: `api_client.ts`, `cache_utils.ts`

**Component Names:**
- Match file name (PascalCase)
- Export as default or named export
- Example: `export const PositionInputForm: React.FC<Props> = (...)`

**Hook Names:**
- Always start with `use` prefix
- Describe return value
- Examples: `usePortfolioAnalysis()`, `useTechnicalAnalysis()`, `useSocketIO()`

**Type/Interface Names:**
- Use `PascalCase`
- Suffix with `Props` for component props
- Examples: `PortfolioAnalysisRequest`, `PositionInputFormProps`, `AIAdvice`

**Enum Names:**
- Use `PascalCase`
- Example: `enum RiskStatus { SAFE, CAUTION, DANGER }`

---

## Code Organization

### Backend Directory Structure

```
backend/app/
├── advisor/                              # Technical analysis modules
│   ├── __init__.py
│   ├── technical_analyzer.py            # Indicator calculation
│   ├── pattern_detector.py              # Candlestick patterns
│   ├── chart_pattern_detector.py        # Chart patterns
│   ├── support_resistance.py            # S/R level calculation
│   ├── risk_analyzer.py                 # Risk metrics
│   ├── ai_summarizer.py                 # LLM integration
│   ├── recommendation_engine.py         # Signal aggregation
│   ├── data_fetcher.py                  # MT5 data fetching
│   └── swing_utils.py                   # Swing high/low detection
│
├── database/                             # Data persistence
│   ├── __init__.py
│   └── redis_client.py                  # Redis wrapper + cache methods
│
├── events/                               # Socket.IO event handlers
│   ├── __init__.py
│   ├── advisor_events.py                # Advisor event handlers
│   └── trading_events.py                # Trading events
│
├── models/                               # Pydantic data models
│   ├── __init__.py
│   ├── advisor_models.py                # Advisor request/response models
│   ├── responses.py                     # Generic response format
│   └── user_profile.py                  # User profile model
│
├── processors/                           # Business logic coordinators
│   ├── __init__.py
│   ├── advisor_processor.py             # Advisor request processor
│   └── command_processor.py             # Command processor
│
├── mt5/                                  # MT5 integration
│   ├── __init__.py
│   ├── connection_manager.py            # Connection lifecycle
│   ├── circuit_breaker.py               # Fault tolerance
│   ├── error_handler.py                 # Error handling
│   └── trading_operations.py            # Trading operations
│
├── config.py                             # Configuration
├── logging_config.py                     # Logging setup
├── main.py                               # Server entry point
├── sio.py                                # Socket.IO singleton
└── validation.py                         # Input validation
```

### Frontend Directory Structure

```
src/
├── components/                           # Reusable React components
│   ├── PositionInputForm.tsx            # Portfolio position input
│   ├── AIRiskAdvisoryPanel.tsx          # Portfolio analysis display
│   ├── TechnicalChart.tsx               # Chart display
│   └── index.ts                         # Component exports
│
├── hooks/                                # Custom React hooks
│   ├── usePortfolioAnalysis.ts          # Portfolio analysis hook
│   ├── useTechnicalAnalysis.ts          # Technical analysis hook
│   ├── useSocketIO.ts                   # Socket.IO management
│   └── index.ts                         # Hook exports
│
├── pages/                                # Page components
│   ├── Portfolio.tsx                    # Portfolio analysis page
│   ├── Technical.tsx                    # Technical analysis page
│   └── index.ts                         # Page exports
│
├── types/                                # TypeScript types
│   ├── advisor.ts                       # Advisor API types
│   ├── portfolio.ts                     # Portfolio types
│   └── index.ts                         # Type exports
│
├── utils/                                # Utility functions
│   ├── api_client.ts                    # API client
│   ├── formatters.ts                    # Data formatting
│   └── validators.ts                    # Input validation
│
├── App.tsx                               # Root component
└── index.tsx                             # Entry point
```

---

## Backend Standards

### Python Code Style

**Imports:**
```python
# Standard library
import os
import json
import asyncio
from typing import Dict, Any, List, Optional

# Third-party
import pandas as pd
from pydantic import BaseModel, Field

# Local
from app.config import config
from app.models.advisor_models import PortfolioAnalysisRequest
```

**Function Documentation:**
```python
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
        risk_profile: User risk tolerance (conservative/moderate/aggressive)
        language: Output language (vi/en)

    Returns:
        PortfolioAnalysisResponse as dict with:
        - portfolio_health: PortfolioHealth object
        - position_analysis: List[PositionAnalysis]
        - ai_advice: AIAdvice object
        - cached: bool
        - computed_at: ISO 8601 timestamp

    Raises:
        ValueError: If positions list is empty or account_balance <= 0

    Note:
        Uses semantic caching via Redis to reduce LLM calls.
        Parallel position analysis via asyncio.gather().
    """
```

**Error Handling Pattern:**
```python
try:
    # Main logic
    result = await self.processor.process_portfolio_analysis(...)
    await sio.emit('advisor:portfolio_result', result, to=sid)

except ValidationError as e:
    logger.warning(f"[{sid}] Validation failed: {e}")
    await sio.emit('advisor:error', error_response(
        ErrorCode.VALIDATION_ERROR,
        f"Invalid portfolio analysis request: {str(e)}"
    ), to=sid)

except Exception as e:
    logger.exception(f"[{sid}] Portfolio analysis failed: {e}")
    await sio.emit('advisor:error', error_response(
        ErrorCode.INTERNAL_ERROR,
        f"Portfolio analysis failed: {str(e)}"
    ), to=sid)
```

**Async/Await Pattern:**
```python
# Parallel processing
position_tasks = [
    self._analyze_single_position(pos, account_balance, risk_profile)
    for pos in positions
]
position_results = await asyncio.gather(*position_tasks, return_exceptions=True)

# Filter exceptions
valid_results = [
    r for r in position_results
    if not isinstance(r, Exception)
]
```

**Type Hints:**
```python
# Function signatures - always include return type
def _calculate_portfolio_health(
    self,
    position_results: List[Dict[str, Any]],
    account_balance: float
) -> Dict[str, Any]:
    """Calculate portfolio health metrics."""

# Optional parameters
def __init__(
    self,
    mt5_manager,
    redis_client: Optional[RedisClient] = None
):
    """Initialize processor."""

# Union types
def validate_signal(signal: str) -> bool:
    """Check if signal is BUY, SELL, or HOLD."""
    return signal in ["BUY", "SELL", "HOLD"]
```

### Pydantic Model Standards

```python
from pydantic import BaseModel, Field

class PortfolioAnalysisRequest(BaseModel):
    """Request for portfolio analysis."""

    # Required fields
    positions: List[PositionInput] = Field(
        ...,                            # Required
        min_length=1,
        max_length=10,
        description="User open positions"
    )
    account_balance: float = Field(
        ...,
        gt=0,                           # Greater than
        description="Total account balance"
    )

    # Optional with defaults
    risk_profile: str = Field(
        default="conservative",
        pattern="^(conservative|moderate|aggressive)$",
        description="User risk tolerance"
    )
    language: str = Field(
        default="vi",
        pattern="^(vi|en)$",
        description="Output language"
    )

    class Config:
        # Immutable after creation
        frozen = False
        # JSON schema generation
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

### Cache Pattern

```python
# Check cache first
cache_key = self._generate_portfolio_cache_key(positions, account_balance, risk_profile)
if self.redis_client:
    try:
        cached = await self.redis_client.get_portfolio_analysis(cache_key)
        if cached:
            logger.debug(f"[{sid}] Portfolio cache hit")
            cached['cached'] = True
            return success_response(cached)
    except Exception as e:
        logger.warning(f"[{sid}] Cache read failed: {e}")
        # Continue without cache

# Process (cache miss)
result = {...}

# Save to cache
if self.redis_client:
    await self.redis_client.set_portfolio_analysis(cache_key, result, ttl=300)

return success_response(result)
```

---

## Audio System Patterns

### Phase 3: SFX Event Emitter

**Threshold-based SFX triggering:**

```typescript
import { sfxEmitter } from '@/services/sfx-event-emitter';

// Trade event with amount threshold
const handleTrade = (orderData: OrderResult) => {
  const tradeType = orderData.order?.type === 0 ? 'trade:buy' : 'trade:sell';
  sfxEmitter.emit({
    type: tradeType,
    metadata: {
      amount: orderData.order?.volume || 0,
      symbol: orderData.order?.symbol
    }
  });
  // SFX only plays if amount >= minTradeAmount threshold
  // Debounced with 500ms cooldown
};

// Market alert with severity filtering
const handlePortfolioAlert = (portfolioStatus: string) => {
  if (portfolioStatus === 'DANGER') {
    sfxEmitter.emit({
      type: 'market:alert:high',
      metadata: { severity: 'high' }
    });
  } else if (portfolioStatus === 'CAUTION') {
    sfxEmitter.emit({
      type: 'market:alert:medium',
      metadata: { severity: 'medium' }
    });
  }
};

// Achievement always plays
const handleAchievement = (badge: string) => {
  sfxEmitter.emit({
    type: 'achievement:unlock',
    metadata: { badge }
  });
};
```

**Emitter Features:**
- Threshold filtering: Only plays if conditions met
- Debouncing: 500ms cooldown per SFX type
- Metadata support: Context for event (amount, severity, symbol)
- Mute state: Respects global mute in AudioManager

**SFX Event Type Safety:**

```typescript
import { SFXEvent, SFXType } from '@/types/audio';

// Type-safe event emission
const event: SFXEvent = {
  type: 'trade:buy' as SFXType,
  metadata: {
    amount: 0.5,
    symbol: 'XAU/USD'
  }
};
sfxEmitter.emit(event);
```

### Phase 3: React Audio Context

**Hook-based audio control:**

```typescript
import { useAudio } from '@/context/AudioContext';

export const MyAudioComponent = () => {
  const {
    isInitialized,
    currentTrack,
    isPlaying,
    isMuted,
    volumes,
    playTrack,
    pauseTrack,
    setVolume,
    toggleMute,
    playSFX,
    setSfxThresholds,
    saveSettings
  } = useAudio();

  // Initialize on demand (requires user gesture)
  const handleInit = async () => {
    if (!isInitialized) {
      await initialize();
    }
  };

  // Control music
  const handlePlayTrack = async (trackId: string) => {
    await playTrack(trackId);
  };

  // Update volume (auto-persists)
  const handleVolumeChange = (channel: VolumeChannel, value: number) => {
    setVolume(channel, value);
  };

  // Update SFX filtering
  const handleThresholds = (thresholds: SFXThresholds) => {
    setSfxThresholds(thresholds);
    saveSettings();  // Explicit persistence after threshold change
  };

  return (
    <div>
      {/* UI elements */}
    </div>
  );
};
```

**Context Benefits:**
- Centralized audio state
- Automatic localStorage persistence
- Auto-resume music on app reload
- Type-safe volume control
- Easy component access via hook

### Phase 3: AudioSettingsModal Component

**Settings UI pattern:**

```typescript
import { AudioSettingsModal } from '@/components/AudioSettingsModal';
import { useState } from 'react';

export const App = () => {
  const [settingsOpen, setSettingsOpen] = useState(false);

  return (
    <>
      <button onClick={() => setSettingsOpen(true)}>Settings</button>
      <AudioSettingsModal
        open={settingsOpen}
        onOpenChange={setSettingsOpen}
      />
    </>
  );
};
```

**Modal Features:**
- Music track selector (dropdown from available tracks)
- Volume sliders (0-1 range):
  - Master: affects all audio
  - Music: music playback level
  - SFX: sound effect level
- Mute toggle (global)
- SFX Thresholds:
  - Minimum trade amount (numeric, prevents small trades from playing SFX)
  - Alert severity (all/high, filters market alerts)
- Apply/Cancel: local state allows discarding changes
- Auto-persistence: saveSettings() on apply

**Modal State Management Pattern:**

```typescript
// Local state for "apply/cancel" workflow
const [localMasterVolume, setLocalMasterVolume] = useState(volumes.master);

// Sync when modal opens
useEffect(() => {
  if (open) {
    setLocalMasterVolume(volumes.master);
    // ... sync other settings
  }
}, [open]);

// Apply changes to context
const handleApply = () => {
  setVolume('master', localMasterVolume);
  saveSettings();
  onOpenChange(false);
};

// Cancel discards local changes
const handleCancel = () => {
  onOpenChange(false);
};
```

### Phase 1: AudioManager Singleton Usage

**Initialization (requires user gesture):**

```typescript
// Initialize on first user interaction
const handleInitAudio = async () => {
  try {
    await audioManager.initialize();
    console.log('Audio ready');
  } catch (error) {
    console.error('Audio init failed:', error);
  }
};

// In component
useEffect(() => {
  document.addEventListener('click', handleInitAudio, { once: true });
  return () => document.removeEventListener('click', handleInitAudio);
}, []);
```

**Music Playback:**

```typescript
// Load and play a track
const playTrack = async (trackId: string) => {
  try {
    await audioManager.loadMusicTrack(trackId);
    audioManager.playMusic();
  } catch (error) {
    console.error('Playback failed:', error);
  }
};

// Pause and resume
audioManager.pauseMusic();
audioManager.playMusic();  // Resumes from saved position

// Stop (resets position)
audioManager.stopMusic();
```

**SFX Triggering:**

```typescript
// Play simple SFX
audioManager.playSFX('trade:buy');

// Play with custom volume
audioManager.playSFX('market:alert:high', { volume: 0.8 });

// SFX is automatically debounced (500ms cooldown per type)
// Mute state is respected (no SFX plays when isMuted=true)
```

**Volume Control:**

```typescript
// Channels: 'master' | 'music' | 'sfx'
audioManager.setVolume('master', 0.8);   // 80% overall
audioManager.setVolume('music', 0.7);    // 70% music relative to master
audioManager.setVolume('sfx', 0.9);      // 90% SFX relative to master

// Final levels: music = 0.8 × 0.7 = 0.56, sfx = 0.8 × 0.9 = 0.72

// Mute/unmute (global)
audioManager.toggleMute();

// Persist settings to localStorage
audioManager.saveSettings();
```

**Settings Management:**

```typescript
// Get current settings snapshot
const settings = audioManager.getSettings();
console.log(settings.masterVolume);      // 0-1
console.log(settings.currentTrackId);    // 'focus-ambient' or null
console.log(settings.isMuted);           // boolean
console.log(settings.playbackPosition);  // seconds

// Reload settings from localStorage
audioManager.loadSettings();
```

**Cleanup (on unmount):**

```typescript
// Component cleanup
useEffect(() => {
  return () => {
    if (audioManager.isInitialized()) {
      audioManager.pauseMusic();
      audioManager.saveSettings();  // Persist before cleanup
    }
  };
}, []);

// App shutdown
audioManager.dispose();  // Free Tone.js resources
```

### Audio Storage Utilities

**Update specific setting:**

```typescript
import { updateAudioSetting, loadAudioSettings, saveAudioSettings } from '@/utils/audio-storage';

// Option 1: Granular update (recommended)
updateAudioSetting('masterVolume', 0.75);
updateAudioSetting('isMuted', true);

// Option 2: Load, modify, save (for multiple changes)
const settings = loadAudioSettings();
settings.masterVolume = 0.75;
settings.musicVolume = 0.6;
saveAudioSettings(settings);
```

**Error handling:**

```typescript
// All audio-storage functions handle errors gracefully
try {
  updateAudioSetting('masterVolume', 0.5);
  // Silently logs error to console if localStorage fails
  // Returns undefined on error
} catch (error) {
  console.error('Storage error:', error);
  // Application continues with default settings
}
```

### Audio Type System

**Type-safe audio operations:**

```typescript
import {
  AudioSettings,
  MusicTrack,
  SFXType,
  SFXOptions,
  VolumeChannel,
  MUSIC_TRACKS
} from '@/types/audio';

// SFX type safety
const sfxType: SFXType = 'trade:buy';  // ✓ Valid
// const invalid: SFXType = 'foo:bar';  // ✗ TypeScript error

// Volume channels
const channels: VolumeChannel[] = ['master', 'music', 'sfx'];

// Available tracks
console.log(MUSIC_TRACKS);  // Pre-configured track list
// [
//   { id: 'focus-ambient', name: 'Focus Ambient', ... },
//   { id: 'energy-upbeat', name: 'Energy Upbeat', ... },
//   ...
// ]
```

### Common Patterns

**Pattern: Initialize on demand**

```typescript
export const useAudioInitialize = () => {
  const [isReady, setIsReady] = useState(false);

  const initialize = useCallback(async () => {
    if (audioManager.isInitialized()) {
      setIsReady(true);
      return;
    }

    try {
      await audioManager.initialize();
      setIsReady(true);
    } catch (error) {
      console.error('Audio init failed:', error);
    }
  }, []);

  return { isReady, initialize };
};
```

**Pattern: Sync audio state with localStorage**

```typescript
// Persist settings after any change
const syncSettings = useCallback(() => {
  audioManager.saveSettings();
  console.log('[Audio] Settings synced to localStorage');
}, []);

// On volume change
const handleVolumeChange = (channel: VolumeChannel, value: number) => {
  audioManager.setVolume(channel, value);
  syncSettings();
};
```

**Pattern: Cleanup on component unmount**

```typescript
useEffect(() => {
  return () => {
    // Always save state before unmounting
    if (audioManager.isInitialized()) {
      audioManager.saveSettings();
    }
  };
}, []);
```

### Known Limitations

**Phase 1 (still applicable):**
1. **Browser autoplay policy:** Must initialize in response to user gesture
2. **No advanced effects:** No fade-in/out, crossfade, or dynamic volume yet

**Phase 3 (addressed from Phase 1):**
- ✓ UI controls added (AudioSettingsModal)
- ✓ Event triggers implemented (trade, portfolio analysis)
- ✓ React Context added
- ✓ localStorage persistence

**Phase 3 Limitations (Phase 4+):**
1. **No keyboard shortcuts:** Will be added in Phase 4
2. **No backend integration:** SFX triggered client-side only
3. **No streaming audio:** All audio files must be pre-downloaded
4. **No audio effects:** No equalizer, reverb, or compression
5. **Single-threaded debouncing:** Per-type cooldown, not global

---

## Frontend Standards

### React Component Structure

```typescript
import React, { useState, useCallback } from 'react';
import { Plus, Trash2 } from 'lucide-react';

interface Position {
  id: string;
  symbol: string;
  entryPrice: number;
  currentPrice: number;
  positionSize: number;
  stopLoss: number;
  timeframe: string;
}

interface PositionInputFormProps {
  onSubmit: (positions: Position[], accountBalance: number) => void;
  isAnalyzing: boolean;
}

/**
 * Form component for entering portfolio positions.
 *
 * @param {PositionInputFormProps} props - Component props
 * @returns {JSX.Element} Rendered form
 *
 * @example
 * <PositionInputForm
 *   onSubmit={handleSubmit}
 *   isAnalyzing={false}
 * />
 */
export const PositionInputForm: React.FC<PositionInputFormProps> = ({
  onSubmit,
  isAnalyzing
}) => {
  const [accountBalance, setAccountBalance] = useState(10000);
  const [positions, setPositions] = useState<Position[]>([
    {
      id: crypto.randomUUID(),
      symbol: 'XAUUSD',
      entryPrice: 0,
      currentPrice: 0,
      positionSize: 0,
      stopLoss: 0,
      timeframe: 'H1'
    }
  ]);

  const addPosition = useCallback(() => {
    setPositions(prev => [
      ...prev,
      {
        id: crypto.randomUUID(),
        symbol: '',
        entryPrice: 0,
        currentPrice: 0,
        positionSize: 0,
        stopLoss: 0,
        timeframe: 'H1'
      }
    ]);
  }, []);

  const removePosition = useCallback((id: string) => {
    setPositions(prev => prev.filter(p => p.id !== id));
  }, []);

  const updatePosition = useCallback(
    (id: string, field: keyof Position, value: string | number) => {
      setPositions(prev =>
        prev.map(p =>
          p.id === id ? { ...p, [field]: value } : p
        )
      );
    },
    []
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(positions, accountBalance);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Form content */}
    </form>
  );
};
```

### Custom Hook Pattern

```typescript
import { useEffect, useRef, useState, useCallback } from 'react';
import io, { Socket } from 'socket.io-client';
import { PortfolioAnalysisRequest, PortfolioAnalysisResponse } from '@/types/advisor';

interface UsePortfolioAnalysisReturn {
  result: PortfolioAnalysisResponse | null;
  error: string | null;
  loading: boolean;
  analyze: (request: PortfolioAnalysisRequest) => void;
}

/**
 * Hook for portfolio analysis with Socket.IO integration.
 *
 * @returns {UsePortfolioAnalysisReturn} Analysis state and analyze function
 *
 * @example
 * const { result, error, loading, analyze } = usePortfolioAnalysis();
 *
 * const handleAnalyze = () => {
 *   analyze({
 *     positions: [...],
 *     account_balance: 10000,
 *     risk_profile: 'conservative',
 *     language: 'en'
 *   });
 * };
 */
export const usePortfolioAnalysis = (): UsePortfolioAnalysisReturn => {
  const socketRef = useRef<Socket | null>(null);
  const [result, setResult] = useState<PortfolioAnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Initialize Socket.IO connection
    socketRef.current = io('ws://localhost:8000');

    // Listen for results
    socketRef.current.on('advisor:portfolio_result', (data) => {
      if (data.success) {
        setResult(data.data);
        setError(null);
        setLoading(false);
      }
    });

    // Listen for errors
    socketRef.current.on('advisor:error', (data) => {
      setError(data.message);
      setLoading(false);
    });

    return () => {
      socketRef.current?.disconnect();
    };
  }, []);

  const analyze = useCallback((request: PortfolioAnalysisRequest) => {
    if (!socketRef.current) return;

    setLoading(true);
    setError(null);
    socketRef.current.emit('advisor:portfolio_analysis', request);
  }, []);

  return { result, error, loading, analyze };
};
```

### TypeScript Interfaces

```typescript
// Strict typing for API requests/responses
interface PortfolioAnalysisRequest {
  positions: PositionInput[];
  account_balance: number;
  risk_profile?: 'conservative' | 'moderate' | 'aggressive';
  language?: 'vi' | 'en';
}

interface PortfolioHealth {
  score: number;              // 0-100
  status: 'HEALTHY' | 'CAUTION' | 'DANGER';
  total_risk_exposure: number;
  current_drawdown: number;
  positions_at_risk: number;
}

interface PositionAnalysis {
  symbol: string;
  entry_price: number;
  current_price: number;
  position_size: number;
  stop_loss: number;
  pnl_pct: number;
  pnl_amount: number;
  r_multiple: number;
  distance_to_stop_pct: number;
  risk_status: 'safe' | 'caution' | 'approaching_stop' | 'danger';
  recommendation: 'HOLD' | 'REDUCE' | 'CLOSE';
  technical_signal: 'bullish' | 'bearish' | 'neutral';
  technical_confidence: number;
}

interface AIAdvice {
  summary: string;
  overall_risk: 'LOW' | 'MODERATE' | 'HIGH';
  priority_actions: string[];
  reasoning: string;
  confidence: number;
  model: 'claude' | 'deepseek';
  cached: boolean;
  generated_at: string;
}
```

---

## Type Safety

### Backend Type Hints

**Always use type hints:**
```python
# Good
def calculate_risk(
    entry: float,
    stop: float,
    position_size: float
) -> float:
    return abs(entry - stop) * position_size

# Avoid
def calculate_risk(entry, stop, position_size):
    return abs(entry - stop) * position_size
```

**Use Optional for nullable types:**
```python
# Good
def fetch_current_price(self, symbol: str) -> Optional[float]:
    try:
        df = await self.data_fetcher.fetch_ohlcv(symbol, 'H1', 1)
        if df is not None and len(df) > 0:
            return float(df['close'].iloc[-1])
    except Exception as e:
        logger.error(f"Failed to fetch price: {e}")
    return None

# Avoid
def fetch_current_price(self, symbol):
    ...
```

**Use Union for multiple types:**
```python
# Good
def format_value(value: Union[float, int, str]) -> str:
    return str(value)

# Avoid
def format_value(value):
    return str(value)
```

### Frontend Type Safety

**Always use TypeScript in components:**
```typescript
// Good - Explicit types
const MyComponent: React.FC<MyComponentProps> = ({ data, onUpdate }) => {
  const [count, setCount] = useState<number>(0);
  return <div>{count}</div>;
};

// Avoid - Implicit any
const MyComponent = ({ data, onUpdate }) => {
  const [count, setCount] = useState(0);
  return <div>{count}</div>;
};
```

**Use interfaces over type aliases for objects:**
```typescript
// Good
interface PositionData {
  symbol: string;
  entryPrice: number;
}

// Less preferred for objects
type PositionData = {
  symbol: string;
  entryPrice: number;
};
```

---

## Error Handling

### Backend Error Pattern

```python
# In event handler
try:
    # Input validation
    if not symbol:
        await sio.emit('advisor:error', error_response(
            ErrorCode.VALIDATION_ERROR,
            "Symbol is required"
        ), to=sid)
        return

    # Main processing
    result = await self.processor.process_portfolio_analysis(...)
    await sio.emit('advisor:portfolio_result', result, to=sid)

except ValidationError as e:
    # Pydantic validation
    await sio.emit('advisor:error', error_response(
        ErrorCode.VALIDATION_ERROR,
        f"Invalid input: {str(e)}"
    ), to=sid)

except KeyError as e:
    # Missing required data
    await sio.emit('advisor:error', error_response(
        ErrorCode.INTERNAL_ERROR,
        f"Missing data: {str(e)}"
    ), to=sid)

except Exception as e:
    # Catch-all for unexpected errors
    logger.exception(f"Unexpected error: {e}")
    await sio.emit('advisor:error', error_response(
        ErrorCode.INTERNAL_ERROR,
        "An unexpected error occurred"
    ), to=sid)
```

### Frontend Error Boundary Pattern (Phase 5.4)

**ErrorBoundary Component Usage:**
```typescript
import { ErrorBoundary, withErrorBoundary } from '@/components/ErrorBoundary';

// Wrap single component
<ErrorBoundary>
  <IndicatorOverlayChart symbol="XAUUSD" timeframe="H1" />
</ErrorBoundary>

// Wrap with custom fallback
<ErrorBoundary
  fallback={<CustomErrorUI />}
  onError={(error, errorInfo) => console.error(error)}
>
  <AccuracyMetricsPanel {...props} />
</ErrorBoundary>

// Higher-order component
const SafeComponent = withErrorBoundary(MyComponent, <CustomFallback />);
```

**Error Boundary Responsibilities:**
- Catches rendering errors from child components
- Prevents cascade failures (rest of app continues)
- Displays user-friendly error UI with "Try Again" option
- Logs errors to console (development mode includes stack trace)
- Optional error callback for reporting services

**Component Error Pattern:**
```typescript
const { result, error, loading, analyze } = usePortfolioAnalysis();

if (loading) {
  return <LoadingSpinner />;
}

if (error) {
  return <ErrorMessage message={error} />;
}

if (!result) {
  return <EmptyState />;
}

return <AIRiskAdvisoryPanel {...result.data} />;
```

**Type Guard Validation (Phase 5.4 - NEW):**
```typescript
// In components receiving Socket.IO data
function isValidTechnicalData(data: unknown): data is TechnicalResultData {
  return (
    typeof data === 'object' &&
    data !== null &&
    'symbol' in data &&
    'timeframe' in data &&
    typeof (data as any).symbol === 'string'
  );
}

// Usage
if (isValidTechnicalData(responseData)) {
  setData(responseData);
} else {
  setError('Invalid data format');
}
```

---

## Testing Standards

### Backend Unit Tests

```python
import pytest
from app.models.advisor_models import PortfolioAnalysisRequest

@pytest.mark.asyncio
async def test_process_portfolio_analysis_success(processor, mock_data_fetcher):
    """Test successful portfolio analysis."""
    # Arrange
    request = PortfolioAnalysisRequest(
        positions=[...],
        account_balance=10000,
        risk_profile='conservative',
        language='vi'
    )

    # Act
    result = await processor.process_portfolio_analysis(
        sid='test-session',
        positions=request.positions,
        account_balance=request.account_balance,
        risk_profile=request.risk_profile,
        language=request.language
    )

    # Assert
    assert result['success'] is True
    assert 'portfolio_health' in result['data']
    assert 'position_analysis' in result['data']
    assert 'ai_advice' in result['data']
    assert result['data']['portfolio_health']['score'] >= 0
    assert result['data']['portfolio_health']['score'] <= 100
```

**Test Coverage Goals:**
- Unit tests: 80%+ coverage for critical paths
- Integration tests: All event handlers
- Edge cases: Empty portfolios, invalid symbols, missing prices

---

## Documentation Standards

### Code Comments

```python
# Good - explains WHY not WHAT
# Round prices to nearest 10 to improve cache hit rate
price_bucket = round(price, -1)

# Avoid - obvious from code
# Create a new list
new_list = []

# Good - complex logic documentation
"""
Risk status determination:
- danger: < 1% away from stop-loss (immediate action needed)
- approaching_stop: 1-3% away (reduce position)
- caution: bearish signal + negative P&L (prepare to close)
- safe: normal operation (hold)
"""
```

### Function Documentation

```python
async def process_portfolio_analysis(
    self,
    sid: str,
    positions: List[PositionInput],
    account_balance: float,
    risk_profile: str,
    language: str
) -> Dict[str, Any]:
    """
    Process comprehensive portfolio analysis.

    Analyzes all positions in parallel, calculates portfolio health,
    and generates LLM-powered capital preservation advice.

    Args:
        sid: Socket.IO session ID for error responses
        positions: List of user open positions (1-10)
        account_balance: Total account balance in USD
        risk_profile: "conservative", "moderate", or "aggressive"
        language: "vi" for Vietnamese, "en" for English

    Returns:
        Dict with keys:
        - success: bool
        - data: PortfolioAnalysisResponse (if successful)
        - error_code, message: (if failed)

    Raises:
        ValueError: If positions empty or account_balance <= 0

    Example:
        >>> result = await processor.process_portfolio_analysis(
        ...     sid='session-123',
        ...     positions=[...],
        ...     account_balance=10000,
        ...     risk_profile='conservative',
        ...     language='vi'
        ... )
        >>> assert result['success']

    Note:
        Positions analyzed in parallel for performance.
        Results cached for 300 seconds (deterministic caching).
        LLM fallback to DeepSeek if Claude unavailable.
    """
```

---

## Code Review Checklist

Before submitting a PR:

- [ ] Type hints present on all functions
- [ ] Error handling for all edge cases
- [ ] Docstrings on public functions
- [ ] No hardcoded values (use config/constants)
- [ ] Proper logging statements
- [ ] Tests pass locally
- [ ] No console.log or print statements left
- [ ] Follows naming conventions
- [ ] Cache keys deterministic and documented
- [ ] Async/await used properly (no fire-and-forget)

---

## Performance Guidelines

### Backend

- Portfolio analysis: < 5 seconds (first request)
- Technical analysis: < 2 seconds (cache hit: < 200ms)
- LLM response: < 3 seconds
- Cache hit rate target: > 60%

### Frontend

- Initial page load: < 3 seconds
- Portfolio form submit: < 0.5 seconds (UI feedback only)
- Results display: < 1 second after socket response
- Zero jank (60 FPS) during animations

---

## Dependencies

### Backend
- `fastapi` - Web framework
- `python-socketio` - WebSocket
- `pydantic` - Validation
- `pandas` - Data manipulation
- `anthropic` - Claude API
- `redis` - Caching

### Frontend
- `react` - UI framework
- `typescript` - Type safety
- `socket.io-client` - WebSocket
- `tailwindcss` - Styling
- `lucide-react` - Icons
- `tone` - Audio playback (v15.1.22) - Phase 1 Audio System

---

## Socket.IO Connection Management (Phase 5.4)

### Cleanup Guidelines

**Memory Leak Prevention:**
- Always unsubscribe from Socket.IO events on component unmount
- Remove event listeners before closing connections
- Clean up timers and intervals

**Hook Cleanup Pattern:**
```typescript
export const useSocketIO = () => {
  const socketRef = useRef<Socket | null>(null);

  useEffect(() => {
    socketRef.current = io(SOCKET_URL);

    // Setup listeners
    socketRef.current.on('event:data', handleData);
    socketRef.current.on('event:error', handleError);

    // CRITICAL: Cleanup on unmount
    return () => {
      if (socketRef.current) {
        socketRef.current.off('event:data', handleData);
        socketRef.current.off('event:error', handleError);
        socketRef.current.disconnect();
      }
    };
  }, []);

  return socketRef.current;
};
```

**Component Cleanup Pattern:**
```typescript
export const MyComponent: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false);
  const isMountedRef = useRef(true);

  useEffect(() => {
    isMountedRef.current = true;

    const handleResponse = (data: unknown) => {
      if (isMountedRef.current) {  // Only update if mounted
        setIsLoading(false);
      }
    };

    socket.on('event:response', handleResponse);

    return () => {
      isMountedRef.current = false;
      socket.off('event:response', handleResponse);
    };
  }, []);

  return <div>...</div>;
};
```

### Reconnection Configuration (Phase 5.4)

**Exponential Backoff Parameters:**
```typescript
io(URL, {
  reconnection: true,
  reconnectionAttempts: 10,          // Max 10 attempts
  reconnectionDelay: 1000,            // Start at 1s
  reconnectionDelayMax: 10000,        // Max 10s
  randomizationFactor: 0.5,           // ±50% jitter
});

// Timeline: 1s → 1.5s → 2.25s → 3.38s → 5.06s → 7.59s → 10s (capped)
```

**Error Handling:**
```typescript
socket.on('disconnect', (reason) => {
  if (reason === 'io client disconnect') {
    // User manually disconnected, don't auto-reconnect
    return;
  }
  // Server disconnect or network error - will auto-reconnect
});

socket.on('reconnect_failed', () => {
  console.error('All reconnection attempts exhausted');
  // Show UI notification to user
});
```

---

**Last Updated:** 2026-01-05 (Phase 1 + Phase 3 Audio System + Phase 5.4)
**Maintained By:** Audio Team (Phase 1 & 3) & Backend & Frontend Teams (Advisor)
