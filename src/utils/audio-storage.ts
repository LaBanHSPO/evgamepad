/**
 * Audio Storage Utilities
 *
 * Handles localStorage persistence for audio settings
 */

import { AudioSettings, DEFAULT_AUDIO_SETTINGS } from '@/types/audio';

const AUDIO_SETTINGS_KEY = 'audioSettings';

/**
 * Save audio settings to localStorage
 *
 * @param settings - Audio settings to save
 */
export const saveAudioSettings = (settings: AudioSettings): void => {
  try {
    localStorage.setItem(AUDIO_SETTINGS_KEY, JSON.stringify(settings));
  } catch (error) {
    console.error('[AudioStorage] Failed to save settings:', error);
  }
};

/**
 * Load audio settings from localStorage
 *
 * @returns Audio settings or default settings if not found
 */
export const loadAudioSettings = (): AudioSettings => {
  try {
    const stored = localStorage.getItem(AUDIO_SETTINGS_KEY);
    if (!stored) {
      return DEFAULT_AUDIO_SETTINGS;
    }

    const parsed = JSON.parse(stored);

    // Merge with defaults to handle missing fields from older versions
    return {
      ...DEFAULT_AUDIO_SETTINGS,
      ...parsed
    };
  } catch (error) {
    console.error('[AudioStorage] Failed to load settings:', error);
    return DEFAULT_AUDIO_SETTINGS;
  }
};

/**
 * Clear audio settings from localStorage
 */
export const clearAudioSettings = (): void => {
  try {
    localStorage.removeItem(AUDIO_SETTINGS_KEY);
  } catch (error) {
    console.error('[AudioStorage] Failed to clear settings:', error);
  }
};

/**
 * Update specific audio setting
 *
 * @param key - Setting key to update
 * @param value - New value
 */
export const updateAudioSetting = <K extends keyof AudioSettings>(
  key: K,
  value: AudioSettings[K]
): void => {
  try {
    const settings = loadAudioSettings();
    settings[key] = value;
    saveAudioSettings(settings);
  } catch (error) {
    console.error('[AudioStorage] Failed to update setting:', error);
  }
};
