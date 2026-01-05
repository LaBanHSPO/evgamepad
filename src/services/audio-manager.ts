/**
 * AudioManager Service
 *
 * Singleton service managing all Tone.js audio operations:
 * - Music playback (Player)
 * - SFX playback (Sampler)
 * - Volume controls
 * - localStorage persistence
 * - Browser autoplay policy handling
 */

import * as Tone from 'tone';
import {
  AudioSettings,
  SFXType,
  SFXOptions,
  VolumeChannel,
  MUSIC_TRACKS
} from '@/types/audio';
import { loadAudioSettings, saveAudioSettings } from '@/utils/audio-storage';

/**
 * AudioManager singleton class
 */
class AudioManager {
  private static instance: AudioManager | null = null;

  private initialized = false;
  private musicPlayer: Tone.Player | null = null;
  private sfxSampler: Tone.Sampler | null = null;
  private settings: AudioSettings;
  private lastSFXPlayTime: Map<SFXType, number> = new Map();
  private currentTrackId: string | null = null;

  // SFX debounce cooldown (ms)
  private readonly SFX_COOLDOWN_MS = 500;

  /**
   * Private constructor (singleton pattern)
   */
  private constructor() {
    this.settings = loadAudioSettings();
  }

  /**
   * Get singleton instance
   */
  public static getInstance(): AudioManager {
    if (!AudioManager.instance) {
      AudioManager.instance = new AudioManager();
    }
    return AudioManager.instance;
  }

  /**
   * Initialize Tone.js audio system
   * Requires user gesture for browser autoplay policy
   */
  public async initialize(): Promise<void> {
    if (this.initialized) {
      console.log('[AudioManager] Already initialized');
      return;
    }

    try {
      // Start Tone.js context (requires user gesture)
      await Tone.start();
      console.log('[AudioManager] Tone.js context started');

      // Initialize music player
      this.musicPlayer = new Tone.Player({
        loop: true,
        autostart: false,
        volume: this._calculateVolume('music')
      }).toDestination();

      // Initialize SFX sampler (preload SFX sounds)
      this.sfxSampler = new Tone.Sampler({
        urls: {
          C4: '/audio/sfx/trade-buy.mp3',
          D4: '/audio/sfx/trade-sell.mp3',
          E4: '/audio/sfx/market-alert.mp3',
          F4: '/audio/sfx/achievement.mp3',
          G4: '/audio/sfx/milestone.mp3'
        },
        volume: this._calculateVolume('sfx')
      }).toDestination();

      this.initialized = true;
      console.log('[AudioManager] Initialized successfully');
    } catch (error) {
      console.error('[AudioManager] Initialization failed:', error);
      throw error;
    }
  }

  /**
   * Check if AudioManager is initialized
   */
  public isInitialized(): boolean {
    return this.initialized;
  }

  /**
   * Load music track by ID
   *
   * @param trackId - Track ID from MUSIC_TRACKS
   */
  public async loadMusicTrack(trackId: string): Promise<void> {
    if (!this.musicPlayer) {
      throw new Error('AudioManager not initialized');
    }

    const track = MUSIC_TRACKS.find(t => t.id === trackId);
    if (!track) {
      throw new Error(`Track not found: ${trackId}`);
    }

    try {
      // Save current playback position if switching tracks
      if (this.currentTrackId && this.currentTrackId !== trackId) {
        this.settings.playbackPosition = 0; // Reset position on track change
      }

      // Load new track
      await this.musicPlayer.load(track.filePath);
      this.currentTrackId = trackId;
      this.settings.currentTrackId = trackId;

      console.log(`[AudioManager] Loaded track: ${track.name}`);
    } catch (error) {
      console.error('[AudioManager] Failed to load track:', error);
      throw error;
    }
  }

  /**
   * Play music
   */
  public playMusic(): void {
    if (!this.musicPlayer) {
      throw new Error('AudioManager not initialized');
    }

    if (!this.settings.isMuted) {
      // Seek to saved position
      if (this.settings.playbackPosition > 0) {
        this.musicPlayer.seek(this.settings.playbackPosition);
      }

      this.musicPlayer.start();
      console.log('[AudioManager] Music playing');
    }
  }

  /**
   * Pause music
   */
  public pauseMusic(): void {
    if (!this.musicPlayer) {
      throw new Error('AudioManager not initialized');
    }

    // Save current position before pausing
    this.settings.playbackPosition = this.getCurrentPosition();
    this.musicPlayer.stop();
    console.log('[AudioManager] Music paused');
  }

  /**
   * Stop music (reset position)
   */
  public stopMusic(): void {
    if (!this.musicPlayer) {
      throw new Error('AudioManager not initialized');
    }

    this.musicPlayer.stop();
    this.settings.playbackPosition = 0;
    console.log('[AudioManager] Music stopped');
  }

  /**
   * Seek to specific position
   *
   * @param position - Position in seconds
   */
  public seekMusic(position: number): void {
    if (!this.musicPlayer) {
      throw new Error('AudioManager not initialized');
    }

    this.musicPlayer.seek(position);
    this.settings.playbackPosition = position;
  }

