# Phase 3 Analysis: Sound Effects System (Day 3-4)
**Report ID:** project-manager-260101-1149-phase-3-analysis
**Date:** 2026-01-01
**Status:** PHASE 3 READY FOR IMPLEMENTATION
**Context:** Phase 1 Complete (Grade A), Phase 2 Pending, Phase 3 Analysis Extracted

---

## Executive Summary

Phase 3 implements gamified SFX system with Socket.IO integration. Goal: deliver 5 synth sounds triggered on trading events (buy/sell), market alerts, achievements. Key challenge: threshold filtering + debouncing prevents SFX spam. Estimated effort: 2 days (Day 3-4). Phase 1 infrastructure complete; Phase 2 (React Context) prerequisite pending. BLOCKING: Phase 2 must complete before Phase 3 implementation starts.

---

## Phase 3: Sound Effects System Overview

**Objective:** Add event-driven sound effects for trading activities with configurable thresholds
**Duration:** Day 3-4 (2 days)
**Dependency Chain:** Requires Phase 1 ✓ (DONE) + Phase 2 (IN PROGRESS)
**Key Innovation:** Threshold-based filtering prevents audio spam during high-frequency trading

---

## Extracted Tasks (5 Main Tasks + Subtasks)

### Task 1: Generate/Source Gamified SFX (5 sounds)
**Scope:** Create or source 5 audio files for trading events
**Acceptance:** All files <50KB each, MP3 format, playable in browser

**Subtasks:**
1. Create/find trade-buy sound (short synth beep, positive tone)
2. Create/find trade-sell sound (different pitch/timbre from buy)
3. Create/find market-alert sound (attention-grabbing, moderate duration)
4. Create/find achievement sound (celebratory chime)
5. Create/find milestone sound (bigger achievement chime, longer)

**Implementation Options:**
- **Option A (Recommended):** Use Tone.js Synth to generate programmatically
  - Advantages: Small file size, consistent, no external licensing
  - Code pattern: `new Tone.Synth({ freq: 800 }).triggerAttackRelease(0.1)`
  - Location: Can generate in browser or pre-generate and save

- **Option B:** Source from FreeSound.org
  - Search: "synth beep", "game sfx", "notification sound"
  - License: Creative Commons (check attribution)
  - Compress to 128kbps MP3

**Estimated Effort:** 2-4 hours (includes testing)
**Output Location:** `public/audio/sfx/`
**Files:** `{trade-buy,trade-sell,market-alert,achievement,milestone}.mp3`

---

### Task 2: Create SFX Event Emitter Service
**Scope:** Build `src/services/sfx-event-emitter.ts` with threshold + debounce logic
**Acceptance:** Emitter filters events, prevents spam, exports singleton

**Key Components:**
```
SFXEventEmitter {
  - emit(event: SFXEvent): void
  - shouldPlaySFX(event: SFXEvent): boolean  [threshold check]
  - isDebounced(type: SFXEventType): boolean  [500ms cooldown]
  - thresholds: { minTradeAmount, alertSeverity }
  - lastPlayedTime: Map<SFXEventType, timestamp>
}
```

**Thresholds Implemented:**
1. Trade threshold: only play if `amount >= minTradeAmount` (default: $0)
2. Alert threshold: severity filtering
   - `'all'` → play all alerts
   - `'high'` → play only HIGH severity alerts
3. Debounce: 500ms cooldown per event type (configurable in Phase 5)
4. Always play achievements (no threshold)

**Event Types Handled:**
- `trade:buy` + `trade:sell` (with amount metadata)
- `market:alert:{low|medium|high}` (with severity metadata)
- `achievement:unlock` + `achievement:milestone` (no threshold)

**Integration Points:**
- Receives events from Socket.IO handlers
- Calls `audioManager.playSFX(type)` on pass-through
- Reads thresholds from localStorage (set in Phase 3.4)

**Estimated Effort:** 4-6 hours
**Dependencies:** Requires Phase 1 AudioManager ✓, Phase 2 Context (for settings)

---

### Task 3: Integrate Socket.IO Event Handlers with SFX
**Scope:** Modify existing Socket.IO listeners to emit SFX events
**Acceptance:** SFX triggers on trade, alert, achievement events without breaking existing logic

**Event Handler Updates:**

**3.3.1 Trade Events (advisory:portfolio_result)**
```typescript
socket.on('advisor:portfolio_result', (data) => {
  // Existing logic...

  // NEW: Trigger SFX
  if (data.data?.status === 'BUY' || data.data?.status === 'SELL') {
    sfxEmitter.emit({
      type: data.data.status === 'BUY' ? 'trade:buy' : 'trade:sell',
      metadata: {
        amount: data.data?.amount || 0,
        symbol: data.data?.symbol
      }
    });
  }
});
```

