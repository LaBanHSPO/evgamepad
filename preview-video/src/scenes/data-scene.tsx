import {AbsoluteFill, Easing, Interactive, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {Background} from '../shared/background';
import {Eyebrow, Subtitle, Title} from '../shared/type';

const DataStep = ({label, detail, delay}: {label: string; detail: string; delay: number}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (
    <Interactive.Div
      name={`${label} data step`}
      style={{
        flex: 1,
        minHeight: 230,
        padding: 30,
        borderRadius: 24,
        border: '1px solid rgba(120,243,179,0.18)',
        background: 'rgba(10,24,34,0.92)',
        opacity: interpolate(frame, [delay * fps, (delay + 0.5) * fps], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}),
        scale: interpolate(frame, [delay * fps, (delay + 0.5) * fps], [0.94, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.spring({damping: 200}), output: 'perceptual-scale'}),
      }}
    >
      <div style={{fontSize: 34, color: '#f6f8fb', fontWeight: 820}}>{label}</div>
      <div style={{fontSize: 24, color: '#9fb0bf', lineHeight: 1.42, marginTop: 16}}>{detail}</div>
    </Interactive.Div>
  );
};

export const DataScene = () => (
  <AbsoluteFill>
    <Background />
    <div style={{position: 'absolute', inset: '90px', fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif'}}>
      <Eyebrow>09 · Own the record</Eyebrow>
      <Title>Your learning history stays portable.</Title>
      <Subtitle>Reports and recovery complete the product—not as an afterthought, but as part of the evening journey.</Subtitle>
      <div style={{display: 'flex', alignItems: 'stretch', gap: 22, marginTop: 58}}>
        <DataStep label="Report" detail="Process-first browser PDF, with Outcome as an optional appendix." delay={0.8} />
        <DataStep label="Export" detail="Streamed CSV and JSON—without tokens, secrets or VPS paths." delay={1.1} />
        <DataStep label="Backup" detail="Manifested database, tapes, voice and attachments with checksums." delay={1.4} />
        <DataStep label="Restore / Delete" detail="Locked-session guards, verified restore and an explicit delete-all path." delay={1.7} />
      </div>
      <div style={{display: 'flex', justifyContent: 'center', gap: 18, marginTop: 44, color: '#b8fbd6', fontSize: 23, fontWeight: 800}}>
        <span>Single account</span><span style={{color: '#526b7d'}}>·</span><span>No history import</span><span style={{color: '#526b7d'}}>·</span><span>No hidden recovery copy</span>
      </div>
    </div>
  </AbsoluteFill>
);
