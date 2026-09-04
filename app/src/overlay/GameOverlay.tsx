import type { CSSProperties } from "react";
import { OVERLAY_DESTINATIONS } from "../journey/graph";
import { useCabinetOrThrow } from "../journey/Cabinet";
import type { OverlayGroup } from "../journey/types";
import { Caps, Term } from "../components/primitives";
import { GamepadKey } from "../ds";

/**
 * Safe GameOverlay. Opening it is a room change, not an order: the reducer can only set `screen`.
 * D-pad moves the cursor, A/Start enters, B/Menu closes. Close and panic stay on the live HUD
 * underneath — this surface has no fire control.
 */

const GROUPS: OverlayGroup[] = ["Play", "Review", "Close", "Setup", "Cabinet", "Art", "Gallery"];

const shell: CSSProperties = {
  position: "fixed",
  inset: 0,
  zIndex: 80,
  display: "grid",
  placeItems: "center",
  background: "rgba(4,6,4,.82)",
  fontFamily: "var(--font-core)",
};

const panel: CSSProperties = {
  width: 720,
  maxHeight: "86vh",
  display: "grid",
  gridTemplateRows: "auto 1fr auto",
  background: "var(--black-2)",
  border: "1px solid var(--line-strong)",
  boxShadow: "var(--glow-md)",
};

export function GameOverlay(): JSX.Element | null {
  const { state, emit, dispatch } = useCabinetOrThrow();
  if (!state.overlayOpen) return null;

  return (
    <div
      style={shell}
      role="dialog"
      aria-modal="true"
      aria-label="Safe menu"
      onClick={() => emit("back")}
    >
      <div style={panel} onClick={(event) => event.stopPropagation()}>
        <header
          style={{
            display: "flex",
            alignItems: "center",
            gap: 16,
            padding: "14px 18px",
            borderBottom: "1px solid var(--line-hairline)",
          }}
        >
          <Caps size={11} weight={700} color="var(--phos-300)">
            Safe menu
          </Caps>
          <Term>opens cancel the arm. nothing here can fire.</Term>
        </header>

        <div style={{ overflow: "auto", padding: "10px 0 18px" }}>
          {GROUPS.map((group) => {
            const items = OVERLAY_DESTINATIONS
              .map((item, index) => ({ item, index }))
              .filter(({ item }) => item.group === group);
            if (items.length === 0) return null;
            return (
              <div key={group} style={{ padding: "8px 0" }}>
                <div style={{ padding: "6px 20px" }}>
                  <Caps color="var(--text-disabled)">{group}</Caps>
                </div>
                {items.map(({ item, index }) => {
                  const active = index === state.overlayIndex;
                  return (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => dispatch({ type: "choose", index })}
                      onMouseEnter={() => dispatch({ type: "hover", index })}
                      style={{
                        display: "grid",
                        gridTemplateColumns: "10px 1fr auto",
                        alignItems: "center",
                        gap: 12,
                        width: "100%",
                        textAlign: "left",
                        padding: "8px 20px",
                        border: 0,
                        borderLeft: `2px solid ${active ? "var(--phos-400)" : "transparent"}`,
                        background: active ? "var(--surface-selected)" : "transparent",
                        color: active ? "var(--phos-300)" : "var(--text-secondary)",
                        fontFamily: "var(--font-core)",
                        cursor: "pointer",
                      }}
                    >
                      <span
                        style={{
                          width: 8,
                          height: 8,
                          background: active ? "var(--phos-400)" : "transparent",
                          border: `1px solid ${active ? "var(--phos-400)" : "var(--text-disabled)"}`,
                        }}
                      />
                      <span
                        style={{
                          fontSize: 12,
                          fontWeight: 700,
                          letterSpacing: ".12em",
                          textTransform: "uppercase",
                        }}
                      >
                        {item.label}
                      </span>
                      <span
                        style={{
                          fontFamily: "var(--font-terminal)",
                          fontSize: 15,
                          color: "var(--phos-600)",
                        }}
                      >
                        {item.hint}
                      </span>
                    </button>
                  );
                })}
              </div>
            );
          })}
        </div>

        <footer
          style={{
            display: "flex",
            alignItems: "center",
            gap: 16,
            padding: "12px 18px",
            borderTop: "1px solid var(--line-hairline)",
            background: "var(--black-1)",
          }}
        >
          <GamepadKey button="a" size="sm" label="Enter" />
          <GamepadKey button="b" size="sm" label="Close" />
          <GamepadKey button="up" size="sm" label="Move" />
          <span
            style={{
              marginLeft: "auto",
              fontFamily: "var(--font-terminal)",
              fontSize: 15,
              color: "var(--phos-600)",
            }}
          >
            &gt; demo only · not advice
          </span>
        </footer>
      </div>
    </div>
  );
}
