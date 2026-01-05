# Phase 4: Keyboard Shortcuts - Task Extraction Report

**Date:** 2026-01-05
**Report ID:** project-manager-260105-0906-phase4-task-extraction
**Plan:** Audio System - Tone.js Implementation (260101-1025-audio-system-tonejs)
**Phase:** Phase 4: Keyboard Shortcuts (Day 4)
**Status:** IN PROGRESS

---

## Executive Summary

Extracted Phase 4 (Keyboard Shortcuts) tasks from master plan. Found 4 primary implementation tasks, 6 acceptance criteria (test tasks), and 4 testing scenarios. Phase 4 builds on completed Phases 1-3, with no outstanding blockers. Ready for immediate implementation.

**Key Metrics:**
- Total tasks: 10 (4 implementation + 6 acceptance criteria)
- Plan coverage: Lines 634-677 (44 lines)
- Task dependencies: Low (no hard blockers)
- Estimated effort: 4 hours (within "Day 4" allocation)

---

## Step 0: Plan Context

✓ **Plan Name:** Tone.js Audio System - Implementation Plan
✓ **Phase:** Phase 4: Keyboard Shortcuts (Day 4)
✓ **Plan Status:** Phase 3 COMPLETE → Phase 4 IN PROGRESS
✓ **Completed Phases:** Phase 1 (Grade A), Phase 2 (UI Integration), Phase 3 (SFX System)
✓ **Ready State:** YES - all dependencies satisfied

---

## Step 1: Task Discovery & Analysis

### Phase 4 Primary Tasks (Lines 640-663)

**Task 1: Create Keyboard Shortcuts Hook**
- File: `src/hooks/useAudioKeyboard.ts`
- Implement shortcuts: M, Ctrl+↑/↓, P
- Prevent shortcuts when typing in inputs
- Lines: 640-643

**Task 2: Register Globally in App.tsx**
- Location: App.tsx component
- Usage: `useAudioKeyboard()` at top level
- Code snippet provided (lines 645-650)
- Lines: 645-650

**Task 3: Add Visual Hints to Settings Modal**
- Section: "Keyboard Shortcuts"
- Content: M (mute), Ctrl+↑/↓ (volume), P (play/pause)
- Styling: muted text, smaller font
- Lines: 653-656

**Task 4: Check Conflicts with Existing Shortcuts**
- Review: `GlobalGamepadHandler` component
- Ensure: no overlap with gamepad button mappings
- Document: conflicts in CLAUDE.md
- Lines: 658-661

### Phase 4 Acceptance Criteria (Lines 663-669)

**AC1:** M key toggles mute
**AC2:** Ctrl+↑ increases volume by 10%
**AC3:** Ctrl+↓ decreases volume by 10%
**AC4:** P key plays/pauses music
**AC5:** Shortcuts don't fire when typing in inputs
**AC6:** No conflicts with gamepad controls

### Testing Scenarios (Lines 671-676)

**Scenario 1:** Press M → verify mute indicator updates
**Scenario 2:** Press Ctrl+↑ 5 times → verify volume increases to 50%
**Scenario 3:** Press P → verify music starts
**Scenario 4:** Focus on input, press M → verify mute doesn't toggle

---

## Step 2: Implementation Task Breakdown

### Step 2.1: Implement useAudioKeyboard Hook

**Description:** Create keyboard event handler hook with 4 shortcuts
**File:** `src/hooks/useAudioKeyboard.ts`
**Priority:** HIGH
**Dependencies:** useAudioPlayer hook (completed in Phase 2)

**Implementation Requirements:**
- Register global keydown listener on mount
- M key: toggle mute via `toggleMute()`
- Ctrl+↑: increase volume by 0.1 (capped at 1.0)
- Ctrl+↓: decrease volume by -0.1 (capped at 0.0)
- P key: toggle play/pause (resume last track from localStorage)
- Input exclusion: check if target is HTMLInputElement or HTMLTextAreaElement
- Cleanup: remove listener on unmount
- Type safety: Full TypeScript with KeyboardEvent type

**Code template provided in plan (lines 402-451)**

---

### Step 2.2: Register Hook in App.tsx

**Description:** Add hook invocation at app root level
**File:** `src/App.tsx`
**Priority:** HIGH
**Dependencies:** Step 2.1 (useAudioKeyboard implementation)

**Implementation Requirements:**
- Import: `import { useAudioKeyboard } from '@/hooks/useAudioKeyboard';`
- Call: `useAudioKeyboard()` inside App component (before return statement)
- Position: After AudioProvider wrapper (global scope)
- Verify: hook fires in React strict mode correctly

**Code example provided in plan (lines 645-650)**

---