  /**
   * Get current playback position
   *
   * @returns Current position in seconds
   */
  public getCurrentPosition(): number {
    if (!this.musicPlayer) {
      return 0;
    }

    // Tone.Player doesn't have immediate() method, use Tone.Transport.seconds
    return Tone.Transport.seconds;
  }

  /**
   * Check if music is playing
   */
  public isPlaying(): boolean {
    if (!this.musicPlayer) {
      return false;
    }

    return this.musicPlayer.state === 'started';
  }

  /**
   * Set volume for specific channel
   *
   * @param channel - Volume channel (master/music/sfx)
   * @param value - Volume value (0-1)
   */
  public setVolume(channel: VolumeChannel, value: number): void {
    const clampedValue = Math.max(0, Math.min(1, value));

    if (channel === 'master') {
      this.settings.masterVolume = clampedValue;
    } else if (channel === 'music') {
      this.settings.musicVolume = clampedValue;
    } else if (channel === 'sfx') {
      this.settings.sfxVolume = clampedValue;
    }

    // Update Tone.js volumes
    this._updateToneVolumes();
  }

  /**
   * Toggle mute
   */
  public toggleMute(): void {
    this.settings.isMuted = !this.settings.isMuted;

    if (this.settings.isMuted) {
      // Mute all
      if (this.musicPlayer) {
        this.musicPlayer.volume.value = -Infinity;
      }
      if (this.sfxSampler) {
        this.sfxSampler.volume.value = -Infinity;
      }
    } else {
      // Restore volumes
      this._updateToneVolumes();
    }

    console.log(`[AudioManager] Mute: ${this.settings.isMuted}`);
  }

  /**
   * Play SFX sound
   *
   * @param type - SFX type
   * @param options - Playback options
   */
  public playSFX(type: SFXType, options?: SFXOptions): void {
    if (!this.sfxSampler || this.settings.isMuted) {
      return;
    }

    // Debounce: prevent spam
    const now = Date.now();
    const lastPlayed = this.lastSFXPlayTime.get(type);
    if (lastPlayed && now - lastPlayed < this.SFX_COOLDOWN_MS) {
      return;
    }

    try {
      // Map SFX type to note
      const note = this._mapSFXTypeToNote(type);

      // Trigger sampler
      this.sfxSampler.triggerAttackRelease(
        note,
        '8n',
        undefined,
        options?.volume ?? 1
      );

      this.lastSFXPlayTime.set(type, now);
    } catch (error) {
      console.error('[AudioManager] Failed to play SFX:', error);
    }
  }

  /**
   * Save settings to localStorage
   */
  public saveSettings(): void {
    saveAudioSettings(this.settings);
    console.log('[AudioManager] Settings saved');
  }

  /**
   * Load settings from localStorage
   */
  public loadSettings(): AudioSettings {
    this.settings = loadAudioSettings();
    this._updateToneVolumes();
    return this.settings;
  }

  /**
   * Get current settings
   */
  public getSettings(): AudioSettings {
    return { ...this.settings };
  }

  /**
   * Set SFX thresholds
   *
   * @param thresholds - New SFX threshold configuration
   */
  public setSfxThresholds(thresholds: import('@/types/audio').SFXThresholds): void {
    this.settings.sfxThresholds = thresholds;
    this.saveSettings();
  }

  /**
   * Dispose AudioManager (cleanup)
   */
  public dispose(): void {
    if (this.musicPlayer) {
      this.musicPlayer.dispose();
      this.musicPlayer = null;
    }

    if (this.sfxSampler) {
      this.sfxSampler.dispose();
      this.sfxSampler = null;
    }

    this.initialized = false;
    console.log('[AudioManager] Disposed');
  }

  /**
   * Calculate Tone.js volume (dB) from settings
   *
   * @param channel - Volume channel
   * @returns Volume in dB
   */
  private _calculateVolume(channel: 'music' | 'sfx'): number {
    if (this.settings.isMuted) {
      return -Infinity;
    }

    const channelVolume =
      channel === 'music' ? this.settings.musicVolume : this.settings.sfxVolume;
    const finalVolume = this.settings.masterVolume * channelVolume;

    // Convert linear (0-1) to dB (Tone.js uses dB scale)
    return Tone.gainToDb(finalVolume);
  }

  /**
   * Update Tone.js player volumes based on settings
   */
  private _updateToneVolumes(): void {
    if (this.musicPlayer) {
      this.musicPlayer.volume.value = this._calculateVolume('music');
    }

    if (this.sfxSampler) {
      this.sfxSampler.volume.value = this._calculateVolume('sfx');
    }
  }

  /**
   * Map SFX type to sampler note
   *
   * @param type - SFX type
   * @returns MIDI note
   */
  private _mapSFXTypeToNote(type: SFXType): string {
    const map: Record<SFXType, string> = {
      'trade:buy': 'C4',
      'trade:sell': 'D4',
      'market:alert:low': 'E4',
      'market:alert:medium': 'E4',
      'market:alert:high': 'E4',
      'achievement:unlock': 'F4',
      'achievement:milestone': 'G4'
    };

    return map[type];
  }
}

// Export singleton instance
export const audioManager = AudioManager.getInstance();
