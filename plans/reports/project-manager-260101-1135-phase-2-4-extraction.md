# Phase 2-4 Task Extraction & TodoWrite Initialization
**Date:** 2026-01-01 11:35
**Plan ID:** 260101-1025-audio-system-tonejs
**Extraction Report:** Project Manager
**Status:** Analysis Complete

---

## Executive Summary

✓ Step 1: Found 33 actionable tasks across 3 phases (2, 3, 4) plus 10 verification/documentation tasks
✓ Ambiguities: 2 identified (SFX file sourcing, iOS banner implementation details)
✓ Blockers: None critical - Phase 1 complete, all dependencies ready

**TodoWrite Initialized:** 39 total tasks (1 Step 0 + 5 workflow steps + 33 phase tasks)

---

## Detailed Task Extraction

### Phase 2: React Context & UI Integration (Day 2-3)
**Status:** PENDING | **Effort:** ~16 hours | **Dependencies:** Phase 1 Complete (✓ verified)

#### Task Breakdown (8 core tasks + 1 verification)

**Step 2.1: Create AudioContext.tsx**
- Initialize AudioManager on mount
- Restore settings from localStorage
- Auto-resume music if was playing
- Export `useAudioPlayer()` hook
- Provide memo-ized context value
- Cleanup on unmount (dispose Tone.js)
- **File:** `src/context/AudioContext.tsx`
- **Dependencies:** AudioManager (Phase 1 ✓), audio-storage.ts (Phase 1 ✓), audio.ts types (Phase 1 ✓)

**Step 2.2: Create useAudioPlayer Hook**
- Wrapper around AudioContext
- Type-safe return interface
- Prevent re-renders via useMemo
- **File:** `src/hooks/useAudioPlayer.ts`
- **Dependencies:** AudioContext (Step 2.1)

**Step 2.3: Create AudioSettingsModal Component**
- shadcn/ui: Dialog, RadioGroup, Slider, Switch, Input, Select, Button
- Music track selector with descriptions (4 tracks)
- Volume sliders: master, music, SFX (real-time preview)
- Mute toggle
- SFX threshold settings (minTradeAmount, alertSeverity)
- Keyboard shortcut hints section
- Save/Cancel buttons
- **File:** `src/components/AudioSettingsModal.tsx`
- **Dependencies:** useAudioPlayer (Step 2.2), shadcn/ui components

**Step 2.4: Add Settings Button to SystemHeader**
- Icon: `Volume2` from lucide-react
- Position: top-right corner
- Trigger: opens AudioSettingsModal
- **File:** `src/components/SystemHeader.tsx` (modify)
- **Dependencies:** AudioSettingsModal (Step 2.3)

**Step 2.5: Create useSoundEffects Hook**
- SFX-specific wrapper around context
- Simplified API for SFX triggering
- **File:** `src/hooks/useSoundEffects.ts`
- **Dependencies:** useAudioPlayer (Step 2.2)

**Step 2.6: Integrate AudioProvider in App.tsx**
- Wrap app with `<AudioProvider>`
- Position: outer layer (before SocketProvider)
- Pattern: `<AudioProvider><SocketProvider><TooltipProvider>...</TooltipProvider></SocketProvider></AudioProvider>`
- **File:** `src/App.tsx` (modify)
- **Dependencies:** AudioContext (Step 2.1)

**Step 2.7: Test Phase 2 Acceptance Criteria**
- Settings button visible in header
- Modal opens/closes smoothly
- Track selection updates context state
- Volume sliders adjust audio in real-time
- Settings persist on "Save" click
- Music auto-resumes on page refresh
- **Test Type:** Manual E2E
- **Duration:** ~30 min

**Step 2.8: Verify Settings Persistence**
- Refresh page after settings change
- Check localStorage: `audioSettings` key exists
- Verify: volume, currentTrack, playbackPosition restored
- Verify: music auto-resumes from saved position
- **Test Type:** Manual + localStorage inspection
- **Duration:** ~15 min

---