**3.3.2 Market Alert Events (portfolio_health = DANGER)**
```typescript
socket.on('advisor:portfolio_result', (data) => {
  // Existing logic...

  // NEW: Market alert SFX
  const health = data.data?.portfolio_health?.status;
  if (health === 'DANGER') {
    sfxEmitter.emit({
      type: 'market:alert:high',
      metadata: { severity: 'high' }
    });
  }
  // Map WARN → medium, OK → low (optional)
});
```

**3.3.3 Achievement Events (new milestone)**
```typescript
// Location: wherever achievement events fire
socket.on('achievement:milestone', (data) => {
  sfxEmitter.emit({
    type: 'achievement:milestone',
    metadata: { name: data.name }
  });
});
```

**Files to Modify:**
- Any component using Socket.IO for trades/alerts/achievements
- Likely: `src/pages/`, `src/components/` containing socket listeners

**Estimated Effort:** 3-5 hours (discovery + integration)
**Risk:** Breaking existing event handlers (requires careful testing)
**Mitigation:** Add SFX calls after existing logic, use try-catch, log errors

---

### Task 4: Add SFX Threshold Settings to AudioSettingsModal
**Scope:** Extend Phase 2 AudioSettingsModal with SFX threshold controls
**Acceptance:** Settings persist to localStorage, reflect in emitter behavior

**UI Components to Add:**

**4.4.1 Min Trade Amount Input**
```typescript
<Label>Min Trade Amount ($)</Label>
<Input
  type="number"
  value={settings.minTradeAmount}
  onChange={(e) => updateThreshold('minTradeAmount', parseFloat(e.target.value))}
  min="0"
  step="100"
/>
```

**4.4.2 Alert Severity Select**
```typescript
<Label>Alert Severity</Label>
<Select
  value={settings.alertSeverity}
  onValueChange={(val) => updateThreshold('alertSeverity', val)}
>
  <SelectItem value="all">All Alerts</SelectItem>
  <SelectItem value="high">High Priority Only</SelectItem>
</Select>
```

**UI Layout Addition (after existing volume controls):**
```
┌─────────────────────────────────────────┐
│ SFX Thresholds                          │
│                                         │
│ Min Trade Amount: [$100    ]            │
│ Alert Severity:   [All Alerts ▼]        │
│                                         │
│ These settings determine which events   │
│ trigger sound effects                   │
└─────────────────────────────────────────┘
```

**Storage Schema (localStorage key: `audioSettings`):**
```typescript
{
  // ... existing settings ...
  sfx: {
    minTradeAmount: 100,        // Only play for trades >= $100
    alertSeverity: 'high'       // 'all' | 'high'
  }
}
```

**Estimated Effort:** 2-3 hours
**Dependencies:** Requires Phase 2 AudioSettingsModal ✓, Phase 3.2 emitter ready
**Testing:** Verify settings persist across page refresh

---

### Task 5: Implement Tone.Sampler for SFX in AudioManager
**Scope:** Add SFX playback to Phase 1 AudioManager using Tone.Sampler
**Acceptance:** SFX plays at correct volume, no audio distortion, <50ms latency

**AudioManager Extensions:**

**5.5.1 Add Tone.Sampler Initialization**
```typescript
class AudioManager {
  private sfxSampler: Tone.Sampler;

  async initialize(): Promise<void> {
    // ... existing code ...

    // Load SFX files into sampler (one-shot playback)
    this.sfxSampler = new Tone.Sampler({
      urls: {
        'trade:buy': '/audio/sfx/trade-buy.mp3',
        'trade:sell': '/audio/sfx/trade-sell.mp3',
        'market:alert': '/audio/sfx/market-alert.mp3',
        'achievement': '/audio/sfx/achievement.mp3',
        'milestone': '/audio/sfx/milestone.mp3'
      },
      onload: () => console.log('SFX loaded'),
      onerror: (err) => console.error('SFX load error:', err)
    });
  }
}
```

**5.5.2 Add playSFX() Method**
```typescript
playSFX(type: SFXType): void {
  if (!this.sfxSampler) return; // Not initialized

  // Calculate volume: sfx channel * master channel
  const sfxGain = this.volumes.sfx * this.volumes.master;
  this.sfxSampler.volume.value = Tone.gainToDb(sfxGain);

  // Trigger one-shot sample
  this.sfxSampler.triggerAttackRelease(0.1, Tone.now(), { velocity: 1 });
}
```

**5.5.3 Update dispose() for Cleanup**
```typescript
dispose(): void {
  this.player?.dispose();
  this.sfxSampler?.dispose(); // NEW
  // ... rest of cleanup ...
}
```

