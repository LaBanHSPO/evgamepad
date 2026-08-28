import {AbsoluteFill, Easing, Interactive, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {Background} from '../shared/background';
import {Eyebrow, Subtitle, Title} from '../shared/type';

const axes = [
  ['Adherence', '95'],
  ['Selectivity', '100'],
  ['Risk discipline', '95'],
  ['Preparation', '100'],
  ['Review', '100'],
];

export const ProcessScene = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (
    <AbsoluteFill>
      <Background accent="#8fe3ff" />
      <div style={{position: 'absolute', inset: '90px', display: 'grid', gridTemplateColumns: '0.95fr 1.05fr', gap: 82, alignItems: 'center', fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif'}}>
        <div>
          <Eyebrow color="#8fe3ff">07 · Score what you control</Eyebrow>
          <Title>A game score for decisions—not profit.</Title>
          <Subtitle>Five process-only axes reward patience, preparation and review. Tilt is retrospective, never a scoring input.</Subtitle>
          <div style={{marginTop: 38, display: 'flex', gap: 14, flexWrap: 'wrap'}}>
            {['No streaks', 'No levels', 'No leaderboard', 'No live score'].map((item) => (
              <div key={item} style={{border: '1px solid rgba(143,227,255,0.22)', borderRadius: 999, padding: '12px 18px', color: '#aeeaff', fontSize: 21, fontWeight: 750}}>{item}</div>
            ))}
          </div>
        </div>
        <Interactive.Div
          name="Process score card"
          style={{
            padding: 40,
            borderRadius: 30,
            border: '1px solid rgba(143,227,255,0.2)',
            background: 'rgba(10,24,35,0.94)',
            opacity: interpolate(frame, [0.45 * fps, 1.1 * fps], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}),
            scale: interpolate(frame, [0.45 * fps, 1.1 * fps], [0.93, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.spring({damping: 200}), output: 'perceptual-scale'}),
          }}
        >
          <div style={{display: 'flex', alignItems: 'end', justifyContent: 'space-between'}}>
            <div><div style={{color: '#8fa3b5', fontSize: 22, textTransform: 'uppercase', letterSpacing: 3}}>Active good evening</div><div style={{fontSize: 110, color: '#f6f8fb', fontWeight: 900, letterSpacing: -5}}>98<span style={{fontSize: 35, color: '#8fa3b5'}}>/100</span></div></div>
            <div style={{textAlign: 'right', color: '#78f3b3', fontSize: 24, fontWeight: 800}}>Dead tape + disciplined stand-down<br /><span style={{fontSize: 52}}>100</span></div>
          </div>
          <div style={{display: 'grid', gap: 17, marginTop: 30}}>
            {axes.map(([label, value], index) => (
              <div key={label} style={{display: 'grid', gridTemplateColumns: '190px 1fr 58px', gap: 16, alignItems: 'center', opacity: interpolate(frame, [(1.1 + index * 0.13) * fps, (1.45 + index * 0.13) * fps], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})}}>
                <div style={{color: '#c5d1db', fontSize: 22}}>{label}</div>
                <div style={{height: 12, borderRadius: 999, background: 'rgba(255,255,255,0.08)', overflow: 'hidden'}}><div style={{height: '100%', width: `${value}%`, borderRadius: 999, background: 'linear-gradient(90deg, #79bdff, #78f3b3)'}} /></div>
                <div style={{color: '#f6f8fb', fontSize: 22, fontWeight: 800}}>{value}</div>
              </div>
            ))}
          </div>
          <div style={{marginTop: 31, color: '#8fa3b5', fontSize: 21}}>Outcome metrics stay behind a deliberate tab click.</div>
        </Interactive.Div>
      </div>
    </AbsoluteFill>
  );
};
