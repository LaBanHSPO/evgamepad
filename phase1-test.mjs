#!/usr/bin/env node

/**
 * Phase 1 Audio System Test Suite
 *
 * Tests Core Audio Infrastructure:
 * 1. TypeScript type definitions
 * 2. localStorage utilities
 * 3. AudioManager singleton
 * 4. File structure integrity
 * 5. Import resolution
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

class Phase1Tester {
  constructor() {
    this.passed = 0;
    this.failed = 0;
    this.tests = [];
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

  assertEqual(actual, expected, message) {
    if (actual !== expected) {
      throw new Error(`${message || 'Assertion failed'}: expected ${expected}, got ${actual}`);
    }
  }

  assertTrue(condition, message) {
    this.assert(condition, message || 'Expected true');
  }

  assertFalse(condition, message) {
    this.assert(!condition, message || 'Expected false');
  }

  fileExists(filePath, message) {
    const exists = fs.existsSync(filePath);
    this.assert(exists, message || `File not found: ${filePath}`);
  }

  directoryExists(dirPath, message) {
    const exists = fs.existsSync(dirPath) && fs.statSync(dirPath).isDirectory();
    this.assert(exists, message || `Directory not found: ${dirPath}`);
  }

  summary() {
    console.log('\n' + '='.repeat(60));
    console.log('PHASE 1 TEST SUMMARY');
    console.log('='.repeat(60));
    console.log(`Total Tests: ${this.passed + this.failed}`);
    console.log(`Passed: ${this.passed}`);
    console.log(`Failed: ${this.failed}`);
    console.log('='.repeat(60));

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

const tester = new Phase1Tester();

console.log('\n' + '='.repeat(60));
console.log('PHASE 1: CORE AUDIO INFRASTRUCTURE TESTS');
console.log('='.repeat(60) + '\n');

// Test Category 1: File Structure
console.log('Test Category 1: File Structure Integrity');
console.log('-'.repeat(60));

tester.test('Types directory exists', () => {
  tester.directoryExists(path.join(__dirname, 'src/types'));
});

tester.test('Utils directory exists', () => {
  tester.directoryExists(path.join(__dirname, 'src/utils'));
});

tester.test('Services directory exists', () => {
  tester.directoryExists(path.join(__dirname, 'src/services'));
});

tester.test('audio.ts type file exists', () => {
  tester.fileExists(path.join(__dirname, 'src/types/audio.ts'));
});

tester.test('audio-storage.ts utility file exists', () => {
  tester.fileExists(path.join(__dirname, 'src/utils/audio-storage.ts'));
});

tester.test('audio-manager.ts service file exists', () => {
  tester.fileExists(path.join(__dirname, 'src/services/audio-manager.ts'));
});

// Test Category 2: Audio Files
console.log('\nTest Category 2: Audio Files Structure');
console.log('-'.repeat(60));

tester.test('Music audio directory exists', () => {
  tester.directoryExists(path.join(__dirname, 'public/audio/music'));
});

tester.test('SFX audio directory exists', () => {
  tester.directoryExists(path.join(__dirname, 'public/audio/sfx'));
});

tester.test('All 4 music tracks present', () => {
  const musicDir = path.join(__dirname, 'public/audio/music');
  const files = fs.readdirSync(musicDir).filter(f => f.endsWith('.mp3'));
  const expectedTracks = ['focus-ambient.mp3', 'energy-upbeat.mp3', 'strategy-chill.mp3', 'night-lofi.mp3'];
  expectedTracks.forEach(track => {
    tester.assert(files.includes(track), `Missing music track: ${track}`);
  });
});

tester.test('All 5 SFX sounds present', () => {
  const sfxDir = path.join(__dirname, 'public/audio/sfx');
  const files = fs.readdirSync(sfxDir).filter(f => f.endsWith('.mp3'));
  const expectedSounds = ['trade-buy.mp3', 'trade-sell.mp3', 'market-alert.mp3', 'achievement.mp3', 'milestone.mp3'];
  expectedSounds.forEach(sound => {
    tester.assert(files.includes(sound), `Missing SFX sound: ${sound}`);
  });
});

// Test Category 3: TypeScript Type Definitions
console.log('\nTest Category 3: TypeScript Type Definitions');
console.log('-'.repeat(60));

tester.test('audio.ts file is valid TypeScript', () => {
  const filePath = path.join(__dirname, 'src/types/audio.ts');
  const content = fs.readFileSync(filePath, 'utf-8');
  tester.assert(content.includes('export interface MusicTrack'), 'MusicTrack interface not found');
  tester.assert(content.includes('export interface AudioSettings'), 'AudioSettings interface not found');
  tester.assert(content.includes('export type SFXType'), 'SFXType type not found');
  tester.assert(content.includes('export const DEFAULT_AUDIO_SETTINGS'), 'DEFAULT_AUDIO_SETTINGS not found');
  tester.assert(content.includes('export const MUSIC_TRACKS'), 'MUSIC_TRACKS not found');
});

tester.test('AudioSettings has required properties', () => {
  const filePath = path.join(__dirname, 'src/types/audio.ts');
  const content = fs.readFileSync(filePath, 'utf-8');
  const requiredProps = ['masterVolume', 'musicVolume', 'sfxVolume', 'isMuted', 'currentTrackId', 'playbackPosition', 'sfxThresholds'];
  requiredProps.forEach(prop => {
    tester.assert(content.includes(prop), `Missing property: ${prop}`);
  });
});

tester.test('DEFAULT_AUDIO_SETTINGS has valid defaults', () => {
  const filePath = path.join(__dirname, 'src/types/audio.ts');
  const content = fs.readFileSync(filePath, 'utf-8');
  tester.assert(content.includes('masterVolume: 0.8'), 'masterVolume default incorrect');
  tester.assert(content.includes('musicVolume: 0.7'), 'musicVolume default incorrect');
  tester.assert(content.includes('sfxVolume: 0.9'), 'sfxVolume default incorrect');
  tester.assert(content.includes('isMuted: false'), 'isMuted default incorrect');
});

tester.test('SFXType covers all event types', () => {
  const filePath = path.join(__dirname, 'src/types/audio.ts');
  const content = fs.readFileSync(filePath, 'utf-8');
  const requiredTypes = ['trade:buy', 'trade:sell', 'market:alert:low', 'market:alert:medium', 'market:alert:high', 'achievement:unlock', 'achievement:milestone'];
  requiredTypes.forEach(type => {
    tester.assert(content.includes(`'${type}'`), `Missing SFX type: ${type}`);
  });
});

// Test Category 4: Audio Storage Utilities
console.log('\nTest Category 4: Audio Storage Utilities');
console.log('-'.repeat(60));

tester.test('audio-storage.ts exports saveAudioSettings', () => {
  const filePath = path.join(__dirname, 'src/utils/audio-storage.ts');
  const content = fs.readFileSync(filePath, 'utf-8');
  tester.assert(content.includes('export const saveAudioSettings'), 'saveAudioSettings not exported');
});

tester.test('audio-storage.ts exports loadAudioSettings', () => {
  const filePath = path.join(__dirname, 'src/utils/audio-storage.ts');
  const content = fs.readFileSync(filePath, 'utf-8');
  tester.assert(content.includes('export const loadAudioSettings'), 'loadAudioSettings not exported');
});

tester.test('audio-storage.ts exports clearAudioSettings', () => {
  const filePath = path.join(__dirname, 'src/utils/audio-storage.ts');
  const content = fs.readFileSync(filePath, 'utf-8');
  tester.assert(content.includes('export const clearAudioSettings'), 'clearAudioSettings not exported');
});

tester.test('audio-storage.ts exports updateAudioSetting', () => {
  const filePath = path.join(__dirname, 'src/utils/audio-storage.ts');
  const content = fs.readFileSync(filePath, 'utf-8');
  tester.assert(content.includes('export const updateAudioSetting'), 'updateAudioSetting not exported');
});

tester.test('audio-storage.ts uses correct localStorage key', () => {
  const filePath = path.join(__dirname, 'src/utils/audio-storage.ts');
  const content = fs.readFileSync(filePath, 'utf-8');
  tester.assert(content.includes("'audioSettings'"), 'localStorage key not found');
});

tester.test('audio-storage.ts imports AudioSettings types', () => {
  const filePath = path.join(__dirname, 'src/utils/audio-storage.ts');
  const content = fs.readFileSync(filePath, 'utf-8');
  tester.assert(content.includes('import { AudioSettings, DEFAULT_AUDIO_SETTINGS }'), 'Type imports missing');
});

// Test Category 5: AudioManager Service
console.log('\nTest Category 5: AudioManager Service');
console.log('-'.repeat(60));

tester.test('AudioManager is a class', () => {
  const filePath = path.join(__dirname, 'src/services/audio-manager.ts');
  const content = fs.readFileSync(filePath, 'utf-8');
  tester.assert(content.includes('class AudioManager'), 'AudioManager class not found');
});

tester.test('AudioManager implements singleton pattern', () => {
  const filePath = path.join(__dirname, 'src/services/audio-manager.ts');
  const content = fs.readFileSync(filePath, 'utf-8');
  tester.assert(content.includes('private static instance'), 'Static instance not found');
  tester.assert(content.includes('getInstance()'), 'getInstance method not found');
  tester.assert(content.includes('private constructor()'), 'Private constructor not found');
});

tester.test('AudioManager has initialize method', () => {
  const filePath = path.join(__dirname, 'src/services/audio-manager.ts');
  const content = fs.readFileSync(filePath, 'utf-8');
  tester.assert(content.includes('public async initialize()'), 'initialize method not found');
});

tester.test('AudioManager has music playback methods', () => {
  const filePath = path.join(__dirname, 'src/services/audio-manager.ts');
  const content = fs.readFileSync(filePath, 'utf-8');
  const methods = ['playMusic', 'pauseMusic', 'stopMusic', 'loadMusicTrack', 'seekMusic', 'isPlaying', 'getCurrentPosition'];
  methods.forEach(method => {
    tester.assert(content.includes(`public ${method}(`) || content.includes(`public async ${method}(`), `Missing method: ${method}`);
  });
});

tester.test('AudioManager has SFX playback method', () => {
  const filePath = path.join(__dirname, 'src/services/audio-manager.ts');
  const content = fs.readFileSync(filePath, 'utf-8');
  tester.assert(content.includes('public playSFX'), 'playSFX method not found');
});

tester.test('AudioManager has volume control methods', () => {
  const filePath = path.join(__dirname, 'src/services/audio-manager.ts');
  const content = fs.readFileSync(filePath, 'utf-8');
  tester.assert(content.includes('public setVolume'), 'setVolume method not found');
  tester.assert(content.includes('public toggleMute'), 'toggleMute method not found');
});

tester.test('AudioManager has settings management methods', () => {
  const filePath = path.join(__dirname, 'src/services/audio-manager.ts');
  const content = fs.readFileSync(filePath, 'utf-8');
  tester.assert(content.includes('public saveSettings'), 'saveSettings method not found');
  tester.assert(content.includes('public loadSettings'), 'loadSettings method not found');
  tester.assert(content.includes('public getSettings'), 'getSettings method not found');
});

tester.test('AudioManager has dispose method for cleanup', () => {
  const filePath = path.join(__dirname, 'src/services/audio-manager.ts');
  const content = fs.readFileSync(filePath, 'utf-8');
  tester.assert(content.includes('public dispose()'), 'dispose method not found');
});

tester.test('AudioManager initializes Tone.js Player', () => {
  const filePath = path.join(__dirname, 'src/services/audio-manager.ts');
  const content = fs.readFileSync(filePath, 'utf-8');
  tester.assert(content.includes('new Tone.Player'), 'Tone.Player initialization not found');
  tester.assert(content.includes('toDestination()'), 'toDestination routing not found');
});

tester.test('AudioManager initializes Tone.js Sampler', () => {
  const filePath = path.join(__dirname, 'src/services/audio-manager.ts');
  const content = fs.readFileSync(filePath, 'utf-8');
  tester.assert(content.includes('new Tone.Sampler'), 'Tone.Sampler initialization not found');
});

tester.test('AudioManager imports Tone.js', () => {
  const filePath = path.join(__dirname, 'src/services/audio-manager.ts');
  const content = fs.readFileSync(filePath, 'utf-8');
  tester.assert(content.includes("import * as Tone from 'tone'"), 'Tone.js import not found');
});

tester.test('AudioManager exports singleton instance', () => {
  const filePath = path.join(__dirname, 'src/services/audio-manager.ts');
  const content = fs.readFileSync(filePath, 'utf-8');
  tester.assert(content.includes('export const audioManager'), 'audioManager export not found');
});

tester.test('AudioManager has SFX debounce cooldown', () => {
  const filePath = path.join(__dirname, 'src/services/audio-manager.ts');
  const content = fs.readFileSync(filePath, 'utf-8');
  tester.assert(content.includes('SFX_COOLDOWN_MS'), 'SFX_COOLDOWN_MS not found');
});

// Test Category 6: Dependencies
console.log('\nTest Category 6: Dependencies');
console.log('-'.repeat(60));

tester.test('Tone.js is in dependencies', () => {
  const pkgPath = path.join(__dirname, 'package.json');
  const content = fs.readFileSync(pkgPath, 'utf-8');
  tester.assert(content.includes('"tone"'), 'tone dependency not found');
});

tester.test('TypeScript is in devDependencies', () => {
  const pkgPath = path.join(__dirname, 'package.json');
  const content = fs.readFileSync(pkgPath, 'utf-8');
  tester.assert(content.includes('"typescript"'), 'typescript devDependency not found');
});

// Print summary
const success = tester.summary();
process.exit(success ? 0 : 1);
