# Audio System Quick Test Checklist
**Tone.js Phase 2, 3, 4 - Manual Verification Checklist**

Complete this checklist while running the application in browser.

---

## Phase 2: React Context & UI Integration
**Time Estimate: 10-15 minutes**

### Module 1: Modal Interaction

- [ ] Settings button visible in header
  - Where: Look for gear/settings icon in top navigation
  - Expected: Button is clickable

- [ ] Click settings button
  - Expected: Modal dialog opens
  - Appearance: Should be centered, dark/light theme matches app

- [ ] Modal displays correctly
  - Expected: Title "Audio Settings" visible
  - Expected: Multiple sections visible (Music, Volume Controls, etc.)

- [ ] Radio buttons for music tracks visible
  - Count: Should see 4 track options
  - Options: Focus Ambient, Energy Upbeat, Strategy Chill, Night Lofi

- [ ] Click different music track
  - Action: Select "Energy Upbeat"
  - Expected: Radio button selected (filled)
  - Expected: Can hear different music (if audio files exist)

### Module 2: Volume Controls

- [ ] Three volume sliders visible
  - Expected: Master, Music, SFX sliders
  - Labels: Should show percentages (e.g., "80%")

- [ ] Adjust Master volume slider
  - Action: Drag slider to 50%
  - Expected: Audio volume changes in real-time
  - Expected: Percentage updates immediately

- [ ] Adjust Music volume slider
  - Action: Drag to different level
  - Expected: Music volume changes independently

- [ ] Adjust SFX volume slider
  - Action: Drag to different level
  - Expected: SFX volume can differ from music

- [ ] Mute toggle available
  - Expected: Switch toggle in modal
  - Expected: Keyboard hint shows "M"

### Module 3: Settings Persistence

- [ ] Click "Save" button
  - Expected: Modal closes smoothly
  - Expected: Settings applied to audio system

- [ ] Refresh page (Ctrl+R or Cmd+R)
  - Expected: Settings restored
  - Expected: Same track selected
  - Expected: Same volume levels
  - Expected: Music resumes from same position (if was playing)

- [ ] Open DevTools (F12)
  - Go to Application → localStorage
  - Look for: "audioSettings" key
  - Expected: Contains JSON with volumes and track info

### Phase 2 Result: [ ] PASS [ ] FAIL [ ] PARTIAL

---

## Phase 3: Sound Effects System
**Time Estimate: 10-15 minutes**

### Prerequisites
- Audio files must exist at `/public/audio/sfx/`
- Navigate to trading section of application

### Module 1: Trade Sound Effects

- [ ] Execute a trade buy for amount > $100
  - Action: Buy stock for $150+
  - Expected: Hear a distinct "buy" sound (different tone)
  - Console: Check for "[AudioManager] Played SFX: trade:buy"

- [ ] Execute a trade sell for amount > $100
  - Action: Sell stock for $150+
  - Expected: Hear different "sell" sound (lower pitch)
  - Console: Check for "[AudioManager] Played SFX: trade:sell"

- [ ] Execute multiple trades within 1 second
  - Action: Buy/sell rapidly (3+ trades in succession)
  - Expected: Hear only FIRST sound
  - Expected: Other sounds blocked by debouncing
  - Console: Some SFX logs might be missing (debounced)

### Module 2: Threshold Filtering

- [ ] Execute trade for amount < $100
  - Action: Buy/sell for $50
  - Expected: NO sound plays
  - Reason: Below $100 threshold (default)

- [ ] Execute trade for amount >= $100
  - Action: Buy/sell for $100
  - Expected: Sound plays
  - Reason: Meets or exceeds threshold

- [ ] Open Settings modal
  - Change "Min Trade Amount" to $200
  - Save settings
  - Execute trade for $150
  - Expected: NO sound (below new threshold)
  - Execute trade for $250
  - Expected: Sound plays

### Module 3: Alert SFX

- [ ] Trigger portfolio alert
  - Action: Buy/sell to cause portfolio health = DANGER
  - Expected: Hear alert sound
  - Expected: Different from trade sounds

