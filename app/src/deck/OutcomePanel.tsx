import type { OutcomeView } from "./types";
import { percent, show, signed } from "./types";

/**
 * The second tab.
 *
 * Reached by a deliberate click, and fetched only then. The Sharpe always carries its sample size,
 * and below the configured threshold it refuses to print a number at all — twenty evenings a month
 * means the first two months of Sharpe are noise, and a confident 2.4 would be worse than silence.
 */
export function OutcomePanel({ view }: { view: OutcomeView | null }): JSX.Element {
  if (view === null) return <p>loading the outcome figures…</p>;

  const { current, previousMonth, delta } = view.months;

  return (
    <>
      <section style={panel}>
        <h2 style={heading}>This month</h2>
        <div style={grid}>
          <Stat label="Return" value={percent(current.returnPct)} delta={delta.returnPct} />
          <Stat label="Average R" value={show(current.averageR)} delta={delta.averageR} />
          <Stat label="Win rate" value={percent(current.winRate)} delta={delta.winRate} />
          <Stat label="Profit factor" value={show(current.profitFactor)} delta={delta.profitFactor} />
          <Stat label="Max drawdown" value={percent(current.maxDrawdown)} />
          <Stat label="Trades" value={String(current.trades)} />
        </div>
        <p style={note}>
          {previousMonth ? `compared with ${previousMonth}` : "no previous month to compare with yet"}
        </p>
      </section>

      <section style={panel}>
        <h2 style={heading}>Sharpe</h2>
        <div style={{ fontSize: 26, fontFamily: "var(--font-data)" }}>{view.sharpe.display}</div>
        <p style={note}>{view.sharpe.note}</p>
      </section>

      <section style={panel}>
        <h2 style={heading}>By setup</h2>
        {Object.keys(view.bySetup).length === 0 ? (
          <p style={note}>no closed trades yet</p>
        ) : (
          <table style={{ borderCollapse: "collapse", width: "100%" }}>
            <thead>
              <tr style={{ textAlign: "left", opacity: 0.7 }}>
                <th style={cell}>Setup</th>
                <th style={cell}>Trades</th>
                <th style={cell}>Avg R</th>
                <th style={cell}>Win rate</th>
                <th style={cell}>Profit factor</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(view.bySetup).map(([tag, row]) => (
                <tr key={tag}>
                  <td style={cell}>{tag.replace(/_/g, " ")}</td>
                  <td style={cell}>{row.trades}</td>
                  <td style={cell}>{show(row.averageR)}</td>
                  <td style={cell}>{percent(row.winRate)}</td>
                  <td style={cell}>{show(row.profitFactor)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <p style={note}>{view.disclaimer}</p>
    </>
  );
}

function Stat({ label, value, delta }: {
  label: string;
  value: string;
  delta?: number | null;
}): JSX.Element {
  return (
    <div>
      <div style={{ opacity: 0.7, fontSize: 12 }}>{label}</div>
      <div style={{ fontSize: 26, fontFamily: "var(--font-data)" }}>{value}</div>
      {delta !== undefined && delta !== null ? (
        <div style={{ fontSize: 12, opacity: 0.8 }}>{signed(delta)} vs last month</div>
      ) : null}
    </div>
  );
}

const panel: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 10,
  padding: 14,
  border: "var(--border-hairline)",
  background: "var(--black-2)",
};
const heading: React.CSSProperties = { margin: 0, fontSize: 14, letterSpacing: "0.08em" };
const grid: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
  gap: 16,
};
const note: React.CSSProperties = { margin: 0, opacity: 0.75, fontSize: 13 };
const cell: React.CSSProperties = { padding: "4px 8px", borderBottom: "var(--border-hairline)" };
