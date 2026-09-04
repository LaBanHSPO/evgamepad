import { useCallback, useEffect, useRef, useState } from "react";
import type { CSSProperties } from "react";
import { PositionSizeCalculator } from "./PositionSizeCalculator";
import { ReadinessChecklist, answered } from "./ReadinessChecklist";
import { WorldSessions } from "./WorldSessions";
import type { ReadinessItem, TodayView } from "./types";
import { apiUrl } from "../net/gateway";

/**
 * `/journal/today` — the page you open before a session and land on after one.
 *
 * Prepare, trade, close, review, without leaving the shell. Everything on it is advisory: the
 * clocks tell you where the day is, the checklist asks five questions it will never enforce, the
 * calculator answers a sizing question and hands the answer to the HUD's *preview*.
 */

const SYMBOLS = ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY"];

export function Today({ onApplyLots }: { onApplyLots?: (lots: number) => void }): JSX.Element {
  const [view, setView] = useState<TodayView | null>(null);
  const [analysis, setAnalysis] = useState({
    thesis: "", invalidation: "", eventRisks: "", notes: "", instruments: "", tags: "",
  });
  const [status, setStatus] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const load = useCallback(() => {
    void fetch(apiUrl("/api/journal/today"))
      .then((response) => response.json())
      .then((body: TodayView) => {
        setView(body);
        if (body.analysis) {
          setAnalysis({
            thesis: body.analysis.thesis ?? "",
            invalidation: body.analysis.invalidation ?? "",
            eventRisks: body.analysis.eventRisks ?? "",
            notes: body.analysis.notes ?? "",
            instruments: body.analysis.instruments.join(", "),
            tags: body.analysis.tags.join(", "),
          });
        }
      })
      .catch(() => setStatus("could not load tonight"));
  }, []);

  useEffect(load, [load]);

  const put = useCallback(async (body: Record<string, unknown>) => {
    const response = await fetch(apiUrl("/api/journal/today"), {
      method: "PUT",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
    });
    if (response.ok) setView((await response.json()) as TodayView);
  }, []);

  const setReadiness = useCallback((item: string, ok: boolean | null) => {
    setView((existing) => existing === null ? existing : {
      ...existing,
      readiness: existing.readiness.map((entry) =>
        entry.item === item ? { ...entry, ok } : entry),
    });
    void put({ readiness: [{ item, ok }] });
  }, [put]);

  const saveAnalysis = useCallback(() => {
    void put({
      analysis: {
        thesis: analysis.thesis,
        invalidation: analysis.invalidation,
        eventRisks: analysis.eventRisks,
        notes: analysis.notes,
        instruments: split(analysis.instruments),
        tags: split(analysis.tags),
        keyLevels: [],
      },
    }).then(() => setStatus("analysis saved"));
  }, [analysis, put]);

  // The file is sent as a raw body: the server reads its magic bytes and names it itself, so the
  // browser's filename never reaches a path.
  const attach = useCallback(async (file: File) => {
    setStatus(null);
    const response = await fetch(
      apiUrl(`/api/journal/attachments?label=${encodeURIComponent(file.name)}`),
      { method: "POST", headers: { "content-type": file.type }, body: file },
    );
    if (!response.ok) {
      setStatus((await response.json().catch(() => ({}))).detail ?? "that file was not stored");
      return;
    }
    load();
  }, [load]);

  if (view === null) return <section style={shell}><p>{status ?? "loading tonight…"}</p></section>;

  const readiness: ReadinessItem[] = view.readiness;
  return (
    <section style={shell}>
      <header style={{ display: "flex", gap: 16, alignItems: "baseline", flexWrap: "wrap" }}>
        <strong>TONIGHT · {view.sessionId}</strong>
        <span style={{ opacity: 0.7, fontSize: 12 }}>
          readiness {answered(readiness)}/{readiness.length} answered
        </span>
      </header>

      <Panel title="Markets"><WorldSessions /></Panel>

      <Panel title="Readiness">
        <ReadinessChecklist items={readiness} onChange={setReadiness} />
      </Panel>

      <Panel title="Tonight's analysis">
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <Text label="Thesis" rows={3} value={analysis.thesis}
                onChange={(v) => setAnalysis({ ...analysis, thesis: v })} />
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            <Text label="Instruments" value={analysis.instruments}
                  onChange={(v) => setAnalysis({ ...analysis, instruments: v })} />
            <Text label="Tags" value={analysis.tags}
                  onChange={(v) => setAnalysis({ ...analysis, tags: v })} />
            <Text label="Invalidation" value={analysis.invalidation}
                  onChange={(v) => setAnalysis({ ...analysis, invalidation: v })} />
            <Text label="Event risks" value={analysis.eventRisks}
                  onChange={(v) => setAnalysis({ ...analysis, eventRisks: v })} />
          </div>
          <Text label="Notes" rows={3} value={analysis.notes}
                onChange={(v) => setAnalysis({ ...analysis, notes: v })} />
          <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
            <button type="button" onClick={saveAnalysis}>save analysis</button>
            {status ? <span style={{ opacity: 0.7, fontSize: 12 }}>{status}</span> : null}
          </div>
        </div>
      </Panel>

      {view.deskPlan ? (
        <Panel title="The desk's plan">
          {/* Beside the player's analysis, never merged into it. */}
          <p style={{ margin: 0, opacity: 0.85 }}>{view.deskPlan.text}</p>
          <p style={note}>
            written by the desk{view.deskPlan.offline ? " (offline)" : ""} — your analysis above is
            yours alone
          </p>
        </Panel>
      ) : null}

      <Panel title="Size a trade">
        <PositionSizeCalculator symbols={SYMBOLS} onApply={onApplyLots} />
      </Panel>

      <Panel title="Charts">
        <input ref={fileRef} type="file" accept="image/png,image/jpeg,image/webp"
               onChange={(e) => {
                 const file = e.target.files?.[0];
                 if (file) void attach(file);
               }} />
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 8 }}>
          {view.attachments.map((attachment) => (
            <img key={attachment.id} src={apiUrl(`/api/journal/attachments/${attachment.id}`)}
                 alt={attachment.label ?? "chart"} style={thumb} />
          ))}
        </div>
        <p style={note}>PNG, JPEG or WebP, attached by hand. Nothing is scraped.</p>
      </Panel>
    </section>
  );
}

