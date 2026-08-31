import type { Playbook } from "./types";

/**
 * Choosing the setup you are about to trade.
 *
 * The active playbook is part of session state, so selecting one sends `playbook.select` on the
 * socket rather than being remembered only in the browser. Retired playbooks never appear here —
 * the API filters them — but their old grades still resolve on the deck.
 *
 * Phase 3 reserved pad-driven navigation for the GameOverlay; that surface does not exist yet, so
 * this is click-driven for now and the overlay will host it when it lands.
 */
export function PlaybookPicker({ playbooks, activeId, onSelect }: {
  playbooks: Playbook[];
  activeId: string | null;
  onSelect: (id: string | null) => void;
}): JSX.Element {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        <button
          type="button"
          onClick={() => onSelect(null)}
          style={activeId === null ? active : inactive}
        >
          Unplanned
        </button>
        {playbooks.map((playbook) => (
          <button
            key={playbook.id}
            type="button"
            onClick={() => onSelect(playbook.id)}
            style={activeId === playbook.id ? active : inactive}
          >
            {playbook.name}
          </button>
        ))}
      </div>
      {activeId === null ? (
        <p style={hint}>
          No playbook selected — fires grade as <strong>unplanned</strong>. That is a valid
          state, and it reads honestly on the deck.
        </p>
      ) : (
        /* Player prose, rendered as a text child so React escapes it. */
        <p style={hint}>{playbooks.find((p) => p.id === activeId)?.narrative}</p>
      )}
    </div>
  );
}

const inactive: React.CSSProperties = {
  background: "transparent",
  color: "inherit",
  border: "var(--border-hairline)",
  padding: "4px 10px",
  cursor: "pointer",
};

const active: React.CSSProperties = {
  ...inactive,
  background: "var(--black-3)",
  color: "var(--phos-200)",
};

const hint: React.CSSProperties = { margin: 0, fontSize: 12, opacity: 0.75 };