### Phase 3: Sound Effects System (Day 3-4)
**Status:** PENDING | **Effort:** ~18 hours | **Dependencies:** Phase 2 Complete

#### Task Breakdown (8 core tasks + 1 verification)

**Step 3.1: Source/Generate Gamified SFX**
- Required files: trade-buy, trade-sell, market-alert, achievement, milestone
- Options:
  - Tone.js programmatic: `Tone.Synth` generation (recommended for consistency)
  - FreeSound.org: search "synth beep", "game sfx"
- Constraints: <50KB per file, short duration, MP3 128kbps
- **Output:** 5 MP3 files in `public/audio/sfx/`
- **Ambiguity:** Programmatic vs. pre-recorded? (See open questions)

**Step 3.2: Create SFX Event Emitter**
- File: `src/services/sfx-event-emitter.ts`
- Implement threshold checking logic
- Implement debouncing (500ms cooldown per type)
- Event types: trade:buy, trade:sell, market:alert:low/medium/high, achievement:unlock, achievement:milestone
- Map events to SFX files
- **Dependencies:** AudioManager (Phase 1 ✓)

**Step 3.3: Integrate with Socket.IO Events**
- Find existing event handlers in components
- Add SFX triggers to:
  - `advisor:portfolio_result` (market alerts)
  - `trade:confirmed` (buy/sell sounds)
  - Achievement events (new milestone reached)
- Pattern: `sfxEmitter.emit({ type: 'event:type', metadata: {...} })`
- **Files:** Components with Socket.IO listeners (need discovery)
- **Dependencies:** sfxEmitter (Step 3.2)

**Step 3.4: Add SFX Threshold Settings to Modal**
- Add to AudioSettingsModal (Step 2.3 already created)
- Number input: "Min Trade Amount" (e.g., $100)
- Select dropdown: "Alert Severity" (all/high/medium)
- Save to localStorage via audioSettings
- **File:** `src/components/AudioSettingsModal.tsx` (enhance)
- **Dependencies:** AudioSettingsModal (Step 2.3), SFXThresholds type

**Step 3.5: Implement Tone.Sampler in AudioManager**
- Add to Phase 1 AudioManager service
- Load all 5 SFX files on initialization
- Use `Tone.Sampler` for one-shot playback
- Apply volume: `sfxVolume * masterVolume`
- Preload samples to prevent latency
- **File:** `src/services/audio-manager.ts` (enhance)
- **Dependencies:** Audio files from Step 3.1

**Step 3.6: Test Phase 3 Acceptance Criteria**
- SFX plays on trade confirmation (buy/sell different tones)
- Market alert SFX plays when portfolio health = DANGER
- Threshold filtering works (e.g., only trades >$100)
- Debouncing prevents SFX spam (max 1/500ms per type)
- SFX volume independent from music volume
- **Test Type:** Manual integration with mock Socket.IO events
- **Duration:** ~45 min

**Step 3.7: Verify Rapid Trade Debouncing**
- Trigger 10 trades rapidly
- Verify: only 1 SFX per 500ms max
- Verify: correct tones for buy/sell
- **Test Type:** Manual with rapid event simulation
- **Duration:** ~15 min

**Step 3.8: Verify Threshold Filtering**
- Set minTradeAmount=$100
- Trigger $50 trade → verify silent
- Trigger $150 trade → verify SFX plays
- Set alertSeverity=high → verify low/medium alerts silent
- **Test Type:** Manual with parametrized events
- **Duration:** ~20 min

---

### Phase 4: Keyboard Shortcuts (Day 4)
**Status:** PENDING | **Effort:** ~12 hours | **Dependencies:** Phase 2-3 Complete

#### Task Breakdown (8 core tasks)

**Step 4.1: Create useAudioKeyboard Hook**
- File: `src/hooks/useAudioKeyboard.ts`
- Shortcuts:
  - `M` → Toggle mute
  - `Ctrl+↑` → Volume up (+10%)
  - `Ctrl+↓` → Volume down (-10%)
  - `P` → Play/pause music
