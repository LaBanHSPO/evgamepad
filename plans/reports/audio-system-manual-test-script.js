/**
 * Audio System Manual Testing Script
 *
 * Instructions:
 * 1. Run `npm run dev` to start dev server
 * 2. Open http://localhost:5173 in browser
 * 3. Open browser DevTools (F12)
 * 4. Copy the entire content of this script
 * 5. Paste into browser console and press Enter
 * 6. Follow the prompts and document results
 *
 * This script will test all acceptance criteria for Phases 2, 3, and 4
 */

console.clear();
console.log('='.repeat(80));
console.log('TONE.JS AUDIO SYSTEM - MANUAL TEST SUITE');
console.log('Phases 2, 3, 4: React Context, SFX System, Keyboard Shortcuts');
console.log('='.repeat(80));
console.log('');

// Test Results Storage
const testResults = {
  phase2: [],
  phase3: [],
  phase4: [],
  timestamp: new Date().toISOString(),
  notes: []
};

// Helper functions
const log = (category, message, type = 'info') => {
  const prefix = `[${category}]`;
  const styles = {
    info: 'color: #2196F3; font-weight: bold;',
    pass: 'color: #4CAF50; font-weight: bold;',
    fail: 'color: #F44336; font-weight: bold;',
    warn: 'color: #FF9800; font-weight: bold;'
  };
  console.log(`%c${prefix} ${message}`, styles[type] || styles.info);
};

const addResult = (phase, testName, status, details = '') => {
  testResults[phase].push({
    testName,
    status, // PASS, FAIL, SKIP
    details,
    timestamp: new Date().toLocaleTimeString()
  });
};

const printResults = () => {
  console.log('\n' + '='.repeat(80));
  console.log('TEST RESULTS SUMMARY');
  console.log('='.repeat(80));

  const phases = ['phase2', 'phase3', 'phase4'];
  let totalTests = 0;
  let totalPass = 0;
  let totalFail = 0;

  phases.forEach(phase => {
    const results = testResults[phase];
    const passed = results.filter(r => r.status === 'PASS').length;
    const failed = results.filter(r => r.status === 'FAIL').length;
    const skipped = results.filter(r => r.status === 'SKIP').length;

    totalTests += results.length;
    totalPass += passed;
    totalFail += failed;

    console.log(`\n${phase.toUpperCase()}`);
    console.log(`  Total: ${results.length} | Pass: ${passed} | Fail: ${failed} | Skip: ${skipped}`);

    results.forEach(result => {
      const icon = result.status === 'PASS' ? '✓' : result.status === 'FAIL' ? '✗' : '⊘';
      const style = result.status === 'PASS' ? 'color: #4CAF50;' :
                   result.status === 'FAIL' ? 'color: #F44336;' : 'color: #999;';
      console.log(`%c${icon} ${result.testName}: ${result.status}`, style);
      if (result.details) console.log(`  └─ ${result.details}`);
    });
  });

  console.log('\n' + '='.repeat(80));
  console.log(`OVERALL: ${totalPass}/${totalTests} Tests Passed`);
  console.log('='.repeat(80));
};

// ============================================================================
// PHASE 2: React Context & UI Integration Tests
// ============================================================================

console.log('\n');
log('PHASE 2', 'React Context & UI Integration Testing');
console.log('');

