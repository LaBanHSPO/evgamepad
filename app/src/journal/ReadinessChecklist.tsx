import type { CSSProperties } from "react";
import type { ReadinessItem } from "./types";

/**
 * Five questions, asked before the session.
 *
 * **Advisory, always.** Nothing here has ever blocked an unlock or a fire, and it must not start:
 * a checklist that can lock you out becomes a checklist you click through, and then it measures
 * nothing.
 *
 * Three answers, not two. `null` is *declined*, which is a real answer and different from "no" —
 * collapsing them would turn a skipped question into a bad night.
 */

export const LABELS: Record<string, string> = {
  sleep: "Slept and rested",
  calm: "Emotionally level",
  focus: "Free of distractions",
  risk_accepted: "Accept tonight's risk cap",
  plan_reviewed: "Plan and news reviewed",
};

export function ReadinessChecklist({ items, onChange, disabled = false }: {
  items: ReadinessItem[];
  onChange?: (item: string, ok: boolean | null, note?: string | null) => void;
  disabled?: boolean;
}): JSX.Element {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      {items.map((entry) => (
        <div key={entry.item} style={row}>
          <span style={{ flex: 1 }}>{LABELS[entry.item] ?? entry.item}</span>
          <div style={{ display: "flex", gap: 6 }}>
            {([true, false, null] as (boolean | null)[]).map((value) => (
              <button
                key={String(value)}
                type="button"
                disabled={disabled}
                onClick={() => onChange?.(entry.item, value)}
                style={entry.ok === value ? activeButton : plainButton}
              >
                {value === true ? "yes" : value === false ? "no" : "skip"}
              </button>
            ))}
          </div>
        </div>
      ))}
      <p style={note}>Advisory only — readiness never blocks an unlock or a trade.</p>
    </div>
  );
}

/** How many were answered either way. A declined item is answered, not missing. */
export function answered(items: ReadinessItem[]): number {
  return items.filter((entry) => entry.ok !== null).length;
}

const row: CSSProperties = {
  display: "flex", alignItems: "center", gap: 12, fontSize: 13,
};

const plainButton: CSSProperties = {
  background: "transparent", color: "inherit", border: "var(--border-hairline)",
  padding: "3px 10px", cursor: "pointer", fontSize: 12,
};

const activeButton: CSSProperties = {
  ...plainButton, background: "var(--black-3)", color: "var(--phos-200)",
  borderColor: "var(--phos-400)",
};

const note: CSSProperties = { margin: 0, opacity: 0.7, fontSize: 12 };
