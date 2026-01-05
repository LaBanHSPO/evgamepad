/**
 * useAudioKeyboard Hook
 *
 * Global keyboard shortcuts for audio controls:
 * - M: Toggle mute
 * - Ctrl+↑: Volume up (+10%)
 * - Ctrl+↓: Volume down (-10%)
 * - P: Play/pause music
 */

import { useEffect } from 'react';
import { useAudioPlayer } from './useAudioPlayer';

/**
 * useAudioKeyboard hook
 *
 * Registers global keyboard shortcuts for audio controls
 */
export const useAudioKeyboard = (): void => {
  const {
    toggleMute,
    setVolume,
    volumes,
    isPlaying,
    currentTrack,
    playTrack,
    pauseTrack,
    availableTracks
  } = useAudioPlayer();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Prevent shortcuts when typing in inputs/textareas
      const target = e.target as HTMLElement;
      if (
        target instanceof HTMLInputElement ||
        target instanceof HTMLTextAreaElement ||
        target.isContentEditable
      ) {
        return;
      }

      // M - Toggle Mute
      if (e.key === 'm' || e.key === 'M') {
        e.preventDefault();
        toggleMute();
        return;
      }

      // Ctrl+↑ - Volume Up
      if (e.ctrlKey && e.key === 'ArrowUp') {
        e.preventDefault();
        const newVolume = Math.min(volumes.master + 0.1, 1);
        setVolume('master', newVolume);
        return;
      }

      // Ctrl+↓ - Volume Down
      if (e.ctrlKey && e.key === 'ArrowDown') {
        e.preventDefault();
        const newVolume = Math.max(volumes.master - 0.1, 0);
        setVolume('master', newVolume);
        return;
      }

      // P - Play/Pause Music
      if (e.key === 'p' || e.key === 'P') {
        e.preventDefault();

        if (isPlaying) {
          pauseTrack();
        } else {
          // Resume last track or play default
          const trackToPlay = currentTrack || availableTracks[0]?.id;
          if (trackToPlay) {
            playTrack(trackToPlay);
          }
        }
        return;
      }
    };

    // Register event listener
    window.addEventListener('keydown', handleKeyDown);

    // Cleanup
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [
    toggleMute,
    setVolume,
    volumes,
    isPlaying,
    currentTrack,
    playTrack,
    pauseTrack,
    availableTracks
  ]);
};
