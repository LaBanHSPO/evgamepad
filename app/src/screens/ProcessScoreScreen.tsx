import { Artboard, Caps, ScreenFooter, ScreenHeader, Term } from "../components/primitives";
import { Badge, GamepadKey, MeterBar, StatTile } from "../ds";

/** Process score — the prototype's `is_score` artboard. Grades the evening, not the money. */

/**
 * Selectivity sits second, in its own slot, drawn as a dashed empty bar — it
 * has no denominator this session, so it has a row but no value.
 */
const AXES: { label: string; value?: number; tone?: "warn"; na?: true }[] = [
  { label: "Compliance", value: 92 },
  { label: "Selectivity", na: true },
  { label: "Risk discipline", value: 88 },
  { label: "Preparation", value: 80 },
  { label: "Review", value: 74, tone: "warn" },
];

const TREND = [
  { label: "Compliance", value: "89%", delta: "+4", up: true },
  { label: "Stand-down rate", value: "58%", delta: "+11", up: true },
  { label: "Self-rating, end", value: "3.8", delta: "-0.2", up: false },
];

/** Score distribution across August's 14 sessions, 40 → 100. */
const DIST = [
  { h: "18%", c: "var(--phos-800)" },
  { h: "34%", c: "var(--phos-700)" },
  { h: "52%", c: "var(--phos-600)" },
  { h: "78%", c: "var(--phos-500)" },
  { h: "100%", c: "var(--phos-400)", glow: true },
  { h: "64%", c: "var(--phos-600)" },
  { h: "30%", c: "var(--phos-700)" },
];

/** Tilt bands across the window — retrospective only, never an input to the score. */
const TILT = [
  { flex: 3, c: "var(--phos-a16)" },
  { flex: 2, c: "rgba(255,212,0,.28)" },
  { flex: 1, c: "rgba(232,32,42,.35)" },
  { flex: 4, c: "var(--phos-a16)" },
  { flex: 2, c: "rgba(255,212,0,.28)" },
];

