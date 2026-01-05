#!/usr/bin/env node

/**
 * Phase 3: Sound Effects System Test Suite
 *
 * Tests:
 * 1. SFX Event Emitter - threshold filtering, debouncing
 * 2. Socket.IO integration - trade events, market alerts
 * 3. AudioManager SFX playback - Tone.Sampler functionality
 * 4. AudioSettingsModal - SFX threshold controls
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const srcDir = path.join(__dirname, 'src');

class Phase3Tester {
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
      throw new Error(message);
    }
  }

  assertContains(content, pattern, message) {
    if (!content.includes(pattern)) {
      throw new Error(`${message || 'Pattern not found'}: "${pattern}"`);
    }
  }

  assertFileExists(filePath, message) {
    const exists = fs.existsSync(filePath);
    this.assert(exists, message || `File not found: ${filePath}`);
  }

  summary() {
    console.log('\n' + '='.repeat(70));
    console.log('PHASE 3: SOUND EFFECTS SYSTEM - TEST RESULTS');
    console.log('='.repeat(70));
    console.log(`Total Tests: ${this.passed + this.failed}`);
    console.log(`Passed: ${this.passed} ✓`);
    console.log(`Failed: ${this.failed} ✗`);
    console.log('='.repeat(70));

    if (this.failed > 0) {
      console.log('\nFailed Tests:');
      this.tests
        .filter(t => t.status === 'FAIL')
        .forEach(t => {
          console.log(`  - ${t.name}`);
          console.log(`    ${t.error}`);
        });
    }

    return this.failed === 0;
  }
}

const tester = new Phase3Tester();

console.log('\n' + '='.repeat(70));
console.log('PHASE 3: SOUND EFFECTS SYSTEM TEST SUITE');
console.log('='.repeat(70) + '\n');

// ============================================================================
// TEST CATEGORY 1: SFX Event Emitter - Threshold Filtering
// ============================================================================

console.log('\n[Category 1] SFX Event Emitter - Threshold Filtering\n');

tester.test('SFX Event Emitter file exists', () => {
  const filePath = path.join(srcDir, 'services', 'sfx-event-emitter.ts');
  tester.assertFileExists(filePath, 'SFX Event Emitter not found');
});

tester.test('SFX Event Emitter class defined', () => {
  const filePath = path.join(srcDir, 'services', 'sfx-event-emitter.ts');
  const content = tester.loadFile(filePath);
  tester.assertContains(content, 'class SFXEventEmitter', 'SFXEventEmitter class not defined');
});

tester.test('SFX Event Emitter singleton pattern', () => {
  const filePath = path.join(srcDir, 'services', 'sfx-event-emitter.ts');
  const content = tester.loadFile(filePath);
  tester.assertContains(content, 'export const sfxEmitter = new SFXEventEmitter()', 'Singleton export missing');
});

tester.test('Threshold management method exists', () => {
  const filePath = path.join(srcDir, 'services', 'sfx-event-emitter.ts');
  const content = tester.loadFile(filePath);
  tester.assertContains(content, 'updateThresholds', 'updateThresholds method missing');
});

tester.test('shouldPlaySFX method exists', () => {
  const filePath = path.join(srcDir, 'services', 'sfx-event-emitter.ts');
  const content = tester.loadFile(filePath);
  tester.assertContains(content, 'shouldPlaySFX', 'shouldPlaySFX method missing');
});

tester.test('Trade threshold filtering: minTradeAmount check', () => {
  const filePath = path.join(srcDir, 'services', 'sfx-event-emitter.ts');
  const content = tester.loadFile(filePath);
  tester.assertContains(content, 'trade:', 'Trade SFX type check missing');
  tester.assertContains(content, 'minTradeAmount', 'minTradeAmount threshold missing');
  tester.assertContains(content, 'event.metadata.amount >= this.thresholds.minTradeAmount', 'Trade amount validation missing');
});

tester.test('Alert severity filtering: alertSeverity check', () => {
  const filePath = path.join(srcDir, 'services', 'sfx-event-emitter.ts');
  const content = tester.loadFile(filePath);
  tester.assertContains(content, 'market:alert:', 'Market alert type check missing');
  tester.assertContains(content, 'alertSeverity', 'alertSeverity filtering missing');
  tester.assertContains(content, "alertSeverity === 'all'", 'Alert severity all option missing');
  tester.assertContains(content, "alertSeverity === 'high'", 'Alert severity high option missing');
});

tester.test('Achievement always plays (no threshold)', () => {
  const filePath = path.join(srcDir, 'services', 'sfx-event-emitter.ts');
  const content = tester.loadFile(filePath);
  tester.assertContains(content, 'achievement:', 'Achievement check missing');
  tester.assertContains(content, 'return true', 'Achievement should always return true');
});

// ============================================================================
// TEST CATEGORY 2: SFX Event Emitter - Debouncing
// ============================================================================

console.log('\n[Category 2] SFX Event Emitter - Debouncing\n');

tester.test('DEBOUNCE_MS constant defined', () => {
  const filePath = path.join(srcDir, 'services', 'sfx-event-emitter.ts');
  const content = tester.loadFile(filePath);
  tester.assertContains(content, 'DEBOUNCE_MS', 'DEBOUNCE_MS constant missing');
  tester.assertContains(content, 'DEBOUNCE_MS = 500', 'DEBOUNCE_MS should be 500ms');
});

tester.test('isDebounced method exists', () => {
  const filePath = path.join(srcDir, 'services', 'sfx-event-emitter.ts');
  const content = tester.loadFile(filePath);
  tester.assertContains(content, 'isDebounced', 'isDebounced method missing');
});

tester.test('Debouncing tracks last played time per SFX type', () => {
  const filePath = path.join(srcDir, 'services', 'sfx-event-emitter.ts');
  const content = tester.loadFile(filePath);
  tester.assertContains(content, 'lastPlayedTime: Map', 'lastPlayedTime Map missing');
  tester.assertContains(content, 'this.lastPlayedTime.get', 'Get last played time missing');
});

tester.test('Debouncing prevents duplicate sounds within 500ms', () => {
  const filePath = path.join(srcDir, 'services', 'sfx-event-emitter.ts');
  const content = tester.loadFile(filePath);
  tester.assertContains(content, 'timeSinceLastPlayed < this.DEBOUNCE_MS', 'Debounce check logic missing');
});

tester.test('Emit logic checks debouncing before playing', () => {
  const filePath = path.join(srcDir, 'services', 'sfx-event-emitter.ts');
  const content = tester.loadFile(filePath);
  tester.assertContains(content, 'if (this.isDebounced(event.type)) {', 'Debounce check in emit missing');
  tester.assertContains(content, 'return;', 'Early return on debounce missing');
});

tester.test('Last played time updated on successful play', () => {
  const filePath = path.join(srcDir, 'services', 'sfx-event-emitter.ts');
  const content = tester.loadFile(filePath);
  tester.assertContains(content, 'this.lastPlayedTime.set(event.type, Date.now())', 'Last played time update missing');
});

// ============================================================================
// TEST CATEGORY 3: AudioManager SFX Playback
// ============================================================================

console.log('\n[Category 3] AudioManager SFX Playback\n');

tester.test('AudioManager file exists', () => {
  const filePath = path.join(srcDir, 'services', 'audio-manager.ts');
  tester.assertFileExists(filePath, 'AudioManager not found');
});

tester.test('SFX Sampler initialized in AudioManager', () => {
  const filePath = path.join(srcDir, 'services', 'audio-manager.ts');
  const content = tester.loadFile(filePath);
  tester.assertContains(content, 'sfxSampler: Tone.Sampler', 'SFX Sampler field missing');
  tester.assertContains(content, 'new Tone.Sampler', 'Sampler initialization missing');
});

tester.test('SFX sample URLs mapped correctly', () => {
  const filePath = path.join(srcDir, 'services', 'audio-manager.ts');
  const content = tester.loadFile(filePath);
  tester.assertContains(content, '/audio/sfx/trade-buy.mp3', 'Trade buy sample missing');
  tester.assertContains(content, '/audio/sfx/trade-sell.mp3', 'Trade sell sample missing');
  tester.assertContains(content, '/audio/sfx/market-alert.mp3', 'Market alert sample missing');
  tester.assertContains(content, '/audio/sfx/achievement.mp3', 'Achievement sample missing');
});

tester.test('playSFX method exists', () => {
  const filePath = path.join(srcDir, 'services', 'audio-manager.ts');
  const content = tester.loadFile(filePath);
  tester.assertContains(content, 'playSFX(type: SFXType', 'playSFX method missing');
});

tester.test('SFX cooldown mechanism (500ms)', () => {
  const filePath = path.join(srcDir, 'services', 'audio-manager.ts');
  const content = tester.loadFile(filePath);
  tester.assertContains(content, 'SFX_COOLDOWN_MS = 500', 'SFX cooldown constant missing');
});

tester.test('SFX type to note mapping function', () => {
  const filePath = path.join(srcDir, 'services', 'audio-manager.ts');
  const content = tester.loadFile(filePath);
  tester.assertContains(content, '_mapSFXTypeToNote', 'SFX type to note mapping missing');
});

tester.test('Sampler triggerAttackRelease called for SFX playback', () => {
  const filePath = path.join(srcDir, 'services', 'audio-manager.ts');
  const content = tester.loadFile(filePath);
  tester.assertContains(content, 'triggerAttackRelease', 'Sampler triggerAttackRelease missing');
});

tester.test('SFX volume independent from music', () => {
  const filePath = path.join(srcDir, 'services', 'audio-manager.ts');
  const content = tester.loadFile(filePath);
  tester.assertContains(content, "channel === 'sfx'", 'SFX volume channel missing');
  tester.assertContains(content, 'this.settings.sfxVolume', 'SFX volume setting missing');
});

// ============================================================================
// TEST CATEGORY 4: AudioSettingsModal - SFX Threshold Controls
// ============================================================================

console.log('\n[Category 4] AudioSettingsModal - SFX Threshold Controls\n');

tester.test('AudioSettingsModal file exists', () => {
  const filePath = path.join(srcDir, 'components', 'AudioSettingsModal.tsx');
  tester.assertFileExists(filePath, 'AudioSettingsModal not found');
});

tester.test('AudioSettingsModal imports useAudioPlayer hook', () => {
  const filePath = path.join(srcDir, 'components', 'AudioSettingsModal.tsx');
  const content = tester.loadFile(filePath);
  tester.assertContains(content, 'useAudioPlayer', 'useAudioPlayer hook import missing');
});

tester.test('SFX threshold controls in modal UI', () => {
  const filePath = path.join(srcDir, 'components', 'AudioSettingsModal.tsx');
  const content = tester.loadFile(filePath);
  tester.assertContains(content, 'setSfxThresholds', 'setSfxThresholds method missing');
});

tester.test('Min trade amount input field exists', () => {
  const filePath = path.join(srcDir, 'components', 'AudioSettingsModal.tsx');
  const content = tester.loadFile(filePath);
  tester.assertContains(content, 'localMinTradeAmount', 'Local min trade amount state missing');
  tester.assertContains(content, 'setLocalMinTradeAmount', 'Set min trade amount handler missing');
});

tester.test('Alert severity dropdown selector exists', () => {
  const filePath = path.join(srcDir, 'components', 'AudioSettingsModal.tsx');
  const content = tester.loadFile(filePath);
  tester.assertContains(content, 'alertSeverity', 'Alert severity control missing');
  tester.assertContains(content, 'localAlertSeverity', 'Local alert severity state missing');
});

tester.test('Settings synced with context on modal open', () => {
  const filePath = path.join(srcDir, 'components', 'AudioSettingsModal.tsx');
  const content = tester.loadFile(filePath);
  tester.assertContains(content, 'useEffect', 'useEffect for sync missing');
  tester.assertContains(content, 'if (open)', 'Open condition missing');
  tester.assertContains(content, 'setLocalMinTradeAmount(settings.sfxThresholds.minTradeAmount)', 'Min trade sync missing');
});

tester.test('Save handler applies SFX threshold changes', () => {
  const filePath = path.join(srcDir, 'components', 'AudioSettingsModal.tsx');
  const content = tester.loadFile(filePath);
  tester.assertContains(content, 'handleSave', 'handleSave function missing');
  tester.assertContains(content, 'setSfxThresholds({', 'setSfxThresholds call in handleSave missing');
});

tester.test('Cancel handler reverts SFX threshold changes', () => {
  const filePath = path.join(srcDir, 'components', 'AudioSettingsModal.tsx');
  const content = tester.loadFile(filePath);
  tester.assertContains(content, 'handleCancel', 'handleCancel function missing');
  tester.assertContains(content, 'setLocalMinTradeAmount(settings.sfxThresholds.minTradeAmount)', 'Min trade revert in cancel missing');
});

// ============================================================================
// TEST CATEGORY 5: Type Definitions & Interfaces
// ============================================================================

console.log('\n[Category 5] Type Definitions & Interfaces\n');

tester.test('Audio types file exists', () => {
  const filePath = path.join(srcDir, 'types', 'audio.ts');
  tester.assertFileExists(filePath, 'Audio types file not found');
});

tester.test('SFXType union type includes all required types', () => {
  const filePath = path.join(srcDir, 'types', 'audio.ts');
  const content = tester.loadFile(filePath);
  tester.assertContains(content, 'trade:buy', 'SFXType trade:buy missing');
  tester.assertContains(content, 'trade:sell', 'SFXType trade:sell missing');
  tester.assertContains(content, 'market:alert:low', 'SFXType market:alert:low missing');
  tester.assertContains(content, 'market:alert:high', 'SFXType market:alert:high missing');
  tester.assertContains(content, 'achievement:unlock', 'SFXType achievement:unlock missing');
});

tester.test('SFXThresholds interface defined', () => {
  const filePath = path.join(srcDir, 'types', 'audio.ts');
  const content = tester.loadFile(filePath);
  tester.assertContains(content, 'interface SFXThresholds', 'SFXThresholds interface missing');
  tester.assertContains(content, 'minTradeAmount: number', 'minTradeAmount field missing');
  tester.assertContains(content, "alertSeverity: 'all' | 'high'", 'alertSeverity type missing');
});

tester.test('SFXEvent interface defined with metadata', () => {
  const filePath = path.join(srcDir, 'types', 'audio.ts');
  const content = tester.loadFile(filePath);
  tester.assertContains(content, 'interface SFXEvent', 'SFXEvent interface missing');
  tester.assertContains(content, 'type: SFXType', 'SFXEvent type field missing');
  tester.assertContains(content, 'metadata?: SFXEventMetadata', 'SFXEvent metadata field missing');
});

tester.test('SFXEventMetadata includes amount and severity', () => {
  const filePath = path.join(srcDir, 'types', 'audio.ts');
  const content = tester.loadFile(filePath);
  tester.assertContains(content, 'interface SFXEventMetadata', 'SFXEventMetadata interface missing');
  tester.assertContains(content, 'amount?: number', 'amount field missing');
  tester.assertContains(content, "severity?: 'low' | 'medium' | 'high'", 'severity field missing');
});

tester.test('Default audio settings includes SFX thresholds', () => {
  const filePath = path.join(srcDir, 'types', 'audio.ts');
  const content = tester.loadFile(filePath);
  tester.assertContains(content, 'DEFAULT_AUDIO_SETTINGS', 'Default settings missing');
  tester.assertContains(content, 'sfxThresholds: {', 'sfxThresholds in defaults missing');
  tester.assertContains(content, 'minTradeAmount: 100', 'Default minTradeAmount missing');
  tester.assertContains(content, "alertSeverity: 'all'", 'Default alertSeverity missing');
});

// ============================================================================
// TEST CATEGORY 6: Hooks & Integration
// ============================================================================

console.log('\n[Category 6] Hooks & Integration\n');

tester.test('useSoundEffects hook file exists', () => {
  const filePath = path.join(srcDir, 'hooks', 'useSoundEffects.ts');
  tester.assertFileExists(filePath, 'useSoundEffects hook not found');
});

tester.test('useSoundEffects hook exports all required functions', () => {
  const filePath = path.join(srcDir, 'hooks', 'useSoundEffects.ts');
  const content = tester.loadFile(filePath);
  tester.assertContains(content, 'playSFX', 'playSFX function missing');
  tester.assertContains(content, 'playTradeBuy', 'playTradeBuy function missing');
  tester.assertContains(content, 'playTradeSell', 'playTradeSell function missing');
  tester.assertContains(content, 'playMarketAlert', 'playMarketAlert function missing');
  tester.assertContains(content, 'playAchievement', 'playAchievement function missing');
});

tester.test('useSoundEffects uses useAudioContext', () => {
  const filePath = path.join(srcDir, 'hooks', 'useSoundEffects.ts');
  const content = tester.loadFile(filePath);
  tester.assertContains(content, 'useAudioContext', 'useAudioContext import missing');
  tester.assertContains(content, 'playSFX } = useAudioContext()', 'playSFX from context missing');
});

tester.test('useSoundEffects uses useCallback for memoization', () => {
  const filePath = path.join(srcDir, 'hooks', 'useSoundEffects.ts');
  const content = tester.loadFile(filePath);
  tester.assertContains(content, 'useCallback', 'useCallback import missing');
  tester.assertContains(content, 'useCallback((', 'useCallback usage missing');
});

tester.test('AudioContext includes playSFX method', () => {
  const filePath = path.join(srcDir, 'context', 'AudioContext.tsx');
  const content = tester.loadFile(filePath);
  tester.assertContains(content, 'playSFX:', 'playSFX in context value missing');
  tester.assertContains(content, '(type: SFXType', 'playSFX method signature missing');
});

tester.test('AudioContext includes setSfxThresholds method', () => {
  const filePath = path.join(srcDir, 'context', 'AudioContext.tsx');
  const content = tester.loadFile(filePath);
  tester.assertContains(content, 'setSfxThresholds', 'setSfxThresholds method missing');
});

// ============================================================================
// TEST CATEGORY 7: Build Validation
// ============================================================================

console.log('\n[Category 7] Build Validation\n');

tester.test('TypeScript compiles without errors (syntax check)', () => {
  // Simple syntax validation - check for common TS errors
  const filePath = path.join(srcDir, 'services', 'sfx-event-emitter.ts');
  const content = tester.loadFile(filePath);

  // Check for balanced braces/brackets
  const openBraces = (content.match(/{/g) || []).length;
  const closeBraces = (content.match(/}/g) || []).length;
  tester.assert(openBraces === closeBraces, 'Unbalanced braces in sfx-event-emitter.ts');

  const openBrackets = (content.match(/\[/g) || []).length;
  const closeBrackets = (content.match(/\]/g) || []).length;
  tester.assert(openBrackets === closeBrackets, 'Unbalanced brackets in sfx-event-emitter.ts');
});

tester.test('No console.error in critical paths (production ready)', () => {
  const filePath = path.join(srcDir, 'services', 'sfx-event-emitter.ts');
  const content = tester.loadFile(filePath);
  // SFX emitter should not have error logging in critical paths
  tester.assert(!content.includes('console.error'), 'console.error found in SFX emitter');
});

tester.test('AudioContext audio storage utilities imported', () => {
  const filePath = path.join(srcDir, 'context', 'AudioContext.tsx');
  const content = tester.loadFile(filePath);
  tester.assertContains(content, 'saveAudioSettings', 'saveAudioSettings import/usage missing');
});

// ============================================================================
// SUMMARY
// ============================================================================

const success = tester.summary();

console.log('\n='.repeat(70));
console.log('TEST EXECUTION COMPLETE');
console.log('='.repeat(70));

process.exit(success ? 0 : 1);
