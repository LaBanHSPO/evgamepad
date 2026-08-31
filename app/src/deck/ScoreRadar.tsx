/**
 * The Process Score, as five spokes.
 *
 * This is the game layer, and it lives on the deck rather than the HUD on purpose: the score is
 * computed at session close and there is no live one to watch. A number you can refresh mid-trade
 * becomes the anxiety the P/L used to be.
 *
 * A **vacuous** axis — one with no evidence, like Adherence on a zero-trade evening — draws as a
 * dashed n/a ring, never as a zero spoke. Those are different claims: a spoke at zero says you did
 * badly, and an evening you correctly sat out did nothing badly at all.
 *
 * Drawn as hand-written SVG rather than pulled from a chart library: five points and two rings is
 * less code than configuring anything, and the n/a ring is not a thing chart libraries draw.
 */

import type { CSSProperties } from "react";

export interface ScoreAxis {
  name: string;
  value: number | null;
  detail: Record<string, unknown>;
}

export interface ScoreView {
  sessionId: string;
  total: number;
  totalExact: number;
  weightsVersion: number;
  oqMean: number | null;
  nFires: number;
  naAxes: string[];
  axes: ScoreAxis[];
  weights: Record<string, number> | null;
}

const LABELS: Record<string, string> = {
  adherence: "Adherence",
  selectivity: "Selectivity",
  risk_discipline: "Risk",
  preparation: "Preparation",
  review: "Review",
};

const SIZE = 220;
const CENTRE = SIZE / 2;
const RADIUS = 82;

/** Spoke `i` of `n`, at `value` percent of full. Starts at twelve o'clock and runs clockwise. */
function point(index: number, count: number, value: number): [number, number] {
  const angle = (index / count) * Math.PI * 2 - Math.PI / 2;
  const r = (RADIUS * value) / 100;
  return [CENTRE + r * Math.cos(angle), CENTRE + r * Math.sin(angle)];
}

export function ScoreRadar({ view }: { view: ScoreView | null }): JSX.Element {
  if (view === null) return <p style={note}>no score for this evening yet</p>;

  const axes = view.axes;
  // A vacuous axis is drawn at the ring, not at the centre — the polygon must not dip toward zero
  // for an axis that was never scored.
  const polygon = axes
    .map((axis, i) => point(i, axes.length, axis.value ?? 100).join(","))
    .join(" ");

  return (
    <div style={{ display: "flex", gap: 20, flexWrap: "wrap", alignItems: "center" }}>
      <svg width={SIZE} height={SIZE} role="img" aria-label={`process score ${view.total}`}>
        {[25, 50, 75, 100].map((ring) => (
          <circle key={ring} cx={CENTRE} cy={CENTRE} r={(RADIUS * ring) / 100}
                  fill="none" stroke="rgba(255,255,255,.08)" />
        ))}
        {axes.map((axis, i) => {
          const [x, y] = point(i, axes.length, 100);
          return <line key={axis.name} x1={CENTRE} y1={CENTRE} x2={x} y2={y}
                       stroke="rgba(255,255,255,.10)" />;
        })}

        <polygon points={polygon} fill="rgba(0,255,65,.16)" stroke="var(--phos-300)"
                 strokeWidth={1.5} />

        {/* The n/a ring: dashed, at full radius, so a missing axis reads as "not asked" rather
            than as a failure. */}
        {axes.filter((a) => a.value === null).map((axis) => {
          const [x, y] = point(axes.indexOf(axis), axes.length, 100);
          return (
            <circle key={`na-${axis.name}`} cx={x} cy={y} r={7} fill="none"
                    stroke="var(--grey-300, #999)" strokeDasharray="3 3" />
          );
        })}

        {axes.map((axis, i) => {
          const [x, y] = point(i, axes.length, 122);
          return (
            <text key={`t-${axis.name}`} x={x} y={y} fontSize={10} textAnchor="middle"
                  fill="var(--phos-400)" opacity={axis.value === null ? 0.5 : 0.9}>
              {LABELS[axis.name] ?? axis.name}
            </text>
          );
        })}

        <text x={CENTRE} y={CENTRE + 6} fontSize={30} textAnchor="middle"
              fontFamily="var(--font-data)" fill="var(--phos-200)">
          {view.total}
        </text>
      </svg>

      <dl style={list}>
        {axes.map((axis) => (
          <div key={axis.name} style={{ display: "contents" }}>
            <dt style={{ opacity: axis.value === null ? 0.5 : 0.75 }}>
              {LABELS[axis.name] ?? axis.name}
            </dt>
            <dd style={{ margin: 0, fontFamily: "var(--font-data)" }}>
              {axis.value === null ? (
                <span style={{ opacity: 0.6 }}>n/a — {naReason(axis)}</span>
              ) : (
                Math.round(axis.value)
              )}
            </dd>
          </div>
        ))}
        <dt style={{ opacity: 0.75 }}>Tape</dt>
        <dd style={{ margin: 0, fontFamily: "var(--font-data)" }}>
          {view.oqMean === null ? "not sampled" : view.oqMean.toFixed(2)}
        </dd>
        <dt style={{ opacity: 0.75 }}>Fires</dt>
        <dd style={{ margin: 0, fontFamily: "var(--font-data)" }}>{view.nFires}</dd>
      </dl>
    </div>
  );
}

/** Why an axis was not scored, from the axis's own detail. Never a number standing in for a reason. */
export function naReason(axis: ScoreAxis): string {
  const reason = axis.detail?.reason;
  return typeof reason === "string" ? reason : "no evidence";
}

const list: CSSProperties = {
  margin: 0,
  display: "grid",
  gridTemplateColumns: "auto auto",
  gap: "4px 14px",
  fontSize: 13,
};

const note: CSSProperties = { margin: 0, opacity: 0.75, fontSize: 13 };
