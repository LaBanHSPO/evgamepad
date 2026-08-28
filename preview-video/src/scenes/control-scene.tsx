import {AbsoluteFill, Easing, Interactive, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {Background} from '../shared/background';
import {Eyebrow, Subtitle, Title} from '../shared/type';
import {AppWindow} from '../shared/window';
import {MiniChart} from '../shared/mini-chart';

const Button = ({label, action, delay}: {label: string; action: string; delay: number}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (
    <div style={{display: 'flex', alignItems: 'center', gap: 18, opacity: interpolate(frame, [delay * fps, (delay + 0.45) * fps], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})}}>
      <div style={{width: 68, height: 52, borderRadius: 14, display: 'grid', placeItems: 'center', color: '#071019', background: '#78f3b3', fontSize: 24, fontWeight: 900}}>{label}</div>
      <div style={{fontSize: 27, color: '#dce6ef', fontWeight: 700}}>{action}</div>
    </div>
  );
};

export const ControlScene = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (
    <AbsoluteFill>
      <Background accent="#65b7ff" />
      <div style={{position: 'absolute', inset: '95px 90px', display: 'flex', alignItems: 'center', gap: 76}}>
        <div style={{width: 650}}>
          <Eyebrow color="#79bdff">02 · Trade with intent</Eyebrow>
          <Title>Trade with two hands.</Title>
          <Subtitle>Trade XAUUSD or three major FX pairs on one cTrader demo account—never live money.</Subtitle>
          <div style={{display: 'grid', gap: 20, marginTop: 42, fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif'}}>
            <Button label="LT" action="Hold the clutch" delay={1.45} />
            <Button label="A / B" action="Choose buy or sell" delay={1.75} />
            <Button label="RT" action="Confirm the demo order" delay={2.05} />
          </div>
          <div style={{marginTop: 26, color: '#79bdff', fontSize: 22, fontWeight: 760, fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif'}}>2.4G dongle primary · wired fallback · right stick previews SL/TP only</div>
        </div>
        <Interactive.Div
          name="Trading console preview"
          style={{
            scale: interpolate(frame, [0.2 * fps, 1.1 * fps], [0.9, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.spring({damping: 200}), output: 'perceptual-scale'}),
            opacity: interpolate(frame, [0.2 * fps, 0.8 * fps], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}),
          }}
        >
          <AppWindow>
            <div style={{padding: 32, fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif'}}>
              <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                <div><div style={{fontSize: 25, color: '#8fa3b5'}}>XAUUSD · M5</div><div style={{fontSize: 56, fontWeight: 800, color: '#f6f8fb'}}>2354.28</div></div>
                <div style={{display: 'flex', gap: 16}}>
                  <div style={{padding: '17px 24px', borderRadius: 16, background: 'rgba(101,183,255,0.12)', color: '#9dccff', fontSize: 22}}>PLAN READY</div>
                  <div style={{padding: '17px 24px', borderRadius: 16, background: 'rgba(120,243,179,0.12)', color: '#78f3b3', fontSize: 22, fontWeight: 800}}>CLUTCH ARMED</div>
                </div>
              </div>
              <div style={{height: 335, marginTop: 24}}><MiniChart /></div>
              <div style={{display: 'flex', justifyContent: 'space-between', borderTop: '1px solid rgba(196,218,238,0.12)', paddingTop: 21, color: '#9fb0bf', fontSize: 21}}>
                <span>Spread OK</span><span>Risk checked</span><span>Session 20:15 / 23:30</span><span style={{color: '#78f3b3'}}>Ready when you are</span>
              </div>
            </div>
          </AppWindow>
        </Interactive.Div>
      </div>
    </AbsoluteFill>
  );
};