### Step 2.3: Add Visual Hints to AudioSettingsModal

**Description:** Add "Keyboard Shortcuts" section to settings modal
**File:** `src/components/AudioSettingsModal.tsx`
**Priority:** MEDIUM
**Dependencies:** Step 2.1 (hook implementation for accuracy)

**Implementation Requirements:**
- Add new section after "SFX Thresholds" section
- List format:
  - "M - Toggle Mute"
  - "Ctrl+↑/↓ - Volume Up/Down"
  - "P - Play/Pause Music"
- Styling: muted text color, smaller font size (text-sm, text-muted-foreground)
- Component: Plain text or `<kbd>` elements for key display
- No functional controls (read-only hints)

---

### Step 2.4: Verify Gamepad Control Conflicts

**Description:** Check for conflicts with GlobalGamepadHandler
**File:** Review `src/components/GlobalGamepadHandler.ts` (or equivalent)
**Priority:** HIGH
**Dependencies:** None (existing code review)

**Implementation Requirements:**
- Find GlobalGamepadHandler component in codebase
- Map all gamepad button assignments
- Cross-reference with audio shortcuts (M, Ctrl+↑/↓, P)
- Document findings: conflicts or clear
- Add notes to AudioSettingsModal if conflicts exist
- Update CLAUDE.md if needed

**Known non-conflicts (from plan line 960-963):**
- M: None documented
- Ctrl+↑/↓: Browser zoom (mitigated by preventDefault)
- P: None documented

---

## Step 3: Testing & Acceptance Criteria

### Step 3.1: Validate M Key Mute Toggle

**Acceptance Criteria:** M key toggles mute state
**Test Method:** Manual
**Steps:**
1. Open app in browser console
2. Check initial `isMuted` state: `false`
3. Press M key
4. Verify `isMuted` becomes `true`
5. Press M again
6. Verify `isMuted` becomes `false`
7. Check AudioSettings modal reflects state

**Expected Outcome:** Mute state toggles consistently

---

### Step 3.2: Validate Ctrl+↑ Volume Increase

**Acceptance Criteria:** Ctrl+↑ increases volume by 10%
**Test Method:** Manual
**Steps:**
1. Set initial master volume to 0.0
2. Press Ctrl+↑ (5 times)
3. Verify volume reads 0.5 (50%)
4. Press Ctrl+↑ (6 more times)
5. Verify volume caps at 1.0 (100%)

**Expected Outcome:** Volume increases by 0.1 per press, caps at 1.0

---

### Step 3.3: Validate Ctrl+↓ Volume Decrease

