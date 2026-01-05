/**
 * useSoundEffects Hook
 *
 * Convenience hook for SFX playback
 */

import { useCallback } from 'react';
import { useAudioContext } from '@/context/AudioContext';
import { SFXType, SFXOptions } from '@/types/audio';

/**
 * Sound effects hook interface
 */
export interface UseSoundEffectsReturn {
  playSFX: (type: SFXType, options?: SFXOptions) => void;
  playTradeBuy: (amount?: number) => void;
  playTradeSell: (amount?: number) => void;
  playMarketAlert: (severity?: 'low' | 'medium' | 'high') => void;
  playAchievement: () => void;
  playMilestone: () => void;
}

/**
 * useSoundEffects hook
 *
 * @returns SFX playback functions
 */
export const useSoundEffects = (): UseSoundEffectsReturn => {
  const { playSFX } = useAudioContext();

  const playTradeBuy = useCallback((amount?: number) => {
    playSFX('trade:buy', { volume: amount ? Math.min(amount / 1000, 1) : 1 });
  }, [playSFX]);

  const playTradeSell = useCallback((amount?: number) => {
    playSFX('trade:sell', { volume: amount ? Math.min(amount / 1000, 1) : 1 });
  }, [playSFX]);

  const playMarketAlert = useCallback((severity: 'low' | 'medium' | 'high' = 'medium') => {
    const sfxType: SFXType = `market:alert:${severity}`;
    playSFX(sfxType);
  }, [playSFX]);

  const playAchievement = useCallback(() => {
    playSFX('achievement:unlock');
  }, [playSFX]);

  const playMilestone = useCallback(() => {
    playSFX('achievement:milestone');
  }, [playSFX]);

  return {
    playSFX,
    playTradeBuy,
    playTradeSell,
    playMarketAlert,
    playAchievement,
    playMilestone
  };
};
