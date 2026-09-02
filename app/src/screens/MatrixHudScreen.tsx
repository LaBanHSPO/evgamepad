import type { ReactNode } from "react";
import { CodeRain } from "../components/CodeRain";
import { Artboard, Caps, DemoNotice, PadHint, Term } from "../components/primitives";
import { Button, Icon, MeterBar, PnLValue, Switch, type IconName } from "../ds";
import { MATRIX_ART } from "./art";

/** HUD on matrix art — the prototype's `is_artmatrix` artboard. */

/** A section head in a HUD rail: lucide glyph + tracked caps, both phosphor. */
function SectionLabel({
  icon,
  children,
  center,
}: {
  icon: IconName;
  children: ReactNode;
  center?: boolean;
}) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: center ? "center" : undefined,
        gap: 7,
        color: "var(--phos-500)",
      }}
    >
      <Icon name={icon} size="xs" />
      <Caps color="inherit">{children}</Caps>
    </div>
  );
}

export function MatrixHudScreen() {
  return (
    <Artboard
      label="HUD on matrix art"
      frameStyle={{
        width: 1440,
        height: 810,
        display: "grid",
        gridTemplateRows: "56px 1fr 64px",
        background: `#040604 url('${MATRIX_ART}') center/cover no-repeat`,
        border: "1px solid var(--line-strong)",
        boxShadow: "var(--glow-md)",
        position: "relative",
      }}
    >
      {/* ── arcade score header ───────────────────────────────── */}
      <header
        style={{
          display: "flex",
          alignItems: "center",
          gap: 26,
          padding: "0 20px",
          borderBottom: "1px solid var(--line-strong)",
          background: "var(--black-2)",
          position: "relative",
          zIndex: 2,
        }}
      >
        <div style={{ display: "grid", gap: 3 }}>
          <Caps color="var(--phos-500)">1P stood down</Caps>
          <span
            style={{
              fontFamily: "var(--font-display)",
              fontSize: 16,
              color: "var(--phos-400)",
              textShadow: "var(--glow-text)",
            }}
          >
            07
          </span>
        </div>
        <div style={{ display: "grid", gap: 3 }}>
          <Caps color="var(--text-muted)">HI</Caps>
          <span
            style={{ fontFamily: "var(--font-display)", fontSize: 16, color: "var(--grey-300)" }}
          >
            12
          </span>
        </div>
        <div style={{ display: "grid", gap: 5 }}>
          <Caps color="var(--text-muted)">Arms left · positions 2 of 2</Caps>
          <div style={{ display: "flex", gap: 5 }}>
            {[true, true, true, false, false].map((lit, i) => (
              <i
                key={i}
                style={{
                  width: 11,
                  height: 11,
                  background: lit ? "var(--phos-400)" : "var(--black-5)",
                  boxShadow: lit ? "var(--glow-xs)" : undefined,
                  border: lit ? undefined : "1px solid var(--line-neutral)",
                }}
              />
            ))}
          </div>
        </div>
        <div style={{ display: "grid", gap: 3 }}>
          <Caps color="var(--text-muted)">Session ends</Caps>
          <span
            style={{
              fontFamily: "var(--font-data)",
              fontSize: 16,
              fontWeight: 700,
              color: "var(--arcade-yellow)",
            }}
          >
            1:12:04
          </span>
        </div>
        <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 18 }}>
          <span
            style={{
              fontFamily: "var(--font-display)",
              fontSize: 12,
              color: "var(--arcade-red)",
              animation: "ev-blink 1s steps(1,end) infinite",
            }}
          >
            PRESS START
          </span>
          <Button variant="danger" size="sm">
            Flatten all
          </Button>
        </div>
      </header>

      {/* ── body: limits rail · tape · positions rail ─────────── */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "300px 1fr 320px",
          minHeight: 0,
          position: "relative",
        }}
      >
        <div style={{ position: "absolute", inset: 0, zIndex: 0, overflow: "hidden" }}>
          <CodeRain opacity={0.12} fontSize={15} />
        </div>

        <aside
          style={{
            position: "relative",
            zIndex: 1,
            borderRight: "1px solid var(--line-strong)",
            background: "rgba(8,12,8,.92)",
            display: "grid",
            gridTemplateRows: "auto auto 1fr",
            minHeight: 0,
          }}
        >
          <div
            style={{
              padding: "16px 18px",
              borderBottom: "1px solid var(--line-hairline)",
              display: "grid",
              gap: 12,
            }}
          >
            <SectionLabel icon="shield">Player limits · gateway enforced</SectionLabel>
            <MeterBar label="Loss meter" value={11} max={30} segments={10} tone="warn" showValue />
            <MeterBar label="Size used" value={20} max={50} segments={10} />
            <MeterBar label="Window burned" value={62} max={100} segments={10} tone="info" />
          </div>

          <div
            style={{
              padding: "16px 18px",
              borderBottom: "1px solid var(--line-hairline)",
              display: "grid",
              gap: 10,
            }}
          >
            <SectionLabel icon="gamepad-2">Instrument · d-pad</SectionLabel>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                height: 34,
                padding: "0 12px",
                border: "1px solid var(--line-strong)",
                background: "var(--phos-a08)",
                boxShadow: "var(--glow-xs)",
              }}
            >
              <span
                style={{
                  fontFamily: "var(--font-display)",
                  fontSize: 12,
                  color: "var(--phos-400)",
                }}
              >
                XAUUSD
              </span>
              <span
                style={{ fontFamily: "var(--font-data)", fontSize: 12, color: "var(--phos-200)" }}
              >
                0.20
              </span>
            </div>
            {[
              { pair: "EURUSD", size: "0.10 open", color: "var(--text-muted)" },
              { pair: "GBPUSD", size: "—", color: "var(--text-disabled)" },
              { pair: "USDJPY", size: "—", color: "var(--text-disabled)" },
            ].map((row) => (
              <div
                key={row.pair}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  fontFamily: "var(--font-data)",
                  fontSize: 11,
                  color: row.color,
                  padding: "0 2px",
                }}
              >
                <span>{row.pair}</span>
                <span>{row.size}</span>
              </div>
            ))}
          </div>

          <div
            style={{
              padding: "16px 18px",
              display: "grid",
              gap: 8,
              alignContent: "start",
              background: "rgba(4,6,4,.7)",
              backgroundImage: "var(--veil-scanline)",
            }}
          >
            <SectionLabel icon="terminal">Session log</SectionLabel>
            <Term color="var(--phos-400)">21:04 stand down +1 · score 07</Term>
            <Term color="var(--phos-500)">20:57 fill buy 0.20 @ 2458.10</Term>
            <Term color="var(--status-agent)">20:56 risk-warden: inside rule 4.</Term>
            <Term color="var(--grey-500)">20:41 limits locked · -3.00R cap</Term>
          </div>
        </aside>

        {/* price header + chart placeholder */}
        <section
          style={{
            position: "relative",
            zIndex: 1,
            display: "grid",
            gridTemplateRows: "auto 1fr",
            minHeight: 0,
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "flex-end",
              gap: 20,
              padding: "16px 20px",
              background: "rgba(4,6,4,.92)",
              borderBottom: "1px solid var(--line-strong)",
            }}
          >
            <span
              style={{
                fontFamily: "var(--font-data)",
                fontSize: 64,
                fontWeight: 700,
                lineHeight: 1,
                color: "var(--phos-100)",
                textShadow: "var(--glow-text)",
                fontVariantNumeric: "tabular-nums",
              }}
            >
              2461.38
            </span>
            <div style={{ display: "grid", gap: 5, paddingBottom: 6 }}>
              <Caps size={10} color="var(--phos-500)">
                XAUUSD · M5
              </Caps>
              <span
                style={{
                  fontFamily: "var(--font-data)",
                  fontSize: 11,
                  color: "var(--text-secondary)",
                }}
              >
                2458.10 → 2461.38 · spread 0.24
              </span>
            </div>
            <div style={{ marginLeft: "auto", display: "grid", gap: 5, justifyItems: "end" }}>
              <Caps size={10} color="var(--phos-500)">
                Session
              </Caps>
              <PnLValue value={1.6} size="lg" />
            </div>
          </div>

          <div
            style={{
              position: "relative",
              background: "rgba(4,6,4,.3)",
              backgroundImage: "var(--veil-grid)",
              overflow: "hidden",
            }}
          >
            {/* target / entry / stop lines */}
            <div
              style={{
                position: "absolute",
                left: 0,
                right: 0,
                top: "26%",
                borderTop: "1px dashed rgba(0,255,65,.42)",
              }}
            >
              <span
                style={{
                  position: "absolute",
                  right: 10,
                  top: -17,
                  fontFamily: "var(--font-data)",
                  fontSize: 11,
                  color: "var(--phos-400)",
                }}
              >
                TP 2473.00 · +2.00R
              </span>
            </div>
            <div
              style={{
                position: "absolute",
                left: 0,
                right: 0,
                top: "52%",
                borderTop: "2px solid var(--phos-400)",
                boxShadow: "var(--glow-sm)",
              }}
            >
              <span
                style={{
                  position: "absolute",
                  right: 10,
                  top: -18,
                  fontFamily: "var(--font-data)",
                  fontSize: 11,
                  color: "var(--phos-200)",
                }}
              >
                ENTRY 2458.10
              </span>
            </div>
            <div
              style={{
                position: "absolute",
                left: 0,
                right: 0,
                top: "78%",
                borderTop: "1px dashed var(--arcade-red-dim)",
              }}
            >
              <span
                style={{
                  position: "absolute",
                  right: 10,
                  top: -17,
                  fontFamily: "var(--font-data)",
                  fontSize: 11,
                  color: "var(--arcade-red)",
                }}
              >
                SL 2455.60 · -1.00R
              </span>
            </div>

            <div
              style={{
                position: "absolute",
                left: 20,
                top: 20,
                padding: "10px 12px",
                background: "rgba(4,6,4,.86)",
                border: "1px solid var(--line-strong)",
                boxShadow: "var(--sprite-shadow)",
                display: "grid",
                gap: 6,
              }}
            >
              <Caps color="var(--phos-500)">Lens · not AI</Caps>
              <span
                style={{
                  fontFamily: "var(--font-data)",
                  fontSize: 11,
                  color: "var(--text-secondary)",
                }}
              >
                range · london low intact
              </span>
            </div>

            <Caps style={{ position: "absolute", left: 20, bottom: 14 }} size={10}>
              Chart placeholder — the city is the backdrop, the tape renders here
            </Caps>

            <div
              style={{
                position: "absolute",
                right: 20,
                bottom: 16,
                padding: "10px 14px",
                background: "rgba(4,6,4,.9)",
                border: "1px solid rgba(255,212,0,.4)",
                boxShadow: "var(--sprite-shadow)",
                display: "flex",
                alignItems: "center",
                gap: 10,
              }}
            >
              <Caps size={10} color="var(--arcade-yellow)">
                Incoming · dxy
              </Caps>
              <span
                style={{
                  fontFamily: "var(--font-data)",
                  fontSize: 14,
                  fontWeight: 700,
                  color: "var(--arcade-yellow)",
                }}
              >
                18:04
              </span>
            </div>
          </div>
        </section>

        <aside
          style={{
            position: "relative",
            zIndex: 1,
            borderLeft: "1px solid var(--line-strong)",
            background: "rgba(8,12,8,.92)",
            display: "grid",
            gridTemplateRows: "auto auto 1fr auto",
            minHeight: 0,
          }}
        >
          <div
            style={{
              padding: "16px 18px",
              borderBottom: "1px solid var(--line-hairline)",
              display: "grid",
              gap: 8,
              justifyItems: "center",
              textAlign: "center",
            }}
          >
            <SectionLabel icon="target" center>
              Stand-down score
            </SectionLabel>
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
            <Term color="var(--phos-500)">7 of 12 arms refused</Term>
          </div>

          <div
            style={{
              padding: "16px 18px",
              borderBottom: "1px solid var(--line-hairline)",
              display: "grid",
              gap: 10,
            }}
          >
            <SectionLabel icon="chart-candlestick">Positions · 2 of 2</SectionLabel>

            <div
              style={{
                border: "1px solid var(--line-strong)",
                background: "var(--phos-a08)",
                boxShadow: "var(--glow-xs)",
                padding: 10,
                display: "grid",
                gap: 6,
              }}
            >
              <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
                <span
                  style={{
                    fontFamily: "var(--font-display)",
                    fontSize: 12,
                    color: "var(--phos-300)",
                  }}
                >
                  XAU
                </span>
                <Caps size={10} weight={700} color="var(--side-buy)">
                  buy
                </Caps>
                <span style={{ marginLeft: "auto" }}>
                  <PnLValue value={1.4} size="sm" />
                </span>
              </div>
              <MeterBar value={58} max={100} segments={12} />
              <span
                style={{ fontFamily: "var(--font-data)", fontSize: 10, color: "var(--text-muted)" }}
              >
                58% of the way to target
              </span>
            </div>

            <div
              style={{
                border: "1px solid var(--line-hairline)",
                padding: 10,
                display: "grid",
                gap: 6,
              }}
            >
              <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
                <span
                  style={{
                    fontFamily: "var(--font-display)",
                    fontSize: 12,
                    color: "var(--grey-300)",
                  }}
                >
                  EUR
                </span>
                <Caps size={10} weight={700} color="var(--side-sell)">
                  sell
                </Caps>
                <span style={{ marginLeft: "auto" }}>
                  <PnLValue value={-0.6} size="sm" />
                </span>
              </div>
              <MeterBar value={22} max={100} segments={12} tone="danger" />
              <span
                style={{ fontFamily: "var(--font-data)", fontSize: 10, color: "var(--text-muted)" }}
              >
                stop 1.09340 · no target set
              </span>
            </div>
          </div>

          <div style={{ padding: "16px 18px", display: "grid", gap: 10, alignContent: "start" }}>
            <SectionLabel icon="timer">Ready state</SectionLabel>
            <div
              style={{
                padding: 14,
                border: "1px solid var(--line-strong)",
                background: "var(--black-3)",
                boxShadow: "var(--sprite-shadow)",
                display: "grid",
                gap: 10,
                justifyItems: "center",
              }}
            >
              <span
                style={{
                  fontFamily: "var(--font-display)",
                  fontSize: 16,
                  color: "var(--phos-400)",
                  textShadow: "var(--glow-text)",
                }}
              >
                SAFE
              </span>
              <Term style={{ textAlign: "center" }}>hold LT to arm. sticks never fire.</Term>
            </div>
          </div>

          <div
            style={{
              borderTop: "1px solid var(--line-hairline)",
              padding: "14px 18px",
              display: "grid",
              gap: 6,
            }}
          >
            <SectionLabel icon="database">Money view</SectionLabel>
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
      </div>

      {/* ── pad legend ───────────────────────────────────────── */}
      <footer
        style={{
          position: "relative",
          zIndex: 2,
          display: "flex",
          alignItems: "center",
          gap: 14,
          padding: "0 20px",
          borderTop: "1px solid var(--line-strong)",
          background: "var(--black-1)",
        }}
      >
        <Caps color="var(--phos-500)">Your controller</Caps>
        <PadHint button="LT" label="Arm" />
        <PadHint button="RT" label="Fire" />
        <PadHint button="a" label="Close" />
        <PadHint button="b" label="Stand down" />
        <PadHint button="y" label="Ask desk" />
        <PadHint button="VIEW" label="Lock" />
        <DemoNotice />
      </footer>
    </Artboard>
  );
}
