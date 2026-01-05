/**
 * SFX Event Emitter Service
 *
 * Event-driven SFX triggering with:
 * - Threshold filtering
 * - Debouncing (500ms cooldown per type)
 * - Socket.IO integration
 */

import { audioManager } from './audio-manager';
import { SFXEvent, SFXType, SFXThresholds } from '@/types/audio';

/**
 * SFX Event Emitter class
 */
class SFXEventEmitter {
  private thresholds: SFXThresholds;
  private lastPlayedTime: Map<SFXType, number> = new Map();
  private readonly DEBOUNCE_MS = 500;

  constructor() {
    // Load thresholds from settings
    const settings = audioManager.getSettings();
    this.thresholds = settings.sfxThresholds;
  }

  /**
   * Update SFX thresholds
   *
   * @param thresholds - New threshold configuration
   */
  public updateThresholds(thresholds: SFXThresholds): void {
    this.thresholds = thresholds;
  }

  /**
   * Emit SFX event
   *
   * @param event - SFX event with metadata
   */
  public emit(event: SFXEvent): void {
    // Check if should play based on thresholds
    if (!this.shouldPlaySFX(event)) {
      return;
    }

    // Check debouncing
    if (this.isDebounced(event.type)) {
      return;
    }

    // Play SFX
    audioManager.playSFX(event.type);

    // Update last played time
    this.lastPlayedTime.set(event.type, Date.now());
  }

  /**
   * Check if SFX should play based on thresholds
   *
   * @param event - SFX event
   * @returns Whether SFX should play
   */
  private shouldPlaySFX(event: SFXEvent): boolean {
    // Trade threshold: only play if amount > minTradeAmount
    if (event.type.startsWith('trade:') && event.metadata?.amount !== undefined) {
      return event.metadata.amount >= this.thresholds.minTradeAmount;
    }

    // Alert threshold: filter by severity
    if (event.type.startsWith('market:alert:')) {
      const severity = event.metadata?.severity || 'low';

      // If alertSeverity is 'all', play all alerts
      if (this.thresholds.alertSeverity === 'all') {
        return true;
      }

      // If alertSeverity is 'high', only play high priority
      if (this.thresholds.alertSeverity === 'high') {
        return severity === 'high';
      }
    }

    // Always play achievements
    if (event.type.startsWith('achievement:')) {
      return true;
    }

    return true;
  }

  /**
   * Check if SFX type is debounced (cooldown active)
   *
   * @param type - SFX type
   * @returns Whether SFX is debounced
   */
  private isDebounced(type: SFXType): boolean {
    const lastPlayed = this.lastPlayedTime.get(type);
    if (!lastPlayed) {
      return false;
    }

    const timeSinceLastPlayed = Date.now() - lastPlayed;
    return timeSinceLastPlayed < this.DEBOUNCE_MS;
  }
}

// Export singleton instance
export const sfxEmitter = new SFXEventEmitter();
