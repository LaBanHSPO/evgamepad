import type { CSSProperties, ReactNode } from "react";
import { Artboard, Caps, Term } from "../components/primitives";
import { Badge, Button, GamepadKey, MeterBar, PnLValue, Switch } from "../ds";

/**
 * Live session HUD — port of HudA.dc.html, driven by the same six states the
 * prototype's enum prop exposed.
 */

export type HudState = "live" | "armed" | "pending" | "stale" | "closeonly" | "locked";

export const HUD_STATES: { id: HudState; label: string }[] = [
  { id: "live", label: "Safe" },
  { id: "armed", label: "Armed" },
  { id: "pending", label: "Result unknown" },
  { id: "stale", label: "Stale price" },
  { id: "closeonly", label: "Close only" },
  { id: "locked", label: "Locked" },
];

const INSTRUMENTS = [
  { symbol: "XAUUSD", price: "2461.38", active: true },
  { symbol: "EURUSD", price: "1.09142", active: false },
  { symbol: "GBPUSD", price: "1.27680", active: false },
  { symbol: "USDJPY", price: "147.215", active: false },
];

const LIMITS = [
  { label: "Max loss", value: "-3.00R" },
  { label: "Max positions", value: "2 / 2" },
  { label: "News guard", value: "15 min" },
];

/** A banner across the top of the body — one per blocking condition. */
function Banner({
  tone,
  title,
  children,
  aside,
}: {
  tone: "warn" | "danger";
  title: string;
  children: ReactNode;
  aside?: ReactNode;
}) {
  const warn = tone === "warn";
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 12,
        height: 34,
        padding: "0 16px",
        background: warn ? "rgba(255,212,0,.10)" : "rgba(232,32,42,.10)",
        borderBottom: `1px solid ${warn ? "rgba(255,212,0,.4)" : "var(--arcade-red-dim)"}`,
      }}
    >
      <Caps size={11} weight={700} color={warn ? "var(--arcade-yellow)" : "var(--arcade-red)"}>
        {title}
      </Caps>
      <Term>{children}</Term>
      {aside}
    </div>
  );
}

const limitRow: CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  fontFamily: "var(--font-data)",
  fontSize: 11,
  color: "var(--text-secondary)",
};

