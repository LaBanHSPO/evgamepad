import { Artboard, Caps, ScreenFooter, ScreenHeader, Term } from "../components/primitives";
import { Badge, Button, GamepadKey } from "../ds";

/** Replay — the prototype's `is_replay` artboard. A frozen tape, never a simulation. */

const LEVELS = [
  {
    top: "22%",
    border: "1px dashed rgba(0,255,65,.42)",
    glow: undefined as string | undefined,
    label: "MFE +2.60R · 21:31",
    color: "var(--phos-400)",
    side: "right" as const,
  },
  {
    top: "33%",
    border: "1px solid var(--phos-300)",
    glow: undefined,
    label: "EXIT 2473.00 · 21:34",
    color: "var(--phos-200)",
    side: "left" as const,
  },
  {
    top: "44%",
    border: "1px solid var(--phos-400)",
    glow: "var(--glow-xs)",
    label: "ENTRY 2458.10 · 20:57",
    color: "var(--phos-300)",
    side: "right" as const,
  },
  {
    top: "62%",
    border: "1px dashed var(--arcade-red-dim)",
    glow: undefined,
    label: "MAE -0.40R · 21:03",
    color: "var(--arcade-red)",
    side: "right" as const,
  },
];

/** The event strip is the point of this screen — the left stick scrubs it. */
const EVENTS = [
  { at: "6%", label: "arm", color: "var(--arcade-cyan)" },
  { at: "11%", label: "stood down", color: "var(--phos-400)" },
  { at: "19%", label: "memo", color: "var(--status-agent)" },
  { at: "24%", label: "fire", color: "var(--phos-200)" },
  { at: "27%", label: "ack", color: "var(--grey-300)" },
  { at: "46%", label: "sl move", color: "var(--arcade-yellow)" },
  { at: "63%", label: "sl move", color: "var(--arcade-yellow)" },
  { at: "72%", label: "tilt band", color: "var(--arcade-orange)" },
  { at: "82%", label: "exit", color: "var(--phos-200)" },
];

const SPEEDS = ["0.5×", "1×", "2×", "4×"];