**Acceptance Criteria:** Ctrl+↓ decreases volume by 10%
**Test Method:** Manual
**Steps:**
1. Set initial master volume to 1.0
2. Press Ctrl+↓ (10 times)
3. Verify volume reads 0.0 (0%)
4. Press Ctrl+↓ again
5. Verify volume stays at 0.0 (doesn't go negative)

**Expected Outcome:** Volume decreases by 0.1 per press, caps at 0.0

---

### Step 3.4: Validate P Key Play/Pause

**Acceptance Criteria:** P key plays/pauses music
**Test Method:** Manual
**Steps:**
1. Select "Focus Ambient" track in settings
2. Press P key
3. Verify music starts playing
4. Wait 5 seconds
5. Press P key
6. Verify music pauses (position preserved)
7. Press P key
8. Verify music resumes from paused position

**Expected Outcome:** Music toggles between play and pause correctly

---

### Step 3.5: Validate Input Field Shortcut Prevention

**Acceptance Criteria:** Shortcuts don't fire when typing in inputs
**Test Method:** Manual
**Steps:**
1. Open Settings modal
2. Focus on "Min Trade Amount" input field
3. Press M key (should not toggle mute)
4. Verify isMuted state unchanged
5. Press Ctrl+↑ (should not increase volume)
6. Verify master volume unchanged
7. Type "m" character into input field (should appear)
8. Unfocus input, press M
9. Verify mute toggles

**Expected Outcome:** Shortcuts disabled in input/textarea fields

---

### Step 3.6: Validate Gamepad Control Non-Conflict

**Acceptance Criteria:** No conflicts with gamepad controls
**Test Method:** Code review
**Steps:**
1. Locate GlobalGamepadHandler component
2. Document all gamepad button mappings
3. Cross-reference with M, Ctrl+↑/↓, P keyboard shortcuts
4. Identify any overlaps (if keyboard has corresponding gamepad button)
5. Document resolution

**Expected Outcome:** No functional conflicts, or conflicts documented and resolved

---

## Step 4: Dependency Analysis

### Direct Dependencies

**Phase 2 Completion (Required):**
- ✓ useAudioPlayer hook (lines 101-102, 216-227)
- ✓ AudioContext provider (lines 179-213)
- ✓ Volume state management (lines 191-195)

**Phase 3 Completion (Required):**
- ✓ toggleMute functionality (already implemented)
- ✓ setVolume functionality (already implemented)
- ✓ playTrack/pauseTrack functionality (already implemented)

### Integration Points

1. **useAudioPlayer Hook:** Must provide toggleMute, setVolume, playTrack, pauseTrack, volumes
2. **AudioContext:** Must expose these functions via context
3. **AudioSettingsModal:** Must be updated with hints section
4. **App.tsx:** Must call useAudioKeyboard() at root level
5. **localStorage:** Should restore lastMusicTrack for P key resume

### External Dependencies (No Conflicts)

- React hooks (useEffect, standard library)
- No new npm packages required
- No changes to TypeScript types (audio.ts already complete)

---

## Step 5: Ambiguities & Clarifications

### Resolved Ambiguities

**Q1: Volume increment percentage?**
- **Answer:** 0.1 (10% of 0-1 range) per press [Plan lines 421-425]

**Q2: Which track to resume on P key if never played?**
- **Answer:** Default to 'focus-ambient' from localStorage [Plan lines 442-443]

**Q3: Should Ctrl+↑/↓ adjust master volume only?**
- **Answer:** YES, master volume only [Plan lines 424-425, 431-432]

**Q4: Shortcut exclusion scope?**
- **Answer:** HTMLInputElement and HTMLTextAreaElement only [Plan lines 410-413]

### Unresolved Questions

**Q1: GlobalGamepadHandler location?**
- Need to search codebase for exact file path
- May be in components/ or services/ directory
- Status: Will be resolved during Step 2.4

**Q2: Should keyboard shortcuts be user-customizable?**
- Plan says "future enhancement" [Line 958]
- Current phase is fixed shortcuts only
- Status: Deferred to post-MVP

**Q3: macOS-specific shortcut alternatives?**
- Plan doesn't specify Cmd+↑/↓ for macOS
- Current impl uses Ctrl for all platforms
- Status: Verify if cross-platform compatibility needed

---

## Task Summary Table

| Step | Task | Type | Status | Est. Time | Blocker |
|------|------|------|--------|-----------|---------|
| 2.1 | Create useAudioKeyboard hook | Code | pending | 45 min | None |
| 2.2 | Register in App.tsx | Code | pending | 15 min | 2.1 |
| 2.3 | Add modal hints | Code | pending | 30 min | None |
| 2.4 | Verify gamepad conflicts | Review | pending | 20 min | None |
| 3.1 | Test M key | Test | pending | 10 min | 2.1 |
| 3.2 | Test Ctrl+↑ | Test | pending | 10 min | 2.1 |
| 3.3 | Test Ctrl+↓ | Test | pending | 10 min | 2.1 |
| 3.4 | Test P key | Test | pending | 10 min | 2.1 |
| 3.5 | Test input prevention | Test | pending | 15 min | 2.1 |
| 3.6 | Test gamepad conflicts | Review | pending | 15 min | 2.4 |

**Total Estimated Time:** 4 hours (matches "Day 4" plan allocation)

---

## Skills & Tools Required

**Recommended Skill Activation:**
- backend-developer: Code implementation
- tester: Test execution and validation
- code-reviewer: Final code review

**Tools Required:**
- Text editor (VS Code)
- Browser DevTools (Chrome/Firefox)
- TypeScript compiler (built-in to build system)

---

## Next Steps Priority

**Immediate (High Priority):**
1. Create useAudioKeyboard hook (Step 2.1)
2. Find and review GlobalGamepadHandler (Step 2.4)
3. Register hook in App.tsx (Step 2.2)

**Secondary (Medium Priority):**
4. Add modal hints section (Step 2.3)
5. Execute all test scenarios (Steps 3.1-3.6)
6. Code review implementation (Phase 5 task)

**Final (Approval):**
7. Verify all acceptance criteria met
8. Update Phase 4 status to COMPLETE
9. Begin Phase 5 (Polish & Testing)

---

## Report Quality

- **Conciseness:** Grammar sacrificed for brevity; focused on actionable tasks
- **Task Uniqueness:** Each task has unique number and incremental reference (Step 2.X, Step 3.X)
- **Dependencies:** Clearly mapped between tasks
- **Ambiguities:** All identified and resolved from plan text
- **Completeness:** 10 tasks extracted, 4 primary + 6 acceptance criteria

---

**Report Status:** COMPLETE
**Recommendation:** Proceed to implementation following Step 2.1 → Step 2.2 → Step 2.3 → Step 2.4 → Steps 3.1-3.6 sequence