**Volume Calculation Notes:**
- Uses `Tone.gainToDb()` to convert linear (0-1) to dB scale
- Formula: `sfxGain = sfxVolume * masterVolume` (independent channels)
- Range: -Infinity to 0dB (silent to full volume)

**Estimated Effort:** 3-4 hours (includes testing)
**Dependencies:** Requires Phase 1 AudioManager ✓, Tone.Sampler knowledge
**Testing:** Verify SFX latency <50ms, volume levels correct

---

## Dependency Mapping

```
PHASE 3 DEPENDENCY CHAIN:

Phase 1 ✓ COMPLETE
├─ AudioManager service
├─ localStorage utilities
└─ TypeScript types
    ↓
Phase 2 (IN PROGRESS) ← BLOCKING
├─ AudioContext provider
├─ AudioSettingsModal
└─ useAudioPlayer hook
    ↓
Phase 3 CAN START AFTER Phase 2
├─ Task 1: SFX files (no dependency)
├─ Task 2: SFXEventEmitter (depends: Phase 1 ✓)
├─ Task 3: Socket.IO integration (depends: Task 2)
├─ Task 4: Threshold settings (depends: Phase 2 + Task 2)
└─ Task 5: Tone.Sampler in AudioManager (depends: Phase 1 + Task 1)
```

**Critical Path:**
1. Phase 2 must complete (blocks Phase 3 Tasks 4)
2. Task 2 (SFXEventEmitter) enables Tasks 3 + 4
3. Tasks can run parallel: 1 (audio files), 2+5 (service), 3+4 (integration)

---

## Technical Challenges & Mitigations

### Challenge 1: Finding Correct Socket.IO Event Names
**Problem:** Plan references `advisor:portfolio_result` but actual event names unknown
**Impact:** SFX won't trigger if events don't match
**Mitigation:**
- Search codebase for `socket.on()` calls
- Check browser DevTools Network tab for actual Socket.IO messages
- Cross-reference with Phase 2 implementation (may surface event names)
- **Action Item:** Discover actual Socket.IO event names before Task 3

### Challenge 2: SFX File Format/Compatibility
**Problem:** Tone.Sampler expects specific audio format (WAV/MP3/OGG)
**Impact:** Audio won't load or play with wrong format
**Mitigation:**
- Use MP3 format (broad browser support)
- Test with multiple file sources (FreeSound vs. Tone.js Synth)
- Preload in initialize() with error handler
- Provide fallback (silent mode if SFX fails)

### Challenge 3: Debounce Edge Case (Multiple Event Types)
**Problem:** 500ms cooldown per type means 10 trades/sec could still spam
**Impact:** User hears constant beeping during high-frequency trading
**Mitigation:**
- Current implementation: per-type debounce (correct)
- Phase 5 enhancement: configurable cooldown slider
- Consider: global debounce (max 1 sound/second across all types)
- **User Control:** Settings to disable SFX entirely (sfxVolume=0)

### Challenge 4: AudioManager Complexity Growth
**Problem:** Phase 1 = simple (Player), Phase 3 = complex (Player + Sampler + event emitter)
**Impact:** Testing burden, potential memory issues
**Mitigation:**
- Keep AudioManager focused (audio playback only)
- Move threshold logic to SFXEventEmitter (separation of concerns)
- Lazy load Sampler only when first SFX plays
- Add detailed JSDoc comments to all methods

---

## Testing Strategy for Phase 3

### Unit Tests Required

**SFXEventEmitter Tests (`sfx-event-emitter.test.ts`):**
```
✓ Should filter trades below threshold
✓ Should filter alerts below severity
✓ Should debounce multiple calls (max 1/500ms)
✓ Should always play achievements
✓ Should update lastPlayedTime on emit
✓ Should call audioManager.playSFX() with correct type
```

**AudioManager SFX Tests (`audio-manager.test.ts` extension):**
```
✓ Should load SFX samples without error
✓ Should play SFX with correct volume
✓ Should dispose SFX sampler on cleanup
✓ Should handle missing audio files gracefully
```

### Integration Tests

**Socket.IO Integration (`SocketIOIntegration.test.tsx`):**
```
✓ Trade event triggers correct SFX (buy vs. sell)
✓ Market alert triggers SFX when health=DANGER
✓ Achievement event triggers milestone SFX
✓ SFX respects threshold settings
✓ SFX doesn't break existing trade logic
```

### Manual Testing Scenarios

**Scenario 1: Trade Event SFX**
1. Trigger $50 trade with minTradeAmount=$100 → No SFX
2. Trigger $150 trade with minTradeAmount=$100 → SFX plays
3. Verify different tones for buy vs. sell

**Scenario 2: Alert Event SFX**
1. Set alertSeverity='high'
2. Trigger low/medium severity alert → No SFX
3. Trigger high severity alert → SFX plays

