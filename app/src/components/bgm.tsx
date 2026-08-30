import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import type { ReactNode } from "react";

/**
 * Chiptune BGM — port of startBgm/stopBgm/gain from the prototype's
 * DCLogic component. Square lead + triangle bass on a 125ms step, generated
 * with WebAudio so no audio file is needed. Nothing plays until PLAY is pressed.
 *
 * The prototype held bgm/vol on the one root component, so the Attract screen
 * and the city-art screen drove the same engine; this context keeps that.
 */

const BASS = [110, 110, 146.83, 110, 98, 98, 130.81, 98];
const LEAD = [
  440, 0, 523.25, 659.25, 587.33, 0, 493.88, 440, 392, 0, 523.25, 587.33, 659.25, 0, 587.33, 523.25,
];

const gainFor = (vol: number) => Math.pow(vol / 8, 1.6) * 0.22;

interface BgmValue {
  playing: boolean;
  vol: number;
  track: string;
  toggle: () => void;
  setVol: (v: number) => void;
}

const BgmContext = createContext<BgmValue | null>(null);

export function BgmProvider({ children }: { children: ReactNode }) {
  const [playing, setPlaying] = useState(false);
  const [vol, setVolState] = useState(4);

  const acRef = useRef<AudioContext | null>(null);
  const masterRef = useRef<GainNode | null>(null);
  const seqRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stop = useCallback(() => {
    if (seqRef.current) clearInterval(seqRef.current);
    seqRef.current = null;
    if (masterRef.current) masterRef.current.gain.value = 0;
  }, []);

  const start = useCallback((level: number) => {
    const AC = window.AudioContext || (window as any).webkitAudioContext;
    if (!AC) return;
    if (!acRef.current) {
      acRef.current = new AC();
      masterRef.current = acRef.current.createGain();
      masterRef.current.connect(acRef.current.destination);
    }
    const ac = acRef.current;
    const master = masterRef.current!;
    if (ac.state === "suspended") void ac.resume();
    master.gain.value = gainFor(level);

    let step = 0;
    const hit = (freq: number, type: OscillatorType, dur: number, gain: number) => {
      if (!freq) return;
      const t = ac.currentTime;
      const o = ac.createOscillator();
      const g = ac.createGain();
      o.type = type;
      o.frequency.value = freq;
      g.gain.setValueAtTime(gain, t);
      g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
      o.connect(g);
      g.connect(master);
      o.start(t);
      o.stop(t + dur);
    };

    seqRef.current = setInterval(() => {
      hit(LEAD[step % LEAD.length], "square", 0.13, 0.5);
      if (step % 2 === 0) hit(BASS[(step / 2) % BASS.length], "triangle", 0.22, 0.9);
      if (step % 4 === 2) hit(1200 + Math.random() * 400, "square", 0.03, 0.18);
      step++;
    }, 125);
  }, []);

  useEffect(() => stop, [stop]);

  const value = useMemo<BgmValue>(
    () => ({
      playing,
      vol,
      track: "stage 04 loop",
      toggle: () => {
        const next = !playing;
        setPlaying(next);
        if (next) start(vol);
        else stop();
      },
      setVol: (v: number) => {
        setVolState(v);
        if (masterRef.current) masterRef.current.gain.value = gainFor(v);
      },
    }),
    [playing, vol, start, stop],
  );

  return <BgmContext.Provider value={value}>{children}</BgmContext.Provider>;
}

export function useBgm(): BgmValue {
  const ctx = useContext(BgmContext);
  if (!ctx) throw new Error("useBgm must be used inside <BgmProvider>");
  return ctx;
}

/**
 * The BGM cluster from the HUD footer: PLAY/STOP, 8 arcade volume notches.
 *
 * `grouped` splits it into the two sub-clusters the Attract screen footer uses
 * (transport, then volume); flat is the city-art footer.
 */
export function BgmControl({
  showTrack = false,
  grouped = false,
}: {
  showTrack?: boolean;
  grouped?: boolean;
}) {
  const { playing, vol, track, toggle, setVol } = useBgm();

  const btnStyle = {
    height: 20,
    padding: "0 10px",
    border: `1px solid ${playing ? "var(--phos-400)" : "var(--line-neutral)"}`,
    background: playing ? "var(--phos-a08)" : "transparent",
    color: playing ? "var(--phos-300)" : "var(--text-secondary)",
    fontFamily: "var(--font-core)",
    fontSize: 9,
    fontWeight: 700,
    letterSpacing: ".18em",
    cursor: "pointer",
  } as const;

  const capStyle = (color: string) =>
    ({ fontSize: 9, letterSpacing: ".18em", textTransform: "uppercase", color }) as const;

  const transport = (
    <>
      <span style={{ fontFamily: "var(--font-display)", fontSize: 9, color: "var(--phos-300)" }}>
        BGM
      </span>
      {showTrack ? <span style={capStyle("var(--text-muted)")}>{track}</span> : null}
      <button
        className="ev-bgm-btn"
        onClick={toggle}
        style={grouped ? { ...btnStyle, marginLeft: "auto" } : btnStyle}
      >
        {playing ? "STOP" : "PLAY"}
      </button>
    </>
  );

  const volume = (
    <>
      <span style={capStyle("var(--text-disabled)")}>Vol</span>
      <div style={{ display: "flex", gap: 3 }}>
        {Array.from({ length: 8 }, (_, i) => (
          <button
            key={i}
            aria-label={`Volume ${i + 1} of 8`}
            onClick={() => setVol(i + 1)}
            style={{
              width: 11,
              height: 16,
              border: 0,
              padding: 0,
              cursor: "pointer",
              background:
                i < vol ? (i > 5 ? "var(--arcade-yellow)" : "var(--phos-400)") : "var(--black-5)",
              ...(i < vol
                ? { boxShadow: "var(--glow-xs)" }
                : { outline: "1px solid var(--line-hairline)" }),
            }}
          />
        ))}
      </div>
      <span
        style={{
          marginLeft: grouped ? "auto" : undefined,
          fontFamily: "var(--font-data)",
          fontSize: 11,
          color: "var(--text-muted)",
          fontVariantNumeric: "tabular-nums",
        }}
      >
        {Math.round((vol / 8) * 100)}%
      </span>
    </>
  );

  if (!grouped) {
    return (
      <>
        {transport}
        {volume}
      </>
    );
  }

  return (
    <>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>{transport}</div>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>{volume}</div>
    </>
  );
}
