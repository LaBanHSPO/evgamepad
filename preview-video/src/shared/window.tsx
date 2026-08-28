import type {ReactNode} from 'react';

export const AppWindow = ({children}: {children: ReactNode}) => (
  <div
    style={{
      width: 1080,
      height: 660,
      borderRadius: 28,
      border: '1px solid rgba(196,218,238,0.19)',
      background: 'linear-gradient(180deg, rgba(20,35,48,0.98), rgba(8,18,28,0.98))',
      boxShadow: '0 38px 100px rgba(0,0,0,0.48), 0 0 0 8px rgba(255,255,255,0.018)',
      overflow: 'hidden',
    }}
  >
    <div
      style={{
        height: 58,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 24px',
        borderBottom: '1px solid rgba(196,218,238,0.12)',
        color: '#dce6ef',
        fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif',
        fontSize: 21,
        fontWeight: 700,
      }}
    >
      <div style={{display: 'flex', gap: 9}}>
        <span style={{width: 12, height: 12, borderRadius: '50%', background: '#ff6b6b'}} />
        <span style={{width: 12, height: 12, borderRadius: '50%', background: '#ffd36a'}} />
        <span style={{width: 12, height: 12, borderRadius: '50%', background: '#78f3b3'}} />
      </div>
      Evening Forex Gold Gamepad
      <span style={{color: '#78f3b3', fontSize: 18}}>DEMO</span>
    </div>
    {children}
  </div>
);
