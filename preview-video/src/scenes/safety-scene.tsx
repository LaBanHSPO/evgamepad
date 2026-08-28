import {AbsoluteFill, Easing, Interactive, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {Background} from '../shared/background';
import {Eyebrow, Subtitle, Title} from '../shared/type';

const SafetyNode = ({number, title, detail, delay}: {number: string; title: string; detail: string; delay: number}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (
    <Interactive.Div
      name={`Safety step ${number}`}
      style={{
        width: 470,
        minHeight: 220,
        borderRadius: 26,
        border: '1px solid rgba(120,243,179,0.2)',
        background: 'rgba(12,25,36,0.94)',
        padding: 34,
        opacity: interpolate(frame, [delay * fps, (delay + 0.55) * fps], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}),
        translate: interpolate(frame, [delay * fps, (delay + 0.55) * fps], ['0px 36px', '0px 0px'], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.16, 1, 0.3, 1)}),
      }}
    >
      <div style={{fontSize: 22, color: '#78f3b3', fontWeight: 900, letterSpacing: 3}}>{number}</div>
      <div style={{fontSize: 38, color: '#f6f8fb', fontWeight: 800, marginTop: 14}}>{title}</div>
      <div style={{fontSize: 26, color: '#9fb0bf', lineHeight: 1.4, marginTop: 14}}>{detail}</div>
    </Interactive.Div>
  );
};

export const SafetyScene = () => (
  <AbsoluteFill>
    <Background />
    <div style={{position: 'absolute', inset: '92px 90px', fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif'}}>
      <Eyebrow>03 · One trusted order path</Eyebrow>
      <Title>Practice real decisions. Keep real money out.</Title>
      <Subtitle>Only the gateway can approve a demo command. Everything that teaches, records or explains stays beside that path.</Subtitle>
      <div style={{display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 32, marginTop: 72}}>
        <SafetyNode number="01" title="You decide" detail="The controller prepares a clear trade intent." delay={1.2} />
        <div style={{fontSize: 54, color: '#547087'}}>→</div>
        <SafetyNode number="02" title="Rules check" detail="The gateway validates demo mode, size and risk." delay={1.6} />
        <div style={{fontSize: 54, color: '#547087'}}>→</div>
        <SafetyNode number="03" title="Demo executes" detail="cTrader remains the broker and matching engine." delay={2.0} />
      </div>
      <div style={{textAlign: 'center', marginTop: 48, color: '#78f3b3', fontSize: 28, fontWeight: 800}}>AI, voice, replay and analytics cannot trade · live host or account refuses to boot</div>
    </div>
  </AbsoluteFill>
);