- Prevent shortcuts when typing in inputs/textareas
- Add preventDefault() for browser conflicts
- **Dependencies:** useAudioPlayer (Step 2.2)

**Step 4.2: Implement Keyboard Event Listener**
- Add `keydown` listener in useEffect
- Check if target is HTMLInputElement or HTMLTextAreaElement
- Call preventDefault() for shortcut keys
- Update volume bounds: 0-1 range
- Resume last track on P press or default to 'focus-ambient'
- Cleanup on unmount
- **File:** `src/hooks/useAudioKeyboard.ts`

**Step 4.3: Register Globally in App.tsx**
- Call `useAudioKeyboard()` in App component root
- Pattern: `function App() { useAudioKeyboard(); return <BrowserRouter>...</BrowserRouter>; }`
- **File:** `src/App.tsx` (modify)
- **Dependencies:** useAudioKeyboard (Step 4.1)

**Step 4.4: Add Keyboard Shortcut Hints to Modal**
- Add section to AudioSettingsModal
- List: M (mute), Ctrl+↑/↓ (volume), P (play/pause)
- Styling: muted text, smaller font, visual guide
- **File:** `src/components/AudioSettingsModal.tsx` (enhance)

**Step 4.5: Check for Keyboard Shortcut Conflicts**
- Review `GlobalGamepadHandler` component for conflicts
- Known: M (none), Ctrl+↑/↓ (browser zoom - mitigated), P (none)
- Document findings in CLAUDE.md or plan
- **Discovery Phase:** Need to locate GlobalGamepadHandler
- **Duration:** ~20 min

**Step 4.6: Test Phase 4 Acceptance Criteria**
- M key toggles mute
- Ctrl+↑ increases volume by 10% (5 presses = 50%)
- Ctrl+↓ decreases volume by 10% (5 presses = -50%)
- P key plays/pauses music
- Shortcuts don't fire when typing in inputs
- No conflicts with gamepad controls
- **Test Type:** Manual keyboard interaction
- **Duration:** ~30 min

**Step 4.7: Verify Input Field Protection**
- Focus on input field, press M → verify mute doesn't toggle
- Focus on textarea, press Ctrl+↑ → verify volume doesn't increase
- **Test Type:** Manual edge case testing
- **Duration:** ~10 min

**Step 4.8: Verify Gamepad Compatibility**
- Document any conflicts discovered in Step 4.5
- Test gamepad buttons alongside keyboard shortcuts
- Verify no interference
- **Test Type:** Manual integration testing
- **Duration:** ~15 min

---

### Verification & Documentation Tasks (Steps 6.1-6.10)

**Step 6.1: Code Review**
- Run code review command across all Phase 2-4 files
- Check: TypeScript errors, ESLint violations, style consistency
- Grade: Target = Grade A (0 critical issues)

**Step 6.2-6.4: Quality Gates**
- Fix TypeScript errors
- Remove console.log statements
- Add JSDoc comments to public methods
- Run full test suite (target: 0 failures)

**Step 6.5-6.8: Documentation Updates**
- Update `docs/system-architecture.md` (add audio system section)
- Update `docs/code-standards.md` (add audio patterns)
- Update `README.md` (add audio settings section)
- Update `CHANGELOG.md` (add Phase 2-4 entries)

**Step 6.9-6.10: Cross-Platform Testing**
- iOS Safari autoplay handling (tap banner test)
- Memory usage verification (<50MB after 30-min session)

---

## Ambiguities & Blockers

### Ambiguities (2 identified)

**1. SFX File Sourcing (Step 3.1)**
- **Question:** Programmatic generation (Tone.js Synth) vs. pre-recorded files?
- **Impact:** Medium - affects file management and consistency
- **Recommendation:** Tone.js programmatic preferred (see plan lines 1170-1171: "Use Tone.js Synth for consistency + smaller files")
- **Action:** Proceed with programmatic approach unless overridden

