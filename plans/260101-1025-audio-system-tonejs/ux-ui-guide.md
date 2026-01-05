# Audio System - UX/UI User Guide

**Date:** 2026-01-01
**Plan:** 260101-1025-audio-system-tonejs
**Purpose:** Show exactly what users see and how to use audio system in-game

---

## UI Changes Overview

### What You'll See in the Game

**1. SystemHeader - Audio Widget (Always Visible)**

```
┌─────────────────────────────────────────────────────────────────────┐
│ MONITOR 1  PORTFOLIO ANALYSIS                                       │
│                                                                      │
│ [🎵 Focus Ambient]  [🔊 80%]  [⚙️]    ONLINE   STABLE   12:34:56   │
└─────────────────────────────────────────────────────────────────────┘
     ↑               ↑         ↑
  Now Playing    Volume   Settings Button
```

**New Elements in SystemHeader:**
- **Music indicator:** Shows current track name (or "No Music" if stopped)
- **Volume indicator:** Shows master volume percentage
- **Settings button:** Opens full audio configuration modal

**Position:** Right side of header, before ONLINE/UPLINK indicators

---

## Session Startup Flow

### Scenario 1: First-Time User (No Saved Settings)

**Step 1:** User opens app
```
┌─────────────────────────────────────────────────────────────────┐
│                    🎵 Welcome to EV GamePad                     │
│                                                                  │
│  Enable background music for better trading experience?         │
│                                                                  │
│  [Enable Music]                          [Skip]                 │
└─────────────────────────────────────────────────────────────────┘
```

**Step 2a:** User clicks "Enable Music" → Music selector appears
```
┌─────────────────────────────────────────────────────────────────┐
│                    Choose Your Trading Music                     │
│                                                                  │
│  ○ Focus Ambient     - Calm, minimal distraction                │
│  ○ Energy Upbeat     - High-tempo for active trading            │
│  ○ Strategy Chill    - Mid-tempo analytical mood                │
│  ○ Night Lofi        - Low-energy for late sessions             │
│                                                                  │
│                          [Start]                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Step 2b:** User clicks "Skip" → No music, goes straight to app

**Step 3:** Music starts playing, header shows:
```
[🎵 Energy Upbeat]  [🔊 80%]  [⚙️]
```

---

### Scenario 2: Returning User (Has Saved Settings)

**Step 1:** User opens app

**Step 2:** Music auto-resumes from last position (silent, smooth)

**Step 3:** Header shows:
```
[🎵 Focus Ambient]  [🔊 70%]  [⚙️]
     ↑ auto-resumed at 2:34 mark
```

**User sees:** Music indicator animates (pulsing icon) to show it's playing

---

## In-Game Audio Experience

### During Trading Session

**Visual Feedback for Audio Events:**

**1. Trade Executed (Buy)**
```
[Trade Confirmed: +0.5 XAUUSD @ 2634.50]
         ↓
   🔊 *beep* (high-pitched synth)
         ↓
   Green flash on trade panel border (100ms)
```

**2. Trade Executed (Sell)**
```
[Trade Confirmed: -0.3 BTCUSD @ 42500]
         ↓
   🔊 *boop* (lower-pitched synth)
         ↓
   Red flash on trade panel border (100ms)
```

**3. Portfolio Risk Alert (High)**
```
[Portfolio Health: DANGER - 85% risk exposure]
         ↓
   🔊 *warning beep* (urgent, 3-note sequence)
         ↓
   Red glow on portfolio panel (500ms pulse)
```

**4. Achievement Unlocked**
```
[Achievement: First Profitable Trade!]
         ↓
   🔊 *celebration chime* (ascending notes)
         ↓
   Gold sparkle animation on achievement badge
```

**Volume Indicator Updates:**
- Real-time: shows current volume when SFX plays
- Flashes briefly when sound triggers
- Returns to normal after 500ms

---

## Audio Controls - Quick Access

### SystemHeader Audio Widget (Detailed)

**Normal State:**
```
┌──────────────────────────────────┐
│ [🎵 Energy Upbeat] [🔊 80%] [⚙️] │
└──────────────────────────────────┘
```

**Hover State:**
```
┌──────────────────────────────────┐
│ [🎵 Energy Upbeat▼] [🔊 80%▼] [⚙️] │
└──────────────────────────────────┘
     ↑ dropdown         ↑ slider appears
