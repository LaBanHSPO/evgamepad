import type { CSSProperties } from "react";

/**
 * What each playbook actually did.
 *
 * Process figures — n, clean rate, adherence — are the default. Expectancy, excursions and capture
 * efficiency are outcome, so they only arrive when the outcome tab has been deliberately opened,
 * the same rule the rest of the deck follows.
 */

export interface PlaybookRow {
  playbookId: string;
  name: string;
  n: number;
  cleanRate: number | null;
  adherence: number | null;
  expectancyR?: number | null;
  avgMfe?: number | null;
  avgMae?: number | null;
  efficiency?: number | null;
}

export function PlaybookStats({ rows, outcome = false }: {
  rows: PlaybookRow[];
  outcome?: boolean;
}): JSX.Element {
  if (rows.length === 0) return <p style={note}>no closed trades yet, so no playbook has a record</p>;

  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ borderCollapse: "collapse", width: "100%", fontSize: 13 }}>
        <thead>
          <tr style={{ textAlign: "left", opacity: 0.7 }}>
            <th style={cell}>Playbook</th>
            <th style={cell}>n</th>
            <th style={cell}>Clean</th>
            <th style={cell}>Adherence</th>
            {outcome ? (
              <>
                <th style={cell}>Expectancy</th>
                <th style={cell}>MFE</th>
                <th style={cell}>MAE</th>
                <th style={cell}>Efficiency</th>
              </>
            ) : null}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.playbookId}>
              <td style={cell}>{row.name}</td>
              <td style={cell}>{row.n}</td>
              <td style={cell}>{pct(row.cleanRate)}</td>
              <td style={cell}>{pct(row.adherence)}</td>
              {outcome ? (
                <>
                  <td style={cell}>{r(row.expectancyR)}</td>
                  <td style={cell}>{num(row.avgMfe)}</td>
                  <td style={cell}>{num(row.avgMae)}</td>
                  <td style={cell}>{pct(row.efficiency)}</td>
                </>
              ) : null}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** A missing figure is a gap, never a zero — the deck's rule since phase 6. */
function pct(value: number | null | undefined): string {
  return value === null || value === undefined ? "—" : `${Math.round(value * 100)}%`;
}

function r(value: number | null | undefined): string {
  return value === null || value === undefined ? "—" : `${value >= 0 ? "+" : ""}${value.toFixed(2)}R`;
}

function num(value: number | null | undefined): string {
  return value === null || value === undefined ? "—" : value.toFixed(2);
}

const cell: CSSProperties = { padding: "4px 10px 4px 0", borderBottom: "var(--border-hairline)" };
const note: CSSProperties = { margin: 0, opacity: 0.75, fontSize: 13 };
