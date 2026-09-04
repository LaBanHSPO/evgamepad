import { useCallback, useEffect, useState } from "react";
import type { CSSProperties } from "react";
import { Heatmap } from "./Heatmap";
import { History } from "./History";
import { MistakeTrends } from "./MistakeTrends";
import { Today } from "./Today";
import { TradeDetail } from "./TradeDetail";
import { GroupChart } from "./TradeQuality";
import type { DayRow, MistakeDefinition, Overview, TradeRow } from "./types";
import { r, show } from "./types";
import { apiUrl } from "../net/gateway";

/**
 * The journal shell: today, the dashboard, history, and one trade.
 *
 * Process leads on every view here. The heatmap is coloured by Process Score, the dashboard's
 * headline is Process Consistency, and there is no dollar figure on any of it — the money stays
 * behind the deck's deliberate Outcome click, which is the one place in this product it belongs.
 */

type Tab = "today" | "dashboard" | "history" | "trade";

const PERIODS: { key: string; label: string; days: number | null }[] = [
  { key: "week", label: "Week", days: 7 },
  { key: "month", label: "Month", days: 31 },
  { key: "custom", label: "All", days: null },
];

export function Journal({ onReplay, onApplyLots }: {
  onReplay?: (cid: string) => void;
  onApplyLots?: (lots: number) => void;
}): JSX.Element {
  const [tab, setTab] = useState<Tab>("today");
  const [period, setPeriod] = useState("month");
  const [overview, setOverview] = useState<Overview | null>(null);
  const [days, setDays] = useState<DayRow[]>([]);
  const [day, setDay] = useState<Record<string, unknown> | null>(null);
  const [definitions, setDefinitions] = useState<MistakeDefinition[]>([]);
  const [cid, setCid] = useState<string | null>(null);

  const window_ = PERIODS.find((p) => p.key === period)?.days ?? null;
  const fromMs = window_ === null ? null : Date.now() - window_ * 86_400_000;

  const load = useCallback(() => {
    const query = fromMs === null ? "" : `?from_ms=${Math.round(fromMs)}`;
    void fetch(apiUrl(`/api/journal/overview${query}`))
      .then((response) => response.json())
      .then((body: Overview) => setOverview(body))
      .catch(() => undefined);
    void fetch(apiUrl(`/api/journal/days${query}`))
      .then((response) => response.json())
      .then((body) => setDays(body.days as DayRow[]))
      .catch(() => undefined);
  }, [fromMs]);

  useEffect(load, [load]);
  useEffect(() => {
    void fetch(apiUrl("/api/journal/mistakes"))
      .then((response) => response.json())
      .then((body) => setDefinitions(body.mistakes as MistakeDefinition[]))
      .catch(() => undefined);
  }, []);

  const openDay = useCallback((sessionId: string) => {
    void fetch(apiUrl(`/api/journal/day/${encodeURIComponent(sessionId)}`))
      .then((response) => response.json())
      .then((body) => setDay(body as Record<string, unknown>))
      .catch(() => undefined);
  }, []);

  const openTrade = useCallback((next: string) => {
    setCid(next);
    setTab("trade");
  }, []);

  const setFocus = useCallback(async (code: string | null) => {
    const current = await fetch(apiUrl("/api/journal/system")).then((response) => response.json());
    await fetch(apiUrl("/api/journal/system"), {
      method: "PUT",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ ...current, focusCode: code }),
    });
    load();
  }, [load]);

  return (
    <main style={shell}>
      <header style={row}>
        <strong>JOURNAL</strong>
        <nav style={{ ...row, marginLeft: 20 }}>
          {(["today", "dashboard", "history"] as Tab[]).map((name) => (
            <button key={name} type="button" onClick={() => setTab(name)}
                    style={tab === name ? activeTab : inactiveTab}>
              {name}
            </button>
          ))}
        </nav>
        {/* One configured account, shown as an identity chip — never a selector. */}
        {overview ? (
          <span style={chip}>
            {overview.account.broker} · {overview.account.kind}
          </span>
        ) : null}
      </header>

      {tab === "today" ? <Today onApplyLots={onApplyLots} /> : null}
      {tab === "history" ? <History onOpen={openTrade} /> : null}
      {tab === "trade" && cid ? <TradeDetail cid={cid} onReplay={onReplay} /> : null}

      {tab === "dashboard" ? (
        <>
          <section style={panel}>
            <div style={row}>
              {PERIODS.map((entry) => (
                <button key={entry.key} type="button" onClick={() => setPeriod(entry.key)}
                        style={period === entry.key ? activeTab : inactiveTab}>
                  {entry.label}
                </button>
              ))}
            </div>
            <div style={grid}>
              <Stat label="Sessions" value={String(overview?.sessions ?? 0)} />
              <Stat label="Process Score" value={show(overview?.processScoreMean ?? null, 0)} />
              <Stat
                label="Process Consistency"
                value={overview?.consistency.value === null || overview === null
                  ? "—" : String(Math.round(overview.consistency.value))}
                caption={overview?.consistency.reason
                  ?? `n=${overview?.consistency.n ?? 0}`}
              />
            </div>
          </section>

          <section style={panel}>
            <h2 style={heading}>Days</h2>
            <Heatmap days={days} selected={String(day?.sessionId ?? "")} onSelect={openDay} />
          </section>

          {day ? <DayPanel day={day} onOpenTrade={openTrade} /> : null}

          <section style={panel}>
            <h2 style={heading}>Latest ten</h2>
            <TradeList rows={overview?.latestTrades ?? []} onOpen={openTrade} />
          </section>

          <section style={panel}>
            <h2 style={heading}>Trade quality</h2>
            {overview ? (
              <GroupChart groups={overview.groups.groups}
                          unclassified={overview.groups.unclassified} />
            ) : null}
          </section>

          <section style={panel}>
            <h2 style={heading}>Mistakes</h2>
            <MistakeTrends rows={overview?.mistakes.mistakes ?? []} definitions={definitions}
                           focus={overview?.mistakes.focus ?? null}
                           onFocus={(code) => void setFocus(code)} />
          </section>
        </>
      ) : null}
    </main>
  );
}

