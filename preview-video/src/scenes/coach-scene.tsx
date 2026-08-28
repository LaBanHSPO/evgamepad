import {AbsoluteFill, Easing, Interactive, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {Background} from '../shared/background';
import {Eyebrow, Subtitle, Title} from '../shared/type';

const Insight = ({title, text, color, delay}: {title: string; text: string; color: string; delay: number}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (
    <Interactive.Div
      name={`${title} card`}
      style={{
        borderRadius: 24,
        border: '1px solid rgba(196,218,238,0.15)',
        background: 'rgba(12,25,36,0.9)',
        padding: '30px 32px',
        opacity: interpolate(frame, [delay * fps, (delay + 0.5) * fps], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}),
        translate: interpolate(frame, [delay * fps, (delay + 0.5) * fps], ['46px 0px', '0px 0px'], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.16, 1, 0.3, 1)}),
      }}
    >
      <div style={{color, fontSize: 22, textTransform: 'uppercase', letterSpacing: 3, fontWeight: 900}}>{title}</div>
      <div style={{color: '#dce6ef', fontSize: 29, lineHeight: 1.42, marginTop: 14}}>{text}</div>
    </Interactive.Div>
  );
};

export const CoachScene = () => (
  <AbsoluteFill>
    <Background accent="#bc8cff" />
    <div style={{position: 'absolute', inset: '94px 90px', display: 'grid', gridTemplateColumns: '0.95fr 1.05fr', gap: 94, alignItems: 'center', fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif'}}>
      <div>
        <Eyebrow color="#c8a7ff">04 · Read-only guidance</Eyebrow>
        <Title>A desk beside the trade—never inside it.</Title>
        <Subtitle>Deterministic signals stay fast. AI explains context asynchronously and has no order or journal-write tools.</Subtitle>
      </div>
      <div style={{display: 'grid', gap: 22}}>
        <Insight title="Sentinel" text="NFP in 11 minutes · stand down" color="#78f3b3" delay={0.7} />
        <Insight title="Volman-style M5 lens" text="EMA20 · range buildup · wait for a clean break" color="#79bdff" delay={1.1} />
        <Insight title="Playbook grade" text="Second-chance break · 4/5 rules before fire" color="#ffd36a" delay={1.5} />
        <Insight title="AI coach" text="Observation, not an order. Clutch + confirm is yours." color="#c8a7ff" delay={1.9} />
      </div>
    </div>
  </AbsoluteFill>
);
