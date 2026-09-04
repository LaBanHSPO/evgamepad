import { useCallback, useEffect, useState } from "react";
import { OutcomePanel } from "./OutcomePanel";
import { ProcessPanel } from "./ProcessPanel";
import type { MonthScores } from "./ProcessPanel";
import { PlaybookStats } from "./PlaybookStats";
import type { PlaybookRow } from "./PlaybookStats";
import type { ScoreView } from "./ScoreRadar";
import type { TiltRetroView } from "./TiltRetro";
import type { OutcomeView, ProcessView } from "./types";
import { apiUrl } from "../net/gateway";

/**
 * The deck.
 *
 * Process is the default and the only view reachable without a deliberate act. The outcome tab
 * exists, but you have to decide to open it — and the outcome data is not even fetched until you
 * do, so a glance at the deck mid-session cannot show you the money.
 *
 * The point of the game is confidence and improvement, not the balance. This layout is the part
 * of the product that has to hold that line when the player is tempted.
 */

type Tab = "process" | "outcome";

export function Deck(): JSX.Element {
  const [tab, setTab] = useState<Tab>("process");
  const [process, setProcess] = useState<ProcessView | null>(null);
  const [outcome, setOutcome] = useState<OutcomeView | null>(null);
  const [score, setScore] = useState<ScoreView | null>(null);
  const [playbooks, setPlaybooks] = useState<PlaybookRow[]>([]);
  // Kept separate so the process panel's state never holds an outcome figure at all.
  const [playbooksOutcome, setPlaybooksOutcome] = useState<PlaybookRow[]>([]);
  const [tilt, setTilt] = useState<TiltRetroView | null>(null);
  const [distribution, setDistribution] = useState<MonthScores[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (path: string, apply: (data: never) => void) => {
    try {
      const response = await fetch(apiUrl(path));
      if (!response.ok) throw new Error(`${response.status}`);
      apply((await response.json()) as never);
      setError(null);
    } catch (err) {
      setError(`could not load the deck (${(err as Error).message})`);
    }
  }, []);

  useEffect(() => {
    void load("/api/deck/process", setProcess as (data: never) => void);
  }, [load]);

  // The process-side panels. Playbook figures here are n and adherence only; the expectancy and
  // excursion columns arrive with the outcome tab, on the same deliberate click as the money.
  useEffect(() => {
    void fetch(apiUrl("/api/deck/playbooks"))
      .then((r) => r.json())
      .then((body) => setPlaybooks(body.playbooks as PlaybookRow[]))
      .catch(() => undefined);
    void fetch(apiUrl("/api/score/month"))
      .then((r) => r.json())
      .then((body) => setDistribution(body.months as MonthScores[]))
      .catch(() => undefined);
  }, []);

  // The score and the tilt retrospective are per-evening, so they follow the latest session the
  // process panel already resolved rather than guessing a date.
  useEffect(() => {
    const sessionId = process?.latestSession?.sessionId;
    if (!sessionId) return;
    void fetch(apiUrl(`/api/score/session/${encodeURIComponent(sessionId)}`))
      .then((r) => r.json())
      .then((body) => setScore(body as ScoreView))
      .catch(() => undefined);
    void fetch(apiUrl(`/api/deck/tilt/${encodeURIComponent(sessionId)}`))
      .then((r) => r.json())
      .then((body) => setTilt(body as TiltRetroView))
      .catch(() => undefined);
  }, [process]);

  const openOutcome = useCallback(() => {
    setTab("outcome");
    // Fetched only on the deliberate click. Nothing pre-loads the money.
    if (outcome === null) {
      void load("/api/deck/outcome", setOutcome as (data: never) => void);
      // Only now are the playbook table's outcome columns fetched.
      void fetch(apiUrl("/api/deck/playbooks/outcome"))
        .then((r) => r.json())
        .then((body) => setPlaybooksOutcome(body.playbooks as PlaybookRow[]))
        .catch(() => undefined);
    }
  }, [load, outcome]);

  return (
    <main style={shell}>
      <header style={row}>
        <strong>DECK</strong>
        <nav style={{ ...row, marginLeft: 24 }}>
          <button
            type="button"
            onClick={() => setTab("process")}
            style={tab === "process" ? activeTab : inactiveTab}
          >
            Process
          </button>
          <button
            type="button"
            onClick={openOutcome}
            style={tab === "outcome" ? activeTab : inactiveTab}
          >
            Outcome
          </button>
        </nav>
        <span style={{ marginLeft: "auto", opacity: 0.7 }}>
          {process?.disclaimer ?? "cTrader demo · entertainment, not advice"}
        </span>
      </header>

      {error ? <p style={{ color: "var(--arcade-red)" }}>{error}</p> : null}

      {tab === "process" ? (
        <ProcessPanel view={process} score={score} playbooks={playbooks} tilt={tilt}
                      distribution={distribution} />
      ) : (
        <>
          <OutcomePanel view={outcome} />
          <section style={outcomeSection}>
            <h2 style={{ margin: 0, fontSize: 14, letterSpacing: "0.08em" }}>By playbook</h2>
            <PlaybookStats rows={playbooksOutcome} outcome />
          </section>
        </>
      )}

      {process?.citation ? (
        <footer style={{ opacity: 0.6, fontSize: 12 }}>{process.citation}</footer>
      ) : null}
    </main>
  );
}

const shell: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 16,
  padding: 16,
  minHeight: "100%",
  background: "var(--black-1)",
  color: "var(--phos-300)",
  fontFamily: "var(--font-core)",
};

const row: React.CSSProperties = { display: "flex", gap: 12, alignItems: "center" };

const outcomeSection: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 10,
  padding: 14,
  border: "var(--border-hairline)",
  background: "var(--black-2)",
};

const inactiveTab: React.CSSProperties = {
  background: "transparent",
  color: "inherit",
  border: "var(--border-hairline)",
  padding: "6px 14px",
  cursor: "pointer",
};

const activeTab: React.CSSProperties = {
  ...inactiveTab,
  background: "var(--black-3)",
  color: "var(--phos-200)",
};