function Panel({ title, children }: { title: string; children: React.ReactNode }): JSX.Element {
  return (
    <section style={panel}>
      <h2 style={heading}>{title}</h2>
      {children}
    </section>
  );
}

function Text({ label, value, onChange, rows }: {
  label: string; value: string; onChange: (next: string) => void; rows?: number;
}): JSX.Element {
  return (
    <label style={{ display: "flex", flexDirection: "column", gap: 3 }}>
      <span style={{ opacity: 0.7, fontSize: 11 }}>{label}</span>
      {rows ? (
        <textarea rows={rows} value={value} onChange={(e) => onChange(e.target.value)} />
      ) : (
        <input value={value} onChange={(e) => onChange(e.target.value)} />
      )}
    </label>
  );
}

function split(value: string): string[] {
  return value.split(",").map((part) => part.trim()).filter(Boolean);
}

const shell: CSSProperties = {
  display: "flex", flexDirection: "column", gap: 14, width: "100%",
};
const panel: CSSProperties = {
  display: "flex", flexDirection: "column", gap: 10, padding: 14,
  border: "var(--border-hairline)", background: "var(--black-2)",
};
const heading: CSSProperties = { margin: 0, fontSize: 14, letterSpacing: "0.08em" };
const note: CSSProperties = { margin: 0, opacity: 0.7, fontSize: 12 };
const thumb: CSSProperties = {
  maxWidth: 160, maxHeight: 110, border: "var(--border-hairline)", objectFit: "cover",
};
