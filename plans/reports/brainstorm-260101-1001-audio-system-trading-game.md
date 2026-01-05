# Audio System Brainstorm - Trading Game Experience

**Date:** 2026-01-01
**Session:** 10:01 AM
**Type:** Solution Architecture Design
**Status:** Recommendations Finalized

---

## Problem Statement

User requires immersive audio experience for fast-paced trading game (EV GamePad) to enhance trader/investor engagement through:
- Background music selection at session start
- Configurable volume controls (up/down/mute)
- Sound effects for trading events (buy/sell, market alerts, achievements)
- Easy accessibility via settings menu + keyboard shortcuts
- Persistence across sessions (volume, music selection, playback position)

---

## User Requirements Summary

### Game Context
- **Game Type:** Fast-paced tick-by-tick trading simulation
- **Current Stack:** React 18 + TypeScript, Socket.IO WebSocket, Vite, shadcn/ui components
- **Target UX:** GamePad-style trading interface with real-time market data (MT5 integration)

### Audio Requirements
**Sound Effects:**
- Transaction sounds (buy/sell confirmations)
- Market event alerts (price movements, volatility, news)
- Achievement/milestone celebrations

**Background Music:**
- 3-5 selectable tracks (lightweight approach)
- Music selection at session startup
- Simple track library, minimal bundle size

**Controls & UX:**
- Settings menu/modal for full configuration
- Keyboard shortcuts (hotkeys for power users)
- Configurable thresholds for SFX triggering (e.g., only trades >$100)

**Persistence:**
- Remember volume settings (localStorage)
- Remember last selected music track
- Resume music from last playback position (not restart)

**Tech Preference:**
- Game engine approach (Tone.js or PixiJS) for advanced audio features

---

## Evaluated Approaches

### Approach 1: Tone.js (Recommended)

**Description:** Full-featured Web Audio API framework designed for interactive music/games, ~200KB gzipped.

**Pros:**
- **Best for trading game:** Precise timing control for real-time SFX synced with market events
- **Advanced features:** Audio scheduling, effects (reverb, distortion), dynamic EQ, envelope shaping
- **Music playback:** Excellent transport controls (play/pause/seek), loop support, BPM sync
- **Performance:** Efficient scheduling engine minimizes audio glitches during CPU spikes (critical for fast-paced trading)
- **TypeScript support:** First-class TypeScript definitions
- **Active maintenance:** Well-documented, large community, used in production apps

**Cons:**
- Bundle size: ~200KB (acceptable for game-level experience)
- Learning curve: More complex API than native HTML5 Audio
- Overkill if only basic play/pause needed (but user wants game engine)

**Implementation Complexity:** Medium (2-3 days for full integration)

**Best For:** This project - aligns with game engine preference + configurable thresholds requirement

---

### Approach 2: Howler.js

**Description:** Lightweight audio library focused on simplicity, ~10KB gzipped.

**Pros:**
- Tiny bundle size (10KB)
- Simple API: `new Howl({ src: ['music.mp3'] }).play()`
- Good cross-browser support (fallback to HTML5 Audio)
- Sprite support (combine multiple SFX into single file)
- Volume control, fade effects, seek position

**Cons:**
- **Lacks advanced features** user wants (configurable thresholds = need audio analysis, scheduling)
- No built-in audio effects (reverb, filters)
- Limited real-time capabilities compared to Tone.js
- Not a "game engine" - contradicts user's tech preference

**Implementation Complexity:** Low (1 day)

**Best For:** Simple music players or basic SFX, NOT this project

---

### Approach 3: Native Web Audio API

**Description:** Browser-native AudioContext + AudioBufferSourceNode, 0KB bundle.

**Pros:**
- Zero dependencies
- Full control over audio graph (nodes, routing, effects)
- Maximum performance (no abstraction overhead)

**Cons:**
- **High development cost:** 5-10x more code than Tone.js for same features
- Complex buffer management (preloading, memory cleanup)
- Cross-browser quirks (Safari autoplay policies, iOS mute switch)
- No built-in music player abstractions (must build transport controls manually)
- Time-consuming for configurable thresholds (need custom audio analyzer)

**Implementation Complexity:** Very High (5-7 days)

**Best For:** Expert audio engineers building custom DSP - NOT pragmatic choice for this project

---

### Approach 4: PixiJS + PixiJS Sound Plugin

**Description:** 2D rendering engine (PixiJS) + audio plugin (~50KB combined).

**Pros:**
- If using PixiJS for visuals, audio plugin integrates seamlessly
- Sprite support, volume control, filters
- WebAudio API under the hood

**Cons:**
- **PixiJS not currently used** in project (React-based, not canvas game)
- Adding PixiJS = 400KB+ bundle just for audio = anti-YAGNI
- Less music-focused than Tone.js (designed for sprite-based games)
- Would require refactoring UI to PixiJS canvas (massive scope creep)

