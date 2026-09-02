import type { CSSProperties } from "react";
import { Artboard, Caps, ScreenFooter, ScreenHeader, Term } from "../components/primitives";
import { Badge, GamepadKey, StatTile, TradeRow } from "../ds";

/** Journal · tonight — the prototype's `is_journal` artboard. */

const TRADES = [
  {
    time: "20:57",
    symbol: "XAUUSD",
    side: "buy" as const,
    entry: "2458.10",
    exit: "2473.00",
    result: 2.4,
  },
  {
    time: "21:38",
    symbol: "XAUUSD",
    side: "buy" as const,
    entry: "2469.40",
    exit: "2464.10",
    result: -1.1,
  },
  {
    time: "22:14",
    symbol: "EURUSD",
    side: "sell" as const,
    entry: "1.09210",
    exit: "1.09080",
    result: 0.9,
  },
  {
    time: "22:51",
    symbol: "EURUSD",
    side: "sell" as const,
    entry: "1.09140",
    exit: "1.09190",
    result: -0.6,
  },
];

/**
 * The August heatmap, coloured by process score. A `null` day is a closed
 * market; `"out"` is a night sat out on purpose, drawn dashed because OQ-1 is
 * still open — the dashed cell is a proposal, not a decision.
 */
const HEAT: (readonly [number | null, string])[][] = [
  [
    [3, "phos-800"],
    [4, "phos-600"],
    [5, "out"],
    [6, "phos-700"],
    [7, "phos-500"],
    [null, ""],
    [null, ""],
  ],
  [
    [10, "phos-600"],
    [11, "phos-400-today"],
    [12, "phos-700"],
    [13, "out"],
    [14, "phos-500"],
    [null, ""],
    [null, ""],
  ],
  [
    [17, "phos-800"],
    [18, "phos-600"],
    [19, "phos-500"],
    [20, "phos-600"],
    [21, "out"],
    [null, ""],
    [null, ""],
  ],
  [
    [24, "phos-700"],
    [25, "phos-500"],
    [26, "phos-600"],
    [27, "phos-800"],
    [28, "phos-400-selected"],
    [null, ""],
    [null, ""],
  ],
];

/** Cell fill and number colour per score band — the darker the ramp, the lower the score. */
const CELL_STYLE: Record<string, CSSProperties> = {
  "phos-800": { background: "var(--phos-800)", color: "var(--phos-200)" },
  "phos-700": { background: "var(--phos-700)", color: "var(--phos-100)" },
  "phos-600": { background: "var(--phos-600)", color: "var(--phos-100)" },
  "phos-500": { background: "var(--phos-500)", color: "var(--black-1)" },
  "phos-400-today": {
    background: "var(--phos-400)",
    color: "var(--black-1)",
    boxShadow: "var(--glow-sm)",
  },
  "phos-400-selected": {
    background: "var(--phos-400)",
    color: "var(--black-1)",
    border: "2px solid var(--phos-400)",
    boxShadow: "var(--glow-md)",
  },
  out: {
    background: "var(--black-3)",
    color: "var(--text-disabled)",
    border: "1px dashed var(--grey-700)",
  },
};

const cellBase: CSSProperties = {
  aspectRatio: "1",
  border: "1px solid var(--line-hairline)",
  display: "flex",
  alignItems: "flex-end",
  padding: 4,
  fontFamily: "var(--font-data)",
  fontSize: 10,
};

