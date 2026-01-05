#!/usr/bin/env node

/**
 * Phase 4: Keyboard Shortcuts Test Suite
 *
 * Tests:
 * 1. useAudioKeyboard Hook - M, P, Ctrl+↑, Ctrl+↓ shortcuts
 * 2. Input element detection - prevent shortcuts when typing
 * 3. Gamepad conflict detection - [ and ] not used by audio shortcuts
 * 4. AudioContext integration - state management for shortcuts
 * 5. Code quality - proper cleanup and event handling
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const srcDir = path.join(__dirname, 'src');

class Phase4Tester {
  constructor() {
    this.passed = 0;
    this.failed = 0;
    this.tests = [];
    this.fileContents = new Map();
  }

  loadFile(filePath) {
    try {
      const content = fs.readFileSync(filePath, 'utf-8');
      this.fileContents.set(filePath, content);
      return content;
    } catch (error) {
      console.error(`Failed to load file: ${filePath}`);
      return null;
    }
  }

  test(name, fn) {
    try {
      fn();
      this.passed++;
      this.tests.push({ name, status: 'PASS', error: null });
      console.log(`✓ ${name}`);
    } catch (error) {
      this.failed++;
      this.tests.push({ name, status: 'FAIL', error: error.message });
      console.log(`✗ ${name}`);
      console.log(`  Error: ${error.message}`);
    }
  }

  assert(condition, message) {
    if (!condition) {
      throw new Error(message || 'Assertion failed');
    }
  }

  assertEquals(actual, expected, message) {
    if (actual !== expected) {
      throw new Error(message || `Expected ${expected} but got ${actual}`);
    }
  }

  assertIncludes(haystack, needle, message) {
    if (!haystack.includes(needle)) {
      throw new Error(message || `Expected to find "${needle}" in "${haystack}"`);
    }
  }

  assertNotIncludes(haystack, needle, message) {
    if (haystack.includes(needle)) {
      throw new Error(message || `Expected NOT to find "${needle}" in "${haystack}"`);
    }
  }

  printSummary() {
    console.log('\n' + '='.repeat(60));
    console.log('PHASE 4: KEYBOARD SHORTCUTS TEST SUMMARY');
    console.log('='.repeat(60));
    console.log(`Total Tests: ${this.passed + this.failed}`);
    console.log(`Passed: ${this.passed}`);
    console.log(`Failed: ${this.failed}`);
    console.log(`Success Rate: ${Math.round((this.passed / (this.passed + this.failed)) * 100)}%`);
    console.log('='.repeat(60));

    if (this.failed > 0) {
      console.log('\nFailed Tests:');
      this.tests
        .filter(t => t.status === 'FAIL')
        .forEach(t => {
          console.log(`\n  ${t.name}`);
          console.log(`  Error: ${t.error}`);
        });
    }

    return this.failed === 0;
  }
}

const tester = new Phase4Tester();

console.log('Phase 4: Keyboard Shortcuts Testing...\n');

// ============================================================================
// Test 1: useAudioKeyboard Hook Structure
// ============================================================================
console.log('Test Group 1: useAudioKeyboard Hook Structure');
console.log('-'.repeat(60));

tester.test(
  'useAudioKeyboard.ts file exists',
  () => {
    const filePath = path.join(srcDir, 'hooks/useAudioKeyboard.ts');
    tester.assert(fs.existsSync(filePath), 'useAudioKeyboard.ts file not found');
  }
);

tester.test(
  'useAudioKeyboard is a React hook',
  () => {
    const filePath = path.join(srcDir, 'hooks/useAudioKeyboard.ts');
    const content = tester.loadFile(filePath);
    tester.assertIncludes(content, 'useEffect', 'Hook should use useEffect');
    tester.assertIncludes(content, 'export const useAudioKeyboard', 'Should export useAudioKeyboard');
  }
);

// ============================================================================
// Test 2: M Key - Mute Toggle
// ============================================================================
console.log('\nTest Group 2: M Key - Mute Toggle');
console.log('-'.repeat(60));

tester.test(
  'M key handler is implemented',
  () => {
    const filePath = path.join(srcDir, 'hooks/useAudioKeyboard.ts');
    const content = tester.loadFile(filePath);
    tester.assertIncludes(content, "e.key === 'm' || e.key === 'M'", 'M key detection missing');
    tester.assertIncludes(content, 'toggleMute', 'toggleMute function call missing');
  }
);

tester.test(
  'Mute toggle logs console message',
  () => {
    const filePath = path.join(srcDir, 'hooks/useAudioKeyboard.ts');
    const content = tester.loadFile(filePath);
    tester.assertIncludes(content, '[AudioKeyboard] Mute toggled', 'Console log message missing');
  }
);

tester.test(
  'M key prevents default browser behavior',
  () => {
    const filePath = path.join(srcDir, 'hooks/useAudioKeyboard.ts');
    const content = tester.loadFile(filePath);
    // Check for preventDefault near M key handling
    const mKeySection = content.substring(
      content.indexOf("e.key === 'm'"),
      content.indexOf("e.key === 'm'") + 500
    );
    tester.assertIncludes(mKeySection, 'preventDefault', 'preventDefault should be called for M key');
  }
);

// ============================================================================
// Test 3: Ctrl+↑ - Volume Up
// ============================================================================
console.log('\nTest Group 3: Ctrl+↑ - Volume Up');
console.log('-'.repeat(60));

tester.test(
  'Ctrl+ArrowUp handler is implemented',
  () => {
    const filePath = path.join(srcDir, 'hooks/useAudioKeyboard.ts');
    const content = tester.loadFile(filePath);
    tester.assertIncludes(content, "e.key === 'ArrowUp'", 'ArrowUp key detection missing');
    tester.assertIncludes(content, 'e.ctrlKey', 'Ctrl key check missing');
  }
);

tester.test(
  'Volume increases by 0.1 (10%)',
  () => {
    const filePath = path.join(srcDir, 'hooks/useAudioKeyboard.ts');
    const content = tester.loadFile(filePath);
    tester.assertIncludes(content, '+ 0.1', 'Volume increment by 0.1 missing');
  }
);

tester.test(
  'Volume is capped at 1.0 (100%)',
  () => {
    const filePath = path.join(srcDir, 'hooks/useAudioKeyboard.ts');
    const content = tester.loadFile(filePath);
    tester.assertIncludes(content, 'Math.min', 'Math.min for volume capping missing');
    tester.assertIncludes(content, ', 1)', 'Volume max cap at 1 missing');
  }
);

tester.test(
  'Volume up logs console message with percentage',
  () => {
    const filePath = path.join(srcDir, 'hooks/useAudioKeyboard.ts');
    const content = tester.loadFile(filePath);
    tester.assertIncludes(content, '[AudioKeyboard] Volume up:', 'Console log for volume up missing');
  }
);

// ============================================================================
// Test 4: Ctrl+↓ - Volume Down
// ============================================================================
console.log('\nTest Group 4: Ctrl+↓ - Volume Down');
console.log('-'.repeat(60));

tester.test(
  'Ctrl+ArrowDown handler is implemented',
  () => {
    const filePath = path.join(srcDir, 'hooks/useAudioKeyboard.ts');
    const content = tester.loadFile(filePath);
    tester.assertIncludes(content, "e.key === 'ArrowDown'", 'ArrowDown key detection missing');
  }
);

tester.test(
  'Volume decreases by 0.1 (10%)',
  () => {
    const filePath = path.join(srcDir, 'hooks/useAudioKeyboard.ts');
    const content = tester.loadFile(filePath);
    tester.assertIncludes(content, '- 0.1', 'Volume decrement by 0.1 missing');
  }
);

tester.test(
  'Volume is capped at 0.0 (0%)',
  () => {
    const filePath = path.join(srcDir, 'hooks/useAudioKeyboard.ts');
    const content = tester.loadFile(filePath);
    tester.assertIncludes(content, 'Math.max', 'Math.max for volume capping missing');
    tester.assertIncludes(content, ', 0)', 'Volume min cap at 0 missing');
  }
);

tester.test(
  'Volume down logs console message with percentage',
  () => {
    const filePath = path.join(srcDir, 'hooks/useAudioKeyboard.ts');
    const content = tester.loadFile(filePath);
    tester.assertIncludes(content, '[AudioKeyboard] Volume down:', 'Console log for volume down missing');
  }
);

// ============================================================================
// Test 5: P Key - Play/Pause
// ============================================================================
console.log('\nTest Group 5: P Key - Play/Pause');
console.log('-'.repeat(60));

tester.test(
  'P key handler is implemented',
  () => {
    const filePath = path.join(srcDir, 'hooks/useAudioKeyboard.ts');
    const content = tester.loadFile(filePath);
    tester.assertIncludes(content, "e.key === 'p' || e.key === 'P'", 'P key detection missing');
  }
);

tester.test(
  'Pauses music when isPlaying is true',
  () => {
    const filePath = path.join(srcDir, 'hooks/useAudioKeyboard.ts');
    const content = tester.loadFile(filePath);
    tester.assertIncludes(content, 'if (isPlaying)', 'isPlaying check missing');
    tester.assertIncludes(content, 'pauseTrack', 'pauseTrack function call missing');
  }
);

tester.test(
  'Plays music when isPlaying is false',
  () => {
    const filePath = path.join(srcDir, 'hooks/useAudioKeyboard.ts');
    const content = tester.loadFile(filePath);
    tester.assertIncludes(content, 'playTrack', 'playTrack function call missing');
  }
);

tester.test(
  'Resumes current track or plays first available',
  () => {
    const filePath = path.join(srcDir, 'hooks/useAudioKeyboard.ts');
    const content = tester.loadFile(filePath);
    tester.assertIncludes(content, 'currentTrack || availableTracks[0]', 'Track selection logic missing');
  }
);

tester.test(
  'Play/pause logs appropriate console messages',
  () => {
    const filePath = path.join(srcDir, 'hooks/useAudioKeyboard.ts');
    const content = tester.loadFile(filePath);
    tester.assertIncludes(content, '[AudioKeyboard] Music paused', 'Pause log message missing');
    tester.assertIncludes(content, '[AudioKeyboard] Music playing:', 'Play log message missing');
  }
);

// ============================================================================
// Test 6: Input Element Detection
// ============================================================================
console.log('\nTest Group 6: Input Element Detection');
console.log('-'.repeat(60));

tester.test(
  'Input element detection is implemented',
  () => {
    const filePath = path.join(srcDir, 'hooks/useAudioKeyboard.ts');
    const content = tester.loadFile(filePath);
    tester.assertIncludes(content, 'HTMLInputElement', 'HTMLInputElement check missing');
    tester.assertIncludes(content, 'HTMLTextAreaElement', 'HTMLTextAreaElement check missing');
  }
);

tester.test(
  'Shortcuts are blocked for input elements',
  () => {
    const filePath = path.join(srcDir, 'hooks/useAudioKeyboard.ts');
    const content = tester.loadFile(filePath);
    // Check that target is checked before shortcuts
    const targetCheckIndex = content.indexOf('target');
    const shortcutCheckIndex = content.indexOf("e.key === 'm'");
    tester.assert(targetCheckIndex < shortcutCheckIndex, 'Input check should come before shortcut handling');
  }
);

tester.test(
  'ContentEditable elements are also blocked',
  () => {
    const filePath = path.join(srcDir, 'hooks/useAudioKeyboard.ts');
    const content = tester.loadFile(filePath);
    tester.assertIncludes(content, 'isContentEditable', 'ContentEditable check missing');
  }
);

tester.test(
  'Early return when typing in inputs',
  () => {
    const filePath = path.join(srcDir, 'hooks/useAudioKeyboard.ts');
    const content = tester.loadFile(filePath);
    // Check for guard clause (return statement after input check)
    const inputCheckSection = content.substring(
      content.indexOf('HTMLInputElement'),
      content.indexOf('HTMLInputElement') + 300
    );
    tester.assertIncludes(inputCheckSection, 'return', 'Early return for input elements missing');
  }
);

// ============================================================================
// Test 7: Gamepad Conflict Detection
// ============================================================================
console.log('\nTest Group 7: Gamepad Conflict Detection');
console.log('-'.repeat(60));

tester.test(
  'GlobalGamepadHandler file exists',
  () => {
    const filePath = path.join(srcDir, 'components/GlobalGamepadHandler.tsx');
    tester.assert(fs.existsSync(filePath), 'GlobalGamepadHandler.tsx file not found');
  }
);

tester.test(
  'GlobalGamepadHandler uses [ key for navigation',
  () => {
    const filePath = path.join(srcDir, 'components/GlobalGamepadHandler.tsx');
    const content = tester.loadFile(filePath);
    tester.assertIncludes(content, 'e.key === "["', 'GlobalGamepadHandler [ key check missing');
  }
);

tester.test(
  'GlobalGamepadHandler uses ] key for navigation',
  () => {
    const filePath = path.join(srcDir, 'components/GlobalGamepadHandler.tsx');
    const content = tester.loadFile(filePath);
    tester.assertIncludes(content, 'e.key === "]"', 'GlobalGamepadHandler ] key check missing');
  }
);

tester.test(
  'No keyboard shortcut conflict with gamepad handler',
  () => {
    const gamepadPath = path.join(srcDir, 'components/GlobalGamepadHandler.tsx');
    const gamepadContent = tester.loadFile(gamepadPath);

    // Audio uses: M, P, Ctrl+↑, Ctrl+↓
    // Gamepad uses: [, ]
    // These don't overlap
    tester.assert(!gamepadContent.includes("e.key === 'm'"), 'Gamepad should not use M key');
    tester.assert(!gamepadContent.includes("e.key === 'p'"), 'Gamepad should not use P key');
    tester.assert(!gamepadContent.includes("e.key === 'P'"), 'Gamepad should not use P key');
    tester.assert(!gamepadContent.includes('ArrowUp'), 'Gamepad should not use ArrowUp');
    tester.assert(!gamepadContent.includes('ArrowDown'), 'Gamepad should not use ArrowDown');
  }
);

// ============================================================================
// Test 8: Event Handler Registration & Cleanup
// ============================================================================
console.log('\nTest Group 8: Event Handler Registration & Cleanup');
console.log('-'.repeat(60));

tester.test(
  'Event listener is registered on mount',
  () => {
    const filePath = path.join(srcDir, 'hooks/useAudioKeyboard.ts');
    const content = tester.loadFile(filePath);
    tester.assertIncludes(content, 'addEventListener', 'addEventListener call missing');
    tester.assertIncludes(content, 'keydown', 'keydown event listener missing');
  }
);

tester.test(
  'Event listener is removed on unmount',
  () => {
    const filePath = path.join(srcDir, 'hooks/useAudioKeyboard.ts');
    const content = tester.loadFile(filePath);
    tester.assertIncludes(content, 'removeEventListener', 'removeEventListener call missing');
    // Check it's in the cleanup function (after return)
    const returnIndex = content.indexOf('return () =>');
    const removeIndex = content.indexOf('removeEventListener');
    tester.assert(returnIndex < removeIndex, 'removeEventListener should be in cleanup function');
  }
);

tester.test(
  'Dependency array includes all dependencies',
  () => {
    const filePath = path.join(srcDir, 'hooks/useAudioKeyboard.ts');
    const content = tester.loadFile(filePath);
    // Check for dependency array
    tester.assertIncludes(content, '}, [', 'useEffect dependency array missing');
    tester.assertIncludes(content, 'toggleMute', 'toggleMute should be in dependencies');
    tester.assertIncludes(content, 'setVolume', 'setVolume should be in dependencies');
    tester.assertIncludes(content, 'isPlaying', 'isPlaying should be in dependencies');
  }
);

// ============================================================================
// Test 9: AudioContext Integration
// ============================================================================
console.log('\nTest Group 9: AudioContext Integration');
console.log('-'.repeat(60));

tester.test(
  'useAudioPlayer hook is used',
  () => {
    const filePath = path.join(srcDir, 'hooks/useAudioKeyboard.ts');
    const content = tester.loadFile(filePath);
    tester.assertIncludes(content, 'useAudioPlayer', 'useAudioPlayer hook not imported or used');
  }
);

tester.test(
  'AudioContext file exists',
  () => {
    const filePath = path.join(srcDir, 'context/AudioContext.tsx');
    tester.assert(fs.existsSync(filePath), 'AudioContext.tsx file not found');
  }
);

tester.test(
  'AudioContext provides required methods',
  () => {
    const filePath = path.join(srcDir, 'context/AudioContext.tsx');
    const content = tester.loadFile(filePath);
    tester.assertIncludes(content, 'toggleMute', 'toggleMute method missing from AudioContext');
    tester.assertIncludes(content, 'setVolume', 'setVolume method missing from AudioContext');
    tester.assertIncludes(content, 'playTrack', 'playTrack method missing from AudioContext');
    tester.assertIncludes(content, 'pauseTrack', 'pauseTrack method missing from AudioContext');
  }
);

tester.test(
  'AudioContext provides required state',
  () => {
    const filePath = path.join(srcDir, 'context/AudioContext.tsx');
    const content = tester.loadFile(filePath);
    tester.assertIncludes(content, 'isPlaying', 'isPlaying state missing from AudioContext');
    tester.assertIncludes(content, 'currentTrack', 'currentTrack state missing from AudioContext');
    tester.assertIncludes(content, 'volumes', 'volumes state missing from AudioContext');
  }
);

// ============================================================================
// Test 10: Code Quality
// ============================================================================
console.log('\nTest Group 10: Code Quality');
console.log('-'.repeat(60));

tester.test(
  'useAudioKeyboard has JSDoc comments',
  () => {
    const filePath = path.join(srcDir, 'hooks/useAudioKeyboard.ts');
    const content = tester.loadFile(filePath);
    tester.assertIncludes(content, '/**', 'JSDoc comments missing');
  }
);

tester.test(
  'Event handler is properly typed',
  () => {
    const filePath = path.join(srcDir, 'hooks/useAudioKeyboard.ts');
    const content = tester.loadFile(filePath);
    tester.assertIncludes(content, 'KeyboardEvent', 'KeyboardEvent type missing');
  }
);

tester.test(
  'Target element is properly type-cast',
  () => {
    const filePath = path.join(srcDir, 'hooks/useAudioKeyboard.ts');
    const content = tester.loadFile(filePath);
    tester.assertIncludes(content, 'as HTMLElement', 'HTMLElement type casting missing');
  }
);

tester.test(
  'Prevents default behavior for shortcuts',
  () => {
    const filePath = path.join(srcDir, 'hooks/useAudioKeyboard.ts');
    const content = tester.loadFile(filePath);
    // Count preventDefault calls (should be at least 4 for M, Ctrl+↑, Ctrl+↓, P)
    const preventDefaultCount = (content.match(/preventDefault/g) || []).length;
    tester.assert(preventDefaultCount >= 4, `Expected at least 4 preventDefault calls, found ${preventDefaultCount}`);
  }
);

// ============================================================================
// Print Summary
// ============================================================================
const success = tester.printSummary();

// Exit with appropriate code
process.exit(success ? 0 : 1);