**Implementation Complexity:** Very High (requires UI rewrite)

**Best For:** Canvas-based games with PixiJS rendering - NOT this React app

---

## Recommended Solution: Tone.js Audio System

### Architecture Design

**Core Components:**

1. **AudioManager Service** (`src/services/audio-manager.ts`)
   - Singleton managing Tone.js Players (music) and Samplers (SFX)
   - Centralized volume control (master, music, SFX channels)
   - Playback state management (current track, position, loop status)
   - Persistence: save/load from localStorage

2. **Music Player Context** (`src/context/MusicContext.tsx`)
   - React Context wrapping AudioManager
   - Provides hooks: `useMusicPlayer()`, `useSoundEffects()`
   - Session startup: restore last music track + position
   - Global state: current track, volume levels, mute status

3. **Settings Modal Component** (`src/components/AudioSettingsModal.tsx`)
   - shadcn/ui Dialog with:
     - Music track selector (Dropdown/RadioGroup)
     - Volume sliders (master, music, SFX) with real-time preview
     - Mute toggles (visual + keyboard shortcut hints)
   - Save button triggers localStorage persistence

4. **SFX Event System** (`src/services/sfx-event-emitter.ts`)
   - Event emitter for trading events: `trade:buy`, `trade:sell`, `market:alert`, `achievement:unlock`
   - Configurable thresholds: filter events (e.g., only trades >$100)
   - Integration with existing Socket.IO events (emit SFX triggers on WebSocket messages)

5. **Keyboard Shortcuts Handler** (`src/hooks/useAudioKeyboard.ts`)
   - Hook listening to `keydown` events:
     - `M` = toggle mute
     - `Ctrl+↑/↓` = volume up/down
     - `P` = play/pause music
   - Global registration in App.tsx

**Music Assets Structure:**
```
public/audio/
├── music/
│   ├── focus-ambient.mp3      # Calm, minimal distraction
│   ├── energy-upbeat.mp3      # High-tempo for active trading
│   ├── strategy-chill.mp3     # Mid-tempo analytical mood
│   └── night-lofi.mp3         # Low-energy for late sessions
└── sfx/
    ├── trade-buy.mp3          # Short click/chime
    ├── trade-sell.mp3         # Different tone from buy
    ├── alert-warning.mp3      # Attention-grabbing beep
    ├── achievement.mp3        # Celebration sound
    └── milestone.mp3          # Bigger achievement
```

**Persistence Schema (localStorage):**
```typescript
interface AudioSettings {
  masterVolume: number;        // 0-1
  musicVolume: number;         // 0-1
  sfxVolume: number;          // 0-1
  isMuted: boolean;
  currentTrackId: string;      // 'focus-ambient'
  playbackPosition: number;    // seconds
  sfxThresholds: {
    minTradeAmount: number;    // Only play trade SFX if >$100
    alertSeverity: 'all' | 'high';  // All alerts or only high-priority
  };
}
```

---

### Implementation Flow

**Session Startup:**
1. User opens app → MusicContext initializes AudioManager
2. AudioManager loads settings from localStorage
3. If `currentTrackId` exists: preload track, seek to `playbackPosition`
4. Render Settings button in SystemHeader (top-right corner)
5. User clicks Settings → AudioSettingsModal opens with current values

**During Gameplay:**
1. Socket.IO receives trade confirmation → emit `trade:buy` event
2. SFX event emitter checks threshold: if trade >$100 → play `trade-buy.mp3`
3. Tone.js Sampler triggers sound at scheduled time (0ms latency)
4. User presses `M` key → toggle mute, update UI + localStorage

**On Page Refresh:**
1. AudioManager reads localStorage → restore volume, track, position
2. Auto-resume music playback (if was playing before refresh)
3. SFX thresholds restored → maintain user preferences

---

### Technical Considerations

**Bundle Size Impact:**
- Tone.js: ~200KB gzipped
- Audio files (4 music + 5 SFX): ~5-10MB total (lazy loaded)
- **Mitigation:** Code-split AudioManager (only load when Settings opened first time)

**Performance:**
- Tone.js uses Web Audio API (hardware-accelerated)
- SFX scheduling: <1ms latency (critical for real-time trading feedback)
- Music streaming: use MP3 (browser-native decoding, no CPU overhead)

**Browser Compatibility:**
- Tone.js supports: Chrome 60+, Firefox 55+, Safari 11+, Edge 79+
- Autoplay policy: Start playback ONLY on user interaction (Settings modal or session start click)
- iOS caveat: require user gesture to unmute (display banner if muted by iOS)

