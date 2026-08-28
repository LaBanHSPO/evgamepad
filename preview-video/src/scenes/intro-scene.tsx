import {AbsoluteFill, CanvasImage, Easing, Interactive, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {Background} from '../shared/background';
import {Eyebrow, StatusPill, Subtitle, Title} from '../shared/type';

export const IntroScene = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (
    <AbsoluteFill>
      <Background />
      <div style={{position: 'absolute', inset: '104px 90px', display: 'flex', alignItems: 'center'}}>
        <div style={{width: '49%', zIndex: 2}}>
          <Eyebrow>14-phase product concept</Eyebrow>
          <Title>One focused evening. Better decisions.</Title>
          <Subtitle>Prepare, trade, record, replay, review—and own every decision in one desktop experience.</Subtitle>
          <div style={{marginTop: 42}}><StatusPill>Planning complete · Implementation not started</StatusPill></div>
        </div>
        <Interactive.Div
          name="Project concept artwork"
          style={{
            position: 'absolute',
            width: 940,
            height: 626,
            right: -80,
            borderRadius: 32,
            overflow: 'hidden',
            border: '1px solid rgba(255,255,255,0.18)',
            boxShadow: '0 48px 120px rgba(0,0,0,0.5)',
            opacity: interpolate(frame, [0.45 * fps, 1.2 * fps], [0, 1], {
              extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.16, 1, 0.3, 1),
            }),
            translate: interpolate(frame, [0.45 * fps, 1.2 * fps], ['80px 0px', '0px 0px'], {
              extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.16, 1, 0.3, 1),
            }),
            rotate: '-1.5deg',
          }}
        >
          <CanvasImage src={staticFile('visual01.png')} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
        </Interactive.Div>
      </div>
    </AbsoluteFill>
  );
};