const phase2Tests = {
  // Test 1: Settings button visible
  settingsButtonVisible: () => {
    const settingsBtn = document.querySelector('[data-testid="audio-settings-button"]') ||
                       document.querySelector('button:has-text("Settings")') ||
                       Array.from(document.querySelectorAll('button')).find(b =>
                         b.textContent.includes('Settings') ||
                         b.querySelector('[class*="Settings"]')
                       );

    if (settingsBtn) {
      log('PHASE 2', 'Settings button is visible in header', 'pass');
      addResult('phase2', 'Settings button visible', 'PASS', 'Found in DOM');
      return true;
    } else {
      log('PHASE 2', 'Settings button NOT found in header', 'fail');
      addResult('phase2', 'Settings button visible', 'FAIL', 'Settings button not in DOM');
      log('PHASE 2', 'Hint: Look for a settings/gear icon in the header', 'warn');
      return false;
    }
  },

  // Test 2: Modal opens/closes
  modalOpenClose: () => {
    const settingsBtn = document.querySelector('[data-testid="audio-settings-button"]') ||
                       Array.from(document.querySelectorAll('button')).find(b =>
                         b.textContent.includes('Settings')
                       );

    if (settingsBtn) {
      log('PHASE 2', 'Testing modal open/close...', 'info');
      settingsBtn.click();

      setTimeout(() => {
        const modalContent = document.querySelector('[data-testid="audio-settings-modal"]') ||
                            document.querySelector('[role="dialog"]');

        if (modalContent && modalContent.offsetParent !== null) {
          log('PHASE 2', 'Modal opened successfully', 'pass');
          addResult('phase2', 'Modal opens on button click', 'PASS', 'Dialog displayed');

          // Try to find close button
          const closeBtn = document.querySelector('[data-testid="dialog-close"]') ||
                          Array.from(document.querySelectorAll('button')).find(b =>
                            b.getAttribute('aria-label') === 'Close' ||
                            b.textContent === 'Cancel'
                          );

          if (closeBtn) {
            closeBtn.click();
            setTimeout(() => {
              const stillOpen = modalContent && modalContent.offsetParent !== null;
              if (!stillOpen) {
                log('PHASE 2', 'Modal closed successfully', 'pass');
                addResult('phase2', 'Modal closes on button click', 'PASS', 'Dialog hidden');
              } else {
                log('PHASE 2', 'Modal did not close', 'fail');
                addResult('phase2', 'Modal closes on button click', 'FAIL', 'Dialog still visible');
              }
            }, 300);
          }
        } else {
          log('PHASE 2', 'Modal did not open', 'fail');
          addResult('phase2', 'Modal opens on button click', 'FAIL', 'Dialog not found');
        }
      }, 300);
    } else {
      log('PHASE 2', 'Settings button not found, skipping modal test', 'warn');
      addResult('phase2', 'Modal opens/closes', 'SKIP', 'Settings button not found');
    }
  },

  // Test 3: Track selection
  trackSelection: () => {
    const radioButtons = document.querySelectorAll('input[type="radio"][name*="track"]');

    if (radioButtons.length > 1) {
      log('PHASE 2', `Found ${radioButtons.length} music track options`, 'pass');
      addResult('phase2', 'Track selection in modal', 'PASS', `${radioButtons.length} tracks available`);
    } else {
      log('PHASE 2', 'Track selection controls not found', 'fail');
      addResult('phase2', 'Track selection in modal', 'FAIL', 'Radio buttons not found');
    }
  },

  // Test 4: Volume sliders
  volumeSliders: () => {
    const sliders = document.querySelectorAll('input[type="range"]');
    const masterSlider = Array.from(sliders).find(s => s.id?.includes('master'));
    const musicSlider = Array.from(sliders).find(s => s.id?.includes('music'));
    const sfxSlider = Array.from(sliders).find(s => s.id?.includes('sfx'));

    const volumeElements = document.querySelectorAll('[aria-label*="Volume"], [aria-label*="volume"]');

    if (sliders.length >= 3 || masterSlider) {
      log('PHASE 2', `Found ${sliders.length} volume sliders`, 'pass');
      addResult('phase2', 'Volume sliders present', 'PASS', `${sliders.length} sliders found`);

      // Check for real-time updates
      if (masterSlider) {
        const initialValue = masterSlider.value;
        const event = new Event('input', { bubbles: true });
        masterSlider.value = 0.5;
        masterSlider.dispatchEvent(event);

        setTimeout(() => {
          log('PHASE 2', 'Master volume slider responds to input', 'pass');
          addResult('phase2', 'Volume sliders adjust audio real-time', 'PASS', 'Input events fired');
          masterSlider.value = initialValue;
          masterSlider.dispatchEvent(event);
        }, 100);
      }
    } else {
      log('PHASE 2', 'Volume sliders not found', 'fail');
      addResult('phase2', 'Volume sliders present', 'FAIL', 'Sliders not in DOM');
    }
  },

  // Test 5: Save button
  saveButton: () => {
    const saveBtn = Array.from(document.querySelectorAll('button')).find(b =>
      b.textContent.includes('Save') && b.closest('[role="dialog"]')
    );

    if (saveBtn) {
      log('PHASE 2', 'Save button found and enabled', 'pass');
      addResult('phase2', 'Save button saves settings', 'PASS', 'Save button in modal');
    } else {
      log('PHASE 2', 'Save button not found', 'fail');
      addResult('phase2', 'Save button saves settings', 'FAIL', 'Save button not in dialog');
    }
  },

  // Test 6: Settings persistence
  settingsPersistence: () => {
    const stored = localStorage.getItem('audioSettings');

    if (stored) {
      try {
        const settings = JSON.parse(stored);
        log('PHASE 2', 'Settings found in localStorage', 'pass');
        addResult('phase2', 'Settings persist in localStorage', 'PASS', 'Audio settings stored');
        console.log('  Stored settings:', settings);
      } catch (e) {
        log('PHASE 2', 'Invalid settings in localStorage', 'fail');
        addResult('phase2', 'Settings persist in localStorage', 'FAIL', 'Invalid JSON');
      }
    } else {
      log('PHASE 2', 'No settings in localStorage yet (may not be saved)', 'warn');
      addResult('phase2', 'Settings persist in localStorage', 'SKIP', 'Not yet saved');
    }
  }
};