function DayPanel({ day, onOpenTrade }: {
  day: Record<string, unknown>;
  onOpenTrade: (cid: string) => void;
}): JSX.Element {
  const score = day.score as { total: number | null } | null;
  const readiness = (day.readiness ?? []) as { item: string; ok: boolean | null }[];
  const analysis = day.analysis as { thesis: string | null } | null;
  const mistakes = (day.mistakes ?? []) as { code: string }[];
  const trades = (day.trades ?? []) as TradeRow[];

  return (
    <section style={panel}>
      <h2 style={heading}>{String(day.sessionId)}</h2>
      <div style={grid}>
        <Stat label="Process Score" value={show(score?.total ?? null, 0)} />
        <Stat label="Trades" value={String(trades.length)} />
        <Stat label="Readiness"
              value={`${readiness.filter((entry) => entry.ok !== null).length}/${readiness.length}`} />
        <Stat label="Mistakes" value={String(mistakes.length)} />
      </div>
      {/* Player text, as a text child. Never markup. */}
      {analysis?.thesis ? <blockquote style={quote}>{analysis.thesis}</blockquote> : null}
      <TradeList rows={trades} onOpen={onOpenTrade} />
    </section>
  );
}

function TradeList({ rows, onOpen }: {
  rows: TradeRow[];
  onOpen: (cid: string) => void;
}): JSX.Element {
  if (rows.length === 0) return <p style={note}>no trades</p>;
  return (
    <ul style={{ margin: 0, padding: 0, listStyle: "none", fontSize: 12 }}>
      {rows.map((trade) => (
        <li key={trade.cid} style={{ padding: "3px 0", borderBottom: "var(--border-hairline)" }}>
          <button type="button" onClick={() => onOpen(trade.cid)} style={linkButton}>
            {new Date(trade.closedAt).toLocaleTimeString()} · {trade.side} {trade.symbol}
            {" · "}{trade.timeframe ?? "—"} · {trade.playbookName ?? "unplanned"}
            {" · "}{trade.intent} · {r(trade.rMultiple)}
            {trade.hasTape ? " · replay" : ""}
          </button>
        </li>
      ))}
    </ul>
  );
}

function Stat({ label, value, caption }: {
  label: string; value: string; caption?: string;
}): JSX.Element {
  return (
    <div>
      <div style={{ opacity: 0.7, fontSize: 12 }}>{label}</div>
      <div style={{ fontSize: 26, fontFamily: "var(--font-data)" }}>{value}</div>
      {caption ? <div style={{ fontSize: 11, opacity: 0.65 }}>{caption}</div> : null}
    </div>
  );
}

const shell: CSSProperties = {
  display: "flex", flexDirection: "column", gap: 16, padding: 16, minHeight: "100%",
  background: "var(--black-1)", color: "var(--phos-300)", fontFamily: "var(--font-core)",
};
const row: CSSProperties = { display: "flex", gap: 12, alignItems: "center" };
const panel: CSSProperties = {
  display: "flex", flexDirection: "column", gap: 10, padding: 14,
  border: "var(--border-hairline)", background: "var(--black-2)",
};
const heading: CSSProperties = { margin: 0, fontSize: 14, letterSpacing: "0.08em" };
const grid: CSSProperties = {
  display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: 16,
};
const inactiveTab: CSSProperties = {
  background: "transparent", color: "inherit", border: "var(--border-hairline)",
  padding: "6px 14px", cursor: "pointer",
};
const activeTab: CSSProperties = {
  ...inactiveTab, background: "var(--black-3)", color: "var(--phos-200)",
};
const chip: CSSProperties = {
  marginLeft: "auto", opacity: 0.7, fontSize: 12, border: "var(--border-hairline)",
  padding: "3px 10px",
};
const linkButton: CSSProperties = {
  background: "transparent", border: "none", color: "inherit", cursor: "pointer",
  padding: 0, font: "inherit", textAlign: "left",
};
const note: CSSProperties = { margin: 0, opacity: 0.7, fontSize: 12 };
const quote: CSSProperties = {
  margin: 0, paddingLeft: 12, borderLeft: "2px solid var(--phos-600)", opacity: 0.9,
};