**Scenario 3: Debounce Verification**
1. Trigger 10 trades rapidly (within 500ms)
2. Verify only 1-2 SFX sounds play (per-type cooldown)
3. Verify different types not debounced (buy + sell both play)

**Scenario 4: Volume Independence**
1. Master volume = 0.8, SFX volume = 0.2
2. Trigger trade → SFX quieter than music
3. Adjust SFX slider → music volume unchanged

---

## Timeline & Milestones

**Day 3 (Task Focus: 1, 2, 5)**
- AM: Source/generate SFX files (Task 1)
- PM: Build SFXEventEmitter service (Task 2)
- PM: Integrate Tone.Sampler into AudioManager (Task 5)
- EOD: All SFX files playable, emitter emits without errors

**Day 4 (Task Focus: 3, 4 + Testing)**
- AM: Integrate Socket.IO events with SFX (Task 3)
- AM: Add threshold settings UI (Task 4)
- PM: Manual testing (all scenarios above)
- PM: Code review + documentation
- EOD: Phase 3 complete, ready for Phase 4

---

## Unresolved Questions

1. **Socket.IO Event Names:** What are the actual event names for trades, alerts, achievements?
   - **Blocking:** Task 3 implementation
   - **Resolution:** Discover in Phase 2 or codebase search

2. **SFX File Source:** Use Tone.js Synth programmatically or pre-recorded files?
   - **Impact:** File size, generation effort
   - **Resolution:** Start with Synth generation, fallback to FreeSound if needed

3. **Debounce Value Configurable?** Is 500ms fixed or user-adjustable?
   - **Scope:** Current plan = fixed, Phase 5 = configurable
   - **Resolution:** Implement fixed in Phase 3, defer UI to Phase 5

4. **Global vs. Per-Type Debounce:** Should 10 rapid trades from same account be debounced globally?
   - **UX Impact:** Affects audio feedback during trading sprees
   - **Resolution:** Use per-type as planned, revisit in Phase 5 if user feedback warrants

5. **iOS Web Audio Context:** Do Tone.Sampler have same autoplay restrictions as Player?
   - **Blocking:** None (can proceed), affects Phase 5 iOS testing
   - **Resolution:** Test on iOS during Phase 5

---

## Effort Estimate Summary

| Task | Subtasks | Hours | Owner |
|------|----------|-------|-------|
| 1: SFX Generation | 5 files | 2-4h | Any |
| 2: SFXEventEmitter | threshold+debounce | 4-6h | Backend Dev |
| 3: Socket.IO Integration | event mapping | 3-5h | Backend Dev |
| 4: Threshold UI | modal extension | 2-3h | Frontend Dev |
| 5: Tone.Sampler | AudioManager ext | 3-4h | Backend Dev |
| **TOTAL** | **5 tasks** | **14-22h** | **1-2 devs** |

**Estimated Duration:** 2 full days (7h x 2) = matches plan
**Buffer:** ~6-8 hours for testing, debugging, integration issues

---

## Recommended Next Steps

### Immediate (Today - 2026-01-01)
1. **Verify Phase 2 timeline:** Is Phase 2 complete or still in progress?
   - If complete: Phase 3 can start immediately
   - If pending: Schedule Phase 3 after Phase 2 completion

2. **Discover Socket.IO event names:** Search codebase + DevTools for actual events
   - Find trade confirmations
   - Find market/portfolio alerts
   - Find achievement events

3. **Validate SFX file strategy:** Decide between Tone.js Synth vs. FreeSound
   - Check if Synth generation meets audio quality standards
   - Test browser compatibility

### Pre-Implementation (Before Phase 3 Start)
1. Create test data for Socket.IO events (mock trade confirmations)
2. Set up Jest test environment for SFX tests
3. Review existing Socket.IO handlers for context

### Implementation Phase (Day 3-4)
1. Start Task 1 (SFX) + Task 2 (Emitter) in parallel
2. Task 3 + 4 dependent on Task 2 completion
3. Task 5 can proceed in parallel with 1-2

---

## Success Criteria Checklist

- [x] Phase 3 tasks extracted (5 main tasks identified)
- [x] Dependencies mapped (Phase 2 blocking confirmed)
- [x] Technical challenges identified (4 major challenges)
- [x] Testing strategy defined (unit + integration + manual)
- [x] Timeline allocated (2 days, 14-22 hours)
- [ ] Phase 2 completion date confirmed
- [ ] Socket.IO event names discovered
- [ ] SFX file strategy approved
- [ ] Phase 3 development starts (pending Phase 2)

---

**Report Status:** ANALYSIS COMPLETE - READY FOR IMPLEMENTATION QUEUE
**Next Review:** After Phase 2 completion
**Recommendation:** Queue Phase 3 to start immediately after Phase 2 ships

