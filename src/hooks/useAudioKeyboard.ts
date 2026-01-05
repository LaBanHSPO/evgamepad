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
      // Prevent shortcuts when typing in inputs
      const target = e.target as HTMLElement;
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable
      ) {
        return;
      }

      // M - Toggle Mute
      if (e.key === 'm' || e.key === 'M') {
        e.preventDefault();
        toggleMute();
        console.log('[AudioKeyboard] Mute toggled');
      }

      // Ctrl+↑ - Volume Up
      if (e.ctrlKey && e.key === 'ArrowUp') {
        e.preventDefault();
        const newVolume = Math.min(volumes.master + 0.1, 1);
        setVolume('master', newVolume);
        console.log(`[AudioKeyboard] Volume up: ${Math.round(newVolume * 100)}%`);
      }

      // Ctrl+↓ - Volume Down
      if (e.ctrlKey && e.key === 'ArrowDown') {
        e.preventDefault();
        const newVolume = Math.max(volumes.master - 0.1, 0);
        setVolume('master', newVolume);
        console.log(`[AudioKeyboard] Volume down: ${Math.round(newVolume * 100)}%`);
      }

      // P - Play/Pause Music
      if (e.key === 'p' || e.key === 'P') {
        e.preventDefault();

        if (isPlaying) {
          pauseTrack();
          console.log('[AudioKeyboard] Music paused');
        } else {
          // Resume last track or play default
          const trackToPlay = currentTrack || availableTracks[0]?.id;
          if (trackToPlay) {
            playTrack(trackToPlay);
            console.log(`[AudioKeyboard] Music playing: ${trackToPlay}`);
          }
        }
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
