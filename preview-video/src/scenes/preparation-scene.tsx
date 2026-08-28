import {AbsoluteFill, Easing, Interactive, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {Background} from '../shared/background';
import {Eyebrow, Subtitle, Title} from '../shared/type';

const PrepItem = ({number, title, detail, delay}: {number: string; title: string; detail: string; delay: number}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (
    <Interactive.Div
      name={`Preparation ${number}`}
      style={{
        display: 'grid',
        gridTemplateColumns: '66px 1fr',
        gap: 22,
        padding: '25px 28px',
        borderRadius: 20,
        border: '1px solid rgba(196,218,238,0.14)',
        background: 'rgba(12,25,36,0.88)',
        opacity: interpolate(frame, [delay * fps, (delay + 0.45) * fps], [0, 1], {
          extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
        }),
        translate: interpolate(frame, [delay * fps, (delay + 0.45) * fps], ['45px 0px', '0px 0px'], {
          extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.16, 1, 0.3, 1),
        }),
      }}
    >
      <div style={{width: 54, height: 54, display: 'grid', placeItems: 'center', borderRadius: 16, background: 'rgba(255,211,106,0.12)', color: '#ffd36a', fontSize: 23, fontWeight: 900}}>{number}</div>
      <div>
        <div style={{fontSize: 30, color: '#f6f8fb', fontWeight: 820}}>{title}</div>
        <div style={{fontSize: 23, color: '#9fb0bf', marginTop: 7, lineHeight: 1.35}}>{detail}</div>
      </div>
    </Interactive.Div>
  );
};

export const PreparationScene = () => (
  <AbsoluteFill>
    <Background accent="#ffd36a" />
    <div style={{position: 'absolute', inset: '92px 90px', display: 'grid', gridTemplateColumns: '0.9fr 1.1fr', gap: 92, alignItems: 'center', fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif'}}>
      <div>
        <Eyebrow color="#ffd36a">01 · Prepare before you play</Eyebrow>
        <Title>Start with readiness, not a flashing price.</Title>
        <Subtitle>The journal opens the evening with a plan and a risk boundary before the controller can tempt you.</Subtitle>
        <div style={{marginTop: 36, color: '#ffd36a', fontSize: 25, fontWeight: 800}}>Focused session · 18:00–23:30 · Asia/Ho_Chi_Minh</div>
      </div>
      <div style={{display: 'grid', gap: 17}}>
        <PrepItem number="01" title="Check yourself" detail="Sleep, calm, focus, risk acceptance and plan review." delay={0.65} />
        <PrepItem number="02" title="Read the evening" detail="DST-aware market clocks, calendar, news and key levels." delay={1.0} />
        <PrepItem number="03" title="Choose your setup" detail="Select a playbook and write the invalidation before entry." delay={1.35} />
        <PrepItem number="04" title="Size the risk" detail="Broker-rounded lots and actual risk—preview only until LT + RT." delay={1.7} />
      </div>
    </div>
  </AbsoluteFill>
);
