import { useCallback, useEffect, useState } from "react";
import type { CSSProperties } from "react";
import { ActualVsPlanPanel, ExecutionScores } from "./TradeQuality";
import type { MistakeDefinition, TradeDetailView } from "./types";
import { r, show } from "./types";
import { apiUrl } from "../net/gateway";

/**
 * `/journal/trade/:cid` — everything known about one trade.
 *
 * The page is split by *who wrote it*. The plan and the execution came from the broker and the
 * gateway and cannot be edited here at all; the review below them is yours and is the only thing
 * this page can change. That is the boundary the whole journal rests on, so it is visible in the
 * layout rather than only in the schema.
 */

const INTENTS = ["planned", "impulsive", "revenge", "unknown"] as const;

export function TradeDetail({ cid, onReplay }: {
  cid: string;
  onReplay?: (cid: string) => void;
}): JSX.Element {
  const [view, setView] = useState<TradeDetailView | null>(null);
  const [definitions, setDefinitions] = useState<MistakeDefinition[]>([]);
  const [note, setNote] = useState("");

  const load = useCallback(() => {
    void fetch(apiUrl(`/api/journal/trade/${encodeURIComponent(cid)}`))
      .then((response) => (response.ok ? response.json() : null))
      .then((body: TradeDetailView | null) => {
        setView(body);
        setNote(body?.review.note ?? "");
      })
      .catch(() => setView(null));
  }, [cid]);

  useEffect(load, [load]);
  useEffect(() => {
    void fetch(apiUrl("/api/journal/mistakes"))
      .then((response) => response.json())
      .then((body) => setDefinitions(body.mistakes as MistakeDefinition[]))
      .catch(() => undefined);
  }, []);

  const review = useCallback(async (body: Record<string, unknown>) => {
    const response = await fetch(apiUrl(`/api/journal/trade/${encodeURIComponent(cid)}`), {
      method: "PUT",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
    });
    if (response.ok) setView((await response.json()) as TradeDetailView);
  }, [cid]);

  const toggleMistake = useCallback(async (code: string, on: boolean) => {
    const url = apiUrl(`/api/journal/trade/${encodeURIComponent(cid)}/mistakes`);
    await (on
      ? fetch(url, { method: "POST", headers: { "content-type": "application/json" },
                     body: JSON.stringify({ code }) })
      : fetch(`${url}/${encodeURIComponent(code)}`, { method: "DELETE" }));
    load();
  }, [cid, load]);

  if (view === null) return <section style={shell}><p>no such trade</p></section>;

  const noted = new Set(view.mistakes.map((m) => m.code));
  const derived = new Set(view.mistakes.filter((m) => m.source === "auto").map((m) => m.code));

  return (
    <section style={shell}>
      <header style={{ display: "flex", gap: 16, alignItems: "baseline", flexWrap: "wrap" }}>
        <strong>{view.plan.side.toUpperCase()} {view.execution.lots} {view.plan.symbol}</strong>
        <span style={{ color: view.execution.rMultiple >= 0
          ? "var(--phos-200)" : "var(--arcade-red)" }}>
          {r(view.execution.rMultiple)}
        </span>
        <span style={{ opacity: 0.7, fontSize: 12 }}>
          {view.plan.playbookName ?? "unplanned"}
        </span>
        {view.hasTape ? (
          <button type="button" onClick={() => onReplay?.(view.plan.cid)}>open the replay</button>
        ) : (
          // Missing tape degrades the link, never the record.
          <span style={{ opacity: 0.6, fontSize: 12 }}>no tape — markers only</span>
        )}
      </header>

      <Panel title="Plan and execution — recorded, not editable">
        <dl style={list}>
          <dt style={caption}>Entry / exit</dt>
          <dd style={value}>{show(view.execution.entry)} → {show(view.execution.exit)}</dd>
          <dt style={caption}>MFE / MAE</dt>
          <dd style={value}>{show(view.execution.mfe)} / {show(view.execution.mae)}</dd>
          <dt style={caption}>Events</dt>
          <dd style={value}>{view.execution.events.map((e) => e.kind).join(" · ") || "—"}</dd>
        </dl>
      </Panel>

      <Panel title="Actual vs Plan">
        <ActualVsPlanPanel view={view.actualVsPlan} />
      </Panel>

      <Panel title="Execution">
        <ExecutionScores scores={view.scores} />
      </Panel>

      {view.grade ? (
        <Panel title="Grade">
          <p style={{ margin: 0 }}>
            {view.grade.requiredPass}/{view.grade.requiredTotal} required rules
            {view.grade.clean ? " · clean" : ""}
          </p>
        </Panel>
      ) : null}

      <Panel title="Your review">
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
          <span style={caption}>Intent</span>
          {INTENTS.map((intent) => (
            <button key={intent} type="button"
                    onClick={() => void review({ intent, note, earlyExit: view.review.earlyExit })}
                    style={view.intent.value === intent ? activeButton : plainButton}>
              {intent}
            </button>
          ))}
          <span style={{ opacity: 0.6, fontSize: 11 }}>
            {view.intent.by === "player" ? "you said so" : "derived from the grade"}
          </span>
        </div>

        <label style={{ display: "flex", gap: 8, alignItems: "center", fontSize: 13 }}>
          <input type="checkbox" checked={view.review.earlyExit}
                 onChange={(e) => void review({ intent: view.intent.value, note,
                                                earlyExit: e.target.checked })} />
          closed early on discretion
        </label>

        <textarea rows={3} value={note} onChange={(e) => setNote(e.target.value)} />
        <div>
          <button type="button"
                  onClick={() => void review({ intent: view.intent.value, note,
                                               earlyExit: view.review.earlyExit })}>
            save review
          </button>
        </div>
      </Panel>

      <Panel title="Mistakes">
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          {definitions.map((definition) => {
            const on = noted.has(definition.code);
            const proved = derived.has(definition.code);
            return (
              <button
                key={definition.code}
                type="button"
                disabled={proved}
                title={proved ? "proved by the rows — not yours to withdraw" : undefined}
                onClick={() => void toggleMistake(definition.code, !on)}
                style={on ? activeButton : plainButton}
              >
                {definition.label}{proved ? " ·" : ""}
              </button>
            );
          })}
        </div>
        <p style={hint}>
          A marked mistake costs nothing — it is counted, never scored.
        </p>
      </Panel>

      {view.attachments.length > 0 ? (
        <Panel title="Charts">
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {view.attachments.map((attachment) => (
              <img key={attachment.id} src={apiUrl(`/api/journal/attachments/${attachment.id}`)}
                   alt={attachment.label ?? "chart"} style={thumb} />
            ))}
          </div>
        </Panel>
      ) : null}
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

const shell: CSSProperties = { display: "flex", flexDirection: "column", gap: 14, width: "100%" };
const panel: CSSProperties = {
  display: "flex", flexDirection: "column", gap: 10, padding: 14,
  border: "var(--border-hairline)", background: "var(--black-2)",
};
const heading: CSSProperties = { margin: 0, fontSize: 14, letterSpacing: "0.08em" };
const list: CSSProperties = {
  margin: 0, display: "grid", gridTemplateColumns: "auto 1fr", gap: "4px 14px", fontSize: 13,
};
const caption: CSSProperties = { opacity: 0.7, fontSize: 11 };
const value: CSSProperties = { margin: 0, fontFamily: "var(--font-data)" };
const hint: CSSProperties = { margin: 0, opacity: 0.7, fontSize: 12 };
const plainButton: CSSProperties = {
  background: "transparent", color: "inherit", border: "var(--border-hairline)",
  padding: "3px 10px", cursor: "pointer", fontSize: 12,
};
const activeButton: CSSProperties = {
  ...plainButton, background: "var(--black-3)", color: "var(--phos-200)",
  borderColor: "var(--phos-400)",
};
const thumb: CSSProperties = {
  maxWidth: 200, maxHeight: 140, border: "var(--border-hairline)", objectFit: "cover",
};