- [ ] Open Settings → "Alert Severity"
  - Change to "High Priority Only"
  - Save settings
  - Trigger low-priority alert
  - Expected: NO sound

- [ ] Trigger high-priority alert
  - Expected: Sound plays
  - Expected: Different/louder alert sound

### Module 4: Volume Independence

- [ ] Open Settings modal
  - Set Master Volume: 80%
  - Set Music Volume: 50%
  - Set SFX Volume: 100%
  - Save settings

- [ ] Play music
  - Expected: Music at lower volume

- [ ] Execute trade
  - Expected: SFX at full volume (louder than music)

- [ ] Adjust music slider while playing
  - Action: Change Music Volume to 100%
  - Expected: Music gets louder but SFX volume unchanged

- [ ] Adjust SFX slider
  - Action: Change SFX Volume to 30%
  - Expected: Next SFX is much quieter
  - Expected: Music volume unchanged

### Phase 3 Result: [ ] PASS [ ] FAIL [ ] PARTIAL

---

## Phase 4: Keyboard Shortcuts
**Time Estimate: 10 minutes**

### Prerequisites
- Open DevTools Console (F12)
- Watch for "[AudioKeyboard]" log messages

### Module 1: M Key - Mute Toggle

- [ ] Press M key
  - Expected: Audio mutes (volume goes to 0)
  - Console: "[AudioKeyboard] Mute toggled"

- [ ] Press M key again
  - Expected: Audio unmutes (volume returns)
  - Console: "[AudioKeyboard] Mute toggled" again

- [ ] Check Settings modal
  - Open settings
  - Expected: Mute switch toggle reflects current state
  - Close and repeat mute test

### Module 2: Ctrl+↑ - Volume Up

- [ ] Note current volume in settings
  - Expected: Something like 80%

- [ ] Press Ctrl+↑ (Ctrl + Up Arrow)
  - Expected: Volume increases by 10% (80% → 90%)
  - Console: "[AudioKeyboard] Volume up: 90%"

