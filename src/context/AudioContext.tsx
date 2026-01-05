/**
 * AudioContext - React Context Provider for Audio System
 *
 * Wraps AudioManager service and provides audio state/actions to React components:
 * - Initializes Tone.js on mount
 * - Restores settings from localStorage
 * - Auto-resumes music if was playing before refresh
 * - Provides hooks for audio controls
 */

import React, { createContext, useContext, useEffect, useState, useCallback, useMemo } from 'react';
import { audioManager } from '@/services/audio-manager';
import { sfxEmitter } from '@/services/sfx-event-emitter';
import { AudioSettings, MusicTrack, SFXType, SFXOptions, VolumeChannel, SFXThresholds, MUSIC_TRACKS } from '@/types/audio';

/**
 * Audio Context value interface
 */
export interface AudioContextValue {
  // State
  isInitialized: boolean;
  currentTrack: string | null;
  isPlaying: boolean;
  isMuted: boolean;
  volumes: {
    master: number;
    music: number;
    sfx: number;
  };
  playbackPosition: number;
  availableTracks: MusicTrack[];
  settings: AudioSettings;

  // Actions
  initialize: () => Promise<void>;
  playTrack: (trackId: string) => Promise<void>;
  pauseTrack: () => void;
  stopTrack: () => void;
  setVolume: (channel: VolumeChannel, value: number) => void;
  toggleMute: () => void;
  playSFX: (type: SFXType, options?: SFXOptions) => void;
  setSfxThresholds: (thresholds: SFXThresholds) => void;
  saveSettings: () => void;
}

/**
 * Audio Context
 */
const AudioContext = createContext<AudioContextValue | undefined>(undefined);

/**
 * AudioProvider component
 */
