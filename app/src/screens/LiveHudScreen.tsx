import { useCallback, useEffect, useRef, useState } from "react";
import { ConfirmGrade } from "../playbook/ConfirmGrade";
import { PlaybookPicker } from "../playbook/PlaybookPicker";
import { PostTradeChecklist } from "../playbook/PostTradeChecklist";
import type { Grade, GradePreview, Playbook } from "../playbook/types";
import { GameAgent } from "../agent";
import type { AgentView } from "../agent";
import { PadPoller } from "../pad/poll";
import { newCid } from "../net/cid";
import { GameClient } from "../net/ws";
import type { SocketStatus } from "../net/ws";
import type { Envelope } from "../protocol/types";

/**
 * The live HUD — the one screen wired to the real gateway.
 *
 * The other screens in this app are the design prototype with fixed data. This one holds a real
 * socket, a real pad, and the real FSM, so two rules from the plan apply here and nowhere else:
 *
 * - **Prices are written imperatively.** React owns layout; it does not re-render on quotes. The
 *   price nodes are refs written at the conflated rate, so a 20 Hz tape costs no reconciliation.
 * - **P/L reads in R by default.** Watching the money mid-trade is what pulls attention off the
 *   process, so dollars are one deliberate toggle away.
 *
 * The token is pasted once and lives in component state for the session — never storage.
 */

const SYMBOLS = ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY"];

const PHASE_COPY: Record<string, string> = {
  LOCKED: "LOCKED — tap View to unlock",
  IDLE: "IDLE — hold LT to clutch",
  CLUTCH: "CLUTCH — A buy · B sell · X close · Y flatten",
  ARMED: "ARMED — pull RT to fire",
  FIRE: "FIRE — waiting on the broker",
  UNKNOWN: "UNRESOLVED — exits allowed, new opens blocked",
};