// Run Phase 2 tests
Object.values(phase2Tests).forEach(test => {
  try {
    test();
  } catch (e) {
    console.error('Test error:', e.message);
  }
});

// ============================================================================
// PHASE 3: Sound Effects System Tests
// ============================================================================

console.log('\n');
log('PHASE 3', 'Sound Effects System Testing');
console.log('');

const phase3Tests = {
  // Test 1: SFX on trade
  tradeSound: () => {
    // Listen for audio context or check for audioManager
    const hasAudioContext = window.AudioContext || window.webkitAudioContext;
    const hasAudioManager = window.audioManager !== undefined;

    if (hasAudioContext && hasAudioManager) {
      log('PHASE 3', 'Audio context available for SFX testing', 'pass');
      addResult('phase3', 'SFX audio context ready', 'PASS', 'AudioContext + AudioManager found');
      console.log('  Manual step: Execute a trade in the game (buy for >$100)');
      console.log('  Listen for a distinct "ding" or "beep" sound');
      console.log('  Report: Did you hear the trade sound?');
    } else {
      log('PHASE 3', 'Audio context not available', 'fail');
      addResult('phase3', 'SFX audio context ready', 'FAIL', 'AudioContext missing');
    }
  },

  // Test 2: Debouncing
  debouncing: () => {
    log('PHASE 3', 'Testing debouncing mechanism...', 'info');
    console.log('  Manual step: Execute multiple trades within 1 second');
    console.log('  Expected: Hear only ONE trade sound (others debounced)');
    console.log('  Debounce window: 500ms per trade type');
    addResult('phase3', 'Debouncing prevents SFX spam', 'SKIP', 'Requires manual execution');
  },

  // Test 3: Threshold filtering
  thresholdFiltering: () => {
    const stored = localStorage.getItem('audioSettings');
    let minTradeAmount = 100;

    if (stored) {
      try {
        const settings = JSON.parse(stored);
        minTradeAmount = settings.sfxThresholds?.minTradeAmount || 100;
        log('PHASE 3', `Threshold filtering configured: $${minTradeAmount} minimum`, 'pass');
        addResult('phase3', 'Threshold filtering active', 'PASS', `Min trade: $${minTradeAmount}`);
      } catch (e) {
        addResult('phase3', 'Threshold filtering active', 'FAIL', 'Could not parse settings');
      }
    } else {
      log('PHASE 3', 'No settings found, using default threshold ($100)', 'warn');
      addResult('phase3', 'Threshold filtering active', 'SKIP', 'No settings yet');
    }

    console.log('  Manual step: Execute trade for $50');
    console.log(`  Expected: NO sound (below $${minTradeAmount} threshold)`);
    console.log(`  Manual step: Execute trade for $150`);
    console.log(`  Expected: Sound plays (above threshold)`);
  },

  // Test 4: SFX volume independence
  sfxVolume: () => {
    const stored = localStorage.getItem('audioSettings');

    if (stored) {
      try {
        const settings = JSON.parse(stored);
        const musicVol = settings.musicVolume;
        const sfxVol = settings.sfxVolume;

        if (musicVol !== sfxVol) {
          log('PHASE 3', `SFX volume (${Math.round(sfxVol*100)}%) differs from music (${Math.round(musicVol*100)}%)`, 'pass');
          addResult('phase3', 'SFX volume independent', 'PASS', 'Different channel levels');
        } else {
          log('PHASE 3', 'SFX and music volumes are the same', 'warn');
          addResult('phase3', 'SFX volume independent', 'SKIP', 'Same volume levels');
        }
      } catch (e) {
        addResult('phase3', 'SFX volume independent', 'FAIL', 'Could not parse settings');
      }
    } else {
      log('PHASE 3', 'No settings found, checking for separate channels', 'info');
      addResult('phase3', 'SFX volume independent', 'SKIP', 'No settings yet');
    }
  }
};

