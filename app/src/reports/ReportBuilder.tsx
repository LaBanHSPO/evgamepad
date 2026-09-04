import { useCallback, useEffect, useState } from "react";
import type { CSSProperties } from "react";
import "./report-print.css";
import type { ReportView } from "../settings/types";
import { apiUrl } from "../net/gateway";

/**
 * The report builder, and the report itself.
 *
 * Two things are load-bearing:
 *
 * - **PDF is the browser's own Save as PDF**, over `report-print.css`. No Chromium on the VPS for
 *   a job the machine in front of the player already does.
 * - **The outcome appendix is fetched, not hidden.** Turning it off does not collapse a section —
 *   the gateway never assembles it, so a report saved without it never contained a money figure.
 */

const PERIODS = ["week", "month", "custom", "session"] as const;

export function ReportBuilder(): JSX.Element {
  const [period, setPeriod] = useState<string>("month");
  const [sessionId, setSessionId] = useState("");
  const [includeOutcome, setIncludeOutcome] = useState(false);
  const [report, setReport] = useState<ReportView | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    const params = new URLSearchParams({ period, include_outcome: String(includeOutcome) });
    if (period === "session" && sessionId) params.set("session_id", sessionId);
    void fetch(apiUrl(`/api/reports?${params}`))
      .then((response) => (response.ok ? response.json() : Promise.reject(new Error("refused"))))
      .then((body: ReportView) => { setReport(body); setError(null); })
      .catch(() => setError("could not build that report"));
  }, [period, sessionId, includeOutcome]);

  useEffect(load, [load]);

  return (
    <main style={shell}>
      <header className="no-print" style={row}>
        <strong>REPORT</strong>
        <nav style={{ ...row, marginLeft: 20 }}>
          {PERIODS.map((name) => (
            <button key={name} type="button" onClick={() => setPeriod(name)}
                    style={period === name ? activeTab : inactiveTab}>
              {name}
            </button>
          ))}
        </nav>
        {period === "session" ? (
          <input placeholder="2026-08-31" value={sessionId}
                 onChange={(e) => setSessionId(e.target.value)} />
        ) : null}
        <label style={{ display: "flex", gap: 6, alignItems: "center", fontSize: 12 }}>
          <input type="checkbox" checked={includeOutcome}
                 onChange={(e) => setIncludeOutcome(e.target.checked)} />
          include the outcome appendix
        </label>
        <button type="button" style={{ marginLeft: "auto" }} onClick={() => window.print()}>
          save as PDF
        </button>
      </header>

      {error ? <p style={{ color: "var(--arcade-red)" }}>{error}</p> : null}

      {report === null ? <p>building…</p> : (
        <article className="report" style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <section className="cover" style={panel}>
            <h1 style={{ margin: 0, fontSize: 20 }}>
              {report.kind === "session" ? `Session ${report.sessionId}` : `${report.period} report`}
            </h1>
            <p style={note}>generated {new Date(report.generatedAt).toLocaleString()}</p>
            <div style={grid}>
              {Object.entries(report.cover).map(([key, value]) => (
                <Stat key={key} label={key} value={value} />
              ))}
            </div>
            <p className="disclaimer" style={note}>{report.disclaimer}</p>
          </section>

          {report.heatmap ? (
            <section style={panel}>
              <h2 style={heading}>Days</h2>
              <table>
                <thead>
                  <tr><th>Session</th><th>Score</th><th>Trades</th><th>Declined</th></tr>
                </thead>
                <tbody>
                  {report.heatmap.map((day) => (
                    <tr key={day.sessionId}>
                      <td>{day.sessionId}</td>
                      {/* Printed as a number as well as a colour: a mono printer has no bands. */}
                      <td className="heatmap-cell">{day.score === null ? "—" : Math.round(day.score)}</td>
                      <td>{day.trades}</td>
                      <td>{day.declined}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          ) : null}

          {report.mistakes?.mistakes?.length ? (
            <section style={panel}>
              <h2 style={heading}>Mistakes</h2>
              <ul style={{ margin: 0, paddingLeft: 18, fontSize: 13 }}>
                {report.mistakes.mistakes.map((entry) => (
                  <li key={entry.code}>{entry.code} — {entry.count}</li>
                ))}
              </ul>
            </section>
          ) : null}

          {report.analysis?.thesis ? (
            <section style={panel}>
              <h2 style={heading}>Analysis</h2>
              {/* Player text as a text child. Never markup, on screen or on paper. */}
              <p style={{ margin: 0 }}>{report.analysis.thesis}</p>
            </section>
          ) : null}

          {report.outcome ? (
            <section className="outcome" style={panel}>
              <h2 style={heading}>Outcome appendix</h2>
              <p style={note}>
                Asked for explicitly. A report built without this section never contained these
                figures at all.
              </p>
              <pre style={{ margin: 0, fontSize: 11, whiteSpace: "pre-wrap" }}>
                {JSON.stringify(report.outcome, null, 2)}
              </pre>
            </section>
          ) : null}
        </article>
      )}
    </main>
  );
}

function Stat({ label, value }: { label: string; value: unknown }): JSX.Element {
  const shown = typeof value === "object" && value !== null
    ? String((value as { value?: unknown }).value ?? "—")
    : String(value ?? "—");
  return (
    <div>
      <div style={{ opacity: 0.7, fontSize: 12 }}>{label}</div>
      <div style={{ fontSize: 24, fontFamily: "var(--font-data)" }}>{shown}</div>
    </div>
  );
}

const shell: CSSProperties = {
  display: "flex", flexDirection: "column", gap: 14, padding: 16, minHeight: "100%",
  background: "var(--black-1)", color: "var(--phos-300)", fontFamily: "var(--font-core)",
};
const row: CSSProperties = { display: "flex", gap: 12, alignItems: "center" };
const panel: CSSProperties = {
  display: "flex", flexDirection: "column", gap: 10, padding: 14,
  border: "var(--border-hairline)", background: "var(--black-2)",
};
const heading: CSSProperties = { margin: 0, fontSize: 14, letterSpacing: "0.08em" };
const grid: CSSProperties = {
  display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))", gap: 14,
};
const note: CSSProperties = { margin: 0, opacity: 0.75, fontSize: 12 };
const inactiveTab: CSSProperties = {
  background: "transparent", color: "inherit", border: "var(--border-hairline)",
  padding: "6px 14px", cursor: "pointer",
};
const activeTab: CSSProperties = {
  ...inactiveTab, background: "var(--black-3)", color: "var(--phos-200)",
};
