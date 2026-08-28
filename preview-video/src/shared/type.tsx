import type {ReactNode} from 'react';
import {Easing, Interactive, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';

export const Eyebrow = ({children, color = '#78f3b3'}: {children: ReactNode; color?: string}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (
    <Interactive.Div
      name="Section label"
      style={{
        color,
        fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif',
        fontSize: 26,
        fontWeight: 800,
        letterSpacing: 5,
        textTransform: 'uppercase',
        opacity: interpolate(frame, [0, 0.45 * fps], [0, 1], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
          easing: Easing.bezier(0.16, 1, 0.3, 1),
        }),
      }}
    >
      {children}
    </Interactive.Div>
  );
};

export const Title = ({children}: {children: ReactNode}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (
    <Interactive.Div
      name="Scene title"
      style={{
        color: '#f6f8fb',
        fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif',
        fontSize: 96,
        lineHeight: 1.02,
        letterSpacing: -4,
        fontWeight: 820,
        maxWidth: 1040,
        marginTop: 24,
        opacity: interpolate(frame, [0.2 * fps, 0.9 * fps], [0, 1], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
          easing: Easing.bezier(0.16, 1, 0.3, 1),
        }),
        translate: interpolate(frame, [0.2 * fps, 0.9 * fps], ['0px 44px', '0px 0px'], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
          easing: Easing.bezier(0.16, 1, 0.3, 1),
        }),
      }}
    >
      {children}
    </Interactive.Div>
  );
};

export const Subtitle = ({children}: {children: ReactNode}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (
    <Interactive.Div
      name="Scene explanation"
      style={{
        color: '#aebcca',
        fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif',
        fontSize: 42,
        lineHeight: 1.35,
        maxWidth: 1050,
        marginTop: 30,
        opacity: interpolate(frame, [0.75 * fps, 1.35 * fps], [0, 1], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
          easing: Easing.bezier(0.16, 1, 0.3, 1),
        }),
      }}
    >
      {children}
    </Interactive.Div>
  );
};

export const StatusPill = ({children}: {children: ReactNode}) => (
  <div
    style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: 12,
      border: '1px solid rgba(120,243,179,0.35)',
      background: 'rgba(120,243,179,0.09)',
      borderRadius: 999,
      padding: '14px 22px',
      color: '#b8fbd6',
      fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif',
      fontSize: 25,
      fontWeight: 700,
    }}
  >
    <span style={{width: 10, height: 10, background: '#78f3b3', borderRadius: '50%'}} />
    {children}
  </div>
);
