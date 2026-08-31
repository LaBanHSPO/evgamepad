import type { CSSProperties } from "react";
import type { ActualVsPlan, StageScore } from "./types";
import { r, show } from "./types";

/**
 * Actual vs Plan, the four groups, and the three execution scores.
 *
 * The name of the first panel is load-bearing. It is **Actual vs Plan**, not "theoretical profit":
 * it compares what you planned with what you did, and it never claims the target would have been
 * reached. Where price went after your exit is not evidence about a position you had closed.
 */

export const GROUP_LABELS: Record<string, string> = {
  "planned-win": "Planned · win",
  "planned-loss": "Planned · loss",
  "impulsive/revenge-win": "Impulsive · win",
  "impulsive/revenge-loss": "Impulsive · loss",
};

export function ActualVsPlanPanel({ view }: { view: ActualVsPlan }): JSX.Element {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      <dl style={list}>
        <dt style={caption}>{view.label}</dt>
        <dd style={value}>
          {r(view.plannedR)} planned → {r(view.realisedR)} realised
          {view.deltaR === null ? "" : ` (${r(view.deltaR)})`}
        </dd>
        <dt style={caption}>Stop / target</dt>
        <dd style={value}>{show(view.plannedSl)} / {show(view.plannedTp)}</dd>
      </dl>

      {view.amendments.length === 0 ? null : (
        <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12 }}>
          {view.amendments.map((amendment, index) => (
            <li key={`${amendment.ts}-${index}`}>
              stop moved to {show(amendment.sl ?? null)}
            </li>
          ))}
        </ul>
      )}

      {view.worsenedStops.length > 0 ? (
        <p style={{ margin: 0, color: "var(--arcade-yellow)", fontSize: 12 }}>
          {view.worsenedStops.length} stop move{view.worsenedStops.length === 1 ? "" : "s"} widened
          the risk
        </p>
      ) : null}
    </div>
  );
}

export function GroupChart({ groups, unclassified }: {
  groups: Record<string, number>;
  unclassified: number;
}): JSX.Element {
  const total = Object.values(groups).reduce((a, b) => a + b, 0);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      {Object.entries(GROUP_LABELS).map(([key, label]) => (
        <div key={key} style={{ display: "flex", gap: 10, alignItems: "center", fontSize: 12 }}>
          <span style={{ width: 130, opacity: 0.8 }}>{label}</span>
          <span style={{ flex: 1, height: 10, background: "rgba(255,255,255,.06)" }}>
            <span style={{
              display: "block", height: "100%",
              width: total === 0 ? 0 : `${((groups[key] ?? 0) / total) * 100}%`,
              background: key.startsWith("planned") ? "var(--phos-300)" : "var(--arcade-yellow)",
            }} />
          </span>
          <span style={{ fontFamily: "var(--font-data)" }}>{groups[key] ?? 0}</span>
        </div>
      ))}
      {/* Excluded, and said so. Guessing at intent is how a clean trade gets libelled. */}
      <p style={note}>
        {unclassified} trade{unclassified === 1 ? "" : "s"} unclassified — excluded rather than
        guessed. Confirm the intent on a trade to place it.
      </p>
    </div>
  );
}

export function ExecutionScores({ scores }: { scores: Record<string, StageScore> }): JSX.Element {
  return (
    <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
      {["before", "during", "after"].map((stage) => {
        const entry = scores[stage];
        return (
          <div key={stage} style={{ minWidth: 120 }}>
            <div style={caption}>{stage}</div>
            <div style={{ fontSize: 22, fontFamily: "var(--font-data)" }}>
              {entry?.value === null || entry === undefined ? "—" : Math.round(entry.value)}
            </div>
            {entry?.dropped?.length ? (
              // Named so a low denominator is visible rather than silently flattering.
              <div style={{ fontSize: 10, opacity: 0.6 }}>
                not measured: {entry.dropped.join(", ")}
              </div>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}

const list: CSSProperties = {
  margin: 0, display: "grid", gridTemplateColumns: "auto 1fr", gap: "4px 14px", fontSize: 13,
};
const caption: CSSProperties = { opacity: 0.7, fontSize: 11 };
const value: CSSProperties = { margin: 0, fontFamily: "var(--font-data)" };
const note: CSSProperties = { margin: 0, opacity: 0.7, fontSize: 12 };