export function SessionHudScreen({ state = "live" }: { state?: HudState }) {
  const pending = state === "pending";
  const stale = state === "stale";
  const closeOnly = state === "closeonly";
  const locked = state === "locked";
  const armed = state === "armed";

  const statusLive = !locked && !pending && !stale && !closeOnly;
  const statusBlocked = pending || stale || closeOnly;
  const armReady = !armed && !locked && !pending && !stale && !closeOnly;
  const armBlocked = stale || closeOnly || locked;
  const lossUsed = closeOnly || locked ? 30 : 11;
  const lossTone = closeOnly || locked ? "danger" : "warn";
  const priceColor = stale ? "var(--grey-500)" : "var(--phos-100)";
  const openR = locked ? 0 : 0.8;
  const sessionR = closeOnly || locked ? -3 : 1.6;

  const hasBanner = pending || stale || closeOnly;

  return (
    <Artboard
      label="Live session HUD"
      frameStyle={{
        width: 1440,
        height: 860,
        display: "grid",
        // The prototype's `auto` banner row collapses to nothing when no
        // banner is rendered, so the same template covers all six states.
        gridTemplateRows: "44px auto 1fr 44px",
        background: "var(--surface-app)",
        border: "1px solid var(--line-hairline)",
        position: "relative",
      }}
    >
      <header
        style={{
          display: "flex",
          alignItems: "center",
          gap: 16,
          padding: "0 16px",
          borderBottom: "1px solid var(--line-hairline)",
          background: "var(--black-2)",
        }}
      >
        <span
          style={{
            fontFamily: "var(--font-display)",
            fontSize: 11,
            color: "var(--phos-400)",
            textShadow: "var(--glow-text)",
          }}
        >
          EV<span style={{ color: "var(--arcade-red)" }}>GAMEPAD</span>
        </span>
        <Caps size={11} weight={700} color="var(--text-body)">
          Session 042
        </Caps>
        <span
          style={{
            fontFamily: "var(--font-data)",
            fontSize: 10,
            letterSpacing: ".12em",
            color: "var(--text-muted)",
          }}
        >
          2026-08-29 · demo
        </span>
        {statusLive ? (
          <Badge tone="live" dot>
            Live
          </Badge>
        ) : null}
        {locked ? (
          <Badge tone="down" dot>
            Locked
          </Badge>
        ) : null}
        {statusBlocked ? (
          <Badge tone="warn" dot>
            Opens blocked
          </Badge>
        ) : null}
        <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 14 }}>
          <Caps size={10} color="var(--text-muted)">
            Window 20:00–23:00
          </Caps>
          <span style={{ fontFamily: "var(--font-data)", fontSize: 11, color: "var(--phos-300)" }}>
            1:12 LEFT
          </span>
          {locked ? (
            <Caps size={10} color="var(--arcade-red)">
              Pad lost
            </Caps>
          ) : (
            <Caps size={10} color="var(--text-muted)">
              Pad ok · 12ms
            </Caps>
          )}
          <Button variant="danger" size="sm">
            Flatten all
          </Button>
        </div>
      </header>

      {/* banners */}
      {hasBanner ? (
        <div>
          {pending ? (
            <Banner
              tone="warn"
              title="Order sent · result unknown"
              aside={
                <Caps size={10} color="var(--text-muted)" style={{ marginLeft: "auto" }}>
                  Override available after warning
                </Caps>
              }
            >
              cid 8841 unresolved for 3.4s — new opens are locked until the broker answers.
            </Banner>
          ) : null}
          {stale ? (
            <Banner tone="danger" title="Price feed stale">
              last tick 4.2s ago — opens blocked until price is live again. no price is invented.
            </Banner>
          ) : null}
          {closeOnly ? (
            <Banner tone="danger" title="Session loss limit reached">
              -3.00R of -3.00R used. close only. unlocking will not give the limit back.
            </Banner>
          ) : null}
        </div>
      ) : (
        <div />
      )}

      <div style={{ display: "grid", gridTemplateColumns: "236px 1fr 312px", minHeight: 0 }}>
        {/* ── left rail: instrument, size, limits ─────────────── */}
        <aside
          style={{
            borderRight: "1px solid var(--line-hairline)",
            background: "var(--black-2)",
            display: "grid",
            gridTemplateRows: "auto auto auto 1fr",
            minHeight: 0,
          }}
        >
          <div style={{ padding: "10px 0 12px" }}>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                padding: "0 12px 8px",
              }}
            >
              <Caps>Instrument</Caps>
              <GamepadKey button="left" size="sm" />
              <GamepadKey button="right" size="sm" />
            </div>
            {INSTRUMENTS.map((row) => (
              <div
                key={row.symbol}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  height: 30,
                  padding: "0 12px",
                  borderLeft: `2px solid ${row.active ? "var(--phos-400)" : "transparent"}`,
                  background: row.active ? "var(--surface-selected)" : undefined,
                  color: row.active ? "var(--phos-300)" : "var(--text-secondary)",
                  fontSize: 11,
                  fontWeight: 700,
                  letterSpacing: ".12em",
                }}
              >
                {row.symbol}
                <span
                  style={{
                    fontFamily: "var(--font-data)",
                    color: row.active ? "var(--text-secondary)" : "var(--text-muted)",
                  }}
                >
                  {row.price}
                </span>
              </div>
            ))}
          </div>

          <div
            style={{
              borderTop: "1px solid var(--line-hairline)",
              padding: 12,
              display: "grid",
              gap: 10,
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
              <Caps>Size</Caps>
              <Caps>Max 0.50</Caps>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <GamepadKey button="LB" size="sm" />
              <span
                style={{
                  flex: 1,
                  textAlign: "center",
                  fontFamily: "var(--font-data)",
                  fontSize: 20,
                  fontWeight: 700,
                  color: "var(--phos-300)",
                  fontVariantNumeric: "tabular-nums",
                  boxShadow: "var(--inset-well)",
                  background: "var(--surface-well)",
                  padding: "4px 0",
                }}
              >
                0.20
              </span>
              <GamepadKey button="RB" size="sm" />
            </div>
            <div style={{ display: "flex", gap: 4 }}>
              {["M1", "M5", "M15", "H1"].map((tf) => {
                const on = tf === "M5";
                return (
                  <span
                    key={tf}
                    style={{
                      flex: 1,
                      textAlign: "center",
                      padding: "4px 0",
                      fontSize: 10,
                      letterSpacing: ".12em",
                      color: on ? "var(--phos-300)" : "var(--text-muted)",
                      border: `1px solid ${on ? "var(--line-strong)" : "var(--line-neutral)"}`,
                      background: on ? "var(--phos-a08)" : undefined,
                    }}
                  >
                    {tf}
                  </span>
                );
              })}
            </div>
          </div>

          <div
            style={{
              borderTop: "1px solid var(--line-hairline)",
              padding: 12,
              display: "grid",
              gap: 12,
            }}
          >
            <Caps>Session limits · self-declared</Caps>
            <MeterBar label="Loss used" value={lossUsed} max={30} segments={10} tone={lossTone} />
            {LIMITS.map((row) => (
              <div key={row.label} style={limitRow}>
                <Caps size={10} color="var(--text-muted)">
                  {row.label}
                </Caps>
                {row.value}
              </div>
            ))}
          </div>

          <div
            style={{
              borderTop: "1px solid var(--line-hairline)",
              padding: 12,
              alignContent: "end",
              display: "grid",
              gap: 8,
            }}
          >
            <Caps>Money view</Caps>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                fontFamily: "var(--font-data)",
                fontSize: 11,
                color: "var(--text-muted)",
              }}
            >
              <Switch checked={false} />
              <span>off — R only</span>
            </div>
          </div>
        </aside>

        {/* ── centre: price, chart, tape, overlays ────────────── */}
        <section
          style={{
            display: "grid",
            gridTemplateRows: "auto 1fr 104px",
            minWidth: 0,
            position: "relative",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "flex-end",
              gap: 16,
              padding: "12px 16px 10px",
              borderBottom: "1px solid var(--line-hairline)",
            }}
          >
            <span
              style={{
                fontFamily: "var(--font-data)",
                fontSize: 46,
                fontWeight: 700,
                lineHeight: 1,
                color: priceColor,
                fontVariantNumeric: "tabular-nums",
                letterSpacing: "-.01em",
              }}
            >
              2461.38
            </span>
            <div style={{ display: "grid", gap: 4, paddingBottom: 4 }}>
              <Caps size={10} color="var(--text-muted)">
                XAUUSD · M5
              </Caps>
              <span
                style={{
                  fontFamily: "var(--font-data)",
                  fontSize: 11,
                  color: "var(--text-secondary)",
                }}
              >
                spread 0.24 · 18412.25 → 2461.38
              </span>
            </div>
            {stale ? (
              <Badge tone="down" dot>
                Stale 4.2s
              </Badge>
            ) : null}
            <div
              style={{ marginLeft: "auto", display: "flex", alignItems: "baseline", gap: 10 }}
            >
              <Caps size={10} color="var(--text-muted)">
                Open risk
              </Caps>
              <PnLValue value={openR} size="lg" />
            </div>
          </div>

          <div
            style={{
              position: "relative",
              background: "var(--black-1)",
              backgroundImage: "var(--veil-grid)",
              borderBottom: "1px solid var(--line-hairline)",
              overflow: "hidden",
            }}
          >
            {[
              {
                top: "26%",
                border: "1px dashed rgba(0,255,65,.42)",
                glow: undefined,
                label: "TP 2473.00 · +2.00R",
                color: "var(--phos-400)",
              },
              {
                top: "52%",
                border: "1px solid var(--phos-400)",
                glow: "var(--glow-xs)",
                label: "ENTRY 2458.10",
                color: "var(--phos-300)",
              },
              {
                top: "76%",
                border: "1px dashed var(--arcade-red-dim)",
                glow: undefined,
                label: "SL 2455.60 · -1.00R",
                color: "var(--arcade-red)",
              },
            ].map((line) => (
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
                    right: 8,
                    top: -16,
                    fontFamily: "var(--font-data)",
                    fontSize: 10,
                    color: line.color,
                  }}
                >
                  {line.label}
                </span>
              </div>
            ))}
            <div
              style={{
                position: "absolute",
                inset: 0,
                display: "flex",
                alignItems: "flex-end",
                justifyContent: "center",
                paddingBottom: 12,
              }}
            >
              <Caps size={10}>Chart placeholder — tape renders here</Caps>
            </div>
          </div>

          <div
            style={{
              padding: "10px 16px",
              display: "grid",
              gap: 2,
              alignContent: "start",
              background: "var(--black-2)",
            }}
          >
            <Caps style={{ paddingBottom: 4 }}>Session tape</Caps>
            <Term color="var(--phos-600)">
              21:04 armed long · released clutch · stood down (7)
            </Term>
            <Term color="var(--phos-500)">
              20:57 filled XAUUSD long 0.20 @ 2458.10 · sl 2455.60 · tp 2473.00
            </Term>
            <Term color="var(--grey-500)">
              20:41 limits locked · window 20:00–23:00 · max loss -3.00R
            </Term>
          </div>

          {/* armed: the two-hand review modal */}
          {armed ? (
            <div
              style={{
                position: "absolute",
                inset: 0,
                background: "var(--black-a88)",
                backdropFilter: "blur(6px)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                zIndex: 60,
              }}
            >
              <div
                style={{
                  width: 520,
                  background: "var(--surface-panel)",
                  border: "1px solid var(--line-strong)",
                  boxShadow: "var(--glow-md),var(--sprite-shadow-lg)",
                }}
              >
                <div
                  style={{
                    height: 34,
                    display: "flex",
                    alignItems: "center",
                    gap: 10,
                    padding: "0 12px",
                    borderBottom: "1px solid var(--line-hairline)",
                    background: "var(--black-3)",
                  }}
                >
                  <Caps
                    size={11}
                    weight={700}
                    color="var(--phos-300)"
                    style={{ textShadow: "var(--glow-text)" }}
                  >
                    Armed · review before fire
                  </Caps>
                  <span
                    style={{
                      marginLeft: "auto",
                      fontFamily: "var(--font-data)",
                      fontSize: 11,
                      color: "var(--arcade-yellow)",
                    }}
                  >
                    21:07:12
                  </span>
                </div>
                <div style={{ padding: 16, display: "grid", gap: 14 }}>
                  <div style={{ display: "flex", alignItems: "baseline", gap: 12 }}>
                    <span
                      style={{
                        fontFamily: "var(--font-display)",
                        fontSize: 24,
                        color: "var(--phos-400)",
                        textShadow: "var(--glow-text)",
                      }}
                    >
                      LONG
                    </span>
                    <span
                      style={{
                        fontFamily: "var(--font-data)",
                        fontSize: 20,
                        fontWeight: 700,
                        color: "var(--text-body)",
                      }}
                    >
                      XAUUSD 0.20
                    </span>
                    <Caps size={10} color="var(--text-muted)" style={{ marginLeft: "auto" }}>
                      Market
                    </Caps>
                  </div>

                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "repeat(3,1fr)",
                      gap: 1,
                      background: "var(--line-hairline)",
                    }}
                  >
                    {[
                      { label: "Entry ~", value: "2461.38", color: "var(--text-body)" },
                      { label: "Stop", value: "2455.60", color: "var(--arcade-red)" },
                      { label: "Target", value: "2473.00", color: "var(--phos-300)" },
                    ].map((cell) => (
                      <div
                        key={cell.label}
                        style={{
                          background: "var(--surface-well)",
                          padding: 10,
                          display: "grid",
                          gap: 4,
                        }}
                      >
                        <Caps color="var(--text-muted)">{cell.label}</Caps>
                        <span
                          style={{
                            fontFamily: "var(--font-data)",
                            fontSize: 16,
                            color: cell.color,
                          }}
                        >
                          {cell.value}
                        </span>
                      </div>
                    ))}
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
                    <Caps size={10} color="var(--text-muted)">
                      Risk
                    </Caps>
                    <PnLValue value={-1} size="md" />
                    <Caps size={10} color="var(--text-muted)">
                      Reward
                    </Caps>
                    <PnLValue value={2.4} size="md" />
                    <Term color="var(--status-agent)" style={{ marginLeft: "auto" }}>
                      risk-warden: within rule 4.
                    </Term>
                  </div>

                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 12,
                      padding: 12,
                      background: "var(--black-3)",
                      border: "1px solid var(--line-strong)",
                    }}
                  >
                    <GamepadKey button="LT" size="lg" pressed label="Hold" />
                    <span style={{ color: "var(--text-disabled)" }}>+</span>
                    <GamepadKey button="RT" size="lg" label="Fire" />
                    <Caps
                      size={11}
                      weight={700}
                      color="var(--phos-300)"
                      style={{ marginLeft: "auto" }}
                    >
                      Two hands to send
                    </Caps>
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <GamepadKey button="b" size="sm" label="Cancel" />
                    <Term color="var(--grey-500)">
                      release the clutch and this counts as a stand-down, not a miss.
                    </Term>
                  </div>
                </div>
              </div>
            </div>
          ) : null}

          {/* locked: the session-locked overlay */}
          {locked ? (
            <div
              style={{
                position: "absolute",
                inset: 0,
                background: "var(--black-a88)",
                backdropFilter: "blur(6px)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                zIndex: 60,
              }}
            >
              <div
                style={{
                  width: 560,
                  background: "var(--surface-panel)",
                  border: "1px solid var(--arcade-red-dim)",
                  boxShadow: "var(--glow-red),var(--sprite-shadow-lg)",
                  padding: 20,
                  display: "grid",
                  gap: 16,
                }}
              >
                <span
                  style={{
                    fontFamily: "var(--font-display)",
                    fontSize: 24,
                    color: "var(--arcade-red)",
                  }}
                >
                  SESSION LOCKED
                </span>
                <span
                  style={{
                    fontSize: 14,
                    lineHeight: 1.5,
                    color: "var(--text-body)",
                    maxWidth: "64ch",
                  }}
                >
                  Everything is flat. You flattened at 22:18 and the session locked itself. Spent
                  limits do not come back when you unlock — the loss is booked and the clock kept
                  running.
                </span>
                <div
                  style={{
                    display: "grid",
                    gap: 6,
                    padding: 12,
                    background: "var(--black-3)",
                    border: "1px solid var(--line-hairline)",
                  }}
                >
                  <Term color="var(--phos-500)">
                    available: close positions · emergency flatten · menu · agent desk
                  </Term>
                  <Term color="var(--arcade-red)">
                    blocked: new opens · size changes · protection edits
                  </Term>
                  <Term color="var(--grey-500)">
                    open positions: none · stood down 7 · loss used -3.00R of -3.00R
                  </Term>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <Button variant="secondary" size="md">
                    Unlock session
                  </Button>
                  <Button variant="ghost" size="md">
                    Close session
                  </Button>
                  <Caps size={10} color="var(--text-muted)" style={{ marginLeft: "auto" }}>
                    Mouse and keyboard work here
                  </Caps>
                </div>
              </div>
            </div>
          ) : null}
        </section>

        {/* ── right rail: score, positions, arm status, P&L ───── */}
        <aside
          style={{
            borderLeft: "1px solid var(--line-hairline)",
            background: "var(--black-2)",
            display: "grid",
            gridTemplateRows: "auto auto 1fr auto",
            minHeight: 0,
          }}
        >
          <div
            style={{
              padding: "14px 16px",
              borderBottom: "1px solid var(--line-hairline)",
              display: "grid",
              gap: 6,
              justifyItems: "start",
            }}
          >
            <Caps>Stood down this session</Caps>
            <span
              style={{
                fontFamily: "var(--font-display)",
                fontSize: 36,
                lineHeight: 1.1,
                color: "var(--phos-400)",
                textShadow: "var(--glow-text)",
              }}
            >
              07
            </span>
            <Term color="var(--phos-600)">7 of 12 arms ended in a stand-down.</Term>
          </div>

          <div
            style={{
              padding: "14px 16px",
              borderBottom: "1px solid var(--line-hairline)",
              display: "grid",
              gap: 10,
            }}
          >
            <Caps>Open positions · 2</Caps>

            <div
              style={{
                borderLeft: "2px solid var(--phos-400)",
                background: "var(--surface-selected)",
                padding: "8px 10px",
                display: "grid",
                gap: 6,
              }}
            >
              <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
                <span
                  style={{
                    fontSize: 11,
                    fontWeight: 700,
                    letterSpacing: ".12em",
                    color: "var(--text-body)",
                  }}
                >
                  XAUUSD
                </span>
                <Caps size={10} weight={700} color="var(--side-long)">
                  long
                </Caps>
                <span
                  style={{
                    fontFamily: "var(--font-data)",
                    fontSize: 11,
                    color: "var(--text-muted)",
                  }}
                >
                  0.20
                </span>
                <span style={{ marginLeft: "auto" }}>
                  <PnLValue value={1.4} size="sm" />
                </span>
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
                <span>2458.10 → 2461.38</span>
                <span>sl 2455.60 · tp 2473.00</span>
              </div>
              <Caps color="var(--phos-300)">Selected · A closes this one</Caps>
            </div>

            <div style={{ borderLeft: "2px solid transparent", padding: "8px 10px", display: "grid", gap: 6 }}>
              <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
                <span
                  style={{
                    fontSize: 11,
                    fontWeight: 700,
                    letterSpacing: ".12em",
                    color: "var(--text-body)",
                  }}
                >
                  EURUSD
                </span>
                <Caps size={10} weight={700} color="var(--side-short)">
                  short
                </Caps>
                <span
                  style={{
                    fontFamily: "var(--font-data)",
                    fontSize: 11,
                    color: "var(--text-muted)",
                  }}
                >
                  0.10
                </span>
                <span style={{ marginLeft: "auto" }}>
                  <PnLValue value={-0.6} size="sm" />
                </span>
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
                <span>1.09210 → 1.09142</span>
                <span>sl 1.09340 · tp —</span>
              </div>
            </div>
          </div>

          <div style={{ padding: "14px 16px", display: "grid", gap: 10, alignContent: "start" }}>
            <Caps>Arm status</Caps>

            {armReady ? (
              <div
                style={{
                  padding: 12,
                  border: "1px solid var(--line-hairline)",
                  background: "var(--black-3)",
                  display: "grid",
                  gap: 10,
                }}
              >
                <Caps size={11} weight={700} color="var(--phos-300)">
                  Safe · nothing armed
                </Caps>
                <Term>hold LT to arm. sticks never send an order.</Term>
                <div style={{ display: "flex", gap: 10 }}>
                  <GamepadKey button="LT" size="md" label="Clutch" />
                  <GamepadKey button="up" size="md" label="Long" />
                  <GamepadKey button="down" size="md" label="Short" />
                </div>
              </div>
            ) : null}

            {armed ? (
              <div
                style={{
                  padding: 12,
                  border: "1px solid var(--line-strong)",
                  background: "var(--phos-a08)",
                  boxShadow: "var(--glow-sm)",
                  display: "grid",
                  gap: 8,
                }}
              >
                <Caps
                  size={11}
                  weight={700}
                  color="var(--phos-300)"
                  style={{ textShadow: "var(--glow-text)" }}
                >
                  Armed long · reviewing
                </Caps>
                <Term>nothing has been sent yet.</Term>
              </div>
            ) : null}

            {armBlocked ? (
              <div
                style={{
                  padding: 12,
                  border: "1px solid var(--line-neutral)",
                  background: "var(--black-3)",
                  display: "grid",
                  gap: 8,
                }}
              >
                <Caps size={11} weight={700} color="var(--text-disabled)">
                  Arming disabled
                </Caps>
                <Term color="var(--grey-500)">closing and emergency exit still work.</Term>
              </div>
            ) : null}

            {pending ? (
              <div
                style={{
                  padding: 12,
                  border: "1px solid rgba(255,212,0,.4)",
                  background: "rgba(255,212,0,.08)",
                  display: "grid",
                  gap: 10,
                }}
              >
                <Caps size={11} weight={700} color="var(--arcade-yellow)">
                  Waiting on cid 8841
                </Caps>
                <Term>
                  the final state will appear here by itself. you do not have to go looking.
                </Term>
                <Button variant="secondary" size="sm" fullWidth>
                  Override
                </Button>
              </div>
            ) : null}
          </div>

          <div
            style={{
              borderTop: "1px solid var(--line-hairline)",
              padding: "12px 16px",
              display: "grid",
              gap: 8,
            }}
          >
            <Caps>Session P&amp;L · risk units</Caps>
            <div
              style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between" }}
            >
              <PnLValue value={sessionR} size="lg" />
              <Caps size={10} color="var(--text-muted)">
                4 trades · 12 arms
              </Caps>
            </div>
          </div>
        </aside>
      </div>

      <footer
        style={{
          display: "flex",
          alignItems: "center",
          gap: 18,
          padding: "0 16px",
          borderTop: "1px solid var(--line-hairline)",
          background: "var(--black-1)",
        }}
      >
        <GamepadKey button="LT" size="sm" label="Clutch" />
        <GamepadKey button="RT" size="sm" label="Fire" />
        <GamepadKey button="a" size="sm" label="Close selected" />
        <GamepadKey button="b" size="sm" label="Cancel arm" />
        <GamepadKey button="y" size="sm" label="Ask agent" />
        <GamepadKey button="START" size="sm" label="Menu" />
        <GamepadKey button="VIEW" size="sm" label="Lock session" />
        <span
          style={{
            marginLeft: "auto",
            fontFamily: "var(--font-terminal)",
            fontSize: 15,
            color: "var(--phos-600)",
          }}
        >
          &gt; pad connected · gateway 12ms · demo account · not advice
        </span>
      </footer>
    </Artboard>
  );
}