- [ ] Press Ctrl+↑ multiple times
  - Expected: Volume increases 10% each time
  - Expected: Stops at 100% (doesn't go over)
  - Console: "[AudioKeyboard] Volume up: 100%"

- [ ] Press Ctrl+↑ when already at 100%
  - Expected: Stays at 100%
  - Console: Message still logged but volume unchanged

### Module 3: Ctrl+↓ - Volume Down

- [ ] Press Ctrl+↓ (Ctrl + Down Arrow)
  - Expected: Volume decreases by 10%
  - Console: "[AudioKeyboard] Volume down: X%"

- [ ] Press Ctrl+↓ multiple times
  - Expected: Decreases 10% each time
  - Expected: Stops at 0% (doesn't go negative)
  - Console: "[AudioKeyboard] Volume down: 0%"

- [ ] Press Ctrl+↓ when at 0%
  - Expected: Stays at 0%
  - Console: Message logged

### Module 4: P Key - Play/Pause

- [ ] Press P key when music is stopped
  - Expected: Music starts playing
  - Expected: From beginning or saved position
  - Console: "[AudioKeyboard] Music playing: [track-name]"

- [ ] Press P key while music is playing
  - Expected: Music pauses
  - Expected: Playback position is saved
  - Console: "[AudioKeyboard] Music paused"

- [ ] Press P key again
  - Expected: Music resumes from where it paused
  - Expected: No interruption or restart

- [ ] Change track in settings
  - Select different music
  - Save settings
  - Press P to play
  - Expected: New track plays
  - Console: Shows new track name

### Module 5: Input Field Safety

- [ ] Click on a text input field
  - Example: Trading amount input, search box, chat input
  - Expected: Focus cursor in field

- [ ] Type some text
  - Action: Type "hello"
  - Expected: Text appears in input

- [ ] Press M key
  - Expected: 'm' appears in text (normal typing)
  - Expected: NO audio mute happens
  - Console: NO "[AudioKeyboard]" message
  - Audio should still be playing

- [ ] Press P key
  - Expected: 'p' appears in text
  - Expected: Music does NOT pause
  - Console: NO shortcut message

- [ ] Press Ctrl+↑
  - Expected: No volume change
  - Expected: No console message
  - Text field behavior depends on app

- [ ] Click outside input field
  - Focus moves away from input

- [ ] Press M key
  - Expected: Audio mutes
  - Console: "[AudioKeyboard] Mute toggled"
  - Shortcuts work again

### Module 6: Textarea Test

- [ ] Click in a textarea field
  - Example: Chat message area, note field

- [ ] Press all shortcuts (M, P, Ctrl+↑, Ctrl+↓)
  - Expected: No shortcuts fire
  - Expected: Normal text input behavior
  - Expected: Typing works normally

- [ ] Click outside textarea
  - Expected: Focus moves away

- [ ] Press shortcuts again
  - Expected: Shortcuts work
  - Console: Appropriate messages logged

### Phase 4 Result: [ ] PASS [ ] FAIL [ ] PARTIAL

---

## Browser DevTools Checks

### Console Log Verification

While testing, check DevTools console (F12 → Console tab) for these patterns:

**Phase 2 Logs (expected during modal operations):**
```
[AudioContext] Initialized successfully
[AudioManager] Initialized successfully
[AudioManager] Settings saved
[AudioManager] Loaded track: [track-name]
[AudioManager] Music playing
[AudioManager] Music paused
```

**Phase 3 Logs (expected during trades/alerts):**
```
[AudioManager] Played SFX: trade:buy
[AudioManager] Played SFX: trade:sell
[AudioManager] Played SFX: market:alert:high
```

**Phase 4 Logs (expected for keyboard shortcuts):**
```
[AudioKeyboard] Mute toggled
[AudioKeyboard] Volume up: 90%
[AudioKeyboard] Volume down: 70%
[AudioKeyboard] Music playing: [track-id]
[AudioKeyboard] Music paused
```

### localStorage Inspection

**Steps:**
1. Open DevTools → Application tab
2. Left sidebar → Storage → localStorage
3. Find: http://localhost:5173 (or your URL)
4. Click to expand
5. Look for key: "audioSettings"
6. Click to view value

**Expected JSON structure:**
```json
{
  "masterVolume": 0.8,
  "musicVolume": 0.7,
  "sfxVolume": 0.9,
  "isMuted": false,
  "currentTrackId": "focus-ambient",
  "playbackPosition": 45.2,
  "sfxThresholds": {
    "minTradeAmount": 100,
    "alertSeverity": "all"
  }
}
```

---

## Summary Results

### Overall Test Status

**Phase 2 (Context & UI):** [ ] PASS [ ] FAIL [ ] PARTIAL
- Modal interactions: [ ] OK
- Settings persistence: [ ] OK
- Auto-resume on refresh: [ ] OK

**Phase 3 (Sound Effects):** [ ] PASS [ ] FAIL [ ] PARTIAL
- Trade sounds: [ ] OK
- Threshold filtering: [ ] OK
- Debouncing: [ ] OK
- Alert sounds: [ ] OK
- Volume independence: [ ] OK

**Phase 4 (Keyboard):** [ ] PASS [ ] FAIL [ ] PARTIAL
- M key mute: [ ] OK
- Ctrl+↑ volume up: [ ] OK
- Ctrl+↓ volume down: [ ] OK
- P key play/pause: [ ] OK
- Input field safety: [ ] OK

### Test Date: _______________
### Tester Name: _______________
### Browser: _______________
### OS: _______________

### Issues Found:
(List any failures, unexpected behavior, errors, etc.)

1.
2.
3.

### Notes:
(Any additional observations, slow features, visual glitches, etc.)

---

## Submission

After completing all tests:

1. Screenshot console logs if any issues found
2. Document all failures with error messages
3. Note browser/OS/device used
4. Submit this checklist with results

**Expected Result:** All items should be [✓] PASS

---

**Test Checklist Version:** 1.0
**Created:** 2026-01-01
**Last Updated:** 2026-01-01
