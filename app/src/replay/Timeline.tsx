import type { CSSProperties } from "react";
import { styleFor } from "./Markers";
import { clamp01 } from "./resample";
import type { ReplayEvent, Tape } from "./types";

/**
 * The event rail — the strip this whole screen exists for.
 *
 * The chart shows what the market did. This shows what you did: the arm you cancelled, the stop
 * you moved, the band you crossed, each at the second it actually happened. Scrubbing the left
 * stick moves the playhead across it, and whatever is nearest gets named.
 */

export function Timeline({ tape, events, playheadMs, nearest, onSeek }: {
  tape: Tape;
  events: ReplayEvent[];
  playheadMs: number;
  nearest: ReplayEvent | null;
  onSeek?: (ms: number) => void;
}): JSX.Element {
  const fromMs = tape.fromTs * 1000;
  const span = Math.max(1, tape.toTs * 1000 - fromMs);
  const at = (ms: number) => `${clamp01((ms - fromMs) / span) * 100}%`;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      <div
        style={rail}
        onClick={(e) => {
          if (!onSeek) return;
          const box = e.currentTarget.getBoundingClientRect();
          onSeek(fromMs + ((e.clientX - box.left) / box.width) * span);
        }}
      >
        {events.map((event, index) => {
          const style = styleFor(event.kind);
          return (
            <span
              key={`${event.ts}-${event.kind}-${index}`}
              title={event.label}
              aria-label={event.label}
              style={{ ...tick, left: at(event.ts), background: style.colour }}
            />
          );
        })}
        <span style={{ ...playhead, left: at(playheadMs) }} />
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, opacity: 0.7 }}>
        <span>{clock(fromMs)}</span>
        {/* The label is what makes scrubbing coaching rather than seeking. */}
        <span style={{ color: nearest ? styleFor(nearest.kind).colour : undefined }}>
          {nearest ? nearest.label : clock(playheadMs)}
        </span>
        <span>{clock(tape.toTs * 1000)}</span>
      </div>
    </div>
  );
}

/** Local wall time, which is how the player remembers the evening. */
export function clock(ms: number): string {
  return new Date(ms).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

const rail: CSSProperties = {
  position: "relative",
  height: 22,
  border: "1px solid var(--grey-700, #333)",
  background: "rgba(0,0,0,.3)",
  cursor: "pointer",
};

const tick: CSSProperties = {
  position: "absolute",
  top: 3,
  width: 2,
  height: 16,
  transform: "translateX(-1px)",
};

const playhead: CSSProperties = {
  position: "absolute",
  top: 0,
  width: 1,
  height: "100%",
  background: "var(--phos-200)",
  boxShadow: "0 0 6px var(--phos-300)",
};
