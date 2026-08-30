import { useEffect, useRef } from "react";

/** Port of CodeRain.jsx — Matrix code rain on a canvas, unchanged draw loop. */

export interface CodeRainProps {
  opacity?: number;
  fontSize?: number;
  speed?: number;
}

const GLYPHS = "01ｦｱｳｴｵｷｹｺｻｼｽｾｿﾀﾂﾃﾅﾆﾇﾈﾊﾋﾎﾏﾐﾑﾔﾕﾗﾘﾜNQESBTCR";

export function CodeRain({ opacity = 0.35, fontSize = 14, speed = 90 }: CodeRainProps) {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const c = ref.current;
    if (!c) return;
    const ctx = c.getContext("2d");
    if (!ctx) return;

    let raf = 0;
    let last = 0;
    let cols: number[] = [];
    let w = 0;
    let h = 0;

    const resize = () => {
      w = c.width = c.offsetWidth;
      h = c.height = c.offsetHeight;
      cols = Array.from({ length: Math.ceil(w / fontSize) }, () => Math.random() * -40);
    };
    resize();
    window.addEventListener("resize", resize);

    const draw = (t: number) => {
      raf = requestAnimationFrame(draw);
      if (t - last < speed) return;
      last = t;
      ctx.fillStyle = "rgba(4,6,4,0.16)";
      ctx.fillRect(0, 0, w, h);
      ctx.font = fontSize + "px 'VT323', monospace";
      cols.forEach((y, i) => {
        const g = GLYPHS[Math.floor(Math.random() * GLYPHS.length)];
        ctx.fillStyle = Math.random() > 0.98 ? "#D2FFDE" : "#00A62A";
        ctx.fillText(g, i * fontSize, y * fontSize);
        cols[i] = y * fontSize > h && Math.random() > 0.975 ? 0 : y + 1;
      });
    };
    raf = requestAnimationFrame(draw);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
    };
  }, [fontSize, speed]);

  return (
    <canvas
      ref={ref}
      style={{
        position: "absolute",
        inset: 0,
        width: "100%",
        height: "100%",
        opacity,
        pointerEvents: "none",
      }}
    />
  );
}