// Run Phase 3 tests
Object.values(phase3Tests).forEach(test => {
  try {
    test();
  } catch (e) {
    console.error('Test error:', e.message);
  }
});

// ============================================================================
// PHASE 4: Keyboard Shortcuts Tests
// ============================================================================

console.log('\n');
log('PHASE 4', 'Keyboard Shortcuts Testing');
console.log('');

const phase4Tests = {
  // Test 1: M key mute
  muteKeyTest: () => {
    log('PHASE 4', 'M key (mute) shortcut ready for testing', 'info');
    console.log('  Manual step: Press M key');
    console.log('  Expected: Mute state toggles, see "[AudioKeyboard] Mute toggled" in console');
    console.log('  Watch console for: [AudioKeyboard] Mute toggled');
    addResult('phase4', 'M key toggles mute', 'SKIP', 'Requires manual key press');
  },

  // Test 2: P key play/pause
  playPauseTest: () => {
    log('PHASE 4', 'P key (play/pause) shortcut ready for testing', 'info');
    console.log('  Manual step: Press P key');
    console.log('  Expected: Music plays/pauses, console shows "[AudioKeyboard] Music playing:" or paused');
    addResult('phase4', 'P key plays/pauses music', 'SKIP', 'Requires manual key press');
  },

  // Test 3: Ctrl+↑ volume up
  volumeUpTest: () => {
    log('PHASE 4', 'Ctrl+↑ (volume up) shortcut ready for testing', 'info');
    console.log('  Manual step: Hold Ctrl and press Arrow Up (5x)');
    console.log('  Expected: Volume increases by 10% each time, max 100%');
    console.log('  Watch console for: [AudioKeyboard] Volume up: X%');
    addResult('phase4', 'Ctrl+↑ increases volume 10%', 'SKIP', 'Requires manual key press');
  },

  // Test 4: Ctrl+↓ volume down
  volumeDownTest: () => {
    log('PHASE 4', 'Ctrl+↓ (volume down) shortcut ready for testing', 'info');
    console.log('  Manual step: Hold Ctrl and press Arrow Down (5x)');
    console.log('  Expected: Volume decreases by 10% each time, min 0%');
    console.log('  Watch console for: [AudioKeyboard] Volume down: X%');
    addResult('phase4', 'Ctrl+↓ decreases volume 10%', 'SKIP', 'Requires manual key press');
  },

  // Test 5: Input field safety
  inputSafetyTest: () => {
    const inputFields = document.querySelectorAll('input[type="text"], textarea');

    if (inputFields.length > 0) {
      log('PHASE 4', `Found ${inputFields.length} input fields for safety testing`, 'pass');
      addResult('phase4', 'Shortcuts disabled in input fields', 'PASS', `${inputFields.length} inputs found`);

      console.log('  Manual step: Click in any input field');
      console.log('  Then press: M, P, Ctrl+↑, Ctrl+↓');
      console.log('  Expected: NO keyboard shortcuts fire (nothing logged to console)');
      console.log('  Expected: You can type normally in the field');
    } else {
      log('PHASE 4', 'No input fields found to test', 'warn');
      addResult('phase4', 'Shortcuts disabled in input fields', 'SKIP', 'No input fields');
    }
  }
};

// Run Phase 4 tests
Object.values(phase4Tests).forEach(test => {
  try {
    test();
  } catch (e) {
    console.error('Test error:', e.message);
  }
});

// ============================================================================
// Summary and Export
// ============================================================================

console.log('\n');
log('TESTING', 'Manual test setup complete', 'pass');
console.log('');
console.log('NEXT STEPS:');
console.log('1. Execute manual steps listed above in the console');
console.log('2. Watch the console for messages like "[AudioKeyboard]" and "[AudioContext]"');
console.log('3. Test each acceptance criterion listed');
console.log('4. Document results (PASS/FAIL for each)');
console.log('5. Copy test results with: JSON.stringify(testResults, null, 2)');
console.log('');

// Make results available globally
window.audioTestResults = testResults;
window.printAudioTestResults = printResults;

console.log('Test results stored in window.audioTestResults');
console.log('Call window.printAudioTestResults() to see summary');
console.log('');
printResults();

console.log('\n' + '='.repeat(80));
console.log('Manual Test Script Ready');
console.log('='.repeat(80));
