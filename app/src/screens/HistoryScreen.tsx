import { Artboard, Caps, ScreenFooter, ScreenHeader, Term } from "../components/primitives";
import { Button, Checkbox, GamepadKey, Input, StatTile, TradeRow } from "../ds";

/** History — the prototype's `is_history` artboard. */

const TRADES = [
  { time: "20:57", symbol: "XAUUSD", side: "buy" as const, entry: "2458.10", exit: "2473.00", result: 2.4, selected: true },
  { time: "21:38", symbol: "XAUUSD", side: "buy" as const, entry: "2469.40", exit: "2464.10", result: -1.1 },
  { time: "22:14", symbol: "EURUSD", side: "sell" as const, entry: "1.09210", exit: "1.09080", result: 0.9 },
  { time: "22:51", symbol: "EURUSD", side: "sell" as const, entry: "1.09140", exit: "1.09190", result: -0.6 },
  { time: "20:41", symbol: "XAUUSD", side: "buy" as const, entry: "2451.80", exit: "2459.20", result: 1.8 },
  { time: "21:09", symbol: "GBPUSD", side: "buy" as const, entry: "1.27610", exit: "1.27590", result: -0.2 },
  { time: "22:02", symbol: "XAUUSD", side: "sell" as const, entry: "2466.30", exit: "2460.10", result: 1.5 },
  { time: "20:52", symbol: "XAUUSD", side: "buy" as const, entry: "2444.90", exit: "2441.20", result: -1 },
  { time: "21:47", symbol: "EURUSD", side: "buy" as const, entry: "1.08940", exit: "1.09120", result: 1.2 },
  { time: "22:36", symbol: "XAUUSD", side: "buy" as const, entry: "2457.60", exit: "2457.60", result: 0 },
];

const INSTRUMENTS = [
  { name: "xauusd", on: true },
  { name: "eurusd", on: false },
  { name: "gbpusd", on: false },
];

const ROW_COLUMNS =
  "minmax(0,52px) minmax(0,74px) 40px minmax(0,84px) minmax(34px,1.2fr) minmax(58px,90px) 20px";

