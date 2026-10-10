import { useCallback, useEffect, useRef, useState } from "react";
import { ConfirmGrade } from "../playbook/ConfirmGrade";
import { PlaybookPicker } from "../playbook/PlaybookPicker";
import { PostTradeChecklist } from "../playbook/PostTradeChecklist";
import type { Grade, GradePreview, Playbook } from "../playbook/types";
import { GameAgent } from "../agent";
import type { AgentView } from "../agent";
import { useCabinet } from "../journey/Cabinet";
import { PadPoller } from "../pad/poll";
import { HOT_HOLD_MS, TiltPip, confirmHoldMsFor } from "../hud/TiltPip";
import type { TiltState } from "../hud/TiltPip";
import { newCid } from "../net/cid";
import { GameClient } from "../net/ws";
import type { SocketStatus } from "../net/ws";
import { apiUrl, wsUrl } from "../net/gateway";
import type { Envelope, Quote } from "../protocol/types";
import { fetchHud } from "../arcade/fetch";
import type { ArcadeHud } from "../arcade/types";
import "../practice/practice.css";

/**
 * The live HUD — socket, pad, and FSM on a plain board.
 *
 * Matrix and city artboards poll `/api/arcade` for the same figures without a token. This screen
 * still holds the socket: prices are written imperatively, P/L reads in R by default, and the
 * token is pasted once into component state — never storage.
 */

const SYMBOLS = ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY"];

const PHASE_COPY: Record<string, string> = {
  LOCKED: "Locked. Tap View on your controller when you are ready.",
  IDLE: "Ready. Hold LT to prepare an action. Nothing is submitted yet.",
  CLUTCH: "Keep holding LT. A prepares BUY, B prepares SELL, X prepares close, Y prepares close all.",
  ARMED: "Check the side, symbol and size. Press RT to confirm, or release LT to cancel.",
  FIRE: "Waiting for the broker to answer. Do not repeat the entry.",
  UNKNOWN: "Result not confirmed. Check positions in cTrader before doing anything else. Do not repeat the entry.",
};

