/**
 * useAudioPlayer Hook
 *
 * Convenience hook wrapping AudioContext for music playback controls
 */

import { useAudioContext, AudioContextValue } from '@/context/AudioContext';

/**
 * Audio player hook interface
 */
export interface UseAudioPlayerReturn extends AudioContextValue {}

/**
 * useAudioPlayer hook
 *
 * @returns Audio player controls and state
 */
export const useAudioPlayer = (): UseAudioPlayerReturn => {
  return useAudioContext();
};
