import {AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';

export const Background = ({accent = '#78f3b3'}: {accent?: string}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();

  return (
    <AbsoluteFill style={{backgroundColor: '#071019', overflow: 'hidden'}}>
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage:
            'linear-gradient(rgba(255,255,255,0.028) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.028) 1px, transparent 1px)',
          backgroundSize: '64px 64px',
          opacity: 0.65,
        }}
      />
      <div
        style={{
          position: 'absolute',
          width: 900,
          height: 900,
          left: -260,
          top: -420,
          borderRadius: '50%',
          background: `radial-gradient(circle, ${accent}32 0%, ${accent}08 45%, transparent 70%)`,
          scale: interpolate(frame, [0, durationInFrames], [0.92, 1.12], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
            easing: Easing.bezier(0.16, 1, 0.3, 1),
            output: 'perceptual-scale',
          }),
        }}
      />
      <div
        style={{
          position: 'absolute',
          width: 760,
          height: 760,
          right: -180,
          bottom: -420,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(71,136,255,0.24) 0%, rgba(71,136,255,0.05) 50%, transparent 72%)',
        }}
      />
    </AbsoluteFill>
  );
};
