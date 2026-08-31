import { useCallback, useEffect, useState } from "react";
import { OutcomePanel } from "./OutcomePanel";
import { ProcessPanel } from "./ProcessPanel";
import type { OutcomeView, ProcessView } from "./types";

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
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (path: string, apply: (data: never) => void) => {
    try {
      const response = await fetch(path);
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

  const openOutcome = useCallback(() => {
    setTab("outcome");
    // Fetched only on the deliberate click. Nothing pre-loads the money.
    if (outcome === null) void load("/api/deck/outcome", setOutcome as (data: never) => void);
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
        <ProcessPanel view={process} />
      ) : (
        <OutcomePanel view={outcome} />
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