export const AudioProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isInitialized, setIsInitialized] = useState(false);
  const [currentTrack, setCurrentTrack] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [volumes, setVolumes] = useState({
    master: 0.8,
    music: 0.7,
    sfx: 0.9
  });
  const [playbackPosition, setPlaybackPosition] = useState(0);
  const [settings, setSettings] = useState<AudioSettings>(audioManager.getSettings());

  /**
   * Initialize audio system on mount
   */
  const initialize = useCallback(async () => {
    if (isInitialized) {
      return;
    }

    try {
      // Initialize AudioManager
      await audioManager.initialize();

      // Load settings from localStorage
      const loadedSettings = audioManager.loadSettings();
      setSettings(loadedSettings);
      setVolumes({
        master: loadedSettings.masterVolume,
        music: loadedSettings.musicVolume,
        sfx: loadedSettings.sfxVolume
      });
      setIsMuted(loadedSettings.isMuted);
      setCurrentTrack(loadedSettings.currentTrackId);
      setPlaybackPosition(loadedSettings.playbackPosition);

      setIsInitialized(true);

      // Auto-resume music if was playing before refresh
      if (loadedSettings.currentTrackId && loadedSettings.playbackPosition > 0) {
        await audioManager.loadMusicTrack(loadedSettings.currentTrackId);
        audioManager.playMusic();
        setIsPlaying(true);
      }

      console.log('[AudioContext] Initialized successfully');
    } catch (error) {
      console.error('[AudioContext] Initialization failed:', error);
    }
  }, [isInitialized]);

  /**
   * Play music track
   */
  const playTrack = useCallback(async (trackId: string) => {
    try {
      await audioManager.loadMusicTrack(trackId);
      audioManager.playMusic();
      setCurrentTrack(trackId);
      setIsPlaying(true);

      // Save to settings
      audioManager.saveSettings();
    } catch (error) {
      console.error('[AudioContext] Failed to play track:', error);
    }
  }, []);

  /**
   * Pause music
   */
  const pauseTrack = useCallback(() => {
    audioManager.pauseMusic();
    setIsPlaying(false);
    setPlaybackPosition(audioManager.getCurrentPosition());

    // Save playback position
    audioManager.saveSettings();
  }, []);

  /**
   * Stop music
   */
  const stopTrack = useCallback(() => {
    audioManager.stopMusic();
    setIsPlaying(false);
    setPlaybackPosition(0);

    // Save settings
    audioManager.saveSettings();
  }, []);

  /**
   * Set volume for channel
   */
  const setVolume = useCallback((channel: VolumeChannel, value: number) => {
    audioManager.setVolume(channel, value);

    setVolumes(prev => ({
      ...prev,
      [channel]: value
    }));

    // Save settings
    audioManager.saveSettings();
  }, []);

  /**
   * Toggle mute
   */
  const toggleMute = useCallback(() => {
    audioManager.toggleMute();
    const newMuteState = !isMuted;
    setIsMuted(newMuteState);

    // Save settings
    audioManager.saveSettings();
  }, [isMuted]);

  /**
   * Play SFX
   */
  const playSFX = useCallback((type: SFXType, options?: SFXOptions) => {
    audioManager.playSFX(type, options);
  }, []);

  /**
   * Set SFX thresholds
   */
  const setSfxThresholds = useCallback((thresholds: SFXThresholds) => {
    // Update AudioManager settings
    audioManager.setSfxThresholds(thresholds);

    // Update sfxEmitter thresholds
    sfxEmitter.updateThresholds(thresholds);

    // Update local state
    setSettings(prev => ({
      ...prev,
      sfxThresholds: thresholds
    }));

    // Save to localStorage
    audioManager.saveSettings();
  }, []);

  /**
   * Save settings to localStorage
   */
  const saveSettings = useCallback(() => {
    audioManager.saveSettings();
  }, []);

  /**
   * Auto-initialize on mount (requires user gesture for iOS)
   */
  useEffect(() => {
    // Auto-initialize on first user interaction
    const handleFirstInteraction = () => {
      initialize();
      // Remove listeners after first interaction
      document.removeEventListener('click', handleFirstInteraction);
      document.removeEventListener('keydown', handleFirstInteraction);
    };

    document.addEventListener('click', handleFirstInteraction);
    document.addEventListener('keydown', handleFirstInteraction);

    return () => {
      document.removeEventListener('click', handleFirstInteraction);
      document.removeEventListener('keydown', handleFirstInteraction);
    };
  }, [initialize]);

  /**
   * Cleanup on unmount
   */
  useEffect(() => {
    return () => {
      if (isInitialized) {
        // Save current state before unmount
        audioManager.saveSettings();

        // Dispose AudioManager
        audioManager.dispose();
      }
    };
  }, [isInitialized]);

  /**
   * Update playback position periodically
   */
  useEffect(() => {
    if (!isPlaying) {
      return;
    }

    const interval = setInterval(() => {
      setPlaybackPosition(audioManager.getCurrentPosition());
    }, 1000); // Update every second

    return () => clearInterval(interval);
  }, [isPlaying]);

  /**
   * Save on page visibility change (user switches tabs)
   */
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden && isPlaying) {
        // Save position when tab becomes hidden
        audioManager.saveSettings();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [isPlaying]);

  /**
   * Memoized context value
   */
  const contextValue = useMemo<AudioContextValue>(
    () => ({
      isInitialized,
      currentTrack,
      isPlaying,
      isMuted,
      volumes,
      playbackPosition,
      availableTracks: MUSIC_TRACKS,
      settings,
      initialize,
      playTrack,
      pauseTrack,
      stopTrack,
      setVolume,
      toggleMute,
      playSFX,
      setSfxThresholds,
      saveSettings
    }),
    [
      isInitialized,
      currentTrack,
      isPlaying,
      isMuted,
      volumes,
      playbackPosition,
      settings,
      initialize,
      playTrack,
      pauseTrack,
      stopTrack,
      setVolume,
      toggleMute,
      playSFX,
      setSfxThresholds,
      saveSettings
    ]
  );

  return (
    <AudioContext.Provider value={contextValue}>
      {children}
    </AudioContext.Provider>
  );
};

/**
 * useAudioContext hook - for internal use
 */
export const useAudioContext = (): AudioContextValue => {
  const context = useContext(AudioContext);
  if (!context) {
    throw new Error('useAudioContext must be used within AudioProvider');
  }
  return context;
};
