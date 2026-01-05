# EV GamePad - System Architecture

**Last Updated:** 2026-01-05
**Version:** Phase 1 (Audio System) + Phase 3 (SFX Event System) + Phase 4 (Keyboard Shortcuts) + Phase 5.4 (Advisor Features)

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture Layers](#architecture-layers)
3. [Audio System Architecture](#audio-system-architecture)
   - [Phase 1: Core Audio Infrastructure](#phase-1-core-audio-infrastructure)
   - [Phase 3: SFX Event System](#phase-3-sfx-event-system)
   - [Phase 4: Keyboard Shortcuts](#phase-4-keyboard-shortcuts)
4. [Advisor System Architecture](#advisor-system-architecture)
5. [Data Flow](#data-flow)
6. [Integration Points](#integration-points)

---

## Overview

EV GamePad is a full-stack trading advisor application with:
- **Frontend:** React + TypeScript with real-time Socket.IO integration
- **Backend:** Python FastAPI with MT5 trading connections and LLM integration
- **Audio System:** Tone.js-based music and SFX management (Phase 1)
- **AI Advisor:** Multi-model LLM integration for portfolio analysis (Phase 5)

---

## Architecture Layers

### Presentation Layer (React Frontend)

```
┌─────────────────────────────────────────┐
│      React Components (Pages)           │
│  - Portfolio Analysis                   │
│  - Technical Analysis                   │
│  - Chat Interface                       │
└────────────────┬────────────────────────┘
         │
┌────────▼────────────────────────────────┐
│    Custom React Hooks & State           │
│  - usePortfolioAnalysis()               │
│  - useTechnicalAnalysis()               │
│  - useSocketIO()                        │
│  - useAudioSystem() [Phase 1]           │
└────────────────┬────────────────────────┘
         │
┌────────▼────────────────────────────────┐
│      Utility Services                   │
│  - API Client (Socket.IO)               │
│  - AudioManager Singleton [Phase 1]     │
│  - Formatters & Validators              │
└──────────────────────────────────────────┘
```

### Backend Layer (Python FastAPI)

```
┌──────────────────────────────────────────┐
│     Socket.IO Event Handlers             │
│  - advisor_events.py                     │
│  - trading_events.py                     │
│  - audio_events.py [Phase 1 Ready]       │
└────────────┬─────────────────────────────┘
         │
┌────────▼──────────────────────────────────┐
│    Business Logic (Processors)            │
│  - AdvisorProcessor                       │
│  - CommandProcessor                       │
│  - PortfolioAnalyzer                      │
└────────────┬──────────────────────────────┘
         │
┌────────▼──────────────────────────────────┐
│    Core Services                          │
│  - TechnicalAnalyzer                      │
│  - RiskAnalyzer                           │
│  - DataFetcher (MT5)                      │
│  - AISummarizer (Claude/DeepSeek)         │
└────────────┬──────────────────────────────┘
         │
┌────────▼──────────────────────────────────┐
│    Data Layer                             │
│  - RedisClient (Cache & Session)          │
│  - MT5Connection (MarketData)             │
│  - localStorage [Browser - Phase 1]       │
└──────────────────────────────────────────┘
```

---

## Audio System Architecture

### Phase 1: Core Audio Infrastructure

**Overview**

Foundational infrastructure for music playback and sound effects using Tone.js. Includes core components (types, singleton service, localStorage persistence) without UI integration.

### Components

#### 1. Type Definitions (`src/types/audio.ts`)

```typescript
// Audio configuration types
interface AudioSettings {
  masterVolume: number;       // 0-1 linear scale
  musicVolume: number;        // 0-1 per-channel
  sfxVolume: number;          // 0-1 per-channel
  isMuted: boolean;           // Global mute state
  currentTrackId: string | null;
  playbackPosition: number;   // seconds
  sfxThresholds: {
    minTradeAmount: number;
    alertSeverity: 'all' | 'high';
  };
}

// Audio track metadata
interface MusicTrack {
  id: string;
  name: string;
  description: string;
  filePath: string;
  duration?: number;
}

// SFX event types (scoped by domain)
type SFXType =
  | 'trade:buy' | 'trade:sell'
  | 'market:alert:low' | 'market:alert:medium' | 'market:alert:high'
  | 'achievement:unlock' | 'achievement:milestone';

// Volume control channels
type VolumeChannel = 'master' | 'music' | 'sfx';
```

**Type Organization:**
- Located in `/src/types/audio.ts` for centralized type management
- Follows camelCase convention for properties
- Uses enums/union types for restricted values (SFXType, VolumeChannel)

#### 2. AudioManager Service (`src/services/audio-manager.ts`)

**Singleton Pattern Implementation:**

```typescript
class AudioManager {
  private static instance: AudioManager | null = null;

  public static getInstance(): AudioManager {
    if (!AudioManager.instance) {
      AudioManager.instance = new AudioManager();
    }
    return AudioManager.instance;
  }

  private constructor() {
    // Load persisted settings on instantiation
    this.settings = loadAudioSettings();
  }
}

// Export singleton instance
export const audioManager = AudioManager.getInstance();
```

**Core Responsibilities:**

| Method | Purpose | Notes |
|--------|---------|-------|
| `initialize()` | Start Tone.js context | Requires user gesture (browser policy) |
| `loadMusicTrack(trackId)` | Load audio file | Async; handles track switching |
| `playMusic()` / `pauseMusic()` | Control playback | Preserves playback position |
| `setVolume(channel, value)` | Update volume levels | Clamps 0-1, updates Tone.js immediately |
| `playSFX(type, options?)` | Trigger sound effect | Debounced at 500ms; respects mute state |
| `saveSettings()` | Persist to localStorage | Called after settings changes |
| `dispose()` | Cleanup resources | Disposes Tone.js nodes |

**Tone.js Integration:**

- **Music Playback:** `Tone.Player` with looping enabled
- **SFX Playback:** `Tone.Sampler` with pre-loaded audio URLs
- **Volume Calculation:** Converts linear (0-1) to dB scale using `Tone.gainToDb()`
- **Context Management:** Requires `await Tone.start()` before playback

#### 3. Audio Storage Utility (`src/utils/audio-storage.ts`)

**Persistence Pattern:**

```typescript
// localStorage key
const AUDIO_SETTINGS_KEY = 'audioSettings';

// Core operations
export const saveAudioSettings = (settings: AudioSettings): void => {
  localStorage.setItem(AUDIO_SETTINGS_KEY, JSON.stringify(settings));
};

export const loadAudioSettings = (): AudioSettings => {
  const stored = localStorage.getItem(AUDIO_SETTINGS_KEY);
  if (!stored) return DEFAULT_AUDIO_SETTINGS;

  const parsed = JSON.parse(stored);
  return { ...DEFAULT_AUDIO_SETTINGS, ...parsed };  // Merge with defaults
};

export const updateAudioSetting = <K extends keyof AudioSettings>(
  key: K,
  value: AudioSettings[K]
): void => {
  const settings = loadAudioSettings();
  settings[key] = value;
  saveAudioSettings(settings);
};
```

**Design Decisions:**
- Graceful fallback to defaults if localStorage unavailable
- Merge strategy handles schema evolution (new settings in future phases)
- Generic `updateAudioSetting()` for granular updates

### Audio Assets Structure

```
public/audio/
├── music/                           # Background music tracks
│   ├── focus-ambient.mp3           # Calm, minimal distraction
│   ├── energy-upbeat.mp3           # High-tempo trading
│   ├── strategy-chill.mp3          # Mid-tempo analytical
│   └── night-lofi.mp3              # Low-energy late sessions
│
└── sfx/                             # Sound effect clips
    ├── trade-buy.mp3               # Buy trade triggered
    ├── trade-sell.mp3              # Sell trade triggered
    ├── market-alert.mp3            # Market alert notification
    ├── achievement.mp3             # Achievement unlocked
    └── milestone.mp3               # Milestone reached
```

### Browser Audio Context Policy

**Requirement:** AudioManager.initialize() must be called in response to user gesture (click, tap, key press) due to browser autoplay policy.

**Recommended Initialization Points:**
- First user interaction (click on app)
- User settings button click
- Audio control UI initialization

```typescript
// Example: Initialize on first user interaction
document.addEventListener('click', async () => {
  if (!audioManager.isInitialized()) {
    await audioManager.initialize();
  }
}, { once: true });
```

### Volume Scaling

**Master + Channel Architecture:**

```
masterVolume (0-1)
       │
       ├─► musicVolume (0-1)  ─► FinalMusicVolume = master × music
       │
       └─► sfxVolume (0-1)    ─► FinalSFXVolume = master × sfx

Conversion to dB: Tone.gainToDb(finalVolume)
Mute state: -Infinity dB (complete silence)
```

### SFX Debouncing

**Purpose:** Prevent rapid-fire repeated sounds from overwhelming user.

**Implementation:**
- Global cooldown: 500ms between same SFX type
- Tracked via `lastSFXPlayTime` Map
- Future phases can add intelligent filtering (e.g., only play low/high alerts)

### Phase 1 Scope & Limitations

**What's Included:**
- Core infrastructure (types, service, storage)
- Singleton pattern for single audio context
- localStorage persistence
- Volume control hierarchy
- SFX debouncing mechanism

**What's NOT Included in Phase 1:**
- React Context for state management (added Phase 3)
- UI controls (volume sliders, music selector) (added Phase 3)
- Keyboard shortcuts (e.g., M for mute)
- SFX event triggering from trading events (added Phase 3)
- Advanced features (fade-in/out, crossfade)

---

### Phase 3: SFX Event System

**Overview**

Extends Phase 1 with event-driven SFX triggering, threshold filtering, React Context provider, and UI components. Integrates SFX with trading and portfolio analysis events.

#### 1. SFX Event Emitter (`src/services/sfx-event-emitter.ts`)

**Singleton Service for Event-Driven SFX:**

```typescript
class SFXEventEmitter {
  // Threshold-based filtering
  private shouldPlaySFX(event: SFXEvent): boolean {
    // Trade events: check minTradeAmount
    if (event.type.startsWith('trade:')) {
      return event.metadata?.amount >= thresholds.minTradeAmount;
    }
    // Market alerts: filter by severity
    if (event.type.startsWith('market:alert:')) {
      return event.metadata?.severity === 'high' || thresholds.alertSeverity === 'all';
    }
    // Achievements: always play
    if (event.type.startsWith('achievement:')) {
      return true;
    }
    return true;
  }

  // Debouncing: 500ms cooldown per SFX type
  public emit(event: SFXEvent): void {
    if (this.isDebounced(event.type)) return;
    audioManager.playSFX(event.type);
    this.lastPlayedTime.set(event.type, Date.now());
  }
}

export const sfxEmitter = new SFXEventEmitter();
```

**Key Features:**
- Threshold filtering (trade amount, alert severity)
- Debouncing: 500ms per SFX type
- Metadata support for context (amount, symbol, severity)
- Respects mute state via AudioManager

**Event Types Supported:**

| Category | Type | Trigger | Threshold |
|----------|------|---------|-----------|
| Trade | `trade:buy` / `trade:sell` | Successful trade | minTradeAmount |
| Market Alert | `market:alert:low` | Low priority alert | alertSeverity == 'all' |
| | `market:alert:medium` | Medium priority | alertSeverity in ['all', 'high'] |
| | `market:alert:high` | Critical alert | Always plays |
| Achievement | `achievement:unlock` | Badge earned | Always plays |
| | `achievement:milestone` | Major milestone | Always plays |

#### 2. React Audio Context (`src/context/AudioContext.tsx`)

**Provider Component with Full Audio State:**

```typescript
interface AudioContextValue {
  // State
  isInitialized: boolean;
  currentTrack: string | null;
  isPlaying: boolean;
  isMuted: boolean;
  volumes: { master: number; music: number; sfx: number };
  playbackPosition: number;
  availableTracks: MusicTrack[];
  settings: AudioSettings;

  // Actions
  initialize(): Promise<void>;
  playTrack(trackId: string): Promise<void>;
  pauseTrack(): void;
  stopTrack(): void;
  setVolume(channel: VolumeChannel, value: number): void;
  toggleMute(): void;
  playSFX(type: SFXType, options?: SFXOptions): void;
  setSfxThresholds(thresholds: SFXThresholds): void;
  saveSettings(): void;
}

export const useAudio = () => useContext(AudioContext);
```

**Provider Responsibilities:**
- Initializes AudioManager on mount (requires user gesture)
- Restores settings from localStorage
- Auto-resumes music if was playing before refresh
- Syncs context state with AudioManager singleton
- Manages SFX threshold updates

#### 3. Audio Hooks

**useAudioPlayer** (`src/hooks/useAudioPlayer.ts`):
- Extracts all audio context actions
- Type-safe volume control
- Automatic settings persistence

**useAudioKeyboard** (`src/hooks/useAudioKeyboard.ts`):
- Keyboard shortcuts (M=mute, P=play/pause, etc.)
- Focus management
- Prevention of form submission conflicts

#### 4. UI Components

**AudioSettingsModal** (`src/components/AudioSettingsModal.tsx`):
- Music track selector (dropdown)
- Volume sliders (master, music, SFX)
- Mute toggle
- SFX threshold settings:
  - Minimum trade amount (numeric input)
  - Alert severity filter (all/high)
- Apply/Cancel buttons with persistence

#### 5. Integration Points

**Trade Events** (GamepadQuickTrade):
```typescript
const tradeType = data.order?.type === 0 ? 'trade:buy' : 'trade:sell';
sfxEmitter.emit({
  type: tradeType,
  metadata: {
    amount: data.order?.volume,
    symbol: data.order?.symbol
  }
});
```

**Portfolio Analysis** (usePortfolioAnalysis):
```typescript
const status = data.data.portfolio_health?.status?.toUpperCase();
if (status === 'DANGER' || status === 'CRITICAL') {
  sfxEmitter.emit({
    type: 'market:alert:high',
    metadata: { severity: 'high' }
  });
}
```

#### 6. Type Definitions (`src/types/audio.ts`)

**SFX Event Structure:**

```typescript
interface SFXEvent {
  type: SFXType;
  metadata?: {
    amount?: number;      // Trade amount
    severity?: 'low' | 'medium' | 'high';  // Alert severity
    symbol?: string;      // Trading symbol
  };
}

interface SFXThresholds {
  minTradeAmount: number;           // Only play trade SFX if >= amount
  alertSeverity: 'all' | 'high';    // Alert filtering
}

type SFXType =
  | 'trade:buy' | 'trade:sell'
  | 'market:alert:low' | 'market:alert:medium' | 'market:alert:high'
  | 'achievement:unlock' | 'achievement:milestone';
```

#### 7. Storage Persistence (`src/utils/audio-storage.ts`)

**Stores in localStorage:**
```json
{
  "masterVolume": 0.8,
  "musicVolume": 0.7,
  "sfxVolume": 0.9,
  "isMuted": false,
  "currentTrackId": "focus-ambient",
  "playbackPosition": 45.5,
  "sfxThresholds": {
    "minTradeAmount": 0.1,
    "alertSeverity": "high"
  }
}
```

### Phase 3 Data Flow

```
SFX Event Trigger
     │
     ├─► GamepadQuickTrade (trade event)
     │   └─► sfxEmitter.emit({ type: 'trade:buy', metadata: {...} })
     │
     ├─► usePortfolioAnalysis (alert event)
     │   └─► sfxEmitter.emit({ type: 'market:alert:high', ... })
     │
     └─► [Future: other events]

            │
            ▼
     SFXEventEmitter.emit()

     │
     ├─► shouldPlaySFX() [threshold check]
     │
     ├─► isDebounced() [cooldown check]
     │
     └─► audioManager.playSFX()
             │
             ▼
         Tone.Sampler.triggerAttackRelease()
             │
             ▼
         Browser Audio (respects volume & mute)
```

### Phase 3 Scope

**What's Included:**
- SFX Event Emitter service with threshold filtering
- React Context Provider for audio state management
- AudioSettings modal UI with all controls
- Audio hooks (useAudioPlayer, useAudioKeyboard)
- Event triggering from:
  - Trade execution (amount-based filtering)
  - Portfolio analysis (risk-based alerts)
- localStorage persistence of all settings
- Settings restoration on app load

**Not Yet Included (Phase 4+):**
- Webhook/backend event integration
- Streaming audio from server
- Custom SFX library uploads
- Advanced audio effects (equalizer, reverb)
- Multi-window audio sync

---

### Phase 4: Keyboard Shortcuts

**Overview**

Adds global keyboard shortcuts for rapid audio control without UI interaction. Enables hands-free volume and playback management during trading sessions.

#### 1. useAudioKeyboard Hook (`src/hooks/useAudioKeyboard.ts`)

**Shortcut Bindings:**

| Shortcut | Action | Behavior |
|----------|--------|----------|
| M | Toggle Mute | Mutes/unmutes all audio globally |
| P | Play/Pause | Starts or resumes last track; pauses if playing |
| Ctrl+↑ | Volume Up | Increases master volume by 10% (capped at 100%) |
| Ctrl+↓ | Volume Down | Decreases master volume by 10% (floor at 0%) |

**Implementation Details:**

```typescript
// Global keyboard event listener
const handleKeyDown = (e: KeyboardEvent) => {
  // Prevent shortcuts when typing in form inputs
  const target = e.target as HTMLElement;
  if (
    target instanceof HTMLInputElement ||
    target instanceof HTMLTextAreaElement ||
    target.isContentEditable
  ) {
    return;  // Form input has focus, don't trigger shortcuts
  }

  // M - Toggle Mute
  if (e.key === 'm' || e.key === 'M') {
    e.preventDefault();
    toggleMute();
  }

  // P - Play/Pause
  if (e.key === 'p' || e.key === 'P') {
    e.preventDefault();
    if (isPlaying) {
      pauseTrack();
    } else {
      playTrack(currentTrack || availableTracks[0]?.id);
    }
  }

  // Ctrl+↑ - Volume Up (+10%)
  if (e.ctrlKey && e.key === 'ArrowUp') {
    e.preventDefault();
    const newVolume = Math.min(volumes.master + 0.1, 1);
    setVolume('master', newVolume);
  }

  // Ctrl+↓ - Volume Down (-10%)
  if (e.ctrlKey && e.key === 'ArrowDown') {
    e.preventDefault();
    const newVolume = Math.max(volumes.master - 0.1, 0);
    setVolume('master', newVolume);
  }
};

// Register listener on component mount
window.addEventListener('keydown', handleKeyDown);

// Cleanup on unmount
return () => window.removeEventListener('keydown', handleKeyDown);
```

**Key Safety Features:**

1. **Form Input Protection:** Shortcuts disabled when focus is on `<input>`, `<textarea>`, or contentEditable elements
2. **Case Insensitive:** Both 'm'/'M' and 'p'/'P' work
3. **Gamepad Safe:** No conflicts with gamepad controls (keyboard only)
4. **Smooth Volume Steps:** 10% increments prevent jarring changes

#### 2. Hook Registration

**App.tsx Integration:**

```typescript
import { useAudioKeyboard } from '@/hooks/useAudioKeyboard';

export const App = () => {
  // Register keyboard shortcuts
  useAudioKeyboard();

  return (
    <div>
      {/* App content */}
    </div>
  );
};
```

**Timing:** Keyboard shortcuts activate after AudioProvider mounts and audio context is initialized.

#### 3. UI Hints

**AudioSettingsModal Keyboard Shortcut Display:**

Modal includes dedicated "Keyboard Shortcuts" section showing all bindings:
- Visual kbd-style badges for visual clarity
- 2-column grid layout for compact display
- Located at bottom of settings panel for quick reference

#### 4. Interaction Flow

```
User Presses Key
     │
     ▼
keydown Event Handler
     │
     ├─► Check focus: Is input/textarea focused?
     │   ├─ YES: Skip (return early)
     │   └─ NO: Continue
     │
     ├─► Match key binding
     │   ├─ M: toggleMute()
     │   ├─ P: playTrack() or pauseTrack()
     │   ├─ Ctrl+↑: setVolume('master', +0.1)
     │   └─ Ctrl+↓: setVolume('master', -0.1)
     │
     ▼
Update AudioContext State
     │
     ▼
Persist to localStorage (via context)
     │
     ▼
AudioManager applies changes immediately
```

#### 5. Volume Increment Logic

**Master Volume Calculation:**

```
Current Volume: 0.5 (50%)
Ctrl+↑ pressed: 0.5 + 0.1 = 0.6 (60%)
  ↓ (cap at 1.0)
Max reached: 0.9 + 0.1 = 1.0 (100%)

Ctrl+↓ pressed: 0.6 - 0.1 = 0.5 (50%)
  ↓ (floor at 0.0)
Min reached: 0.1 - 0.1 = 0.0 (0%)
```

#### 6. Focus Management

**Form Input Detection:**

```typescript
const target = e.target as HTMLElement;

// Skip shortcuts if:
if (target instanceof HTMLInputElement) {
  return;  // Text input focused
}

if (target instanceof HTMLTextAreaElement) {
  return;  // Textarea focused
}

if (target.isContentEditable) {
  return;  // Editable div/span focused
}

// Proceed with shortcut handling
```

**Effect:** Users can safely type in settings forms without accidentally triggering shortcuts.

#### 7. Dependencies

Hook imports:
- `useAudioPlayer()` - Audio state and control functions
- React's `useEffect` - Event listener lifecycle management

#### 8. Phase 4 Scope

**What's Included:**
- Global keyboard event listener (window-level)
- Four keyboard bindings (M, P, Ctrl+↑, Ctrl+↓)
- Form input safety checks
- Volume increment clamping (0-1 range)
- Audio context state updates
- localStorage persistence via context
- UI hints in AudioSettingsModal

**What's NOT Included (Phase 5+):**
- Customizable key bindings
- Keyboard preference panel
- Alternative shortcuts (e.g., arrow keys for volume)
- Command palette for shortcuts
- Gamepad shortcut integration

---

## Advisor System Architecture

### Overview

AI-powered advisor system analyzing portfolio risk and providing capital preservation recommendations using Claude and DeepSeek LLMs.

### Core Components

#### 1. Technical Analysis Engine (`backend/app/advisor/`)

```
technical_analyzer.py
  ├─ OHLCV Data Processing
  ├─ Indicator Calculation (RSI, MACD, Bollinger Bands, etc.)
  └─ Price Action Analysis

pattern_detector.py
  ├─ Candlestick Pattern Recognition
  ├─ Chart Patterns (Double Top, Head & Shoulders)
  └─ Trend Detection

support_resistance.py
  ├─ S/R Level Identification
  └─ Breakout Analysis

risk_analyzer.py
  ├─ Position Risk Metrics
  ├─ Portfolio Risk Aggregation
  └─ Drawdown Calculations
```

#### 2. Data Fetching (`backend/app/advisor/data_fetcher.py`)

**Architecture:**

```
User Request
     │
     ▼
DataFetcher.fetch_ohlcv()
     │
     ├─► MT5 Connection (live data)
     │
     └─► Redis Cache (deterministic caching)
           ├─ Cache Key: symbol:timeframe:bars
           └─ TTL: 300 seconds (5 minutes)
```

**Features:**
- Direct MT5 connection for real-time market data
- Semantic caching via Redis for improved performance
- Error handling with fallback strategies

#### 3. LLM Integration (`backend/app/advisor/ai_summarizer.py`)

**Model Strategy:**

```
Portfolio Analysis Request
         │
         ▼
    Try Claude API
         │
    ┌────┴────┐
    │          │
  Success   Failure
    │          │
    ▼          ▼
Return      Fallback to
Response    DeepSeek
```

**Prompt Engineering:**
- Chain-of-Thought (CoT) reasoning for explainability
- Structured outputs (JSON) for frontend parsing
- Capital preservation focus over profit maximization

#### 4. Recommendation Engine (`backend/app/advisor/recommendation_engine.py`)

Aggregates signals from multiple analysis sources:
- Technical indicators (bullish/bearish)
- Support/resistance proximity
- Risk status (SAFE/CAUTION/DANGER)
- Portfolio health score

---

## Data Flow

### Portfolio Analysis Request Flow

```
┌─────────────────────┐
│  React Component    │
│  (Portfolio Form)   │
└──────────┬──────────┘
           │ Socket.IO emit
           ▼
┌─────────────────────────────────────────┐
│  Backend Event Handler                  │
│  (advisor_events.py)                    │
└──────────┬──────────────────────────────┘
           │ Validate input
           ▼
┌─────────────────────────────────────────┐
│  AdvisorProcessor                       │
│  - Fetch data for each position         │
│  - Analyze in parallel (asyncio)        │
│  - Aggregate results                    │
└──────────┬──────────────────────────────┘
           │
    ┌──────┼──────┐
    │      │      │
    ▼      ▼      ▼
┌──────┐┌──────┐┌──────────────┐
│Cache?││Fetch││Analyze Each  │
│Redis ││MT5  ││Position      │
└──┬───┘└──┬──┘└──┬───────────┘
   │       │      │
   └───┬───┘      │
       │          │
       ▼          │
    ┌─────────────┴─────────────┐
    │ TechnicalAnalyzer         │
    │ RiskAnalyzer              │
    │ PatternDetector           │
    │ Support/Resistance        │
    └────────────┬──────────────┘
                 │
                 ▼
    ┌────────────────────────────┐
    │ AISummarizer (Claude/DeepSeek)
    │ Generate capital preservation advice
    └────────────┬───────────────┘
                 │
                 ▼
    ┌────────────────────────────┐
    │ RecommendationEngine       │
    │ Aggregate all signals      │
    └────────────┬───────────────┘
                 │
                 ▼ Socket.IO emit
         ┌─────────────────┐
         │ React Component │
         │ (Results Panel) │
         └─────────────────┘
```

### Audio System Initialization Flow (Phase 1)

```
App Load
   │
   ▼
User Gesture (click/tap)
   │
   ▼
audioManager.initialize()
   │
   ├─► await Tone.start() [Browser context]
   │
   ├─► Create Tone.Player [Music playback]
   │
   ├─► Create Tone.Sampler [SFX playback]
   │
   └─► Load audio settings from localStorage
        │
        ▼
   AudioManager Ready
   (Can call playMusic(), playSFX(), setVolume())
```

---

## Integration Points

### Current (Phase 5.4)

1. **Socket.IO Communication**
   - Event handlers in `backend/app/events/`
   - React hooks consuming Socket.IO events
   - Error propagation through Socket.IO error channel

2. **MT5 Connection**
   - Live market data via `MetaTrader5` library
   - Connection pooling via `ConnectionManager`
   - Circuit breaker pattern for fault tolerance

3. **Redis Cache**
   - Semantic caching for portfolio analysis
   - Cache key: deterministic hash of inputs
   - TTL: 300 seconds (configurable)

### Current (Phase 3)

1. **Audio Events (SFX Event Emitter)**
   - SFX triggering on trade events (buy/sell)
   - SFX triggering on portfolio analysis results (risk-based alerts)
   - Threshold-based filtering (trade amount, alert severity)
   - Debouncing per SFX type (500ms cooldown)

2. **React Context Provider (AudioContext)**
   - Global audio state management
   - Component-level audio controls
   - Settings persistence across sessions
   - Auto-resume music if was playing before refresh

3. **Audio Settings UI**
   - AudioSettingsModal for all audio configuration
   - Volume sliders (master, music, SFX)
   - Music track selector
   - Mute toggle
   - SFX threshold controls

### Future (Phase 4+)

1. **Keyboard Shortcuts**
   - M = mute/unmute
   - P = play/pause
   - N = next track
   - Music context awareness (aggressive trading = energy track)

2. **Advanced Audio Features**
   - Fade-in/out during track transitions
   - Dynamic volume based on market volatility
   - Custom SFX library uploads
   - Streaming audio from backend

3. **Webhook/Backend Integration**
   - Server-side event emission
   - Real-time market alert SFX
   - Multi-window audio sync

---

## Technology Stack

### Frontend

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Framework | React | 18.3 | UI rendering |
| Language | TypeScript | 5.9 | Type safety |
| Routing | React Router | 6.30 | Page navigation |
| State | TanStack Query | 5.90 | Server state |
| WebSocket | Socket.IO | 4.8 | Real-time events |
| **Audio** | **Tone.js** | **15.1** | **Audio playback** |
| Styling | Tailwind CSS | 3.4 | Utility CSS |
| UI Components | shadcn/ui | - | Accessible components |

### Backend

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Framework | FastAPI | Web server + routing |
| Language | Python | 3.10+ |
| WebSocket | python-socketio | Real-time events |
| Data Processing | Pandas | OHLCV manipulation |
| Trading API | MetaTrader5 | Live market data |
| Cache | Redis | Session + query cache |
| LLM | Claude / DeepSeek | Portfolio advice |
| Validation | Pydantic | Request validation |

---

**Last Updated:** 2026-01-05
**Maintained By:** Audio Team (Phase 1 & 3) & Backend Team (Advisor)
**Next Review:** Phase 4 (Keyboard Shortcuts & Advanced Features)
