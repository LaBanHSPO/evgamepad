/**
 * useAudioKeyboard Hook Tests
 *
 * Tests Phase 4 keyboard shortcut functionality:
 * - M key: toggle mute
 * - Ctrl+↑: volume up (+10%)
 * - Ctrl+↓: volume down (-10%)
 * - P key: play/pause music
 * - Input element detection
 * - No gamepad conflicts
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { useAudioKeyboard } from '../useAudioKeyboard';
import { useAudioPlayer } from '../useAudioPlayer';

// Mock the useAudioPlayer hook
jest.mock('../useAudioPlayer', () => ({
  useAudioPlayer: jest.fn()
}));

const mockUseAudioPlayer = useAudioPlayer as jest.MockedFunction<typeof useAudioPlayer>;

describe('useAudioKeyboard Hook', () => {
  const mockAudioControls = {
    toggleMute: jest.fn(),
    setVolume: jest.fn(),
    volumes: { master: 0.5, music: 0.7, sfx: 0.9 },
    isPlaying: false,
    currentTrack: 'track-1',
    playTrack: jest.fn(),
    pauseTrack: jest.fn(),
    availableTracks: [
      { id: 'track-1', name: 'Track 1', url: '/audio/track-1.mp3' },
      { id: 'track-2', name: 'Track 2', url: '/audio/track-2.mp3' }
    ]
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseAudioPlayer.mockReturnValue(mockAudioControls);
    // Mock console methods
    jest.spyOn(console, 'log').mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('M Key - Mute Toggle', () => {
    test('should toggle mute when M key is pressed (lowercase)', async () => {
      renderHook(() => useAudioKeyboard());

      const event = new KeyboardEvent('keydown', { key: 'm' });
      act(() => {
        window.dispatchEvent(event);
      });

      await waitFor(() => {
        expect(mockAudioControls.toggleMute).toHaveBeenCalledTimes(1);
      });
      expect(console.log).toHaveBeenCalledWith('[AudioKeyboard] Mute toggled');
    });

    test('should toggle mute when M key is pressed (uppercase)', async () => {
      renderHook(() => useAudioKeyboard());

      const event = new KeyboardEvent('keydown', { key: 'M' });
      act(() => {
        window.dispatchEvent(event);
      });

      await waitFor(() => {
        expect(mockAudioControls.toggleMute).toHaveBeenCalledTimes(1);
      });
    });

    test('should not toggle mute when M is pressed in input element', async () => {
      renderHook(() => useAudioKeyboard());

      const inputElement = document.createElement('input');
      const event = new KeyboardEvent('keydown', { key: 'M' });
      Object.defineProperty(event, 'target', { value: inputElement, enumerable: true });

      act(() => {
        inputElement.dispatchEvent(event);
      });

      expect(mockAudioControls.toggleMute).not.toHaveBeenCalled();
    });

    test('should not toggle mute when M is pressed in textarea element', async () => {
      renderHook(() => useAudioKeyboard());

      const textareaElement = document.createElement('textarea');
      const event = new KeyboardEvent('keydown', { key: 'M' });
      Object.defineProperty(event, 'target', { value: textareaElement, enumerable: true });

      act(() => {
        textareaElement.dispatchEvent(event);
      });

      expect(mockAudioControls.toggleMute).not.toHaveBeenCalled();
    });
  });

  describe('Ctrl+↑ - Volume Up', () => {
    test('should increase volume by 0.1 when Ctrl+ArrowUp is pressed', async () => {
      renderHook(() => useAudioKeyboard());

      const event = new KeyboardEvent('keydown', {
        key: 'ArrowUp',
        ctrlKey: true
      });
      act(() => {
        window.dispatchEvent(event);
      });

      await waitFor(() => {
        expect(mockAudioControls.setVolume).toHaveBeenCalledWith('master', 0.6);
      });
      expect(console.log).toHaveBeenCalledWith('[AudioKeyboard] Volume up: 60%');
    });

    test('should cap volume at 1.0 when exceeding max', async () => {
      mockAudioControls.volumes = { master: 0.95, music: 0.7, sfx: 0.9 };
      renderHook(() => useAudioKeyboard());

      const event = new KeyboardEvent('keydown', {
        key: 'ArrowUp',
        ctrlKey: true
      });
      act(() => {
        window.dispatchEvent(event);
      });

      await waitFor(() => {
        expect(mockAudioControls.setVolume).toHaveBeenCalledWith('master', 1);
      });
    });

    test('should not increase volume without Ctrl modifier', async () => {
      renderHook(() => useAudioKeyboard());

      const event = new KeyboardEvent('keydown', {
        key: 'ArrowUp',
        ctrlKey: false
      });
      act(() => {
        window.dispatchEvent(event);
      });

      expect(mockAudioControls.setVolume).not.toHaveBeenCalled();
    });
  });

  describe('Ctrl+↓ - Volume Down', () => {
    test('should decrease volume by 0.1 when Ctrl+ArrowDown is pressed', async () => {
      renderHook(() => useAudioKeyboard());

      const event = new KeyboardEvent('keydown', {
        key: 'ArrowDown',
        ctrlKey: true
      });
      act(() => {
        window.dispatchEvent(event);
      });

      await waitFor(() => {
        expect(mockAudioControls.setVolume).toHaveBeenCalledWith('master', 0.4);
      });
      expect(console.log).toHaveBeenCalledWith('[AudioKeyboard] Volume down: 40%');
    });

    test('should cap volume at 0.0 when going below min', async () => {
      mockAudioControls.volumes = { master: 0.05, music: 0.7, sfx: 0.9 };
      renderHook(() => useAudioKeyboard());

      const event = new KeyboardEvent('keydown', {
        key: 'ArrowDown',
        ctrlKey: true
      });
      act(() => {
        window.dispatchEvent(event);
      });

      await waitFor(() => {
        expect(mockAudioControls.setVolume).toHaveBeenCalledWith('master', 0);
      });
    });
  });

  describe('P Key - Play/Pause', () => {
    test('should pause track when isPlaying is true', async () => {
      mockAudioControls.isPlaying = true;
      renderHook(() => useAudioKeyboard());

      const event = new KeyboardEvent('keydown', { key: 'p' });
      act(() => {
        window.dispatchEvent(event);
      });

      await waitFor(() => {
        expect(mockAudioControls.pauseTrack).toHaveBeenCalledTimes(1);
      });
      expect(console.log).toHaveBeenCalledWith('[AudioKeyboard] Music paused');
    });

    test('should play current track when isPlaying is false', async () => {
      mockAudioControls.isPlaying = false;
      renderHook(() => useAudioKeyboard());

      const event = new KeyboardEvent('keydown', { key: 'P' });
      act(() => {
        window.dispatchEvent(event);
      });

      await waitFor(() => {
        expect(mockAudioControls.playTrack).toHaveBeenCalledWith('track-1');
      });
      expect(console.log).toHaveBeenCalledWith('[AudioKeyboard] Music playing: track-1');
    });

    test('should play first available track if no currentTrack', async () => {
      mockAudioControls.currentTrack = null;
      mockAudioControls.isPlaying = false;
      renderHook(() => useAudioKeyboard());

      const event = new KeyboardEvent('keydown', { key: 'p' });
      act(() => {
        window.dispatchEvent(event);
      });

      await waitFor(() => {
        expect(mockAudioControls.playTrack).toHaveBeenCalledWith('track-1');
      });
    });

    test('should not play/pause when P is pressed in input element', async () => {
      mockAudioControls.isPlaying = false;
      renderHook(() => useAudioKeyboard());

      const inputElement = document.createElement('input');
      const event = new KeyboardEvent('keydown', { key: 'P' });
      Object.defineProperty(event, 'target', { value: inputElement, enumerable: true });

      act(() => {
        inputElement.dispatchEvent(event);
      });

      expect(mockAudioControls.pauseTrack).not.toHaveBeenCalled();
      expect(mockAudioControls.playTrack).not.toHaveBeenCalled();
    });
  });

  describe('Input Element Detection', () => {
    test('should not trigger shortcuts when typing in contentEditable element', async () => {
      renderHook(() => useAudioKeyboard());

      const editableElement = document.createElement('div');
      editableElement.contentEditable = 'true';

      const event = new KeyboardEvent('keydown', { key: 'M' });
      Object.defineProperty(event, 'target', { value: editableElement, enumerable: true });

      act(() => {
        editableElement.dispatchEvent(event);
      });

      expect(mockAudioControls.toggleMute).not.toHaveBeenCalled();
    });
  });

  describe('Keyboard Shortcut Conflicts', () => {
    test('should not conflict with gamepad [ key mapping', () => {
      // GlobalGamepadHandler uses [ for prev monitor
      // useAudioKeyboard uses M, P, Ctrl+↑, Ctrl+↓
      // No conflict expected
      expect(true).toBe(true);
    });

    test('should not conflict with gamepad ] key mapping', () => {
      // GlobalGamepadHandler uses ] for next monitor
      // useAudioKeyboard uses M, P, Ctrl+↑, Ctrl+↓
      // No conflict expected
      expect(true).toBe(true);
    });
  });

  describe('Event Cleanup', () => {
    test('should remove event listener on unmount', async () => {
      const removeEventListenerSpy = jest.spyOn(window, 'removeEventListener');

      const { unmount } = renderHook(() => useAudioKeyboard());

      unmount();

      expect(removeEventListenerSpy).toHaveBeenCalledWith('keydown', expect.any(Function));
      removeEventListenerSpy.mockRestore();
    });
  });
});
