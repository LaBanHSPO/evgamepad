import type { CSSProperties } from "react";
import type { MistakeDefinition, MistakeTrendRow } from "./types";

/**
 * What keeps going wrong, counted.
 *
 * Counts and one optional focus — no streak, no badge, no penalty. A mistake here costs nothing:
 * it does not touch the Process Score and it does not accumulate. The only mechanic is choosing
 * **one** thing to work on, because a ranked list of your own failures is not a training aid.
 *
 * The auto/player split is shown because it changes what the number means. `auto` is something the
 * rows prove; `player` is something you decided. Conflating them would let the journal appear to
 * know things it cannot.
 */

export function MistakeTrends({ rows, definitions, focus, onFocus }: {
  rows: MistakeTrendRow[];
  definitions: MistakeDefinition[];
  focus: string | null;
  onFocus?: (code: string | null) => void;
}): JSX.Element {
  if (rows.length === 0) return <p style={note}>nothing recorded yet</p>;

  const labels = Object.fromEntries(definitions.map((d) => [d.code, d.label]));
  const worst = Math.max(...rows.map((row) => row.count));

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      {rows.map((row) => (
        <div key={row.code} style={{ display: "flex", gap: 10, alignItems: "center", fontSize: 12 }}>
          <span style={{ width: 170, opacity: 0.85 }}>{labels[row.code] ?? row.code}</span>
          <span style={{ flex: 1, height: 10, background: "rgba(255,255,255,.06)" }}>
            <span style={{
              display: "block", height: "100%", width: `${(row.count / worst) * 100}%`,
              background: focus === row.code ? "var(--phos-200)" : "var(--arcade-yellow)",
            }} />
          </span>
          <span style={{ fontFamily: "var(--font-data)", width: 74 }}>
            {row.count} · {row.trades} trade{row.trades === 1 ? "" : "s"}
          </span>
          <span style={{ opacity: 0.6, width: 92 }}>
            {row.auto} proved · {row.player} noted
          </span>
          <button
            type="button"
            onClick={() => onFocus?.(focus === row.code ? null : row.code)}
            style={focus === row.code ? activeButton : plainButton}
          >
            {focus === row.code ? "working on it" : "focus"}
          </button>
        </div>
      ))}
      <p style={note}>Counts only — one focus at a time, and nothing here reaches the score.</p>
    </div>
  );
}

const plainButton: CSSProperties = {
  background: "transparent", color: "inherit", border: "var(--border-hairline)",
  padding: "2px 8px", cursor: "pointer", fontSize: 11,
};
const activeButton: CSSProperties = {
  ...plainButton, background: "var(--black-3)", color: "var(--phos-200)",
  borderColor: "var(--phos-400)",
};
const note: CSSProperties = { margin: 0, opacity: 0.7, fontSize: 12 };
