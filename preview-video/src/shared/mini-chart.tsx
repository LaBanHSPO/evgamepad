import {Easing, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';

const points = [255, 238, 246, 214, 220, 182, 195, 160, 169, 128, 146, 112, 126, 96, 115, 82, 94, 72];

export const MiniChart = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (
    <svg viewBox="0 0 760 320" style={{width: '100%', height: '100%', overflow: 'visible'}}>
      <defs>
        <linearGradient id="area" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#78f3b3" stopOpacity="0.26" />
          <stop offset="1" stopColor="#78f3b3" stopOpacity="0" />
        </linearGradient>
      </defs>
      {[80, 160, 240].map((y) => (
        <line key={y} x1="0" y1={y} x2="760" y2={y} stroke="rgba(196,218,238,0.1)" strokeWidth="1" />
      ))}
      <polyline
        points={points.map((y, index) => `${index * 44},${y}`).join(' ')}
        fill="none"
        stroke="#78f3b3"
        strokeWidth="6"
        strokeLinecap="round"
        strokeLinejoin="round"
        pathLength="1"
        strokeDasharray="1"
        strokeDashoffset={interpolate(frame, [0.65 * fps, 2.2 * fps], [1, 0], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
          easing: Easing.bezier(0.16, 1, 0.3, 1),
        })}
      />
      <path
        d={`M 0 ${points[0]} ${points.map((y, index) => `L ${index * 44} ${y}`).join(' ')} L 748 310 L 0 310 Z`}
        fill="url(#area)"
        opacity={interpolate(frame, [1.7 * fps, 2.5 * fps], [0, 1], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        })}
      />
    </svg>
  );
};