**2. iOS Autoplay Banner Implementation (Potential Phase 5, not in Phase 2-4)**
- **Question:** Show banner on iOS, tap-to-start logic, device detection?
- **Impact:** Low - Phase 5 task, not blocking Phase 2-4
- **Status:** Document in Phase 5 requirements
- **Current Status:** Not in Phase 2-4 scope (Phases 2-4 don't handle iOS-specific UX)

### Blockers (0 critical)

✓ **Phase 1 Complete:** All dependencies ready (AudioManager, types, storage)
✓ **Tone.js Installed:** v15.1.22 already in package.json
✓ **Socket.IO Available:** Existing infrastructure (need to locate event handlers)
✓ **shadcn/ui Available:** Components ready for Modal/Slider/RadioGroup

**Potential Minor Blocker:**
- Socket.IO event handler locations (Step 3.3) - need code discovery
- **Action:** Search codebase for `socket.on('trade:confirmed')` patterns

---

## Dependencies & Workflow Mapping

### Phase 2 → Phase 3 → Phase 4 Sequence

```
Phase 1 ✓ COMPLETE
  ↓
Phase 2 (Steps 2.1-2.8)
  Context + UI Integration
  ↓ (Must complete before Phase 3)
Phase 3 (Steps 3.1-3.8)
  SFX System + Socket.IO
  ↓ (Must complete before Phase 4)
Phase 4 (Steps 4.1-4.8)
  Keyboard Shortcuts
  ↓
Verification (Steps 6.1-6.10)
  Code Review, Testing, Documentation
```

### Critical Dependencies

| Step | Depends On | Status |
|------|-----------|--------|
| 2.1 AudioContext | Phase 1 (audio-manager, types, storage) | ✓ Ready |
| 2.2 useAudioPlayer | Step 2.1 AudioContext | Pending |
| 2.3 AudioSettingsModal | Step 2.2 useAudioPlayer, shadcn/ui | Pending |
| 2.4 SystemHeader Integration | Step 2.3 AudioSettingsModal | Pending |
| 2.5 useSoundEffects | Step 2.2 useAudioPlayer | Pending |
| 2.6 App.tsx Integration | Step 2.1 AudioContext | Pending |
| 3.1 SFX Files | None (external) | Pending |
| 3.2 SFX Emitter | AudioManager (Phase 1) | Pending |
| 3.3 Socket.IO Integration | Step 3.2 SFX Emitter | Pending |
| 3.4 Modal Enhancement | Step 2.3 AudioSettingsModal | Pending |
| 3.5 Tone.Sampler | Step 3.1 SFX Files | Pending |
| 4.1 Keyboard Hook | Step 2.2 useAudioPlayer | Pending |
| 4.3 App.tsx Register | Step 4.1 Keyboard Hook | Pending |

---

## Skills & Tools Required

### Required Skills to Activate

1. **backend-developer** (Optional review)
   - Code quality validation
   - TypeScript best practices
   - Integration patterns

2. **code-reviewer** (Required)
   - Code quality checks (Grade A target)
   - TypeScript validation
   - ESLint compliance

3. **tester** (Required)
   - Manual E2E testing (Phase 2-4 acceptance criteria)
   - Cross-browser testing (Phase 5)
   - Performance profiling (Step 6.10)

4. **debugger** (If needed)
   - Issues during integration or testing
   - Memory leak investigation
   - Browser compatibility debugging

### Required Tools & Libraries

| Tool | Version | Purpose |
|------|---------|---------|
| Tone.js | 15.1.22 | Audio API wrapper |
| React | 18+ | Context, hooks |
| TypeScript | Latest | Type safety |
| shadcn/ui | Latest | UI components |
| lucide-react | Latest | Icons (Volume2) |
| localStorage API | Native | Settings persistence |
| Web Audio API | Native | Audio playback |

---

## Quality Gates & Success Metrics

### Phase 2 Success Criteria (8 items)

- [ ] Settings button visible in header
- [ ] Modal opens/closes smoothly (<200ms)
- [ ] Track selection updates context state
- [ ] Volume sliders adjust audio in real-time
- [ ] Settings persist on "Save" click
- [ ] Music auto-resumes on page refresh
- [ ] localStorage: `audioSettings` key exists with correct data
- [ ] No TypeScript errors or console warnings

### Phase 3 Success Criteria (5 items)

- [ ] SFX plays on trade confirmation (buy/sell different tones)
- [ ] Market alert SFX plays when portfolio health = DANGER
- [ ] Threshold filtering works (e.g., only trades >$100)
- [ ] Debouncing prevents SFX spam (max 1/500ms per type)
- [ ] SFX volume independent from music volume

### Phase 4 Success Criteria (6 items)

- [ ] M key toggles mute
- [ ] Ctrl+↑ increases volume by 10%
- [ ] Ctrl+↓ decreases volume by 10%
- [ ] P key plays/pauses music
- [ ] Shortcuts don't fire when typing in inputs
- [ ] No conflicts with gamepad controls

### Overall Quality Gates

- [ ] Code Review: Grade A (0 critical issues)
- [ ] TypeScript: 0 errors
- [ ] ESLint: 0 errors
- [ ] Test Suite: 0 failures
- [ ] Documentation: 100% complete (4 docs updated)
- [ ] Cross-Browser: Chrome/Firefox/Safari/Edge pass
- [ ] Memory Usage: <50MB after 30-min session

---

## Workflow Command Steps (Steps 1-5)

**Step 1:** Run phase-1-test.mjs to verify Phase 1 completion
**Step 2:** Install Phase 2 dependencies and verify Tone.js (already installed)
**Step 3:** Review existing Phase 1 artifacts (audio-manager.ts, audio.ts, audio-storage.ts)
**Step 4:** Validate Socket.IO integration requirements for Phase 3
**Step 5:** Plan workflow execution sequence (Phase 2 → Phase 3 → Phase 4 with integrated testing)

---

## Estimated Timeline

| Phase | Effort | Est. Duration | Start Date | End Date |
|-------|--------|---------------|-----------|----------|
| Phase 2 | 16 hours | 2 days | 2026-01-01 | 2026-01-02 |
| Phase 3 | 18 hours | 2-3 days | 2026-01-02 | 2026-01-04 |
| Phase 4 | 12 hours | 1-2 days | 2026-01-04 | 2026-01-05 |
| Verification | 8 hours | 1 day | 2026-01-05 | 2026-01-05 |
| **Total** | **54 hours** | **5-6 days** | 2026-01-01 | 2026-01-05 |

---

## Summary Statistics

- **Total Tasks Extracted:** 33 (Phase 2: 8 + Phase 3: 8 + Phase 4: 8 + Verification: 9)
- **Workflow Steps:** 5 (pre-phase planning)
- **Critical Path Items:** 12 (sequential dependencies)
- **Parallel Tasks:** 0 (all tasks sequential due to dependencies)
- **Ambiguities Identified:** 2 (SFX sourcing, iOS banner)
- **Blockers:** None critical
- **Code Quality Target:** Grade A (0 critical issues)
- **Test Coverage Target:** 100% acceptance criteria passed

---

## Unresolved Questions

1. **SFX Generation Approach:** Should Step 3.1 use Tone.js Synth (programmatic) or pre-recorded files from FreeSound? (Plan suggests Synth - recommend confirming)
2. **Socket.IO Event Handler Locations:** Where are existing event handlers located? Need to search codebase for `socket.on('trade:confirmed')`, `socket.on('advisor:portfolio_result')` patterns.
3. **GlobalGamepadHandler Location:** Where is this component? Needed for Step 4.5 conflict check.
4. **Phase 5 Scope:** Are iOS autoplay restrictions (banner/tap-to-start) in Phase 5 or Phase 2-4 scope?
5. **Testing Environment:** Should Phase 3 testing use mock Socket.IO events or actual trading events? Recommend mocks for deterministic testing.

---

**Report Generated:** 2026-01-01 11:35
**Status:** ✓ Complete - Ready for Phase 2-4 Implementation
**Next Action:** Execute Step 1 (Phase 1 verification) then proceed with Phase 2 tasks
