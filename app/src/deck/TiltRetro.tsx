import type { CSSProperties } from "react";

/**
 * Tilt, as a record of an evening.
 *
 * Read this next to what it is *not*: an input to the Process Score. Phase 9 decided that taxing an
 * evening for a bad ten minutes reintroduces the punishment this whole design avoids, so the score
 * never sees it. What it is placed beside matters too — the comparison drawn here is against
 * adherence, never against P/L.
 */

export interface TiltRetroView {
  samples: { ts: number; score: number; band: string }[];
  bands: Record<string, number>;
  topDrivers: { driver: string; samples: number }[];
  adherence: number | null;
  peak?: number;
}

const BAND_COLOUR: Record<string, string> = {
  calm: "var(--phos-400)",
  warm: "var(--arcade-yellow)",
  hot: "var(--arcade-red)",
  scorched: "var(--arcade-red)",
};

export function TiltRetro({ view }: { view: TiltRetroView | null }): JSX.Element {
  if (view === null || view.samples.length === 0) {
    return <p style={note}>no tilt samples for this evening</p>;
  }

  const total = view.samples.length;
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      {/* Bands over the evening, in proportion. A shape, not a verdict. */}
      <div style={{ display: "flex", height: 14, width: "100%" }}>
        {Object.entries(view.bands).map(([band, n]) => (
          <span
            key={band}
            title={`${band} · ${n} of ${total} samples`}
            style={{ width: `${(n / total) * 100}%`, background: BAND_COLOUR[band] ?? "var(--grey-300)" }}
          />
        ))}
      </div>

      <div style={{ fontSize: 12, opacity: 0.8 }}>
        {Object.entries(view.bands)
          .map(([band, n]) => `${band} ${Math.round((n / total) * 100)}%`)
          .join(" · ")}
        {view.peak === undefined ? "" : ` · peak ${view.peak.toFixed(2)}`}
      </div>

      {view.topDrivers.length > 0 ? (
        <ul style={{ margin: 0, paddingLeft: 18, fontSize: 13 }}>
          {view.topDrivers.map((driver) => (
            <li key={driver.driver}>{driver.driver}</li>
          ))}
        </ul>
      ) : null}

      <p style={note}>
        {view.adherence === null
          ? "no fires tonight, so there is no adherence to set this against"
          : `adherence that evening: ${Math.round(view.adherence * 100)}%`}
        {" · "}a retrospective, never a score input
      </p>
    </div>
  );
}

const note: CSSProperties = { margin: 0, opacity: 0.75, fontSize: 13 };