export function HistoryScreen() {
  return (
    <Artboard
      label="History"
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
        title="History"
        meta="38 trades in august · 10 shown"
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
          gridTemplateColumns: "280px 1fr",
          gap: 1,
          background: "var(--line-hairline)",
          minHeight: 0,
        }}
      >
        {/* filters */}
        <aside
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
          <Caps size={10} weight={700} color="var(--phos-300)">
            Filters
          </Caps>

          <div style={{ display: "grid", gap: 8 }}>
            <Caps>Period</Caps>
            <Input value="2026-08-01 → 2026-08-29" />
          </div>

          <div style={{ display: "grid", gap: 8 }}>
            <Caps>Instrument</Caps>
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
              {INSTRUMENTS.map((i) => (
                <span
                  key={i.name}
                  style={{
                    padding: "5px 9px",
                    fontSize: 10,
                    fontWeight: 700,
                    letterSpacing: ".12em",
                    textTransform: "uppercase",
                    color: i.on ? "var(--phos-300)" : "var(--text-muted)",
                    border: `1px solid ${i.on ? "var(--line-strong)" : "var(--line-neutral)"}`,
                    background: i.on ? "var(--phos-a08)" : undefined,
                  }}
                >
                  {i.name}
                </span>
              ))}
            </div>
          </div>

          <div style={{ display: "grid", gap: 8 }}>
            <Caps>Playbook</Caps>
            <div style={{ display: "grid", gap: 8 }}>
              <Checkbox checked label="orb" />
              <Checkbox checked label="retest" />
              <Checkbox checked label="unplanned" />
              <Checkbox
                checked={false}
                label="retired playbooks"
                description="kept with full history"
              />
            </div>
          </div>

          <div style={{ display: "grid", gap: 8 }}>
            <Caps>Adherence</Caps>
            <div style={{ display: "flex", gap: 6 }}>
              {["All", "Full", "Broken"].map((a) => {
                const on = a === "All";
                return (
                  <span
                    key={a}
                    style={{
                      flex: 1,
                      textAlign: "center",
                      padding: "6px 0",
                      fontSize: 10,
                      color: on ? "var(--phos-300)" : "var(--text-muted)",
                      border: `1px solid ${on ? "var(--line-strong)" : "var(--line-neutral)"}`,
                      background: on ? "var(--phos-a08)" : undefined,
                    }}
                  >
                    {a}
                  </span>
                );
              })}
            </div>
          </div>

          <div style={{ display: "grid", gap: 8 }}>
            <Caps>Has</Caps>
            <div style={{ display: "grid", gap: 8 }}>
              <Checkbox checked={false} label="voice memo" />
              <Checkbox checked={false} label="replay opened" />
              <Checkbox checked={false} label="protection edited" />
            </div>
          </div>

          {/* drawn as unavailable rather than hidden — the spec does not exist yet */}
          <div
            style={{
              display: "grid",
              gap: 8,
              padding: 12,
              border: "1px dashed var(--grey-700)",
              background: "var(--black-3)",
            }}
          >
            <Caps>Mistake type · unavailable</Caps>
            <Term color="var(--grey-500)">
              execution-learning owns this definition and has no spec yet. the other filters work.
            </Term>
          </div>
        </aside>

        {/* results */}
        <section
          style={{
            background: "var(--black-2)",
            display: "grid",
            gridTemplateRows: "auto 1fr auto",
            minHeight: 0,
          }}
        >
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(4,1fr)",
              gap: 1,
              background: "var(--line-hairline)",
              borderBottom: "1px solid var(--line-hairline)",
            }}
          >
            <StatTile
              label="Trades in filter"
              value="24"
              sub="of 38 in august"
              icon="chart-candlestick"
            />
            <StatTile label="Adherence" value="90%" sub="216 of 240 checkable rules" icon="target" />
            <StatTile label="With a memo" value="15" sub="9 without" icon="bot" />
            <StatTile label="Replayed" value="11" sub="counts once per trade" icon="timer" />
          </div>

          <div
            style={{
              padding: "14px 0",
              display: "grid",
              gap: 0,
              alignContent: "start",
              minHeight: 0,
              overflow: "hidden",
            }}
          >
            <div
              style={{
                display: "grid",
                gridTemplateColumns: ROW_COLUMNS,
                gap: 8,
                padding: "0 12px 8px",
                fontSize: 9,
                letterSpacing: ".18em",
                textTransform: "uppercase",
                color: "var(--text-disabled)",
              }}
            >
              <span>Time</span>
              <span>Symbol</span>
              <span>Side</span>
              <span>Entry → exit</span>
              <span>Tags</span>
              <span style={{ textAlign: "right" }}>Result</span>
              <span />
            </div>
            {TRADES.map((t, i) => (
              <TradeRow key={`${t.time}-${i}`} {...t} />
            ))}
          </div>

          <div
            style={{
              borderTop: "1px solid var(--line-hairline)",
              padding: "12px 16px",
              display: "flex",
              alignItems: "center",
              gap: 14,
              background: "var(--black-1)",
            }}
          >
            <Term>the selected row opens trade detail. from there, replay.</Term>
            <div style={{ marginLeft: "auto", display: "flex", gap: 10 }}>
              <Button variant="ghost" size="sm">
                Load 10 more
              </Button>
              <Button variant="secondary" size="sm">
                Open detail
              </Button>
            </div>
          </div>
        </section>
      </div>

      <ScreenFooter>
        <GamepadKey button="b" size="sm" label="Back" />
        <Caps size={10} color="var(--text-muted)">
          Broker facts are read-only · your words are edits
        </Caps>
      </ScreenFooter>
    </Artboard>
  );
}
