import {AbsoluteFill, Easing, Interactive, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {Background} from '../shared/background';
import {Eyebrow, Subtitle, Title} from '../shared/type';

const LoopStep = ({icon, title, text, delay}: {icon: string; title: string; text: string; delay: number}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (
    <Interactive.Div
      name={`${title} learning step`}
      style={{
        flex: 1,
        minHeight: 290,
        padding: 36,
        borderRadius: 26,
        border: '1px solid rgba(196,218,238,0.15)',
        background: 'linear-gradient(180deg, rgba(18,35,49,0.96), rgba(9,20,30,0.96))',
        opacity: interpolate(frame, [delay * fps, (delay + 0.55) * fps], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}),
        scale: interpolate(frame, [delay * fps, (delay + 0.55) * fps], [0.92, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.spring({damping: 200}), output: 'perceptual-scale'}),
      }}
    >
      <div style={{fontSize: 54, color: '#ffd36a', fontWeight: 800}}>{icon}</div>
      <div style={{fontSize: 34, color: '#f6f8fb', fontWeight: 820, marginTop: 22}}>{title}</div>
      <div style={{fontSize: 25, lineHeight: 1.42, color: '#9fb0bf', marginTop: 14}}>{text}</div>
    </Interactive.Div>
  );
};

export const LearnScene = () => (
  <AbsoluteFill>
    <Background accent="#ffd36a" />
    <div style={{position: 'absolute', inset: '90px', fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif'}}>
      <Eyebrow color="#ffd36a">06 · Replay the decision</Eyebrow>
      <Title>Review more than the candles.</Title>
      <Subtitle>The frozen tape preserves what you saw, what you did, and what you said around the trade.</Subtitle>
      <div style={{display: 'flex', gap: 26, marginTop: 62}}>
        <LoopStep icon="▦" title="Tape" text="Five minutes before entry through five minutes after close." delay={0.9} />
        <LoopStep icon="⌁" title="Events" text="See arms, cancels, signals, grades and protection changes." delay={1.25} />
        <LoopStep icon="↕" title="MFE / MAE" text="Inspect favorable and adverse excursion on the correct quote side." delay={1.6} />
        <LoopStep icon="◉" title="Voice" text="Hear the memo again at the moment it was recorded." delay={1.95} />
      </div>
      <div style={{textAlign: 'center', marginTop: 34, color: '#ffd36a', fontSize: 24, fontWeight: 800}}>Replay is hard-locked: the controller cannot place an order here.</div>
    </div>
  </AbsoluteFill>
);
