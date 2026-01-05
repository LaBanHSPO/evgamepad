/**
 * AudioSettingsModal Component
 *
 * Modal UI for audio configuration:
 * - Music track selector
 * - Volume sliders (master, music, SFX)
 * - Mute toggle
 * - SFX threshold settings
 * - Keyboard shortcut hints
 */

import React, { useState, useEffect } from 'react';
import { Volume2, VolumeX } from 'lucide-react';
import { useAudioPlayer } from '@/hooks/useAudioPlayer';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter
} from '@/components/ui/dialog';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '@/components/ui/select';

interface AudioSettingsModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export const AudioSettingsModal: React.FC<AudioSettingsModalProps> = ({
  open,
  onOpenChange
}) => {
  const {
    currentTrack,
    volumes,
    isMuted,
    availableTracks,
    settings,
    playTrack,
    setVolume,
    toggleMute,
    setSfxThresholds,
    saveSettings
  } = useAudioPlayer();

  // Local state for settings (allows cancel)
  const [localTrackId, setLocalTrackId] = useState(currentTrack || '');
  const [localMasterVolume, setLocalMasterVolume] = useState(volumes.master);
  const [localMusicVolume, setLocalMusicVolume] = useState(volumes.music);
  const [localSfxVolume, setLocalSfxVolume] = useState(volumes.sfx);
  const [localIsMuted, setLocalIsMuted] = useState(isMuted);
  const [localMinTradeAmount, setLocalMinTradeAmount] = useState(
    settings.sfxThresholds.minTradeAmount
  );
  const [localAlertSeverity, setLocalAlertSeverity] = useState(
    settings.sfxThresholds.alertSeverity
  );

  /**
   * Sync local state with context when modal opens
   */
  useEffect(() => {
    if (open) {
      setLocalTrackId(currentTrack || '');
      setLocalMasterVolume(volumes.master);
      setLocalMusicVolume(volumes.music);
      setLocalSfxVolume(volumes.sfx);
      setLocalIsMuted(isMuted);
      setLocalMinTradeAmount(settings.sfxThresholds.minTradeAmount);
      setLocalAlertSeverity(settings.sfxThresholds.alertSeverity);
    }
  }, [open, currentTrack, volumes, isMuted, settings]);

  /**
   * Handle save
   */
  const handleSave = () => {
    // Apply track change
    if (localTrackId && localTrackId !== currentTrack) {
      playTrack(localTrackId);
    }

    // Apply volume changes
    setVolume('master', localMasterVolume);
    setVolume('music', localMusicVolume);
    setVolume('sfx', localSfxVolume);

    // Apply mute change
    if (localIsMuted !== isMuted) {
      toggleMute();
    }

    // Update SFX thresholds
    setSfxThresholds({
      minTradeAmount: localMinTradeAmount,
      alertSeverity: localAlertSeverity
    });

    // Save to localStorage
    saveSettings();

    // Close modal
    onOpenChange(false);
  };

  /**
   * Handle cancel
   */
  const handleCancel = () => {
    // Reset local state to context values
    setLocalTrackId(currentTrack || '');
    setLocalMasterVolume(volumes.master);
    setLocalMusicVolume(volumes.music);
    setLocalSfxVolume(volumes.sfx);
    setLocalIsMuted(isMuted);
    setLocalMinTradeAmount(settings.sfxThresholds.minTradeAmount);
    setLocalAlertSeverity(settings.sfxThresholds.alertSeverity);

    // Close modal
    onOpenChange(false);
  };

  /**
   * Real-time volume preview
   */
  const handleVolumePreview = (channel: 'master' | 'music' | 'sfx', value: number) => {
    if (channel === 'master') {
      setLocalMasterVolume(value);
      setVolume('master', value);
    } else if (channel === 'music') {
      setLocalMusicVolume(value);
      setVolume('music', value);
    } else if (channel === 'sfx') {
      setLocalSfxVolume(value);
      setVolume('sfx', value);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {localIsMuted ? <VolumeX className="h-5 w-5" /> : <Volume2 className="h-5 w-5" />}
            Audio Settings
          </DialogTitle>
          <DialogDescription>
            Configure music, sound effects, and volume controls
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Music Track Selector */}
          <div className="space-y-3">
            <Label className="text-base font-semibold">Music Track</Label>
            <RadioGroup
              value={localTrackId}
              onValueChange={setLocalTrackId}
              className="space-y-2"
            >
              {availableTracks.map(track => (
                <div
                  key={track.id}
                  className="flex items-center space-x-2 rounded-md border border-border p-3 hover:bg-accent/50 transition-colors"
                >
                  <RadioGroupItem value={track.id} id={track.id} />
                  <Label
                    htmlFor={track.id}
                    className="flex-1 cursor-pointer"
                  >
                    <div className="font-medium">{track.name}</div>
                    <div className="text-xs text-muted-foreground">
                      {track.description}
                    </div>
                  </Label>
                </div>
              ))}
            </RadioGroup>
          </div>

          {/* Volume Controls */}
          <div className="space-y-4">
            <Label className="text-base font-semibold">Volume Controls</Label>

            {/* Master Volume */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="master-volume">Master</Label>
                <span className="text-sm text-muted-foreground">
                  {Math.round(localMasterVolume * 100)}%
                </span>
              </div>
              <Slider
                id="master-volume"
                value={[localMasterVolume]}
                onValueChange={([value]) => handleVolumePreview('master', value)}
                min={0}
                max={1}
                step={0.01}
                className="w-full"
              />
            </div>

            {/* Music Volume */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="music-volume">Music</Label>
                <span className="text-sm text-muted-foreground">
                  {Math.round(localMusicVolume * 100)}%
                </span>
              </div>
              <Slider
                id="music-volume"
                value={[localMusicVolume]}
                onValueChange={([value]) => handleVolumePreview('music', value)}
                min={0}
                max={1}
                step={0.01}
                className="w-full"
              />
            </div>

            {/* SFX Volume */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="sfx-volume">SFX</Label>
                <span className="text-sm text-muted-foreground">
                  {Math.round(localSfxVolume * 100)}%
                </span>
              </div>
              <Slider
                id="sfx-volume"
                value={[localSfxVolume]}
                onValueChange={([value]) => handleVolumePreview('sfx', value)}
                min={0}
                max={1}
                step={0.01}
                className="w-full"
              />
            </div>
          </div>

          {/* Mute Toggle */}
          <div className="flex items-center justify-between rounded-md border border-border p-3">
            <div className="space-y-0.5">
              <Label htmlFor="mute-toggle" className="cursor-pointer">
                Mute All
              </Label>
              <div className="text-xs text-muted-foreground">
                Keyboard shortcut: M
              </div>
            </div>
            <Switch
              id="mute-toggle"
              checked={localIsMuted}
              onCheckedChange={setLocalIsMuted}
            />
          </div>

          {/* SFX Thresholds */}
          <div className="space-y-3">
            <Label className="text-base font-semibold">SFX Thresholds</Label>

            {/* Min Trade Amount */}
            <div className="space-y-2">
              <Label htmlFor="min-trade-amount">
                Min Trade Amount ($)
              </Label>
              <Input
                id="min-trade-amount"
                type="number"
                value={localMinTradeAmount}
                onChange={e => setLocalMinTradeAmount(Number(e.target.value))}
                min={0}
                step={10}
                className="w-full"
              />
              <p className="text-xs text-muted-foreground">
                Only play trade SFX for amounts above this threshold
              </p>
            </div>

            {/* Alert Severity */}
            <div className="space-y-2">
              <Label htmlFor="alert-severity">Alert Severity</Label>
              <Select
                value={localAlertSeverity}
                onValueChange={(value: 'all' | 'high') => setLocalAlertSeverity(value)}
              >
                <SelectTrigger id="alert-severity">
                  <SelectValue placeholder="Select severity" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Alerts</SelectItem>
                  <SelectItem value="high">High Priority Only</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                Filter which market alerts play SFX
              </p>
            </div>
          </div>

          {/* Keyboard Shortcuts */}
          <div className="space-y-3 rounded-md border border-border p-4 bg-accent/20">
            <Label className="text-base font-semibold">Keyboard Shortcuts</Label>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Toggle Mute</span>
                <kbd className="rounded bg-background px-2 py-1 font-mono text-xs border border-border">
                  M
                </kbd>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Play/Pause</span>
                <kbd className="rounded bg-background px-2 py-1 font-mono text-xs border border-border">
                  P
                </kbd>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Volume Up</span>
                <kbd className="rounded bg-background px-2 py-1 font-mono text-xs border border-border">
                  Ctrl+↑
                </kbd>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Volume Down</span>
                <kbd className="rounded bg-background px-2 py-1 font-mono text-xs border border-border">
                  Ctrl+↓
                </kbd>
              </div>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleCancel}>
            Cancel
          </Button>
          <Button onClick={handleSave}>
            Save
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