export function LiveHudScreen(): JSX.Element {
  const [token, setToken] = useState("");
  const [status, setStatus] = useState<SocketStatus | "idle">("idle");
  const [view, setView] = useState<AgentView | null>(null);
  const [showDollars, setShowDollars] = useState(false);
  const [refused, setRefused] = useState<number | null>(null);
  const [log, setLog] = useState<string[]>([]);
  const [playbooks, setPlaybooks] = useState<Playbook[]>([]);
  const [activePlaybook, setActivePlaybook] = useState<string | null>(null);
  const [preview, setPreview] = useState<GradePreview | null>(null);
  const [grade, setGrade] = useState<Grade | null>(null);
  const clientRef = useRef<GameClient | null>(null);

  const bidRef = useRef<HTMLSpanElement>(null);
  const askRef = useRef<HTMLSpanElement>(null);
  const pnlRef = useRef<HTMLSpanElement>(null);
  const agentRef = useRef<GameAgent | null>(null);
  const pollerRef = useRef<PadPoller | null>(null);
  const rUsdRef = useRef(20);

  const note = useCallback((line: string) => {
    setLog((prev) => [`${new Date().toLocaleTimeString()} ${line}`, ...prev].slice(0, 8));
  }, []);

  // The book loads once; retired playbooks never appear, but their old grades still resolve.
  useEffect(() => {
    void fetch("/api/playbooks")
      .then((r) => r.json())
      .then((body) => setPlaybooks(body.playbooks as Playbook[]))
      .catch(() => undefined);
  }, []);

  const onMessage = useCallback(
    (envelope: Envelope) => {
      agentRef.current?.onMessage(envelope);
      const payload = envelope.p as Record<string, number | string>;

      switch (envelope.t) {
        case "quote": {
          // Direct DOM writes: the price tape must not cost a React render per tick.
          if (bidRef.current) bidRef.current.textContent = String(payload.bid ?? "—");
          if (askRef.current) askRef.current.textContent = String(payload.ask ?? "—");
          break;
        }
        case "pnl": {
          const open = Number(payload.openPnl ?? 0);
          if (pnlRef.current) {
            pnlRef.current.textContent = showDollars
              ? `${open >= 0 ? "+" : ""}${open.toFixed(2)} USD`
              : `${open >= 0 ? "+" : ""}${(open / rUsdRef.current).toFixed(2)}R`;
          }
          break;
        }
        case "order.reject":
          note(`reject: ${payload.reason}`);
          break;
        case "order.ack":
          note(`ack ${payload.side} ${payload.lots} ${payload.sym}`);
          break;
        case "maint":
          note(`maint: ${payload.note ?? "broker unavailable"}`);
          break;
        case "grade": {
          // The authoritative grade, pushed at FIRE. The preview above it was only a look.
          setGrade(envelope.p as unknown as Grade);
          break;
        }
        default:
          break;
      }
    },
    [note, showDollars],
  );

  const connect = useCallback(() => {
    if (!token) return;
    const client = new GameClient(`${location.origin.replace(/^http/, "ws")}/ws`, token, {
      onMessage,
      onStatus: (next) => {
        setStatus(next);
        if (next === "closed") agentRef.current?.onSocketClosed();
      },
      onProtocolMismatch: (theirs) => setRefused(theirs),
    });

    const agent = new GameAgent({
      client,
      symbols: SYMBOLS,
      onView: setView,
      onStandDown: (conditions) => {
        note(`stood down (${conditions.join(", ")})`);
        void fetch("/api/journal/stand-down", {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ conditions }),
        });
      },
    });

    clientRef.current = client;
    agentRef.current = agent;
    const poller = new PadPoller({
      onFrame: (frame) => agent.onFrame(frame),
      onAbsent: (input) => agent.onAbsent(input),
      onProfile: (profile) => note(`pad: ${profile.id} (${profile.buttons} buttons)`),
    });
    pollerRef.current = poller;

    client.connect();
    poller.start();
    client.send("sub", "session", { ch: "quotes", syms: SYMBOLS });
  }, [note, onMessage, token]);

  useEffect(() => () => {
    pollerRef.current?.stop();
  }, []);

  const selectPlaybook = useCallback((id: string | null) => {
    setActivePlaybook(id);
    // The active playbook is session state, so the gateway is told rather than only the browser.
    clientRef.current?.send("playbook.select", "session", { playbookId: id });
  }, []);

  /** The grade shown before you commit. Nothing is persisted by a preview. */
  const previewGrade = useCallback(async (side: "buy" | "sell") => {
    const current = agentRef.current?.view;
    if (!current) return;
    try {
      const response = await fetch("/api/playbooks/grade-preview", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          cid: newCid(), sym: current.symbol, side, lots: current.lots,
          playbookId: activePlaybook,
        }),
      });
      setPreview((await response.json()) as GradePreview);
    } catch {
      setPreview(null);
    }
  }, [activePlaybook]);

  const submitChecklist = useCallback((answers: Record<string, boolean>) => {
    const cid = grade?.cid;
    setGrade(null);
    if (!cid || Object.keys(answers).length === 0) return;
    void fetch("/api/playbooks/checklist", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ cid, answers }),
    }).then(() => note("checklist saved"));
  }, [grade, note]);

  const checkIn = useCallback((phase: "pre" | "post", rating: number | null) => {
    void fetch("/api/journal/checkin", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ phase, rating }),
    }).then(() => note(rating === null ? `${phase} check-in skipped` : `${phase} check-in ${rating}/5`));
  }, [note]);

  if (refused !== null) {
    return (
      <main style={shell}>
        <h1 style={{ color: "var(--arcade-red)" }}>PROTOCOL MISMATCH</h1>
        <p>
          The gateway speaks protocol v{refused}; this build speaks v1. Reload to pick up the new
          bundle. The HUD will not guess at an envelope it does not know.
        </p>
      </main>
    );
  }

  return (
    <main style={shell}>
      <header style={row}>
        <strong>LIVE HUD</strong>
        <span style={{ opacity: 0.7 }}>cTrader demo · not advice</span>
        <span style={{ marginLeft: "auto" }}>socket: {status}</span>
      </header>

      {status === "idle" ? (
        <section style={panel}>
          <label htmlFor="ws-token">
            Session token — pasted once, kept in memory, never stored
          </label>
          <div style={row}>
            <input
              id="ws-token"
              type="password"
              value={token}
              onChange={(event) => setToken(event.target.value)}
              style={{ flex: 1, background: "var(--black-2)", color: "inherit", padding: 8 }}
            />
            <button type="button" onClick={connect} disabled={!token}>
              Connect
            </button>
          </div>
        </section>
      ) : null}

      <section style={panel}>
        <div style={{ fontSize: 32, fontFamily: "var(--font-data)" }}>
          <span ref={bidRef}>—</span>
          <span style={{ opacity: 0.4 }}> / </span>
          <span ref={askRef}>—</span>
        </div>
        <div style={row}>
          <span>{view?.symbol ?? SYMBOLS[0]}</span>
          <span>{view?.lots ?? 0.01} lots</span>
          <span>{view?.timeframe ?? "M5"}</span>
          <span style={{ marginLeft: "auto" }}>
            open <span ref={pnlRef}>0.00R</span>
          </span>
          <button type="button" onClick={() => setShowDollars((prev) => !prev)}>
            {showDollars ? "show R" : "show $"}
          </button>
        </div>
      </section>

      <section style={panel}>
        <PlaybookPicker playbooks={playbooks} activeId={activePlaybook} onSelect={selectPlaybook} />
      </section>

      <section style={panel}>
        <div>{PHASE_COPY[view?.phase ?? "LOCKED"]}</div>
        {view?.side ? <div>armed: {view.side}</div> : null}
        <ConfirmGrade preview={preview} />
        <div style={row}>
          <button type="button" onClick={() => void previewGrade("buy")}>
            preview buy
          </button>
          <button type="button" onClick={() => void previewGrade("sell")}>
            preview sell
          </button>
        </div>
        <div style={row}>
          <span>stood down tonight: {view?.stoodDown ?? 0}</span>
          <span>pad: {view?.padConnected ? "connected" : "absent"}</span>
          <span>pending: {view?.pendingIntents ?? 0}</span>
        </div>
      </section>

      <section style={row}>
        {/* Safety exits: reachable with no pad, no focus, and a dead session. */}
        <button type="button" onClick={() => agentRef.current?.flatten()}>
          FLATTEN
        </button>
        <button type="button" onClick={() => agentRef.current?.closePosition()}>
          CLOSE
        </button>
        <span style={{ marginLeft: "auto", opacity: 0.7 }}>tab must stay focused</span>
      </section>

      <section style={panel}>
        <div style={row}>
          <span>check-in</span>
          {[1, 2, 3, 4, 5].map((rating) => (
            <button key={rating} type="button" onClick={() => checkIn("pre", rating)}>
              {rating}
            </button>
          ))}
          <button type="button" onClick={() => checkIn("pre", null)}>
            skip
          </button>
        </div>
      </section>

      <PostTradeChecklist cid={grade?.cid ?? ""} grade={grade} onDone={submitChecklist} />

      <section style={{ ...panel, fontFamily: "var(--font-terminal)", opacity: 0.8 }}>
        {log.length === 0 ? <div>no events yet</div> : log.map((line) => <div key={line}>{line}</div>)}
      </section>
    </main>
  );
}

const shell: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 12,
  padding: 16,
  minHeight: "100%",
  background: "var(--black-1)",
  color: "var(--phos-300)",
  fontFamily: "var(--font-core)",
};

const panel: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 8,
  padding: 12,
  border: "var(--border-hairline)",
  background: "var(--black-2)",
};

const row: React.CSSProperties = { display: "flex", gap: 12, alignItems: "center" };
