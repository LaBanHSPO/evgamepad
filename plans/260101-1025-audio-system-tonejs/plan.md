---
title: "Tone.js Audio System - Implementation Plan"
description: "Core audio infrastructure with Tone.js for background music, SFX, and Socket.IO integration"
status: "Phase 4 DONE - Phase 5 NEXT"
priority: "high"
effort: "5 days"
branch: "feat/music-background-and-sfx-effect-sound"
tags: ["audio", "tone.js", "web-audio", "react"]
created: "2026-01-01"
phase_1_completed: "2026-01-01"
phase_2_completed: "2026-01-05"
phase_3_completed: "2026-01-05"
phase_4_completed: "2026-01-05"
---

# Tone.js Audio System - Implementation Plan

**Date:** 2026-01-01
**Plan ID:** 260101-1025-audio-system-tonejs
**Branch:** feat/music-background-and-sfx-effect-sound
**Status:** PHASE 4 DONE - PHASE 5 NEXT (2026-01-05)
**Estimated Effort:** 5 days (1 developer)
**Phase 1 Completion:** 2026-01-01 (Code Review: Grade A, Tests: 35/35 PASS)
**Phase 2 Completion:** 2026-01-05 (UI Integration Complete)
**Phase 3 Completion:** 2026-01-05 (Sound Effects System COMPLETE)
**Phase 4 Completion:** 2026-01-05 (Keyboard Shortcuts COMPLETE)

---

## Executive Summary

Implement immersive audio system for EV GamePad trading game using Tone.js framework. Provides background music player (3-4 selectable tracks), gamified SFX (synth beeps/chimes) for trading events, configurable volume controls, keyboard shortcuts, and localStorage persistence.

**Key Features:**
- Background music: 3-4 tracks, auto-resume playback position
- Gamified SFX: buy/sell, market alerts, achievements with configurable thresholds
- Settings modal: volume sliders (master/music/sfx), mute toggles
- Keyboard shortcuts: M=mute, Ctrl+↑/↓=volume
- Socket.IO integration: trigger SFX on trade events
- localStorage: persist all settings across sessions

**Tech Stack:**
- Tone.js ~200KB (Web Audio API framework)
- React 18 + TypeScript
- shadcn/ui components
- Existing Socket.IO infrastructure

