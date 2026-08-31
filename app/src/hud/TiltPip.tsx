import type { CSSProperties } from "react";

/**
 * The tilt pip: a colour, and always a sentence.
 *
 * A bare number would be a judgement. The whole reason every component is a measured behaviour is
 * so the HUD can say *what* it saw — "re-entered 40 s after a loss" — which is something you can
 * act on. From the warm band up, the top driver is always shown.
 *
 * The warm band deliberately costs nothing. A warning that never charges you is one you keep
 * listening to.
 */

export type TiltBand = "calm" | "warm" | "hot" | "scorched";

export interface TiltState {
  score: number;
  band: TiltBand;
  top: string[];
  cooldownUntil?: number;
}

/**
 * Mirrors `tilt.confirm_hold_ms` in `config/default.yaml`. The server owns the block; this is only
 * the UX friction, so it lives client-side — and `tilt.test.ts` fails the build if the two drift.
 */
export const HOT_HOLD_MS = 750;

const COLOURS: Record<TiltBand, string> = {
  calm: "var(--phos-400)",
  warm: "var(--arcade-yellow)",
  hot: "var(--arcade-red)",
  scorched: "var(--arcade-red)",
};

/** What each band changes about firing. Exits appear nowhere in this table, by design. */
export const BAND_FRICTION: Record<TiltBand, string> = {
  calm: "",
  warm: "",
  hot: "hold RT to fire",
  scorched: "opens paused",
};

export function TiltPip({ tilt, nowMs = Date.now() }: {
  tilt: TiltState | null;
  nowMs?: number;
}): JSX.Element {
  const band: TiltBand = tilt?.band ?? "calm";
  const remaining =
    tilt?.cooldownUntil && tilt.cooldownUntil > nowMs
      ? Math.ceil((tilt.cooldownUntil - nowMs) / 1000)
      : 0;

  return (
    <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
      <span style={{ ...pip, background: COLOURS[band] }} aria-label={`tilt ${band}`} />
      <span style={{ fontSize: 12, opacity: 0.85 }}>{band}</span>
      {/* From warm up, name the behaviour. Never a bare number on its own. */}
      {band !== "calm" && tilt?.top?.[0] ? (
        <span style={{ fontSize: 12, opacity: 0.85 }}>· {tilt.top[0]}</span>
      ) : null}
      {BAND_FRICTION[band] ? (
        <span style={{ fontSize: 12, color: COLOURS[band] }}>· {BAND_FRICTION[band]}</span>
      ) : null}
      {remaining > 0 ? (
        <span style={{ fontSize: 12, color: COLOURS[band] }}>· {remaining}s</span>
      ) : null}
    </div>
  );
}

const pip: CSSProperties = {
  width: 10,
  height: 10,
  borderRadius: "50%",
  display: "inline-block",
};

/**
 * The client-side friction, as a parameter of the existing fire predicate.
 *
 * This is the *only* thing tilt changes about the FSM, which is why phase 3's suite stays valid
 * unchanged. The server owns the actual block; the client is never the security boundary.
 */
export function confirmHoldMsFor(band: TiltBand, hotHoldMs: number): number {
  return band === "hot" || band === "scorched" ? hotHoldMs : 0;
}
