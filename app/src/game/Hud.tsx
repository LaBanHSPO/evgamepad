/**
 * The evening HUD.
 *
 * Dark, few colours, one symbol, one lot, one position strip. Not a DOM-dense
 * Bloomberg clone -- what is on screen is what a person can act on with a
 * gamepad in their hands.
 *
 * The Process Score is deliberately absent: it lives on the deck (phase 11), so
 * there is no live score to watch mid-session.
 */

import { useMemo } from "react";
import { Badge, Button, GamepadKey, MeterBar, Tag } from "../ds";
import { CLUTCH_ON } from "../pad/map";
import { Chart } from "./Chart";
import { ConfirmOverlay } from "./ConfirmOverlay";
import { PriceTape } from "./PriceTape";
import { adherenceCues, formatOpenPnl } from "./process";
import type { GameApi } from "./useGame";

export function Hud({ game, onOpenOverlay }: { game: GameApi; onOpenOverlay: () => void }) {
  const { view, quotes } = game;
  const cues = useMemo(() => adherenceCues(game.marketContext()), [game, view.sym, view.lots, view.sessionOpen]);
  const quote = quotes.current.get(view.sym);

  return (
    <div className="hud">
      <header className="hud__bar">
        <div className="hud__conn">
          <Badge tone={view.conn === "open" ? "live" : "down"}>
            {view.conn === "open" ? "linked" : view.conn}
          </Badge>
          <Badge tone={view.padConnected ? "live" : "warn"}>
            {view.padConnected ? "pad" : "no pad"}
          </Badge>
          <Badge tone={view.sessionOpen ? "up" : "neutral"}>
            {view.sessionOpen ? "session open" : "out of session"}
          </Badge>
        </div>
        {/* Entertainment copy, not a disclaimer buried in a footer. */}
        <div className="hud__legal">cTrader demo · not advice · process over outcome</div>
      </header>

      <main className="hud__main">
        <PriceTape quotes={quotes} sym={view.sym} />

        <Chart candles={game.candles} sym={view.sym} tf={view.timeframe} />

        <section className="hud__state">
          <div className="hud__fsm" data-state={view.fsm}>
            {view.fsm}
            {view.armed ? ` · ${view.armed.toUpperCase()}` : ""}
          </div>
          <MeterBar
            value={Math.min(view.clutch / CLUTCH_ON, 1) * 100}
            tone={view.clutch >= CLUTCH_ON ? "phos" : "info"}
            label="clutch"
          />
          <div className="hud__size">
            <span>{view.lots.toFixed(2)} lot</span>
            <span>{view.timeframe}</span>
          </div>
        </section>

        <section className="hud__process">
          {/* Advisory only. None of these can block a fire -- the gateway's
              risk rules are the only thing that does. */}
          {cues.map((cue) => (
            <Tag key={cue.id} color={cue.ok ? "var(--pnl-up)" : "var(--warn)"}>
              {cue.ok ? "✓" : "!"} {cue.label}
            </Tag>
          ))}
          {/* Standing down reads as a win, because it is one. */}
          <Tag color={view.playbookId ? "var(--pnl-up)" : "var(--warn)"}>
            {view.playbookId
              ? view.playbooks.find((b) => b.playbookId === view.playbookId)?.name.replace(" ✓", "")
              : "no playbook"}
          </Tag>
          <Tag color="var(--text-muted)">stood down {view.standDowns}×</Tag>
          {view.pttActive && <Tag color="var(--warn)">● memo</Tag>}
        </section>

        <section className="hud__pnl">
          <button
            type="button"
            className="hud__pnl-toggle"
            onClick={() => game.setPnlUnit(view.pnlUnit === "R" ? "USD" : "R")}
            title="R keeps attention on the process. Dollars are one deliberate click away."
          >
            {formatOpenPnl(view.positions, view.pnlUnit)}
            <small>{view.pnlUnit === "R" ? "in R" : "in $"}</small>
          </button>
        </section>

        <section className="hud__positions">
          {view.positions.length === 0 ? (
            <p className="hud__flat">flat</p>
          ) : (
            view.positions.map((p) => (
              <div key={p.positionId} className="hud__position">
                <span>
                  {p.side.toUpperCase()} {p.lots.toFixed(2)} {p.sym} @ {p.entry}
                </span>
                <Button size="sm" variant="ghost" onClick={() => game.closePosition(p.positionId)}>
                  close
                </Button>
              </div>
            ))
          )}
        </section>

        {/* Phase 4 fills these. Empty shells now so the layout is honest. */}
        <section className="hud__sentinel" data-stub>
          sentinel · phase 4
        </section>
      </main>

      {view.armed && (
        <ConfirmOverlay
          side={view.armed}
          sym={view.sym}
          lots={view.lots}
          quote={quote}
          relativeSl={null}
          relativeTp={null}
          rUsd={null}
          grade={view.grade}
        />
      )}

      {view.unknownFires.length > 0 && (
        <div className="hud__unknown" role="alert">
          {/* Unknown, not failed: the order may well have reached the broker,
              so new fires stay blocked until this resolves. */}
          <strong>{view.unknownFires.length} fire(s) unresolved</strong>
          <p>New opens are blocked. Check cTrader before clearing.</p>
          {view.unknownFires.map((f) => (
            <Button key={f.cid} size="sm" variant="ghost" onClick={() => game.clearUnknown(f.cid)}>
              clear {f.kind} {f.cid.slice(-6)}
            </Button>
          ))}
        </div>
      )}

      {view.lastReject && <div className="hud__reject">refused: {view.lastReject}</div>}

      <footer className="hud__footer">
        {/* Works with no pad and bypasses the dead-man. A safety exit must not
            depend on hardware the player may have just unplugged. */}
        <Button variant="danger" onClick={game.flatten}>
          Flatten (panic)
        </Button>
        <Button variant="ghost" onClick={onOpenOverlay}>
          <GamepadKey button="menu" label="Open menu" />
        </Button>
      </footer>
    </div>
  );
}
