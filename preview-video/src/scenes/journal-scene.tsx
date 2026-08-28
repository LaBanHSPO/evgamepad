import {AbsoluteFill, Easing, Interactive, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {Background} from '../shared/background';
import {Eyebrow, Subtitle, Title} from '../shared/type';

const heat = [28, 55, 0, 82, 64, 0, 96, 45, 72, 0, 88, 34, 0, 91, 68, 76, 0, 100, 52, 81, 0, 92, 61, 74, 87, 0, 97, 66];

export const JournalScene = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (
    <AbsoluteFill>
      <Background accent="#b58cff" />
      <div style={{position: 'absolute', inset: '90px', display: 'grid', gridTemplateColumns: '0.9fr 1.1fr', gap: 86, alignItems: 'center', fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif'}}>
        <div>
          <Eyebrow color="#c8a7ff">08 · Build a useful journal</Eyebrow>
          <Title>See the pattern behind the evening.</Title>
          <Subtitle>Every trade connects its plan, execution, voice, replay and review under one auditable record.</Subtitle>
          <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginTop: 35}}>
            {['Actual vs Plan', 'Before · During · After', 'Mistake trends', 'Playbook history'].map((item) => (
              <div key={item} style={{padding: '15px 18px', borderRadius: 14, background: 'rgba(181,140,255,0.09)', border: '1px solid rgba(181,140,255,0.18)', color: '#d8c5ff', fontSize: 22, fontWeight: 760}}>{item}</div>
            ))}
          </div>
        </div>
        <Interactive.Div
          name="Journal dashboard preview"
          style={{
            borderRadius: 30,
            border: '1px solid rgba(196,218,238,0.17)',
            background: 'rgba(10,22,33,0.96)',
            padding: 34,
            opacity: interpolate(frame, [0.4 * fps, 1.0 * fps], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}),
            translate: interpolate(frame, [0.4 * fps, 1.0 * fps], ['50px 0px', '0px 0px'], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.16, 1, 0.3, 1)}),
          }}
        >
          <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}><div style={{fontSize: 29, color: '#f6f8fb', fontWeight: 800}}>Process heatmap</div><div style={{fontSize: 19, color: '#8fa3b5'}}>One IC Markets demo account</div></div>
          <div style={{display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 12, marginTop: 28}}>
            {heat.map((value, index) => (
              <div key={index} style={{height: 64, borderRadius: 12, display: 'grid', placeItems: 'center', background: value === 0 ? 'rgba(255,255,255,0.035)' : `rgba(120,243,179,${0.12 + value / 155})`, color: value === 0 ? '#526373' : '#effff6', fontSize: 18, fontWeight: 800}}>{value === 0 ? '—' : value}</div>
            ))}
          </div>
          <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 14, marginTop: 25}}>
            {[['Plan', 'Ready'], ['Review', 'Complete'], ['Consistency', 'n = 18']].map(([label, value]) => (
              <div key={label} style={{padding: 20, borderRadius: 16, background: 'rgba(255,255,255,0.035)'}}><div style={{fontSize: 18, color: '#8fa3b5'}}>{label}</div><div style={{fontSize: 26, color: '#f6f8fb', fontWeight: 800, marginTop: 5}}>{value}</div></div>
            ))}
          </div>
          <div style={{marginTop: 22, color: '#9fb0bf', fontSize: 20}}>Player notes can annotate the record. They can never rewrite broker facts.</div>
        </Interactive.Div>
      </div>
    </AbsoluteFill>
  );
};
