import type { CSSProperties } from "react";
import type { DayRow } from "./types";

/**
 * The day heatmap, coloured by **process**.
 *
 * Colour encodes the Process Score and activity, and P/L is not available here at all — it lives
 * behind the deck's deliberate Outcome click. A calendar coloured by money is a calendar you read
 * for money, and that is the habit this whole product is built against.
 *
 * A day with no score is drawn as an outline, not as a dark red square. Nothing measured is not a
 * bad day.
 */

const BANDS: { min: number; colour: string }[] = [
  { min: 90, colour: "var(--phos-200)" },
  { min: 75, colour: "var(--phos-300)" },
  { min: 60, colour: "var(--phos-400)" },
  { min: 0, colour: "var(--arcade-yellow)" },
];

export function colourFor(score: number | null): string | null {
  if (score === null) return null;
  return (BANDS.find((band) => score >= band.min) ?? BANDS[BANDS.length - 1]).colour;
}

export function Heatmap({ days, selected, onSelect }: {
  days: DayRow[];
  selected?: string | null;
  onSelect?: (sessionId: string) => void;
}): JSX.Element {
  if (days.length === 0) return <p style={note}>no sessions in this period yet</p>;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      <div style={grid}>
        {days.map((day) => {
          const colour = colourFor(day.score);
          return (
            <button
              key={day.sessionId}
              type="button"
              onClick={() => onSelect?.(day.sessionId)}
              title={`${day.sessionId} · ${day.trades} trades · ${day.declined} declined`}
              style={{
                ...cell,
                background: colour ?? "transparent",
                border: colour ? "1px solid transparent"
                               : "1px dashed var(--grey-700, #444)",
                outline: selected === day.sessionId ? "2px solid var(--phos-200)" : undefined,
                // Activity is the second dimension: a busier day reads denser.
                opacity: colour ? Math.min(1, 0.55 + day.trades * 0.15) : 0.8,
              }}
            >
              <span style={{ fontSize: 9, color: colour ? "var(--black-1)" : "inherit" }}>
                {day.sessionId.slice(8)}
              </span>
            </button>
          );
        })}
      </div>
      <p style={note}>
        Colour is Process Score; density is activity. A dashed day has no score yet — dollars live
        behind the deck's Outcome tab.
      </p>
    </div>
  );
}

const grid: CSSProperties = {
  display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(26px, 1fr))", gap: 4,
};

const cell: CSSProperties = {
  aspectRatio: "1", display: "flex", alignItems: "center", justifyContent: "center",
  cursor: "pointer", color: "inherit", padding: 0,
};

const note: CSSProperties = { margin: 0, opacity: 0.7, fontSize: 12 };