**Accessibility:**
- Volume sliders: ARIA labels + keyboard navigation
- Mute indicator: visual icon in header (screen reader friendly)
- Alternative: Add "Reduce motion" setting to disable distracting SFX

**Security:**
- Audio files: serve from `public/` (no CORS issues)
- localStorage: max 5MB limit (audio settings ~1KB, well within limit)

---

### Risks & Mitigations

**Risk 1: Tone.js bundle size impacts load time**
- **Impact:** Medium (200KB = ~200ms on 4G)
- **Mitigation:**
  - Code-split: load Tone.js only when user opens Settings first time
  - Use Vite dynamic import: `const Tone = await import('tone')`
  - Show loading skeleton while AudioManager initializes

**Risk 2: Music files too large (slow download)**
- **Impact:** High (10MB music = 10s on slow connection)
- **Mitigation:**
  - Use compressed MP3 (128kbps = ~3MB per 3-min track)
  - Lazy load: only download selected track (not all 4 upfront)
  - Show download progress bar in Settings modal

**Risk 3: iOS autoplay restrictions (music doesn't start)**
- **Impact:** Medium (affects 20-30% mobile users)
- **Mitigation:**
  - Detect iOS: display "Tap to start music" banner on session load
  - Require user gesture before first `audioContext.resume()`
  - Test on real iOS devices (Safari + Chrome iOS)

**Risk 4: SFX spam during high-frequency trading (annoying)**
- **Impact:** Medium (100 trades/min = constant beeping)
- **Mitigation:**
  - Implement debouncing: max 1 SFX per event type per 500ms
  - Add "SFX cooldown" setting (default: 1 sound per second)
  - Visual preference: flashing border instead of sound for rapid events

**Risk 5: Memory leak from audio buffers**
- **Impact:** Low (only affects multi-hour sessions)
- **Mitigation:**
  - Dispose Tone.js Players on unmount: `player.dispose()`
  - Use single Sampler instance for all SFX (shared buffer)
  - Monitor memory in DevTools during long sessions

---

## Alternative Considered: Hybrid Approach (Howler.js + Web Audio API)

**Why Not This:**
- Defeats KISS principle (two audio libraries for same goal)
- Howler.js can't do configurable thresholds → need Web Audio API anyway
- If using Web Audio API, might as well use Tone.js abstraction (better DX)
- Maintenance burden: two APIs to update, two sets of browser quirks

**When This Makes Sense:**
- If user changes requirement to "simplest possible" (Howler.js alone)
- If advanced features dropped (no thresholds, no effects)

---

## Success Metrics

**User-Facing:**
- Session startup: music auto-resumes within 500ms of page load
- Settings modal: <200ms open latency (code-split effective)
- SFX latency: <50ms from trade event to sound playback
- Persistence: 100% accuracy (volume/track/position restored)

**Technical:**
- Bundle size: +200KB (Tone.js), acceptable for game UX
- Audio files: lazy loaded (not in initial bundle)
- Memory usage: <50MB for audio system (reasonable for game)
- Browser support: 95%+ (all modern browsers except IE)

**Business:**
- User engagement: measure session duration before/after audio (expect +20-30%)
- Settings adoption: >60% users customize audio within first 3 sessions
- Mobile usage: iOS/Android users enable music (track autoplay success rate)

---

## Implementation Roadmap

### Phase 1: Core Audio Infrastructure (Day 1-2)
- Install Tone.js: `npm install tone`
- Create `AudioManager` service with music playback
- Add 3-4 royalty-free music tracks to `public/audio/music/`
- Implement localStorage persistence (volume, track, position)
- Unit tests: AudioManager save/load/playback

### Phase 2: UI Integration (Day 2-3)
- Build `AudioSettingsModal` with shadcn/ui components
- Add Settings button to SystemHeader (icon: Volume2 from lucide-react)
- Create `MusicContext` provider, wrap App.tsx
- Implement volume sliders (Slider component) + mute toggles (Switch)
- Session startup: auto-restore music on mount

### Phase 3: Sound Effects System (Day 3-4)
- Add SFX files to `public/audio/sfx/` (5 sounds)
- Create `SFXEventEmitter` with threshold configuration
- Integrate with Socket.IO: emit SFX events on trade confirmations
- Add threshold settings UI (number input for minTradeAmount)
- Test SFX triggering with real trade events

### Phase 4: Keyboard Shortcuts (Day 4)
- Implement `useAudioKeyboard` hook (M = mute, Ctrl+↑/↓ = volume)
- Add visual hints in Settings modal ("Press M to mute")
- Global registration in App.tsx
- Prevent conflicts with existing shortcuts (check GamepadControllerHints)

### Phase 5: Polish & Testing (Day 5)
- iOS testing: autoplay restrictions, mute switch behavior
- Performance profiling: memory usage during long sessions
- Accessibility audit: ARIA labels, keyboard navigation
- Documentation: update docs/system-architecture.md with audio system
- User guide: add audio settings section to README

**Total Timeline:** 5 days (1 developer)

---

## Open Questions

1. **Music licensing:** Are you using royalty-free tracks (FreeSound, Incompetech) or need budget for licensed music?
2. **SFX design:** Should sounds be realistic (cash register, bell) or gamified (synth beeps, chimes)?
3. **Dynamic music:** Future consideration - should music tempo change with market volatility? (out of scope for MVP)
4. **Voice alerts:** Any interest in text-to-speech for critical alerts ("Large position at risk")? (could use Web Speech API)
5. **Multi-user sync:** If multiple devices, should audio settings sync via backend? (requires DB schema change)

---

## Next Steps

1. **User Decision:** Approve Tone.js approach or request modifications?
2. **Asset Sourcing:** Provide preferred music tracks or delegate to implementation team?
3. **Priority:** Should audio system block other features or run parallel?
4. **Create Implementation Plan:** If approved, generate detailed plan via `/plan` command?

---

## Appendix: Code Samples

### AudioManager Service (Pseudocode)

```typescript
// src/services/audio-manager.ts
import * as Tone from 'tone';

interface AudioSettings {
  masterVolume: number;
  musicVolume: number;
  sfxVolume: number;
  isMuted: boolean;
  currentTrackId: string;
  playbackPosition: number;
}

class AudioManager {
  private musicPlayer: Tone.Player | null = null;
  private sfxSampler: Tone.Sampler | null = null;
  private settings: AudioSettings;

  constructor() {
    this.settings = this.loadSettings();
    this.initializePlayers();
  }

  loadSettings(): AudioSettings {
    const saved = localStorage.getItem('audioSettings');
    return saved ? JSON.parse(saved) : DEFAULT_SETTINGS;
  }

  saveSettings(): void {
    localStorage.setItem('audioSettings', JSON.stringify(this.settings));
  }

  async loadMusicTrack(trackId: string): Promise<void> {
    this.musicPlayer?.dispose();
    this.musicPlayer = new Tone.Player({
      url: `/audio/music/${trackId}.mp3`,
      loop: true,
      volume: this.calculateVolume(),
    }).toDestination();
    await Tone.loaded();
    this.musicPlayer.seek(this.settings.playbackPosition);
  }

  play(): void {
    Tone.start(); // Required for browser autoplay policy
    this.musicPlayer?.start();
  }

  pause(): void {
    this.settings.playbackPosition = this.musicPlayer?.immediate() || 0;
    this.musicPlayer?.stop();
    this.saveSettings();
  }

  playSFX(eventType: 'buy' | 'sell' | 'alert'): void {
    if (this.settings.isMuted) return;
    this.sfxSampler?.triggerAttackRelease(`/audio/sfx/${eventType}.mp3`, '16n');
  }

  setVolume(channel: 'master' | 'music' | 'sfx', value: number): void {
    this.settings[`${channel}Volume`] = value;
    this.updateVolumes();
    this.saveSettings();
  }

  private calculateVolume(): number {
    return Tone.gainToDb(
      this.settings.masterVolume * this.settings.musicVolume
    );
  }
}

export const audioManager = new AudioManager();
```

### Settings Modal Component (Pseudocode)

```typescript
// src/components/AudioSettingsModal.tsx
import { Dialog, Slider, Switch, RadioGroup } from '@/components/ui';
import { useMusicPlayer } from '@/context/MusicContext';

export function AudioSettingsModal() {
  const { currentTrack, volume, isMuted, setTrack, setVolume, toggleMute } =
    useMusicPlayer();

  return (
    <Dialog>
      <DialogContent>
        <h2>Audio Settings</h2>

        {/* Music Track Selector */}
        <RadioGroup value={currentTrack} onValueChange={setTrack}>
          <RadioGroupItem value="focus-ambient">Focus Ambient</RadioGroupItem>
          <RadioGroupItem value="energy-upbeat">Energy Upbeat</RadioGroupItem>
        </RadioGroup>

        {/* Volume Sliders */}
        <div>
          <Label>Master Volume</Label>
          <Slider
            value={[volume.master]}
            onValueChange={([v]) => setVolume('master', v)}
            max={100}
          />
        </div>

        {/* Mute Toggle */}
        <Switch checked={isMuted} onCheckedChange={toggleMute}>
          Mute All (M)
        </Switch>

        {/* Keyboard Hints */}
        <p className="text-sm text-muted-foreground">
          Press M to mute • Ctrl+↑/↓ for volume
        </p>
      </DialogContent>
    </Dialog>
  );
}
```

---

**Report Status:** Complete
**Recommendations:** Tone.js audio system with 5-day implementation
**Awaiting:** User approval to proceed with `/plan` command