export function ProcessScoreScreen() {
  return (
    <Artboard
      label="Process score"
      frameStyle={{
        width: 1280,
        height: 860,
        display: "grid",
        gridTemplateRows: "44px auto 1fr auto",
        background: "var(--surface-app)",
        border: "1px solid var(--line-hairline)",
      }}
    >
      <ScreenHeader
        title="Process score"
        meta="Session 042 · closed 23:04"
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
                borderBottomColor: "transparent",
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
              Results · shows money
            </span>
          </div>
        }
      />

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "320px 1fr",
          gap: 1,
          background: "var(--line-hairline)",
          borderBottom: "1px solid var(--line-hairline)",
        }}
      >
        <div
          style={{
            background: "var(--black-2)",
            padding: "18px 20px",
            display: "grid",
            gap: 10,
            alignContent: "center",
          }}
        >
          <Caps>Tonight</Caps>
          <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
            <span
              style={{
                fontFamily: "var(--font-display)",
                fontSize: 36,
                lineHeight: 1,
                color: "var(--phos-400)",
                textShadow: "var(--glow-text)",
              }}
            >
              86
            </span>
            <Caps size={11} color="var(--text-muted)">
              of 100
            </Caps>
          </div>
          <Badge tone="info">Built on 4 of 5 axes</Badge>
          <Term>
            selectivity dropped out — the desk was silent all evening, so it has no denominator.
          </Term>
        </div>

        <div
          style={{
            padding: "18px 20px",
            display: "grid",
            gridTemplateColumns: "repeat(4,1fr)",
            gap: 1,
            backgroundColor: "var(--line-hairline)",
          }}
        >
          <StatTile
            label="Stood down"
            value="07"
            sub="4 while a stand-down condition held"
            icon="shield"
          />
          <StatTile
            label="Playbook compliance"
            value="92%"
            sub="11 of 12 checkable rules"
            icon="target"
          />
          <StatTile label="Self-rating" value="4 → 4" sub="start · end of session" icon="pencil" />
          <StatTile
            label="Trades"
            value="4"
            sub="12 arms · 2 held to target"
            icon="chart-candlestick"
          />
        </div>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 1,
          background: "var(--line-hairline)",
          minHeight: 0,
        }}
      >
        {/* five axes */}
        <div
          style={{
            background: "var(--black-2)",
            padding: "18px 20px",
            display: "grid",
            gridTemplateRows: "auto 1fr",
            gap: 14,
            minHeight: 0,
          }}
        >
          <Caps>Five axes · shape of the evening</Caps>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "300px 1fr",
              gap: 20,
              alignItems: "center",
              minHeight: 0,
            }}
          >
            <svg
              viewBox="0 0 300 300"
              width={300}
              height={300}
              role="img"
              aria-label="Five axis radar: compliance 92, selectivity not applicable, risk discipline 88, preparation 80, review 74"
            >
              <polygon points="150,20 273,110 226,254 74,254 27,110" fill="none" stroke="rgba(0,255,65,.16)" />
              <polygon points="150,85 211,130 188,202 112,202 89,130" fill="none" stroke="rgba(0,255,65,.16)" />
              <line x1="150" y1="150" x2="150" y2="20" stroke="rgba(0,255,65,.16)" />
              <line x1="150" y1="150" x2="273" y2="110" stroke="rgba(0,255,65,.16)" />
              <line x1="150" y1="150" x2="226" y2="254" stroke="rgba(0,255,65,.16)" />
              <line x1="150" y1="150" x2="74" y2="254" stroke="rgba(0,255,65,.16)" />
              <line x1="150" y1="150" x2="27" y2="110" stroke="rgba(0,255,65,.16)" />
              {/* the shape stops short of the selectivity spoke — that axis has no denominator */}
              <path
                d="M150,30 L217,241 L82,241 L42,116"
                fill="rgba(0,255,65,.16)"
                stroke="#00FF41"
                strokeWidth="1.5"
                strokeLinejoin="round"
              />
              <circle cx="150" cy="150" r="118" fill="none" stroke="#6E7C6E" strokeWidth="1" strokeDasharray="4 5" />
              <text x="150" y="12" fill="#A8B6A8" fontSize="9" fontFamily="'JetBrains Mono',monospace" letterSpacing="1.6" textAnchor="middle">COMPLIANCE</text>
              <text x="288" y="108" fill="#6E7C6E" fontSize="9" fontFamily="'JetBrains Mono',monospace" letterSpacing="1.6" textAnchor="end">SELECTIVITY</text>
              <text x="246" y="272" fill="#A8B6A8" fontSize="9" fontFamily="'JetBrains Mono',monospace" letterSpacing="1.6" textAnchor="end">RISK DISC.</text>
              <text x="54" y="272" fill="#A8B6A8" fontSize="9" fontFamily="'JetBrains Mono',monospace" letterSpacing="1.6">PREPARATION</text>
              <text x="12" y="108" fill="#A8B6A8" fontSize="9" fontFamily="'JetBrains Mono',monospace" letterSpacing="1.6">REVIEW</text>
            </svg>

            <div style={{ display: "grid", gap: 10, alignContent: "center" }}>
              {AXES.map((axis) => (
                <div key={axis.label} style={{ display: "grid", gap: 4 }}>
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      fontSize: 10,
                      letterSpacing: ".18em",
                      textTransform: "uppercase",
                      color: axis.na ? "var(--text-disabled)" : "var(--text-muted)",
                    }}
                  >
                    <span>{axis.label}</span>
                    {axis.na ? (
                      <span>not applicable</span>
                    ) : (
                      <span
                        style={{
                          fontFamily: "var(--font-data)",
                          color: axis.tone === "warn" ? "var(--arcade-yellow)" : "var(--phos-300)",
                        }}
                      >
                        {axis.value}
                      </span>
                    )}
                  </div>
                  {axis.na ? (
                    <div style={{ height: 8, border: "1px dashed var(--grey-700)" }} />
                  ) : (
                    <MeterBar value={axis.value} max={100} segments={12} tone={axis.tone} />
                  )}
                </div>
              ))}

              <Term color="var(--grey-500)">
                review is the axis holding tonight down: no memo on two of four trades.
              </Term>
            </div>
          </div>
        </div>

        {/* month trend, distribution, tilt */}
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
          <div style={{ display: "grid", gap: 8 }}>
            <Caps>This month vs last · process only</Caps>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr auto auto",
                gap: "10px 16px",
                fontSize: 11,
                color: "var(--text-secondary)",
                alignItems: "baseline",
              }}
            >
              {TREND.map((row) => (
                <div key={row.label} style={{ display: "contents" }}>
                  <Caps size={10} color="var(--text-muted)">
                    {row.label}
                  </Caps>
                  <span style={{ fontFamily: "var(--font-data)" }}>{row.value}</span>
                  <span
                    style={{
                      fontFamily: "var(--font-data)",
                      color: row.up ? "var(--phos-400)" : "var(--arcade-red)",
                    }}
                  >
                    {row.delta}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div style={{ display: "grid", gap: 8 }}>
            <div
              style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}
            >
              <Caps>Score distribution · august</Caps>
              <Caps color="var(--text-muted)">14 sessions</Caps>
            </div>
            <div
              style={{
                display: "flex",
                alignItems: "flex-end",
                gap: 6,
                height: 96,
                padding: "0 2px",
                borderBottom: "1px solid var(--line-hairline)",
              }}
            >
              {DIST.map((bar, i) => (
                <span
                  key={i}
                  style={{
                    flex: 1,
                    height: bar.h,
                    background: bar.c,
                    boxShadow: bar.glow ? "var(--glow-sm)" : undefined,
                  }}
                />
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
              {["40", "55", "70", "85", "100"].map((n) => (
                <span key={n}>{n}</span>
              ))}
            </div>
            <Term color="var(--grey-500)">
              a distribution, not a streak. nothing here carries over.
            </Term>
          </div>

          <div style={{ display: "grid", gap: 8 }}>
            <Caps>Tilt retrospective · never an input to the score</Caps>
            <div style={{ display: "flex", height: 22, border: "1px solid var(--line-hairline)" }}>
              {TILT.map((band, i) => (
                <span key={i} style={{ flex: band.flex, background: band.c }} />
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
              {["20:00", "21:00", "22:00", "23:00"].map((t) => (
                <span key={t}>{t}</span>
              ))}
            </div>
            <Term>
              the hot band at 21:40 follows the -1.10R stop, and compliance held through it.
            </Term>
          </div>
        </div>
      </div>

      <ScreenFooter height={44}>
        <GamepadKey button="START" size="sm" label="Back to session" />
        <Caps size={10} color="var(--text-muted)">
          Read with mouse and keyboard
        </Caps>
      </ScreenFooter>
    </Artboard>
  );
}
