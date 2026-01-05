/**
 * Audio System TypeScript Type Definitions
 *
 * Defines interfaces for the Tone.js audio system including:
 * - Music tracks metadata
 * - Audio settings and configuration
 * - SFX event types
 * - Volume channel types
 */

/**
 * Music track metadata
 */
export interface MusicTrack {
  id: string;
  name: string;
  description: string;
  filePath: string;
  duration?: number; // in seconds
}

/**
 * Sound effect event types
 */
export type SFXType =
  | 'trade:buy'
  | 'trade:sell'
  | 'market:alert:low'
  | 'market:alert:medium'
  | 'market:alert:high'
  | 'achievement:unlock'
  | 'achievement:milestone';

/**
 * Volume channel types
 */
export type VolumeChannel = 'master' | 'music' | 'sfx';

/**
 * SFX threshold configuration
 */
export interface SFXThresholds {
  minTradeAmount: number;
  alertSeverity: 'all' | 'high';
}

/**
 * SFX event metadata
 */
export interface SFXEventMetadata {
  amount?: number;
  severity?: 'low' | 'medium' | 'high';
  symbol?: string;
}

/**
 * SFX event structure
 */
export interface SFXEvent {
  type: SFXType;
  metadata?: SFXEventMetadata;
}

/**
 * SFX playback options
 */
export interface SFXOptions {
  volume?: number;
  pitch?: number;
}

/**
 * Audio settings persisted to localStorage
 */
export interface AudioSettings {
  masterVolume: number;      // 0-1
  musicVolume: number;        // 0-1
  sfxVolume: number;          // 0-1
  isMuted: boolean;
  currentTrackId: string | null;
  playbackPosition: number;   // in seconds
  sfxThresholds: SFXThresholds;
}

/**
 * Default audio settings
 */
export const DEFAULT_AUDIO_SETTINGS: AudioSettings = {
  masterVolume: 0.8,
  musicVolume: 0.7,
  sfxVolume: 0.9,
  isMuted: false,
  currentTrackId: null,
  playbackPosition: 0,
  sfxThresholds: {
    minTradeAmount: 100,
    alertSeverity: 'all'
  }
};

/**
 * Available music tracks
 */
export const MUSIC_TRACKS: MusicTrack[] = [
  {
    id: 'focus-ambient',
    name: 'Focus Ambient',
    description: 'Calm, minimal distraction',
    filePath: '/audio/music/focus-ambient.mp3'
  },
  {
    id: 'energy-upbeat',
    name: 'Energy Upbeat',
    description: 'High-tempo trading',
    filePath: '/audio/music/energy-upbeat.mp3'
  },
  {
    id: 'strategy-chill',
    name: 'Strategy Chill',
    description: 'Mid-tempo analytical',
    filePath: '/audio/music/strategy-chill.mp3'
  },
  {
    id: 'night-lofi',
    name: 'Night Lofi',
    description: 'Low-energy late sessions',
    filePath: '/audio/music/night-lofi.mp3'
  }
];