export function JournalScreen() {
  return (
    <Artboard
      label="Journal"
      frameStyle={{
        width: 1440,
        height: 860,
        display: "grid",
        gridTemplateRows: "44px 1fr 44px",
        background: "var(--surface-app)",
        border: "1px solid var(--line-hairline)",
      }}
    >
      <ScreenHeader
        title="Journal · tonight"
        meta="2026-08-29 · session 042 closed 23:04"
        right={
          <div style={{ display: "flex", gap: 0 }}>
            <span
              style={{
                height: 26,
                padding: "0 14px",
                display: "inline-flex",
                alignItems: "center",
                fontSize: 10,
                fontWeight: 700,
                letterSpacing: ".18em",
                textTransform: "uppercase",
                color: "var(--phos-300)",
                border: "1px solid var(--line-strong)",
                background: "var(--phos-a08)",
              }}
            >
              Process
            </span>
            <span
              style={{
                height: 26,
                padding: "0 14px",
                display: "inline-flex",
                alignItems: "center",
                fontSize: 10,
                fontWeight: 700,
                letterSpacing: ".18em",
                textTransform: "uppercase",
                color: "var(--text-muted)",
                border: "1px solid var(--line-neutral)",
                borderLeft: 0,
              }}
            >
              Money · one click away
            </span>
          </div>
        }
      />

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 620px",
          gap: 1,
          background: "var(--line-hairline)",
          minHeight: 0,
        }}
      >
        {/* tonight */}
        <div
          style={{
            background: "var(--black-2)",
            padding: "18px 20px",
            display: "grid",
            gap: 16,
            alignContent: "start",
            minHeight: 0,
            overflow: "hidden",
          }}
        >
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(4,1fr)",
              gap: 1,
              background: "var(--line-hairline)",
            }}
          >
            <StatTile
              label="Process score"
              value="86"
              sub="4 of 5 axes · read from the deck"
              icon="shield"
            />
            <StatTile label="Readiness" value="4 / 5" sub="one item left blank" icon="check" />
            <StatTile label="Check-in" value="4 → 3" sub="start · end" icon="pencil" />
            <StatTile label="Stood down" value="07" sub="12 arms · 4 trades" icon="timer" />
          </div>

          <div style={{ display: "grid", gap: 10 }}>
            <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
              <Caps>Plan · frozen at your first fill 20:57</Caps>
              <Badge tone="neutral">Immutable</Badge>
            </div>
            <div
              style={{
                padding: 12,
                background: "var(--surface-well)",
                boxShadow: "var(--inset-well)",
                fontSize: 14,
                lineHeight: 1.5,
                color: "var(--text-body)",
              }}
            >
              Gold has held 2455 twice today. I want one buy from a retest with the London low
              intact, and nothing else.
            </div>
            <div
              style={{
                padding: 12,
                borderLeft: "2px solid var(--arcade-cyan)",
                background: "var(--black-3)",
                display: "grid",
                gap: 4,
              }}
            >
              <Caps color="var(--arcade-cyan)">Added later · 22:40</Caps>
              <span style={{ fontSize: 14, lineHeight: 1.5, color: "var(--text-body)" }}>
                Second entry was not in the plan. I took it because the first one was working.
              </span>
            </div>
          </div>

          <div style={{ display: "grid", gap: 8 }}>
            <Caps>Tonight&apos;s trades · 4</Caps>
            {TRADES.map((t) => (
              <TradeRow key={t.time} {...t} status="closed" />
            ))}
            <Term color="var(--grey-500)">
              two of four have no memo. that is the axis holding tonight down.
            </Term>
          </div>
        </div>

        {/* the month, coloured by process */}
        <div
          style={{
            background: "var(--black-2)",
            padding: "18px 20px",
            display: "grid",
            gap: 18,
            alignContent: "start",
            minHeight: 0,
            overflow: "hidden",
          }}
        >
          <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between" }}>
            <Caps size={10} weight={700} color="var(--phos-300)">
              August · coloured by process
            </Caps>
            <Caps color="var(--text-muted)">One cell = one evening</Caps>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(7,1fr)", gap: 6 }}>
            {/* the caps style goes on the grid item itself — a wrapper span
                would inherit the body line-height and grow the header row */}
            {["M", "T", "W", "T", "F", "S", "S"].map((d, i) => (
              <Caps key={i} style={{ textAlign: "center" }}>
                {d}
              </Caps>
            ))}
            {HEAT.flat().map(([day, kind], i) => {
              if (day == null) {
                return (
                  <span
                    key={i}
                    style={{
                      aspectRatio: "1",
                      background: "var(--black-2)",
                      border: "1px solid var(--line-neutral)",
                    }}
                  />
                );
              }
              return (
                <span key={i} style={{ ...cellBase, ...CELL_STYLE[kind] }}>
                  {day}
                </span>
              );
            })}
          </div>

          <div
            style={{
              display: "grid",
              gap: 10,
              padding: 14,
              background: "var(--black-3)",
              border: "1px solid var(--line-hairline)",
            }}
          >
            <Caps>Legend</Caps>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ width: 14, height: 14, background: "var(--phos-800)" }} />
              <span style={{ width: 14, height: 14, background: "var(--phos-600)" }} />
              <span style={{ width: 14, height: 14, background: "var(--phos-400)" }} />
              <span style={{ fontSize: 11, color: "var(--text-secondary)" }}>
                process score, low to high
              </span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span
                style={{
                  width: 14,
                  height: 14,
                  background: "var(--black-3)",
                  border: "1px dashed var(--grey-700)",
                }}
              />
              <span style={{ fontSize: 11, color: "var(--text-secondary)" }}>
                sat out on purpose — valid data, not a bad night
              </span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span
                style={{
                  width: 14,
                  height: 14,
                  background: "var(--black-2)",
                  border: "1px solid var(--line-neutral)",
                }}
              />
              <span style={{ fontSize: 11, color: "var(--text-secondary)" }}>market closed</span>
            </div>
            <Term color="var(--grey-500)">
              OQ-1 is still open: the dashed cell is a proposal, not a decision.
            </Term>
          </div>

          <div style={{ display: "grid", gap: 8 }}>
            <Caps>Day 28 · selected</Caps>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr 1fr",
                gap: 12,
                fontFamily: "var(--font-data)",
                fontSize: 11,
                color: "var(--text-secondary)",
              }}
            >
              <span>1 session · 4 trades</span>
              <span>process 86</span>
              <span>readiness 4 of 5</span>
            </div>
            <Term>open the day to read the plan, the memos and every fill.</Term>
          </div>
        </div>
      </div>

      <ScreenFooter>
        <GamepadKey button="START" size="sm" label="Back to session" />
        <Caps size={10} color="var(--text-muted)">
          Read with mouse and keyboard
        </Caps>
      </ScreenFooter>
    </Artboard>
  );
}