export function LiveHudScreen(): JSX.Element {
  const cabinet = useCabinet();
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
  const [tilt, setTilt] = useState<TiltState | null>(null);
  // The evening's realised P/L in R, straight from the broker's `dayPnl`. Never re-derived from
  // summed fills, and shown only in the hot-band confirm block.
  const [dayR, setDayR] = useState<number | null>(null);
  const [hud, setHud] = useState<ArcadeHud | null>(null);
  const [openPnl, setOpenPnl] = useState<number | null>(null);
  const [quoteStatus, setQuoteStatus] = useState("Waiting for a price");
  const clientRef = useRef<GameClient | null>(null);

  const bidRef = useRef<HTMLSpanElement>(null);
  const askRef = useRef<HTMLSpanElement>(null);
  const quotesRef = useRef<Record<string, Quote>>({});
  const agentRef = useRef<GameAgent | null>(null);
  const pollerRef = useRef<PadPoller | null>(null);
  const rUsdRef = useRef<number | null>(null);
  const previewVersionRef = useRef(0);

  useEffect(() => {
    previewVersionRef.current += 1;
    setPreview(null);
  }, [view?.symbol, view?.lots, view?.side, activePlaybook]);

  const paintQuote = useCallback((symbol = agentRef.current?.view.symbol ?? SYMBOLS[0]) => {
    const quote = quotesRef.current[symbol];
    const age = quote ? Math.max(0, Date.now() - quote.ts) : Infinity;
    const fresh = age < 5000;
    if (bidRef.current) bidRef.current.textContent = fresh ? String(quote.bid) : "--";
    if (askRef.current) askRef.current.textContent = fresh ? String(quote.ask) : "--";
    setQuoteStatus(!quote ? "Waiting for a price" : fresh ? "Recent price received" : `Price is ${Math.floor(age / 1000)}s old. Wait for an update.`);
  }, []);

  useEffect(() => {
    let active = true;
    const refresh = async () => {
      const body = await fetchHud();
      if (!active) return;
      setHud(body);
      rUsdRef.current = body && body.risk.rUsd > 0 ? body.risk.rUsd : null;
    };
    void refresh();
    const timer = window.setInterval(() => { void refresh(); paintQuote(); }, 5000);
    return () => { active = false; window.clearInterval(timer); };
  }, [paintQuote]);

  const note = useCallback((line: string) => {
    setLog((prev) => [`${new Date().toLocaleTimeString()} ${line}`, ...prev].slice(0, 8));
  }, []);

  // The book loads once; retired playbooks never appear, but their old grades still resolve.
  useEffect(() => {
    void fetch(apiUrl("/api/playbooks"))
      .then((r) => r.json())
      .then((body) => setPlaybooks(Array.isArray(body.playbooks) ? body.playbooks as Playbook[] : []))
      .catch(() => undefined);
  }, []);

  const onMessage = useCallback(
    (envelope: Envelope) => {
      agentRef.current?.onMessage(envelope);
      const payload = envelope.p as Record<string, number | string>;

      switch (envelope.t) {
        case "quote": {
          const quote = envelope.p as unknown as Quote;
          quotesRef.current[quote.sym] = quote;
          paintQuote();
          break;
        }
        case "pnl": {
          const open = Number(payload.openPnl ?? 0);
          setDayR(payload.dayPnl == null || rUsdRef.current === null ? null : Number(payload.dayPnl) / rUsdRef.current);
          setOpenPnl(open);
          break;
        }
        case "order.reject":
          note(`Not placed: ${payload.reason}. Check the message and your limits before trying again.`);
          break;
        case "order.ack":
          note("Broker acknowledged the request. Refreshing open positions.");
          clientRef.current?.send("snap", "session", {});
          break;
        case "maint":
          note(`maint: ${payload.note ?? "broker unavailable"}`);
          break;
        case "error":
          note(`Gateway: ${payload.message ?? payload.code ?? "request unavailable"}`);
          break;
        case "tilt": {
          // The band raises the confirm hold. It never touches a close, and never a state.
          const state = envelope.p as unknown as TiltState;
          setTilt(state);
          agentRef.current?.setConfirmHoldMs(confirmHoldMsFor(state.band, HOT_HOLD_MS));
          break;
        }
        case "grade": {
          // The authoritative grade, pushed at FIRE. The preview above it was only a look.
          setGrade(envelope.p as unknown as Grade);
          break;
        }
        default:
          break;
      }
    },
    [note, paintQuote],
  );

  const connect = useCallback(() => {
    if (!token.trim() || clientRef.current?.pending) return;
    pollerRef.current?.stop();
    clientRef.current?.disconnect();
    const client = new GameClient(wsUrl(), token.trim(), {
      onMessage,
      onStatus: (next) => {
        setStatus(next);
        if (next === "open") {
          clientRef.current?.send("sub", "session", { ch: "quotes", syms: SYMBOLS });
          clientRef.current?.send("snap", "session", {});
          pollerRef.current?.start();
        } else {
          pollerRef.current?.stop();
          agentRef.current?.onSocketClosed();
          quotesRef.current = {};
          paintQuote();
          setOpenPnl(null);
        }
      },
      onProtocolMismatch: (theirs) => setRefused(theirs),
    });

    const agent = new GameAgent({
      client,
      symbols: SYMBOLS,
      onView: (next) => {
        setView((previous) => JSON.stringify(previous) === JSON.stringify(next) ? previous : next);
        paintQuote(next.symbol);
      },
      onStandDown: (conditions) => {
        note(`stood down (${conditions.join(", ")})`);
        void fetch(apiUrl("/api/journal/stand-down"), {
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
  }, [note, onMessage, token, paintQuote]);

  useEffect(() => () => {
    pollerRef.current?.stop();
    clientRef.current?.disconnect();
  }, []);

  useEffect(() => {
    agentRef.current?.setOverlayOpen(Boolean(cabinet?.state.overlayOpen));
  }, [cabinet?.state.overlayOpen]);

  const selectPlaybook = useCallback((id: string | null) => {
    setActivePlaybook(id);
    // The active playbook is session state, so the gateway is told rather than only the browser.
    clientRef.current?.send("playbook.select", "session", { playbookId: id });
  }, []);

  /** The grade shown before you commit. Nothing is persisted by a preview. */
  const previewGrade = useCallback(async (side: "buy" | "sell") => {
    const current = agentRef.current?.view;
    if (!current) return;
    const version = ++previewVersionRef.current;
    try {
      const response = await fetch(apiUrl("/api/playbooks/grade-preview"), {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          cid: newCid(), sym: current.symbol, side, lots: current.lots,
          playbookId: activePlaybook,
        }),
      });
      if (!response.ok) throw new Error("Preview unavailable");
      const result = (await response.json()) as GradePreview;
      if (version === previewVersionRef.current) setPreview(result);
    } catch {
      setPreview(null);
      note("Preview unavailable. No order was placed. Check the gateway connection.");
    }
  }, [activePlaybook, note]);

  const submitChecklist = useCallback((answers: Record<string, boolean>) => {
    const cid = grade?.cid;
    setGrade(null);
    if (!cid || Object.keys(answers).length === 0) return;
    void fetch(apiUrl("/api/playbooks/checklist"), {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ cid, answers }),
    }).then((response) => { if (!response.ok) throw new Error(); note("Checklist saved."); })
      .catch(() => note("Checklist could not be saved. Check the connection and try again."));
  }, [grade, note]);

  const checkIn = useCallback((phase: "pre" | "post", rating: number | null) => {
    void fetch(apiUrl("/api/journal/checkin"), {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ phase, rating }),
    }).then((response) => { if (!response.ok) throw new Error(); note(rating === null ? `${phase} check-in skipped` : `${phase} check-in saved: ${rating}/5`); })
      .catch(() => note("Check-in could not be saved. Check the connection and try again."));
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
    <main className="demo-desk" style={shell}>
      <header style={row}>
        <strong>DEMO DESK</strong>
        <span>cTrader demo account</span>
        <button type="button" onClick={() => cabinet?.emit("menu")}>
          Menu
        </button>
        <button type="button" onClick={() => cabinet?.dispatch({ type: "warp", screen: "journallive" })}>
          Leave desk &amp; review
        </button>
        <span style={{ marginLeft: "auto" }}>Connection: {status === "idle" ? "not connected" : status === "open" ? "gateway connected" : status}</span>
      </header>

      <section style={panel}>
        <strong>Your next step</strong>
        <p style={{ margin: 0 }} role="status">{status !== "open"
          ? "Connect below. You can learn every control in practice while the gateway is offline."
          : !view?.padConnected ? "Press a button on your controller. Use XInput mode or USB if it is not detected."
          : PHASE_COPY[view.phase]}</p>
        <button onClick={() => cabinet?.dispatch({ type: "warp", screen: "practice" })}>Practise the controls</button>
        <small>Leaving this desk disconnects the controls. It does not close demo positions. Use Close all or manage them in cTrader first.</small>
      </section>

      {status === "idle" || status === "closed" || status === "connecting" ? (
        <section style={panel}>
          <p style={{ margin: 0 }}>Run the gateway with your cTrader demo account configured, then paste its EV_WS_TOKEN here.</p>
          <label htmlFor="ws-token">
            Gateway session token (kept in memory until you leave)
          </label>
          <div style={row}>
            <input
              id="ws-token"
              type="password"
              value={token}
              onChange={(event) => setToken(event.target.value)}
              style={{ flex: 1, background: "var(--black-2)", color: "inherit", padding: 8 }}
            />
            <button type="button" onClick={connect} disabled={!token.trim() || Boolean(view?.pendingIntents)}>
              {status === "idle" ? "Connect demo account" : "Retry with this token"}
            </button>
          </div>
          {status !== "idle" && <p role="status" style={{ margin: 0 }}>Trying to connect. If this continues, check that the gateway is running and the token matches. No account connection has been confirmed.</p>}
          {Boolean(view?.pendingIntents) && <p role="alert">A request is unresolved. Automatic reconnection keeps its original ID. Check cTrader and wait for the result before starting another connection.</p>}
        </section>
      ) : null}

      <section style={panel}>
        <span>Broker: {hud ? hud.broker.connected ? "connected to demo" : "not connected" : "not verified"} · Session window: {hud ? `${hud.session.start} to ${hud.session.end} (${hud.session.timezone}) · ${hud.session.open ? "open" : "closed"}` : "not available"}</span>
        <small>{hud ? `Limits from gateway: ${hud.risk.maxPositions} open positions, ${hud.risk.maxDayLossUsd} USD daily loss cap. 1R = ${hud.risk.rUsd} USD of planned risk.` : "Account limits load from the gateway. No sample limits are shown here."}</small>
        <span>Bid / Ask · {quoteStatus}</span>
        <div style={{ fontSize: 32, fontFamily: "var(--font-data)" }}>
          <span ref={bidRef}>--</span>
          <span style={{ opacity: 0.4 }}> / </span>
          <span ref={askRef}>--</span>
        </div>
        <div style={row}>
          <span>{view?.symbol ?? SYMBOLS[0]}</span>
          <span>{view?.lots ?? 0.01} lots</span>
          <span>{view?.timeframe ?? "M5"}</span>
          <span style={{ marginLeft: "auto" }}>
            open {openPnl === null ? "not available" : showDollars ? `${openPnl.toFixed(2)} USD` : rUsdRef.current ? `${(openPnl / rUsdRef.current).toFixed(2)}R` : "R unit not available"}
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
        <ConfirmGrade preview={preview} tilt={tilt} dayR={dayR} />
        <div style={row}>
          <button type="button" disabled={status !== "open"} onClick={() => void previewGrade("buy")}>
            Check BUY rules (no order)
          </button>
          <button type="button" disabled={status !== "open"} onClick={() => void previewGrade("sell")}>
            Check SELL rules (no order)
          </button>
        </div>
        {tilt ? <TiltPip tilt={tilt} /> : <span>Pace feedback: not measured yet</span>}
        <div style={row}>
          <span>stood down tonight: {view?.stoodDown ?? 0}</span>
          <span>pad: {view?.padConnected ? "connected" : "absent"}</span>
          <span>pending: {view?.pendingIntents ?? 0}</span>
        </div>
      </section>

      <section style={row}>
        {/* Safety exits: reachable with no pad, no focus, and a dead session. */}
        <button type="button" disabled={status !== "open"} onClick={() => { agentRef.current?.flatten(); note("Close all requested. Wait for broker confirmation."); }}>
          Close all demo positions
        </button>
        <button type="button" disabled={status !== "open" || view?.activePositionId == null} onClick={() => { agentRef.current?.closePosition(); note(`Close requested for position ${view?.activePositionId}. Wait for broker confirmation.`); }}>
          {view?.activePositionId == null ? "No active position to close" : `Close position #${view.activePositionId}`}
        </button>
        <span style={{ marginLeft: "auto", opacity: 0.7 }}>tab must stay focused</span>
      </section>

      <section style={panel}>
        <div style={row}>
          <span>How settled do you feel? 1 = unsettled, 5 = calm</span>
          {[1, 2, 3, 4, 5].map((rating) => (
            <button key={rating} type="button" disabled={status !== "open"} onClick={() => checkIn("pre", rating)}>
              {rating}
            </button>
          ))}
          <button type="button" disabled={status !== "open"} onClick={() => checkIn("pre", null)}>
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

const row: React.CSSProperties = { display: "flex", flexWrap: "wrap", gap: 12, alignItems: "center" };