```

**Quick Actions:**

**1. Click Music Indicator → Quick Track Selector**
```
┌─────────────────────────┐
│ ● Energy Upbeat         │
│ ○ Focus Ambient         │
│ ○ Strategy Chill        │
│ ○ Night Lofi            │
│ ────────────────────    │
│ ○ Stop Music            │
└─────────────────────────┘
```

**2. Click Volume Indicator → Quick Volume Slider**
```
┌─────────────────────────┐
│ Master:  [━━━━━●━━━] 80%│
│ Music:   [━━━━━━●━] 70% │
│ SFX:     [━━━━━━━●] 90% │
│ ────────────────────    │
│ [🔇 Mute All]           │
└─────────────────────────┘
```

**3. Click Settings Icon → Full Settings Modal**
(See Settings Modal section below)

---

## Settings Modal - Full Configuration

### Access
- Click ⚙️ icon in SystemHeader
- Or press `Ctrl+,` (keyboard shortcut)

### Layout
```
┌────────────────────────────────────────────────────────────┐
│  Audio Settings                                        [X] │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  🎵 Background Music                                        │
│  ┌────────────────────────────────────────────────────┐   │
│  │ ● Focus Ambient     - Calm, minimal distraction     │   │
│  │ ○ Energy Upbeat     - High-tempo for active trading │   │
│  │ ○ Strategy Chill    - Mid-tempo analytical mood     │   │
│  │ ○ Night Lofi        - Low-energy for late sessions  │   │
│  │ ○ No Music          - Disable background music      │   │
│  └────────────────────────────────────────────────────┘   │
│                                                             │
│  🔊 Volume Controls                                         │
│  ┌────────────────────────────────────────────────────┐   │
│  │ Master Volume:    [━━━━━━━━━━━━━━] 80%            │   │
│  │ Music Volume:     [━━━━━━━━━━━━━━] 70%            │   │
│  │ SFX Volume:       [━━━━━━━━━━━━━━] 90%            │   │
│  │                                                      │   │
│  │ [✓] Mute All                                        │   │
│  └────────────────────────────────────────────────────┘   │
│                                                             │
│  ⚡ Sound Effect Triggers                                   │
│  ┌────────────────────────────────────────────────────┐   │
│  │ Min Trade Amount:     [$100      ]                  │   │
│  │ Alert Severity:       [High Priority ▼]            │   │
│  │ SFX Cooldown:         [500ms     ]                  │   │
│  └────────────────────────────────────────────────────┘   │
│                                                             │
│  ⌨️ Keyboard Shortcuts                                      │
│  ┌────────────────────────────────────────────────────┐   │
│  │ M            - Toggle Mute                          │   │
│  │ Ctrl+↑/↓     - Volume Up/Down                       │   │
│  │ P            - Play/Pause Music                     │   │
│  │ Ctrl+,       - Open Settings                        │   │
│  └────────────────────────────────────────────────────┘   │
│                                                             │
│  📱 Mobile Support                                          │
│  ┌────────────────────────────────────────────────────┐   │
│  │ [✓] Enable autoplay (requires tap on iOS)          │   │
│  │ [✓] Continue playback in background                │   │
│  └────────────────────────────────────────────────────┘   │
│                                                             │
│               [Reset to Default]      [Cancel]  [Save]     │
└────────────────────────────────────────────────────────────┘
```

### Interactive Elements
- **Track selector:** Click to change music immediately (preview)
- **Volume sliders:** Drag to adjust, hear change in real-time
- **Mute toggle:** Instant mute/unmute with visual feedback
- **Threshold inputs:** Type numbers, validated on blur

---

## Visual Feedback Examples

### 1. Music Playing Indicator
```
SystemHeader (Normal):
[🎵 Focus Ambient]
     ↑ static

SystemHeader (Playing):
[🎵 Focus Ambient]
 ✨ ↑ pulsing animation (1s interval)
```

### 2. Volume Adjustment Feedback
```
User presses Ctrl+↑:
[🔊 80%] → [🔊 90%] ← flashes green for 300ms
            ↑
     visual feedback
```

### 3. Mute State
```
Unmuted:
[🔊 80%]

Muted:
[🔇 --]  ← red icon, strikethrough volume
```

### 4. SFX Trigger Visual
```
Trade panel before SFX:
┌──────────────────┐
│ Trade Confirmed  │
│ +0.5 XAUUSD      │
└──────────────────┘

Trade panel during SFX (50ms):
┌══════════════════┐  ← green glow
║ Trade Confirmed  ║
║ +0.5 XAUUSD      ║
└══════════════════┘
   🔊 *beep*