**Success Criteria:**
- Session startup: music auto-resumes <500ms
- SFX latency: <50ms from trade event to sound
- Settings modal: <200ms open latency
- Persistence: 100% accuracy (volume/track/position restored)

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Component Breakdown](#component-breakdown)
3. [Implementation Phases](#implementation-phases)
4. [Testing Strategy](#testing-strategy)
5. [Risk Mitigation](#risk-mitigation)
6. [Documentation Updates](#documentation-updates)

---

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                      App.tsx                            │
│  ┌───────────────────────────────────────────────────┐  │
│  │           AudioProvider (Context)                  │  │
│  │  ┌─────────────────────────────────────────────┐  │  │
│  │  │       AudioManager (Service)                 │  │  │
│  │  │  ┌──────────────┐  ┌───────────────────┐   │  │  │
│  │  │  │ Tone.Player  │  │  Tone.Sampler     │   │  │  │
│  │  │  │  (Music)     │  │    (SFX)          │   │  │  │
│  │  │  └──────────────┘  └───────────────────┘   │  │  │
│  │  │           ↓                  ↓              │  │  │
│  │  │       localStorage       Socket.IO          │  │  │
│  │  └─────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────┘  │
│                       ↓                                  │
│  ┌──────────────┐  ┌────────────────┐  ┌────────────┐  │
│  │ Settings     │  │ useAudioPlayer │  │ Keyboard   │  │
│  │ Modal        │  │ Hook           │  │ Shortcuts  │  │
│  └──────────────┘  └────────────────┘  └────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### File Structure

```
src/
├── context/
│   └── AudioContext.tsx                  # React Context provider
├── services/
│   ├── audio-manager.ts                  # Tone.js wrapper singleton
│   └── sfx-event-emitter.ts              # Event-based SFX system
├── hooks/
│   ├── useAudioPlayer.ts                 # Music control hook
│   ├── useSoundEffects.ts                # SFX hook
│   └── useAudioKeyboard.ts               # Keyboard shortcuts
├── components/
│   └── AudioSettingsModal.tsx            # Settings UI
├── types/
│   └── audio.ts                          # TypeScript interfaces
└── utils/
    └── audio-storage.ts                  # localStorage helpers

public/audio/
├── music/
│   ├── focus-ambient.mp3                 # Calm, minimal distraction
│   ├── energy-upbeat.mp3                 # High-tempo trading
│   ├── strategy-chill.mp3                # Mid-tempo analytical
│   └── night-lofi.mp3                    # Low-energy late sessions
└── sfx/
    ├── trade-buy.mp3                     # Gamified synth beep
    ├── trade-sell.mp3                    # Different tone from buy
    ├── market-alert.mp3                  # Attention-grabbing
    ├── achievement.mp3                   # Celebration chime
    └── milestone.mp3                     # Bigger achievement
```

---

## Component Breakdown

### 1. AudioManager Service (`src/services/audio-manager.ts`)

**Responsibility:** Singleton managing all Tone.js audio operations

**Key Methods:**
```typescript
class AudioManager {
  // Initialization
  async initialize(): Promise<void>
  dispose(): void

  // Music Controls
  async loadMusicTrack(trackId: string): Promise<void>
  playMusic(): void
  pauseMusic(): void
  stopMusic(): void
  seekMusic(position: number): void
  getCurrentPosition(): number

  // Volume Controls
  setMasterVolume(value: number): void
  setMusicVolume(value: number): void
  setSFXVolume(value: number): void
  toggleMute(): void

  // SFX
  playSFX(type: SFXType, options?: SFXOptions): void

  // Persistence
  saveSettings(): void
  loadSettings(): AudioSettings
}
```

**Technical Details:**
- Uses `Tone.Player` for music (loop=true, autostart=false)
- Uses `Tone.Sampler` for SFX (one-shot playback)
- Lazy loads Tone.js on first use (code splitting)
- Disposes players on cleanup to prevent memory leaks
- Handles browser autoplay policy (requires user gesture)

**Implementation Notes:**
- Volume calculation: `Tone.gainToDb(masterVolume * channelVolume)`
- Music position tracking: `player.immediate()` for current time
- SFX debouncing: max 1 sound per type per 500ms
- Error handling: fallback to silent mode if Tone.js fails

---

### 2. AudioContext (`src/context/AudioContext.tsx`)

**Responsibility:** React Context wrapping AudioManager

**Provides:**
```typescript
interface AudioContextValue {
  // State
  isInitialized: boolean;
  currentTrack: string | null;
  isPlaying: boolean;
  isMuted: boolean;
  volumes: {
    master: number;
    music: number;
    sfx: number;
  };
  playbackPosition: number;
  availableTracks: MusicTrack[];

  // Actions
  playTrack: (trackId: string) => Promise<void>;
  pauseTrack: () => void;
  setVolume: (channel: VolumeChannel, value: number) => void;
  toggleMute: () => void;
  playSFX: (type: SFXType, options?: SFXOptions) => void;
}
```

**Implementation Pattern:**
- Initializes AudioManager on mount
- Restores settings from localStorage on mount
- Auto-resumes music if was playing before refresh
- Provides memo-ized context value (prevent re-renders)
- Cleans up on unmount (dispose Tone.js resources)

**Example Usage:**
```typescript
const { playTrack, setVolume, playSFX } = useAudioPlayer();

// Play music
await playTrack('focus-ambient');

// Adjust volume
setVolume('master', 0.8);

// Trigger SFX
playSFX('trade:buy');
```

---

### 3. AudioSettingsModal (`src/components/AudioSettingsModal.tsx`)

**Responsibility:** UI for audio configuration

**Features:**
- Music track selector (RadioGroup with track names + descriptions)
- Volume sliders (master, music, SFX) with real-time preview
- Mute toggle (Switch component)
- SFX threshold settings (number input for minTradeAmount)
- Keyboard shortcut hints (visual guide)
- Save/Cancel buttons

**UI Layout:**
```
┌─────────────────────────────────────────┐
│  Audio Settings                     [X] │
├─────────────────────────────────────────┤
│                                         │
│  Music Track                            │
│  ○ Focus Ambient (calm, minimal)        │
│  ● Energy Upbeat (high-tempo)           │
│  ○ Strategy Chill (mid-tempo)           │
│  ○ Night Lofi (low-energy)              │
│                                         │
│  Volume Controls                        │
│  Master:  [━━━━━━━━━━━━━━] 80%         │
│  Music:   [━━━━━━━━━━━━━━] 70%         │
│  SFX:     [━━━━━━━━━━━━━━] 90%         │
│                                         │
│  [✓] Mute All (M)                       │
│                                         │
│  SFX Thresholds                         │
│  Min Trade Amount: [$100   ]            │
│  Alert Severity: [High Priority ▼]     │
│                                         │
│  Keyboard Shortcuts                     │
│  M - Toggle Mute                        │
│  Ctrl+↑/↓ - Volume Up/Down              │
│  P - Play/Pause Music                   │
│                                         │
│         [Cancel]        [Save]          │
└─────────────────────────────────────────┘
```

**shadcn/ui Components:**
- `Dialog` (modal wrapper)
- `RadioGroup` + `RadioGroupItem` (track selector)
- `Slider` (volume controls)
- `Switch` (mute toggle)
- `Input` (threshold number input)
- `Select` (alert severity dropdown)
- `Button` (save/cancel)

**Integration:**
- Triggered by Settings button in SystemHeader
- Uses `useAudioPlayer()` hook for state/actions
- Auto-saves to localStorage on "Save" click
- Real-time volume preview (slider onChange)

---

### 4. SFX Event System (`src/services/sfx-event-emitter.ts`)

**Responsibility:** Event-driven SFX triggering

**Event Types:**
```typescript
type SFXEventType =
  | 'trade:buy'
  | 'trade:sell'
  | 'market:alert:low'
  | 'market:alert:medium'
  | 'market:alert:high'
  | 'achievement:unlock'
  | 'achievement:milestone';

interface SFXEvent {
  type: SFXEventType;
  metadata?: {
    amount?: number;           // For trade events
    severity?: 'low' | 'medium' | 'high';  // For alerts
    symbol?: string;
  };
}
```

**Implementation:**
```typescript
class SFXEventEmitter {
  private emitter = new EventTarget();
  private thresholds: SFXThresholds;
  private lastPlayedTime: Map<SFXEventType, number>;

  emit(event: SFXEvent): void {
    // Check threshold
    if (!this.shouldPlaySFX(event)) return;

    // Check debounce (500ms cooldown per type)
    if (this.isDebounced(event.type)) return;

    // Trigger SFX
    const sfxType = this.mapEventToSFX(event.type);
    audioManager.playSFX(sfxType);

    // Update last played time
    this.lastPlayedTime.set(event.type, Date.now());
  }

  private shouldPlaySFX(event: SFXEvent): boolean {
    // Trade threshold: only play if amount > minTradeAmount
    if (event.type.startsWith('trade:') && event.metadata?.amount) {
      return event.metadata.amount >= this.thresholds.minTradeAmount;
    }

    // Alert threshold: only play if severity >= configured level
    if (event.type.startsWith('market:alert:')) {
      const severity = event.metadata?.severity || 'low';
      return this.thresholds.alertSeverity === 'all' ||
             (this.thresholds.alertSeverity === 'high' && severity === 'high');
    }

    // Always play achievements
    return true;
  }

  private isDebounced(type: SFXEventType): boolean {
    const lastPlayed = this.lastPlayedTime.get(type);
    if (!lastPlayed) return false;
    return (Date.now() - lastPlayed) < 500; // 500ms cooldown
  }
}

export const sfxEmitter = new SFXEventEmitter();
```

**Socket.IO Integration:**
```typescript
// In existing Socket.IO event handlers
socket.on('advisor:portfolio_result', (data) => {
  // Existing logic...

  // Trigger SFX based on result
  if (data.data?.portfolio_health?.status === 'DANGER') {
    sfxEmitter.emit({
      type: 'market:alert:high',
      metadata: { severity: 'high' }
    });
  }
});

socket.on('trade:confirmed', (data) => {
  sfxEmitter.emit({
    type: data.side === 'buy' ? 'trade:buy' : 'trade:sell',
    metadata: { amount: data.amount, symbol: data.symbol }
  });
});
```

---

### 5. Keyboard Shortcuts (`src/hooks/useAudioKeyboard.ts`)

**Responsibility:** Global keyboard shortcut handling

**Shortcuts:**
- `M` → Toggle mute
- `Ctrl+↑` → Volume up (+10%)
- `Ctrl+↓` → Volume down (-10%)
- `P` → Play/pause music

**Implementation:**
```typescript
export const useAudioKeyboard = () => {
  const { toggleMute, setVolume, isPlaying, playTrack, pauseTrack, volumes } =
    useAudioPlayer();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Prevent shortcuts when typing in inputs
      if (e.target instanceof HTMLInputElement ||
          e.target instanceof HTMLTextAreaElement) {
        return;
      }

      // M - Toggle Mute
      if (e.key === 'm' || e.key === 'M') {
        e.preventDefault();
        toggleMute();
      }

      // Ctrl+↑ - Volume Up
      if (e.ctrlKey && e.key === 'ArrowUp') {
        e.preventDefault();
        const newVolume = Math.min(volumes.master + 0.1, 1);
        setVolume('master', newVolume);
      }

      // Ctrl+↓ - Volume Down
      if (e.ctrlKey && e.key === 'ArrowDown') {
        e.preventDefault();
        const newVolume = Math.max(volumes.master - 0.1, 0);
        setVolume('master', newVolume);
      }

      // P - Play/Pause
      if (e.key === 'p' || e.key === 'P') {
        e.preventDefault();
        if (isPlaying) {
          pauseTrack();
        } else {
          // Resume last track or play default
          const lastTrack = localStorage.getItem('lastMusicTrack') || 'focus-ambient';
          playTrack(lastTrack);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [toggleMute, setVolume, volumes, isPlaying, playTrack, pauseTrack]);
};
```

**Conflict Prevention:**
- Check if target is input/textarea before handling
- Check existing gamepad shortcuts (GamepadControllerHints component)
- Document conflicts in AudioSettingsModal

---

## Implementation Phases

### Phase 1: Core Audio Infrastructure (Day 1-2)

**Goal:** Tone.js integration + basic music playback

**Tasks:**
1. Install dependencies
   ```bash
   npm install tone
   npm install --save-dev @types/tone
   ```

2. Create AudioManager service
   - File: `src/services/audio-manager.ts`
   - Implement: initialization, music loading, play/pause
   - Add: volume controls, mute toggle
   - Handle: browser autoplay policy (user gesture required)

3. Create localStorage helpers
   - File: `src/utils/audio-storage.ts`
   - Functions: `saveAudioSettings()`, `loadAudioSettings()`
   - Schema: AudioSettings interface

4. Add TypeScript types
   - File: `src/types/audio.ts`
   - Interfaces: AudioSettings, MusicTrack, SFXType, VolumeChannel

5. Source music files
   - Find 3-4 royalty-free tracks (FreeSound.org, Incompetech)
   - Compress to MP3 128kbps (~3MB per 3-min track)
   - Add to `public/audio/music/` directory
   - Create metadata file: `public/audio/music/tracks.json`

**Acceptance Criteria:** ALL COMPLETE
- [x] AudioManager can load and play MP3 tracks ✓ VERIFIED
- [x] Volume controls working (master, music) ✓ VERIFIED
- [x] Playback position tracking functional ✓ VERIFIED
- [x] Settings persist to localStorage ✓ VERIFIED
- [x] No console errors or warnings ✓ VERIFIED (0 errors, 0 warnings)

**Code Review Status:** ✓ APPROVED (Grade A - 0 critical issues)
**Test Results:** 35/35 tests passed (100% coverage)
**Build Status:** ✓ SUCCESS (TypeScript: 0 errors, ESLint: 0 errors)
**Phase 1 Status:** COMPLETE - Approved for Phase 2

**Review Report:** `plans/260101-1025-audio-system-tonejs/code-review-phase-1.md`

**Testing:**
```typescript
// Manual test in browser console
import { audioManager } from '@/services/audio-manager';

await audioManager.initialize();
await audioManager.loadMusicTrack('focus-ambient');
audioManager.playMusic();
console.log(audioManager.getCurrentPosition()); // Should show current time
audioManager.setMasterVolume(0.5);
audioManager.pauseMusic();
audioManager.saveSettings();
```

---

### Phase 2: React Context & UI Integration (Day 2-3) - NEXT

**Status:** PENDING (Ready to Start)
**Goal:** Connect AudioManager to React components

**Tasks:**
1. Create AudioContext provider
   - File: `src/context/AudioContext.tsx`
   - Initialize AudioManager on mount
   - Restore settings from localStorage
   - Auto-resume music if was playing
   - Export `useAudioPlayer()` hook

2. Integrate into App.tsx
   ```typescript
   // Wrap app with AudioProvider
   <AudioProvider>
     <SocketProvider>
       <TooltipProvider>
         {/* existing app */}
       </TooltipProvider>
     </SocketProvider>
   </AudioProvider>
   ```

3. Create AudioSettingsModal component
   - File: `src/components/AudioSettingsModal.tsx`
   - Use shadcn/ui components (Dialog, Slider, RadioGroup, Switch)
   - Real-time volume preview
   - Track selector with descriptions
   - Save/Cancel buttons

4. Add Settings button to SystemHeader
   - Icon: `Volume2` from lucide-react
   - Position: top-right corner (next to existing controls)
   - Trigger: opens AudioSettingsModal

5. Create custom hooks
   - File: `src/hooks/useAudioPlayer.ts` (wrapper around context)
   - File: `src/hooks/useSoundEffects.ts` (SFX-specific hook)

**Acceptance Criteria:**
- [ ] Settings button visible in header
- [ ] Modal opens/closes smoothly
- [ ] Track selection updates context state
- [ ] Volume sliders adjust audio in real-time
- [ ] Settings persist on "Save" click
- [ ] Music auto-resumes on page refresh

**Testing:**
- Open Settings modal
- Change volume → verify audio adjusts immediately
- Select different track → verify music switches
- Refresh page → verify settings restored (volume, track, position)
- Check localStorage: `audioSettings` key exists

---

### Phase 3: Sound Effects System (Day 3-4) - COMPLETE

**Status:** COMPLETE (2026-01-05)
**Goal:** Implement gamified SFX with Socket.IO integration

**Tasks:** ALL COMPLETE
1. Generate/source gamified SFX ✓
   - Use Tone.js `Tone.Synth` to generate beeps programmatically
   - Or source from FreeSound.org (search: "synth beep", "game sfx")
   - 5 sounds: trade-buy, trade-sell, market-alert, achievement, milestone
   - Keep files <50KB each (short duration, compressed)

2. Create SFX Event Emitter ✓
   - File: `src/services/sfx-event-emitter.ts`
   - Implement: threshold checking, debouncing
   - Export: `sfxEmitter` singleton

3. Integrate with Socket.IO events ✓
   - Update existing event handlers in components
   - Add SFX triggers for:
     - Trade confirmations (`advisor:portfolio_result`)
     - Market alerts (portfolio health = DANGER)
     - Achievements (new milestone reached)

4. Add SFX threshold settings to modal ✓
   - Number input: "Min Trade Amount"
   - Select dropdown: "Alert Severity" (all/high)
   - Save thresholds to localStorage

5. Implement SFX in AudioManager ✓
   - Use `Tone.Sampler` for one-shot playback
   - Preload all SFX samples on initialization
   - Apply volume: `sfxVolume * masterVolume`

**Acceptance Criteria:** ALL MET
- [x] SFX plays on trade confirmation (buy/sell different tones) ✓ VERIFIED
- [x] Market alert SFX plays when portfolio health = DANGER ✓ VERIFIED
- [x] Threshold filtering works (e.g., only trades >$100) ✓ VERIFIED
- [x] Debouncing prevents SFX spam (max 1/500ms per type) ✓ VERIFIED
- [x] SFX volume independent from music volume ✓ VERIFIED

**Testing:** ALL PASSED
- Trigger trade event → verify correct SFX plays ✓
- Trigger 10 trades rapidly → verify only 1 SFX per 500ms ✓
- Set minTradeAmount=1000 → verify $500 trade is silent ✓
- Adjust SFX volume slider → verify SFX louder/quieter ✓

**Phase 3 Status:** COMPLETE - Ready for Phase 4 (Keyboard Shortcuts)

---

### Phase 4: Keyboard Shortcuts (Day 4) - IN PROGRESS

**Status:** IN PROGRESS (Started 2026-01-05)
**Goal:** Power user controls via keyboard

**Tasks:**
1. Create keyboard shortcuts hook
   - File: `src/hooks/useAudioKeyboard.ts`
   - Implement: M, Ctrl+↑/↓, P shortcuts
   - Prevent: shortcuts when typing in inputs

2. Register globally in App.tsx
   ```typescript
   function App() {
     useAudioKeyboard(); // Register global shortcuts
     return <BrowserRouter>...</BrowserRouter>;
   }
   ```

3. Add visual hints to Settings modal
   - Section: "Keyboard Shortcuts"
   - List: M (mute), Ctrl+↑/↓ (volume), P (play/pause)
   - Styling: muted text, smaller font

4. Check for conflicts with existing shortcuts
   - Review: `GlobalGamepadHandler` component
   - Ensure: no overlap with gamepad button mappings
   - Document: any conflicts in CLAUDE.md

**Acceptance Criteria:**
- [ ] M key toggles mute
- [ ] Ctrl+↑ increases volume by 10%
- [ ] Ctrl+↓ decreases volume by 10%
- [ ] P key plays/pauses music
- [ ] Shortcuts don't fire when typing in inputs
- [ ] No conflicts with gamepad controls

**Testing:**
- Press M → verify mute indicator updates
- Press Ctrl+↑ 5 times → verify volume increases to 50%
- Press P → verify music starts
- Focus on input, press M → verify mute doesn't toggle

---

### Phase 5: Polish & Testing (Day 5)

**Goal:** Cross-browser testing, optimization, documentation

**Tasks:**
1. iOS testing (Safari + Chrome iOS)
   - Test: autoplay restrictions
   - Implement: "Tap to start music" banner if iOS
   - Test: mute switch behavior (hardware switch)

2. Performance profiling
   - Chrome DevTools: Memory tab
   - Monitor: heap size during 30-min session
   - Verify: no memory leaks (<50MB audio system)
   - Check: CPU usage during SFX spam (<5%)

3. Accessibility audit
   - Run: WAVE browser extension
   - Fix: ARIA labels on sliders/switches
   - Test: keyboard navigation in modal
   - Add: screen reader hints

4. Code review
   - Use: `/review-code` command
   - Fix: any TypeScript errors
   - Add: JSDoc comments to public methods
   - Remove: console.log statements

5. Documentation updates
   - File: `docs/system-architecture.md` (add audio system diagram)
   - File: `docs/code-standards.md` (add audio coding patterns)
   - File: `README.md` (add audio settings section)
   - File: `CHANGELOG.md` (add Phase X: Audio System)

**Acceptance Criteria:**
- [ ] Works on iOS Safari without errors
- [ ] Memory usage <50MB after 30-min session
- [ ] All ARIA labels present
- [ ] Code review passes with 0 critical issues
- [ ] Documentation updated

**Testing Checklist:**
- [ ] Desktop Chrome: all features work
- [ ] Desktop Firefox: all features work
- [ ] Desktop Safari: all features work
- [ ] Mobile iOS Safari: autoplay handled correctly
- [ ] Mobile Android Chrome: all features work
- [ ] Low bandwidth: music loads progressively
- [ ] High CPU load: SFX timing remains <50ms

---

## Testing Strategy

### Unit Tests

**AudioManager (`audio-manager.test.ts`):**
```typescript
describe('AudioManager', () => {
  it('should initialize without errors', async () => {
    const manager = new AudioManager();
    await manager.initialize();
    expect(manager.isInitialized).toBe(true);
  });

  it('should save and load settings', () => {
    const manager = new AudioManager();
    manager.setMasterVolume(0.7);
    manager.setMusicVolume(0.5);
    manager.saveSettings();

    const loaded = manager.loadSettings();
    expect(loaded.masterVolume).toBe(0.7);
    expect(loaded.musicVolume).toBe(0.5);
  });

  it('should debounce SFX calls', () => {
    const manager = new AudioManager();
    const spy = jest.spyOn(manager, 'playSFX');

    manager.playSFX('trade:buy');
    manager.playSFX('trade:buy'); // Should be debounced
    manager.playSFX('trade:buy'); // Should be debounced

    expect(spy).toHaveBeenCalledTimes(1);
  });
});
```

**SFXEventEmitter (`sfx-event-emitter.test.ts`):**
```typescript
describe('SFXEventEmitter', () => {
  it('should filter events by threshold', () => {
    const emitter = new SFXEventEmitter({ minTradeAmount: 100 });
    const spy = jest.spyOn(audioManager, 'playSFX');

    emitter.emit({
      type: 'trade:buy',
      metadata: { amount: 50 }
    }); // Below threshold

    expect(spy).not.toHaveBeenCalled();

    emitter.emit({
      type: 'trade:buy',
      metadata: { amount: 150 }
    }); // Above threshold

    expect(spy).toHaveBeenCalledWith('trade:buy');
  });
});
```

### Integration Tests

**AudioContext (`AudioContext.test.tsx`):**
```typescript
describe('AudioContext', () => {
  it('should restore settings on mount', async () => {
    localStorage.setItem('audioSettings', JSON.stringify({
      masterVolume: 0.8,
      currentTrackId: 'energy-upbeat',
      playbackPosition: 120
    }));

    const { result } = renderHook(() => useAudioPlayer(), {
      wrapper: AudioProvider
    });

    await waitFor(() => {
      expect(result.current.volumes.master).toBe(0.8);
      expect(result.current.currentTrack).toBe('energy-upbeat');
    });
  });
});
```

### E2E Tests (Manual)

**Scenario 1: First-time user**
1. Open app (no localStorage)
2. Click Settings button
3. Verify: default settings (masterVolume=0.8, no track selected)
4. Select "Focus Ambient", click Save
5. Verify: music starts playing
6. Refresh page
7. Verify: music auto-resumes from saved position

**Scenario 2: Power user workflow**
1. Press M → verify mute toggles
2. Press Ctrl+↑ 3 times → verify volume increases
3. Press P → verify music pauses
4. Open Settings → verify current values match
5. Adjust SFX threshold to $500
6. Trigger $200 trade → verify no SFX plays
7. Trigger $600 trade → verify SFX plays

**Scenario 3: iOS autoplay**
1. Open app on iOS Safari
2. Verify: "Tap to start music" banner appears
3. Tap banner
4. Verify: music starts playing
5. Lock device, unlock
6. Verify: music still playing (background playback)

---

## Risk Mitigation

### Risk 1: Tone.js Bundle Size Impact

**Risk:** 200KB Tone.js increases initial load time

**Impact:** Medium (200ms delay on 4G)

**Mitigation:**
- Code-split Tone.js: `const Tone = await import('tone')`
- Load only when Settings opened first time
- Show loading skeleton during initialization
- Lazy load music files (only selected track)

**Validation:**
```bash
# Check bundle size after build
npm run build
ls -lh dist/assets/*.js | grep tone
```

---

### Risk 2: iOS Autoplay Restrictions

**Risk:** Music doesn't start automatically on iOS

**Impact:** Medium (affects 20-30% mobile users)

**Mitigation:**
- Detect iOS: `navigator.userAgent.includes('iPhone')`
- Show "Tap to start music" banner on session load
- Require user gesture before `Tone.start()`
- Test on real iOS devices (Safari + Chrome iOS)

**Implementation:**
```typescript
useEffect(() => {
  const isIOS = /iPhone|iPad|iPod/.test(navigator.userAgent);
  if (isIOS && !hasUserGesture) {
    setShowAutoplayBanner(true);
  }
}, []);

const handleStartMusic = async () => {
  await Tone.start();
  setHasUserGesture(true);
  setShowAutoplayBanner(false);
  playTrack(currentTrack);
};
```

---

### Risk 3: SFX Spam During High-Frequency Trading

**Risk:** 100 trades/min = constant beeping (annoying)

**Impact:** High (user disables audio)

**Mitigation:**
- Debouncing: max 1 SFX per type per 500ms
- Configurable thresholds: only play for important events
- SFX cooldown setting in modal (default: 500ms)
- Visual alternative: flashing border for rapid events

**User Control:**
- Settings modal: "SFX Cooldown" slider (100ms - 2000ms)
- Disable SFX entirely: sfxVolume=0

---

### Risk 4: Memory Leak from Audio Buffers

**Risk:** Long sessions (>1 hour) cause memory growth

**Impact:** Low (only affects multi-hour sessions)

**Mitigation:**
- Dispose Tone.js Players on unmount: `player.dispose()`
- Use single Sampler instance for all SFX (shared buffer)
- Monitor memory in DevTools during long sessions
- Implement cleanup on visibility change (page hidden)

**Cleanup Pattern:**
```typescript
useEffect(() => {
  return () => {
    audioManager.dispose();
  };
}, []);

document.addEventListener('visibilitychange', () => {
  if (document.hidden) {
    audioManager.pauseMusic();
    audioManager.saveSettings(); // Save position
  }
});
```

---

### Risk 5: Keyboard Shortcut Conflicts

**Risk:** Audio shortcuts conflict with gamepad/browser shortcuts

**Impact:** Low (confused users)

**Mitigation:**
- Check existing shortcuts in `GlobalGamepadHandler`
- Document conflicts in AudioSettingsModal
- Prevent shortcuts when typing in inputs
- Allow customization (future enhancement)

**Known Conflicts:**
- M: None
- Ctrl+↑/↓: Browser zoom (mitigated by preventDefault)
- P: None

---

## Documentation Updates

### 1. System Architecture (`docs/system-architecture.md`)

**Add Section:**
```markdown
### Audio System (Phase X)

**Components:**
- AudioManager: Tone.js wrapper for music/SFX playback
- AudioContext: React Context provider for global audio state
- SFXEventEmitter: Event-driven SFX triggering

**Data Flow:**
1. User action → AudioContext action (playTrack, setVolume)
2. Context → AudioManager service
3. AudioManager → Tone.js API → Web Audio API
4. Settings → localStorage (persist across sessions)

**Socket.IO Integration:**
- Trade events → SFXEventEmitter → AudioManager.playSFX()
- Threshold filtering → only important events trigger SFX

**Browser Compatibility:**
- Chrome 60+, Firefox 55+, Safari 11+, Edge 79+
- iOS: requires user gesture (autoplay policy)
```

---

### 2. Code Standards (`docs/code-standards.md`)

**Add Section:**
```markdown
### Audio System Patterns

**AudioManager Usage:**
```typescript
// Good - Singleton pattern
import { audioManager } from '@/services/audio-manager';
await audioManager.loadMusicTrack('focus-ambient');
audioManager.playMusic();

// Avoid - Multiple instances
const manager = new AudioManager(); // Don't instantiate
```

**Context Usage:**
```typescript
// Good - Use hook
const { playTrack, setVolume } = useAudioPlayer();

// Avoid - Direct context
const context = useContext(AudioContext); // Use hook instead
```

**SFX Triggering:**
```typescript
// Good - Event-driven
sfxEmitter.emit({ type: 'trade:buy', metadata: { amount: 500 } });

// Avoid - Direct call
audioManager.playSFX('trade:buy'); // Bypasses threshold filtering
```
```

---

### 3. User Guide (`README.md`)

**Add Section:**
```markdown
## Audio Settings

### Background Music
- 4 selectable tracks: Focus Ambient, Energy Upbeat, Strategy Chill, Night Lofi
- Auto-resumes from last playback position on refresh
- Keyboard shortcut: `P` to play/pause

### Sound Effects
- Gamified SFX for trading events (buy/sell, alerts, achievements)
- Configurable thresholds (e.g., only trades >$100)
- Debouncing prevents spam (max 1 sound per 500ms)

### Volume Controls
- Master volume (affects both music and SFX)
- Music volume (independent control)
- SFX volume (independent control)
- Keyboard shortcuts: `Ctrl+↑/↓` to adjust master volume

### Keyboard Shortcuts
- `M` - Toggle mute
- `Ctrl+↑` - Volume up (+10%)
- `Ctrl+↓` - Volume down (-10%)
- `P` - Play/pause music

### Mobile Support
- iOS Safari: tap "Start Music" banner to enable autoplay
- Android Chrome: full support
```

---

### 4. Changelog (`CHANGELOG.md`)

**Add Entry:**
```markdown
## [Phase X] - 2026-01-XX

### Added
- **Audio System**: Tone.js-based music player with 4 selectable tracks
- **Gamified SFX**: Synth beeps for trading events (buy/sell, alerts, achievements)
- **Settings Modal**: Volume controls, track selector, SFX thresholds
- **Keyboard Shortcuts**: M (mute), Ctrl+↑/↓ (volume), P (play/pause)
- **localStorage Persistence**: Settings + playback position across sessions
- **Socket.IO Integration**: SFX triggers on trade events with threshold filtering

### Technical
- Tone.js ~200KB (code-split on first use)
- AudioContext React provider
- SFX debouncing (max 1/500ms per type)
- iOS autoplay policy handling
- Memory leak prevention (dispose on unmount)

### Browser Support
- Chrome 60+, Firefox 55+, Safari 11+, Edge 79+
- iOS Safari with autoplay banner
```

---

## File Checklist

**Files to Create:**
- [ ] `src/services/audio-manager.ts`
- [ ] `src/services/sfx-event-emitter.ts`
- [ ] `src/context/AudioContext.tsx`
- [ ] `src/hooks/useAudioPlayer.ts`
- [ ] `src/hooks/useSoundEffects.ts`
- [ ] `src/hooks/useAudioKeyboard.ts`
- [ ] `src/components/AudioSettingsModal.tsx`
- [ ] `src/types/audio.ts`
- [ ] `src/utils/audio-storage.ts`
- [ ] `public/audio/music/tracks.json` (metadata)
- [ ] `public/audio/music/*.mp3` (4 tracks)
- [ ] `public/audio/sfx/*.mp3` (5 sounds)

**Files to Modify:**
- [ ] `src/App.tsx` (add AudioProvider, useAudioKeyboard)
- [ ] `src/components/SystemHeader.tsx` (add Settings button)
- [ ] Existing Socket.IO event handlers (add SFX triggers)
- [ ] `docs/system-architecture.md`
- [ ] `docs/code-standards.md`
- [ ] `README.md`
- [ ] `CHANGELOG.md`
- [ ] `package.json` (add tone dependency)

---

## Success Metrics

**Performance:**
- [ ] Session startup: music auto-resumes <500ms
- [ ] Settings modal open: <200ms latency
- [ ] SFX latency: <50ms from event to sound
- [ ] Memory usage: <50MB after 30-min session

**Functionality:**
- [ ] Persistence: 100% accuracy (volume/track/position restored)
- [ ] SFX threshold filtering: 100% correct
- [ ] Debouncing: prevents spam (max 1/500ms)
- [ ] Keyboard shortcuts: all working

**Quality:**
- [ ] Code review: 0 critical issues
- [ ] TypeScript: 0 errors
- [ ] Accessibility: WCAG 2.1 AA compliant
- [ ] Documentation: 100% complete

---

## Dependencies

**New Dependencies:**
```json
{
  "dependencies": {
    "tone": "^15.0.4"
  },
  "devDependencies": {
    "@types/tone": "^15.0.0"
  }
}
```

**Audio Assets:**
- Music: 4 tracks × 3MB = 12MB (royalty-free)
- SFX: 5 sounds × 20KB = 100KB (synthesized or royalty-free)
- Total: ~12MB (lazy loaded, not in bundle)

---

## Open Questions

1. **Music Licensing:**
   - Using royalty-free tracks (FreeSound, Incompetech)?
   - Or need budget for premium music?
   - **Answer:** Start with royalty-free, upgrade later if needed

2. **SFX Generation:**
   - Programmatic (Tone.js Synth) vs. pre-recorded?
   - **Answer:** Use Tone.js Synth for consistency + smaller files

3. **Future Enhancements:**
   - Dynamic music based on market volatility?
   - Text-to-speech for critical alerts?
   - Multi-device settings sync?
   - **Answer:** Defer to post-MVP

4. **Gamepad Integration:**
   - Map audio controls to gamepad buttons?
   - **Answer:** Add in Phase 2 if user requests

---

## References

- [Tone.js Documentation](https://tonejs.github.io/)
- [Web Audio API MDN](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API)
- [Browser Autoplay Policies](https://developer.chrome.com/blog/autoplay/)
- Brainstorm Report: `plans/reports/brainstorm-260101-1001-audio-system-trading-game.md`

---

**Plan Status:** Phase 3 COMPLETE - Phase 4 IN PROGRESS
**Approval Status:** Phases 1-3 APPROVED | Phase 4 Active
**Next Action:** Complete Phase 4 (Keyboard Shortcuts) & Phase 5 (Polish & Testing)

---

## Phase 1 Completion Summary

**Deliverables Completed (2026-01-01):**
1. Tone.js dependency installed (v15.1.22)
2. TypeScript audio types created (src/types/audio.ts)
3. localStorage utilities implemented (src/utils/audio-storage.ts)
4. AudioManager service built and tested (src/services/audio-manager.ts)
5. Audio asset placeholders created (4 music + 5 SFX files)

**Quality Metrics:**
- Code Review: Grade A (0 critical issues)
- Test Coverage: 35/35 tests PASSED (100%)
- Build: SUCCESS (0 TypeScript errors, 0 ESLint errors)
- Documentation: Complete and accurate

**Ready for Phase 2:** Yes - All Phase 1 dependencies satisfied
