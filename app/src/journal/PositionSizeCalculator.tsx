import { useCallback, useState } from "react";
import type { CSSProperties } from "react";
import type { SizeAnswer } from "./types";
import { show } from "./types";

/**
 * Lots for a risk — computed on the gateway, through the same conversion and volume rounding the
 * broker itself enforces.
 *
 * The arithmetic deliberately does not live here. A client-side calculator would agree with the
 * journal and disagree with the broker the first time a volume step changed, and a sizing tool
 * that is wrong about the step is worse than none.
 *
 * **Applying a result changes the HUD's preview only.** There is no path from this panel to an
 * order; LT+RT is still the only thing that trades.
 */

export function PositionSizeCalculator({ symbols, onApply }: {
  symbols: string[];
  onApply?: (lots: number) => void;
}): JSX.Element {
  const [symbol, setSymbol] = useState(symbols[0] ?? "XAUUSD");
  const [entry, setEntry] = useState("");
  const [stop, setStop] = useState("");
  const [equity, setEquity] = useState("");
  const [riskUsd, setRiskUsd] = useState("");
  const [riskPercent, setRiskPercent] = useState("");
  const [answer, setAnswer] = useState<SizeAnswer | null>(null);
  const [error, setError] = useState<string | null>(null);

  const calculate = useCallback(async () => {
    setError(null);
    try {
      const response = await fetch("/api/journal/size", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          symbol,
          entry: Number(entry),
          stop: Number(stop),
          equity: equity ? Number(equity) : null,
          riskUsd: riskUsd ? Number(riskUsd) : null,
          riskPercent: riskPercent ? Number(riskPercent) : null,
        }),
      });
      if (!response.ok) throw new Error(`${response.status}`);
      setAnswer((await response.json()) as SizeAnswer);
    } catch (err) {
      setError(`could not size that (${(err as Error).message})`);
    }
  }, [symbol, entry, stop, equity, riskUsd, riskPercent]);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      <div style={grid}>
        <label style={field}>
          <span style={caption}>Symbol</span>
          <select value={symbol} onChange={(e) => setSymbol(e.target.value)}>
            {symbols.map((name) => <option key={name} value={name}>{name}</option>)}
          </select>
        </label>
        <Field label="Entry" value={entry} onChange={setEntry} />
        <Field label="Stop" value={stop} onChange={setStop} />
        <Field label="Equity" value={equity} onChange={setEquity} />
        <Field label="Risk USD" value={riskUsd} onChange={setRiskUsd} />
        <Field label="Risk %" value={riskPercent} onChange={setRiskPercent} />
      </div>

      <div>
        <button type="button" onClick={() => void calculate()}>size it</button>
      </div>

      {error ? <p style={{ color: "var(--arcade-red)", margin: 0 }}>{error}</p> : null}

      {answer === null ? null : answer.roundedLots === null ? (
        // A refusal with its reason, never a zero standing in for "cannot".
        <p style={{ margin: 0, color: "var(--arcade-yellow)" }}>{answer.reason}</p>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          <dl style={results}>
            <dt style={caption}>Requested</dt>
            <dd style={value}>{show(answer.requestedLots, 3)} lots</dd>
            <dt style={caption}>Broker-rounded</dt>
            <dd style={value}>{show(answer.roundedLots, 2)} lots</dd>
            <dt style={caption}>Risk you asked for</dt>
            <dd style={value}>{show(answer.riskUsd)}</dd>
            {/* Recomputed from the rounded volume — the risk you will actually carry. */}
            <dt style={caption}>Risk you will carry</dt>
            <dd style={value}>{show(answer.actualRiskUsd)}</dd>
            <dt style={caption}>Conversion</dt>
            <dd style={value}>{answer.rateChain ?? "—"} @ {show(answer.rate, 6)}</dd>
          </dl>
          {answer.cappedAt === null ? null : (
            <p style={{ margin: 0, color: "var(--arcade-yellow)", fontSize: 12 }}>
              capped at the configured {answer.cappedAt} lots
            </p>
          )}
          <div>
            <button type="button" onClick={() => onApply?.(answer.roundedLots!)}>
              use as the HUD preview
            </button>
          </div>
          <p style={{ margin: 0, opacity: 0.7, fontSize: 12 }}>
            Applying changes the preview only. LT + RT is still the only thing that trades.
          </p>
        </div>
      )}
    </div>
  );
}

function Field({ label, value, onChange }: {
  label: string; value: string; onChange: (next: string) => void;
}): JSX.Element {
  return (
    <label style={field}>
      <span style={caption}>{label}</span>
      <input inputMode="decimal" value={value} onChange={(e) => onChange(e.target.value)} />
    </label>
  );
}

const grid: CSSProperties = {
  display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))", gap: 10,
};
const field: CSSProperties = { display: "flex", flexDirection: "column", gap: 3 };
const caption: CSSProperties = { opacity: 0.7, fontSize: 11 };
const value: CSSProperties = { margin: 0, fontFamily: "var(--font-data)" };
const results: CSSProperties = {
  margin: 0, display: "grid", gridTemplateColumns: "auto 1fr", gap: "4px 14px", fontSize: 13,
};
