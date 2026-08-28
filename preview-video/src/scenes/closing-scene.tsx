import {AbsoluteFill, CanvasImage, Easing, Interactive, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {Background} from '../shared/background';

export const ClosingScene = () => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  return (
    <AbsoluteFill>
      <Background />
      <CanvasImage
        src={staticFile('visual01.png')}
        style={{
          position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover',
          opacity: 0.12,
          scale: interpolate(frame, [0, durationInFrames], [1.06, 1.16], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', output: 'perceptual-scale'}),
        }}
      />
      <div style={{position: 'absolute', inset: 0, background: 'linear-gradient(90deg, rgba(7,16,25,0.97), rgba(7,16,25,0.82), rgba(7,16,25,0.94))'}} />
      <div style={{position: 'absolute', inset: '120px 150px', display: 'grid', placeItems: 'center', textAlign: 'center', fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif'}}>
        <div>
          <Interactive.Div
            name="Closing title"
            style={{
              color: '#f6f8fb', fontSize: 112, lineHeight: 1, letterSpacing: -5, fontWeight: 850,
              opacity: interpolate(frame, [0.25 * fps, 1.05 * fps], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.16, 1, 0.3, 1)}),
              scale: interpolate(frame, [0.25 * fps, 1.05 * fps], [0.94, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.spring({damping: 200}), output: 'perceptual-scale'}),
            }}
          >
            Confidence. Enjoyment.<br /><span style={{color: '#78f3b3'}}>Process over outcome.</span>
          </Interactive.Div>
          <Interactive.Div
            name="Closing explanation"
            style={{
              marginTop: 40, color: '#b7c5d1', fontSize: 39, lineHeight: 1.4,
              opacity: interpolate(frame, [1.0 * fps, 1.7 * fps], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}),
            }}
          >
            One planned desktop journey: first run → prepare → demo trade → review → own the record.
          </Interactive.Div>
          <div style={{display: 'flex', justifyContent: 'center', gap: 18, marginTop: 54, opacity: interpolate(frame, [1.55 * fps, 2.2 * fps], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})}}>
            {['Demo only', 'Not financial advice', 'AI never trades', 'Player-owned journal'].map((item) => (
              <div key={item} style={{border: '1px solid rgba(120,243,179,0.25)', background: 'rgba(120,243,179,0.08)', color: '#c6f8db', borderRadius: 999, padding: '14px 22px', fontSize: 22, fontWeight: 750}}>{item}</div>
            ))}
          </div>
          <div style={{marginTop: 72, color: '#708395', fontSize: 22, letterSpacing: 2}}>EVENING FOREX GOLD GAMEPAD · 14-PHASE CONCEPT PREVIEW</div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