export function ReplayScreen() {
  return (
    <Artboard
      label="Replay"
      frameStyle={{
        width: 1440,
        height: 860,
        display: "grid",
        gridTemplateRows: "44px 34px 1fr auto 44px",
        background: "var(--surface-app)",
        border: "1px solid var(--line-hairline)",
      }}
    >
      <ScreenHeader
        title="Replay · cid 8836"
        meta="XAUUSD long 0.20 · window 20:52 → 21:40"
        right={
          <Button variant="danger" size="sm">
            Flatten all
          </Button>
        }
      >
        <Badge tone="up">+2.40R</Badge>
      </ScreenHeader>

      {/* what is locked while a position is open, said plainly */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 12,
          padding: "0 16px",
          background: "rgba(255,212,0,.08)",
          borderBottom: "1px solid rgba(255,212,0,.4)",
        }}
      >
        <Caps size={11} weight={700} color="var(--arcade-yellow)">
          1 position still open
        </Caps>
        <Term>
          new opens and protection edits are locked while you review. closing the selected position
          and emergency exit are not.
        </Term>
      </div>

      <div
        style={{
          position: "relative",
          background: "var(--black-1)",
          backgroundImage: "var(--veil-grid)",
          minHeight: 0,
          overflow: "hidden",
        }}
      >
        {LEVELS.map((line) => (
          <div
            key={line.label}
            style={{
              position: "absolute",
              left: 0,
              right: 0,
              top: line.top,
              borderTop: line.border,
              boxShadow: line.glow,
            }}
          >
            <span
              style={{
                position: "absolute",
                [line.side]: 10,
                top: -17,
                fontFamily: "var(--font-data)",
                fontSize: 11,
                color: line.color,
              }}
            >
              {line.label}
            </span>
          </div>
        ))}

        {/* playhead */}
        <div
          style={{
            position: "absolute",
            left: "46%",
            top: 0,
            bottom: 0,
            borderLeft: "2px solid var(--phos-400)",
            boxShadow: "var(--glow-sm)",
          }}
        >
          <span
            style={{
              position: "absolute",
              left: 6,
              top: 8,
              fontFamily: "var(--font-data)",
              fontSize: 11,
              color: "var(--phos-200)",
              background: "rgba(4,6,4,.8)",
              padding: "2px 5px",
            }}
          >
            21:12:04
          </span>
        </div>

        <div
          style={{
            position: "absolute",
            left: "calc(46% + 14px)",
            top: 44,
            width: 330,
            padding: 12,
            background: "rgba(4,6,4,.92)",
            border: "1px solid var(--line-strong)",
            boxShadow: "var(--sprite-shadow)",
            display: "grid",
            gap: 6,
          }}
        >
          <Caps color="var(--phos-300)">Event at the playhead</Caps>
          <Term color="var(--text-terminal)">
            stop moved 2455.60 → 2458.10 — risk off the table, 15 minutes after entry.
          </Term>
        </div>

        <Caps size={10} style={{ position: "absolute", left: 16, bottom: 12 }}>
          Context placeholder — frozen tape, not a simulation
        </Caps>

        <div
          style={{
            position: "absolute",
            right: 16,
            bottom: 12,
            padding: "8px 12px",
            background: "rgba(4,6,4,.9)",
            border: "1px solid var(--line-hairline)",
            display: "flex",
            alignItems: "center",
            gap: 10,
          }}
        >
          <Caps size={10} color="var(--text-muted)">
            Post-roll
          </Caps>
          <span style={{ fontFamily: "var(--font-data)", fontSize: 11, color: "var(--phos-300)" }}>
            complete · 5:00
          </span>
        </div>
      </div>

      {/* scrubber */}
      <div
        style={{
          padding: "14px 16px",
          display: "grid",
          gap: 12,
          background: "var(--black-2)",
          borderTop: "1px solid var(--line-hairline)",
        }}
      >
        <div
          style={{
            position: "relative",
            height: 56,
            border: "1px solid var(--line-hairline)",
            background: "var(--surface-well)",
          }}
        >
          <span
            style={{
              position: "absolute",
              left: 0,
              top: 0,
              bottom: 0,
              width: "46%",
              background: "var(--phos-a08)",
            }}
          />
          <span
            style={{
              position: "absolute",
              left: "46%",
              top: 0,
              bottom: 0,
              borderLeft: "2px solid var(--phos-400)",
              boxShadow: "var(--glow-sm)",
            }}
          />
          {EVENTS.map((e, i) => (
            <span key={i}>
              <span
                style={{
                  position: "absolute",
                  left: e.at,
                  top: 8,
                  width: 2,
                  height: 40,
                  background: e.color,
                }}
              />
              <span
                style={{
                  position: "absolute",
                  left: e.at,
                  top: -1,
                  transform: "translateX(-50%)",
                  fontFamily: "var(--font-data)",
                  fontSize: 9,
                  color: e.color,
                }}
              >
                {e.label}
              </span>
            </span>
          ))}
        </div>

        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            fontFamily: "var(--font-data)",
            fontSize: 10,
            color: "var(--text-muted)",
          }}
        >
          {["20:52", "21:00", "21:12", "21:24", "21:40"].map((t) => (
            <span key={t}>{t}</span>
          ))}
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              padding: "6px 10px",
              border: "1px solid var(--line-hairline)",
            }}
          >
            <GamepadKey button="left" size="sm" />
            <GamepadKey button="right" size="sm" />
            <Caps size={10} weight={700} color="var(--text-secondary)">
              Left stick scrubs
            </Caps>
          </div>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              padding: "6px 10px",
              border: "1px solid var(--line-hairline)",
            }}
          >
            <GamepadKey button="up" size="sm" />
            <GamepadKey button="down" size="sm" />
            <Caps size={10} weight={700} color="var(--text-secondary)">
              Right stick zooms
            </Caps>
          </div>
          <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
            <Caps size={10} color="var(--text-muted)">
              Speed
            </Caps>
            {SPEEDS.map((s) => {
              const on = s === "1×";
              return (
                <span
                  key={s}
                  style={{
                    padding: "4px 8px",
                    fontFamily: "var(--font-data)",
                    fontSize: 11,
                    color: on ? "var(--phos-300)" : "var(--text-muted)",
                    border: `1px solid ${on ? "var(--line-strong)" : "var(--line-neutral)"}`,
                    background: on ? "var(--phos-a08)" : undefined,
                  }}
                >
                  {s}
                </span>
              );
            })}
            <Term size={16} color="var(--grey-500)" style={{ marginLeft: 6 }}>
              audio mutes from 2× up
            </Term>
          </div>
        </div>
      </div>

      <ScreenFooter notice="nothing here can send an order · demo only · not advice">
        <GamepadKey button="a" size="sm" label="Play · pause" />
        <GamepadKey button="x" size="sm" label="Speed" />
        <GamepadKey button="y" size="sm" label="Record review memo" />
        <GamepadKey button="b" size="sm" label="Back where you came from" />
      </ScreenFooter>
    </Artboard>
  );
}
