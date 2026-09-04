import { useCallback, useEffect, useState } from "react";
import type { CSSProperties } from "react";
import type { TradeRow } from "./types";
import { r } from "./types";
import { apiUrl } from "../net/gateway";

/**
 * `/journal/history` — every trade, filtered along every dimension the journal records.
 *
 * The filters combine on the server against a fixed clause table, so a combination can never
 * return a trade outside what was asked for, and an unknown filter is dropped rather than
 * interpolated. Paging is real: the page size is capped at 200 by the gateway, not by a promise
 * here.
 */

export const FILTERS: { key: string; label: string; options?: string[] }[] = [
  { key: "symbol", label: "Symbol" },
  { key: "timeframe", label: "Timeframe" },
  { key: "playbook", label: "Playbook" },
  { key: "setup", label: "Setup" },
  { key: "side", label: "Side", options: ["", "buy", "sell"] },
  { key: "market_session", label: "Session", options: ["", "asia", "london", "ny"] },
  { key: "intent", label: "Intent",
    options: ["", "planned", "impulsive", "revenge", "unknown"] },
  { key: "result", label: "Result", options: ["", "win", "loss", "breakeven"] },
  { key: "mistake", label: "Mistake" },
];

export function History({ onOpen }: { onOpen?: (cid: string) => void }): JSX.Element {
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [rows, setRows] = useState<TradeRow[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);

  const load = useCallback(() => {
    const params = new URLSearchParams({ page: String(page), size: "50" });
    for (const [key, value] of Object.entries(filters)) {
      if (value) params.set(key, value);
    }
    void fetch(apiUrl(`/api/journal/history?${params}`))
      .then((response) => response.json())
      .then((body) => {
        setRows(body.trades as TradeRow[]);
        setTotal(body.total as number);
      })
      .catch(() => undefined);
  }, [filters, page]);

  useEffect(load, [load]);

  const set = (key: string, value: string) => {
    setPage(0);
    setFilters((existing) => ({ ...existing, [key]: value }));
  };

  return (
    <section style={shell}>
      <header style={{ display: "flex", gap: 12, alignItems: "baseline", flexWrap: "wrap" }}>
        <strong>HISTORY</strong>
        <span style={{ opacity: 0.7, fontSize: 12 }}>{total} trades</span>
      </header>

      <div style={filterGrid}>
        {FILTERS.map((filter) => (
          <label key={filter.key} style={field}>
            <span style={caption}>{filter.label}</span>
            {filter.options ? (
              <select value={filters[filter.key] ?? ""}
                      onChange={(e) => set(filter.key, e.target.value)}>
                {filter.options.map((option) => (
                  <option key={option} value={option}>{option || "any"}</option>
                ))}
              </select>
            ) : (
              <input value={filters[filter.key] ?? ""}
                     onChange={(e) => set(filter.key, e.target.value)} />
            )}
          </label>
        ))}
      </div>

      <div style={{ overflowX: "auto" }}>
        <table style={{ borderCollapse: "collapse", width: "100%", fontSize: 12 }}>
          <thead>
            <tr style={{ textAlign: "left", opacity: 0.7 }}>
              {["Closed", "Symbol", "Side", "TF", "Playbook", "Intent", "R", "Before/During/After",
                "Tape"].map((head) => <th key={head} style={cell}>{head}</th>)}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.cid} style={{ cursor: "pointer" }} onClick={() => onOpen?.(row.cid)}>
                <td style={cell}>{new Date(row.closedAt).toLocaleString()}</td>
                <td style={cell}>{row.symbol}</td>
                <td style={cell}>{row.side}</td>
                <td style={cell}>{row.timeframe ?? "—"}</td>
                <td style={cell}>{row.playbookName ?? "unplanned"}</td>
                <td style={cell}>{row.intent}</td>
                <td style={cell}>{r(row.rMultiple)}</td>
                <td style={cell}>
                  {["before", "during", "after"]
                    .map((stage) => {
                      const value = row.scores?.[stage]?.value;
                      return value === null || value === undefined ? "—" : Math.round(value);
                    })
                    .join(" / ")}
                </td>
                <td style={cell}>{row.hasTape ? "yes" : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {rows.length === 0 ? <p style={note}>nothing matches those filters</p> : null}

      <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
        <button type="button" disabled={page === 0} onClick={() => setPage(page - 1)}>prev</button>
        <span style={{ fontSize: 12, opacity: 0.7 }}>page {page + 1}</span>
        <button type="button" disabled={(page + 1) * 50 >= total}
                onClick={() => setPage(page + 1)}>next</button>
      </div>
    </section>
  );
}

const shell: CSSProperties = { display: "flex", flexDirection: "column", gap: 14, width: "100%" };
const filterGrid: CSSProperties = {
  display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))", gap: 10,
};
const field: CSSProperties = { display: "flex", flexDirection: "column", gap: 3 };
const caption: CSSProperties = { opacity: 0.7, fontSize: 11 };
const cell: CSSProperties = { padding: "4px 10px 4px 0", borderBottom: "var(--border-hairline)" };
const note: CSSProperties = { margin: 0, opacity: 0.7, fontSize: 12 };
