/**
 * The one safe navigation surface.
 *
 * Everything reachable from `Menu` goes through here, and none of it can place
 * an order -- the reducer in `model.ts` has no order-emitting effect, and
 * `overlay.test.ts` asserts that. An SL/TP edit stages a preview that still
 * needs LT+RT back in the game.
 *
 * Full close and panic stay on screen while this is open. A menu that traps the
 * player with a live position would be worse than no menu at all.
 */

import { useEffect } from "react";
import { Badge, Button } from "../ds";
import {
  DESK_TABS,
  DESTINATIONS,
  DISABLED_TABS,
  reduce,
  type Destination,
  type OverlayState,
} from "./model";

const TITLES: Record<Destination, string> = {
  desk: "Agent desk",
  playbook: "Playbook",
  journal: "Journal",
  system: "System",
  reports: "Reports",
  settings: "Settings",
};

/** What each destination will hold, and which phase fills it. */
const PENDING: Record<Destination, string | null> = {
  desk: "sentinel, news, setups and coach arrive in phase 4",
  playbook: null,
  journal: "the daily cockpit arrives in phase 12",
  system: null,
  reports: "reports and export arrive in phase 13",
  settings: null,
};

export function GameOverlay({
  state,
  onState,
  onClose,
  onFlatten,
  padId,
  conn,
  playbooks = [],
  activePlaybook = null,
  onSelectPlaybook,
}: {
  state: OverlayState;
  onState: (next: OverlayState) => void;
  onClose: () => void;
  onFlatten: () => void;
  padId: string;
  conn: string;
  playbooks?: { playbookId: string; name: string; ruleCount: number; requiredCount: number }[];
  activePlaybook?: string | null;
  onSelectPlaybook?: (playbookId: string) => void;
}) {
  // Keyboard mirrors the pad contract, so the overlay is usable with no pad.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const map: Record<string, Parameters<typeof reduce>[1]> = {
        ArrowDown: { kind: "nav", direction: 1 },
        ArrowUp: { kind: "nav", direction: -1 },
        ArrowRight: { kind: "tab", direction: 1 },
        ArrowLeft: { kind: "tab", direction: -1 },
        Enter: { kind: "enter" },
        Escape: { kind: "close" },
      };
      const action = map[e.key];
      if (!action) return;
      e.preventDefault();
      const result = reduce(state, action);
      onState(result.state);
      if (action.kind === "close") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [state, onState, onClose]);

  if (!state.open) return null;

  return (
    <div className="overlay" role="dialog" aria-modal="true" aria-label="Game overlay">
      <header className="overlay__head">
        <strong>Menu</strong>
        {/* Opening the overlay hard locks new opens. Said out loud, because a
            silent lock reads as a bug. */}
        <Badge tone="warn">new opens locked</Badge>
        <Badge tone={conn === "open" ? "live" : "down"}>{conn}</Badge>
      </header>

      <div className="overlay__body">
        <nav className="overlay__nav" aria-label="Destinations">
          {DESTINATIONS.map((d) => (
            <button
              key={d}
              type="button"
              data-active={d === state.destination}
              onClick={() => onState(reduce(state, { kind: "goto", destination: d }).state)}
            >
              {TITLES[d]}
            </button>
          ))}
        </nav>

        <section className="overlay__panel">
          <h2>{TITLES[state.destination]}</h2>

          {state.destination === "desk" && (
            <div className="overlay__tabs" role="tablist">
              {DESK_TABS.map((tab) => (
                <button
                  key={tab}
                  role="tab"
                  aria-selected={tab === state.tab}
                  aria-disabled={DISABLED_TABS.has(tab)}
                  data-disabled={DISABLED_TABS.has(tab)}
                  disabled={DISABLED_TABS.has(tab)}
                  title={DISABLED_TABS.has(tab) ? "voice unavailable until phase 8" : undefined}
                >
                  {tab}
                  {DISABLED_TABS.has(tab) ? " (phase 8)" : ""}
                </button>
              ))}
            </div>
          )}

          {state.destination === "playbook" && (
            <ul className="overlay__playbooks">
              {playbooks.length === 0 && <li>no playbooks loaded</li>}
              {playbooks.map((b) => (
                <li key={b.playbookId}>
                  <button
                    type="button"
                    data-active={b.playbookId === activePlaybook}
                    onClick={() => onSelectPlaybook?.(b.playbookId)}
                  >
                    <strong>{b.name.replace(" ✓", "")}</strong>
                    <span>
                      {b.requiredCount} required of {b.ruleCount} rules
                    </span>
                  </button>
                </li>
              ))}
              {/* Selecting is session state, never a broker action -- the
                  overlay's reducer has no order-emitting effect at all. */}
              <li className="overlay__note">
                Selecting a playbook grades your fires against it. It cannot place,
                modify, or close anything.
              </li>
            </ul>
          )}

          {state.destination === "system" && (
            <dl className="overlay__system">
              <div>
                <dt>pad</dt>
                <dd>{padId || "none detected"}</dd>
              </div>
              <div>
                <dt>socket</dt>
                <dd>{conn}</dd>
              </div>
            </dl>
          )}

          {state.destination === "settings" && (
            <ul className="overlay__settings">
              <li>
                Microphone — <em>disabled until phase 8</em>
              </li>
              <li>
                {/* Applying an SL/TP edit stages it; the broker still needs LT+RT. */}
                SL/TP edits stage an armed preview and are confirmed with LT+RT in the game.
              </li>
            </ul>
          )}

          {PENDING[state.destination] && (
            <p className="overlay__pending">{PENDING[state.destination]}</p>
          )}

          {state.staged && (
            <div className="overlay__staged" role="status">
              staged modify · position {state.staged.positionId} · SL {state.staged.sl ?? "—"} · TP{" "}
              {state.staged.tp ?? "—"}
              <strong> — confirm with LT+RT in the game</strong>
            </div>
          )}
        </section>
      </div>

      <footer className="overlay__foot">
        {/* Emergency exits stay reachable with the overlay open. */}
        <Button variant="danger" onClick={onFlatten}>
          Flatten (panic)
        </Button>
        <Button variant="ghost" onClick={onClose}>
          Close menu
        </Button>
      </footer>
    </div>
  );
}
