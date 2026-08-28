import {AbsoluteFill, Easing, Interactive, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {Background} from '../shared/background';
import {Eyebrow, Subtitle, Title} from '../shared/type';

const SupportCard = ({label, title, detail, footer, color, delay}: {label: string; title: string; detail: string; footer: string; color: string; delay: number}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (
    <Interactive.Div
      name={`${label} support card`}
      style={{
        flex: 1,
        minHeight: 420,
        borderRadius: 30,
        border: '1px solid rgba(196,218,238,0.17)',
        background: 'linear-gradient(180deg, rgba(18,35,49,0.98), rgba(8,19,29,0.98))',
        padding: 40,
        opacity: interpolate(frame, [delay * fps, (delay + 0.6) * fps], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}),
        translate: interpolate(frame, [delay * fps, (delay + 0.6) * fps], ['0px 50px', '0px 0px'], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.16, 1, 0.3, 1)}),
      }}
    >
      <div style={{color, fontSize: 22, fontWeight: 900, letterSpacing: 4, textTransform: 'uppercase'}}>{label}</div>
      <div style={{color: '#f6f8fb', fontSize: 45, fontWeight: 840, marginTop: 22, lineHeight: 1.08}}>{title}</div>
      <div style={{color: '#aebcca', fontSize: 28, lineHeight: 1.45, marginTop: 24}}>{detail}</div>
      <div style={{marginTop: 34, paddingTop: 24, borderTop: '1px solid rgba(196,218,238,0.12)', color, fontSize: 24, fontWeight: 800}}>{footer}</div>
    </Interactive.Div>
  );
};

export const SupportScene = () => (
  <AbsoluteFill>
    <Background accent="#ff9f70" />
    <div style={{position: 'absolute', inset: '90px', fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif'}}>
      <Eyebrow color="#ffad84">05 · Support the human</Eyebrow>
      <Title>Capture the reason. Notice the rush.</Title>
      <Subtitle>The system helps when typing is impossible and when controller behaviour starts to change.</Subtitle>
      <div style={{display: 'flex', gap: 28, marginTop: 52}}>
        <SupportCard
          label="Voice memo"
          title="Hold LB + RB and speak."
          detail="The audio stays on the VPS, transcribes locally with whisper.cpp, and remains playable even if transcription fails."
          footer="Memo or ask-the-coach · never navigation"
          color="#79bdff"
          delay={0.85}
        />
        <SupportCard
          label="Tilt telemetry"
          title="Measure behaviour—not emotion."
          detail="Re-entry speed, lot escalation, clutch cycles and arm flips can add friction to a new open. No keyword or mood guessing."
          footer="Close and panic are always immediate"
          color="#ffad84"
          delay={1.25}
        />
      </div>
    </div>
  </AbsoluteFill>
);
