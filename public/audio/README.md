# Audio Assets

This directory contains audio assets for the EV GamePad trading game.

## Music Tracks

Place 4 royalty-free music tracks in `public/audio/music/`:

1. **focus-ambient.mp3** - Calm, minimal distraction (3-5 min loop)
2. **energy-upbeat.mp3** - High-tempo trading (3-5 min loop)
3. **strategy-chill.mp3** - Mid-tempo analytical (3-5 min loop)
4. **night-lofi.mp3** - Low-energy late sessions (3-5 min loop)

### Recommended Sources for Royalty-Free Music:
- [Incompetech](https://incompetech.com/music/royalty-free/) - Large library, CC-BY license
- [FreeSound](https://freesound.org/) - Community-uploaded sounds
- [Bensound](https://www.bensound.com/) - High-quality tracks
- [YouTube Audio Library](https://www.youtube.com/audiolibrary) - Free music

### Audio Specifications:
- Format: MP3
- Bitrate: 128 kbps (compressed for web)
- Duration: 3-5 minutes
- Loopable: Seamless loop at end
- File size: ~3-5 MB per track

## Sound Effects (SFX)

Place 5 SFX files in `public/audio/sfx/`:

1. **trade-buy.mp3** - Gamified synth beep (short, <1 sec)
2. **trade-sell.mp3** - Different tone from buy (short, <1 sec)
3. **market-alert.mp3** - Attention-grabbing (short, <1 sec)
4. **achievement.mp3** - Celebration chime (short, <1 sec)
5. **milestone.mp3** - Bigger achievement (1-2 sec)

### Recommended Sources for SFX:
- [FreeSound](https://freesound.org/) - Search "synth beep", "game sfx"
- [Zapsplat](https://www.zapsplat.com/) - Game sound effects
- Generate with Tone.js Synth (programmatic approach)

### SFX Specifications:
- Format: MP3
- Bitrate: 96 kbps
- Duration: <1 second (milestone: 1-2 sec)
- File size: <50 KB each

## License Compliance

Ensure all audio assets are:
- Royalty-free or CC-BY licensed
- Attributed in `AUDIO_CREDITS.md` if required
- Commercial use allowed

## Integration

Audio files are loaded by `src/services/audio-manager.ts` using Tone.js.
Track metadata is defined in `src/types/audio.ts`.