```

---

## User Workflows

### Workflow 1: Change Music During Trading

**User Action:**
1. Click music indicator in header: `[🎵 Focus Ambient ▼]`
2. Dropdown appears with track list
3. Click "Energy Upbeat"

**System Response:**
1. Current music fades out (500ms)
2. New music loads (300ms)
3. New music fades in (500ms)
4. Header updates: `[🎵 Energy Upbeat]`
5. localStorage saves: `currentTrackId="energy-upbeat"`

**Total transition time:** ~1.3 seconds (smooth, no jarring stop)

---

### Workflow 2: Adjust Volume with Keyboard

**User Action:**
1. Press `Ctrl+↑` (while trading)

**System Response:**
1. Master volume increases 10% (70% → 80%)
2. Header shows: `[🔊 80%]` ← flashes green
3. SFX plays preview beep at new volume
4. localStorage saves: `masterVolume=0.8`

**Visual feedback:** 300ms green flash on volume indicator

---

### Workflow 3: Quick Mute During Phone Call

**User Action:**
1. Press `M` key

**System Response:**
1. All audio mutes instantly (<10ms)
2. Header shows: `[🔇 --]` (mute icon)
3. Music continues playing (position tracked)
4. localStorage saves: `isMuted=true`

**To unmute:** Press `M` again → audio resumes at current position

---

### Workflow 4: Disable SFX for Specific Trades

**User Action:**
1. Open Settings modal (click ⚙️)
2. Set "Min Trade Amount" to $500
3. Click Save

**System Response:**
1. Settings saved to localStorage
2. Modal closes
3. Next $200 trade → NO SFX plays (below threshold)
4. Next $600 trade → SFX plays (above threshold)

**Visual confirmation:** Toast notification "SFX threshold updated to $500"

---

## Mobile Experience (iOS/Android)

### iOS Safari - Autoplay Banner

**First session (no saved settings):**
```
┌─────────────────────────────────────────────────────┐
│  🎵 Tap to Enable Audio                              │
│  Background music & sound effects require user tap   │
│                                                       │
│              [Enable Audio]                          │
└─────────────────────────────────────────────────────┘
      ↑ appears at top of screen
```

**After user taps "Enable Audio":**
1. Music selector appears (same as desktop)
2. User chooses track
3. Music starts playing
4. Banner dismisses

**Subsequent sessions:**
- Music auto-resumes (iOS allows after first gesture)
- No banner required

---

### Mobile Quick Controls

**Tap header audio widget:**
```
┌─────────────────────────────┐
│ [🎵 Energy Upbeat]          │ ← opens bottom sheet
└─────────────────────────────┘

Bottom Sheet:
┌─────────────────────────────┐
│ Audio Controls              │
├─────────────────────────────┤
│ ● Energy Upbeat             │
│ ○ Focus Ambient             │
│ ○ Strategy Chill            │
│ ○ Night Lofi                │
│ ────────────────────        │
│ Master:  [━━━━━●━━━] 80%   │
│ Music:   [━━━━━━●━] 70%    │
│ SFX:     [━━━━━━━●] 90%    │
│ ────────────────────        │
│ [🔇 Mute]    [⚙️ Settings]  │
└─────────────────────────────┘
```

---

## Edge Cases & Error States

### 1. Music File Load Failure
```
SystemHeader shows:
[🎵 Loading...] → [⚠️ Music Unavailable]
                      ↑
              click to retry or choose different track
```

### 2. No Internet (Music File Missing)
```
Toast notification:
┌─────────────────────────────────────┐
│ ⚠️ Cannot load music (offline)      │
│ SFX will still work                 │
└─────────────────────────────────────┘
```

### 3. Browser Autoplay Blocked
```
Banner appears:
┌─────────────────────────────────────────────────┐
│  🔇 Your browser blocked autoplay                │
│  Click to enable: [Enable Audio]                │
└─────────────────────────────────────────────────┘
```

---

## Summary: What Users Experience

### Visual Changes in UI
1. **SystemHeader:** Audio widget (music, volume, settings) always visible
2. **Session startup:** Music selector or auto-resume
3. **Trade events:** Visual flashes + SFX sounds
4. **Settings modal:** Full audio configuration

### How to Use
- **Change music:** Click music indicator in header
- **Adjust volume:** Click volume indicator OR use Ctrl+↑/↓
- **Mute quickly:** Press M key
- **Full settings:** Click ⚙️ icon in header

### When Audio Plays
- **Music:** Continuous loop (user-selected track)
- **SFX:** On trade confirmations, alerts, achievements (respects thresholds)

### Mobile-Specific
- **iOS:** "Tap to Enable Audio" banner on first session
- **Android:** Works like desktop (no restrictions)

---

## Implementation Checklist

### Phase 1: Core Infrastructure
- [ ] AudioManager service
- [ ] localStorage helpers
- [ ] Music files sourced

### Phase 2: UI Integration
- [ ] Audio widget in SystemHeader
- [ ] Session startup flow (first-time + returning)
- [ ] Settings modal
- [ ] Quick controls (dropdowns)

### Phase 3: SFX System
- [ ] Visual flash effects on trade panels
- [ ] SFX event emitter
- [ ] Socket.IO integration

### Phase 4: Mobile
- [ ] iOS autoplay banner
- [ ] Bottom sheet controls
- [ ] Touch-friendly sliders

### Phase 5: Polish
- [ ] Animations (fade in/out, flashes)
- [ ] Error state handling
- [ ] Accessibility (ARIA labels)

---

**Questions?**
- Where should music indicator go if header is too crowded?
  → **Answer:** Can collapse to icon-only mode (🎵 ⚙️)

- Should we add visual equalizer animation?
  → **Answer:** Defer to post-MVP (nice-to-have)

- Should SFX visual flashes be configurable?
  → **Answer:** Yes, add "Visual SFX Feedback" toggle in settings

---

**Next Steps:**
1. Review this UX guide
2. Confirm UI placement in SystemHeader
3. Begin implementation Phase 1 (backend audio system)
4. Then Phase 2 (UI integration with these designs)
