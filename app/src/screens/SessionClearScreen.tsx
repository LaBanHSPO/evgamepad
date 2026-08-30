import { Artboard, Caps, PadHint, Term } from "../components/primitives";
import { tally, tallyTotal } from "../data/arcade";
import { Badge, MeterBar, PnLValue } from "../ds";
import { CITY_ART } from "./art";

/** Session clear · the tally — the prototype's `is_clear` artboard. */

const SUMMARY = [
  { label: "Fills", value: "4", color: "var(--text-body)" },
  { label: "Arms refused", value: "8", color: "var(--phos-300)" },
  { label: "Median hold", value: "14m", color: "var(--text-body)" },
];

export function SessionClearScreen() {
  return (
    <Artboard
      label="Session clear · the tally"
      frameStyle={{
        width: 1440,
        height: 810,
        position: "relative",
        background: `#040604 url('${CITY_ART}') center/cover no-repeat`,
        border: "1px solid var(--line-strong)",
        boxShadow: "var(--glow-md)",
      }}
    >
      <div style={{ position: "absolute", inset: 0, background: "rgba(4,6,4,.78)" }} />
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage: "var(--veil-grid)",
          opacity: 0.5,
        }}
      />
      <div style={{ position: "absolute", inset: 0, background: "var(--veil-vignette)" }} />

      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: 0,
          height: 44,
          display: "flex",
          alignItems: "center",
          gap: 20,
          padding: "0 20px",
          background: "rgba(4,6,4,.9)",
          borderBottom: "1px solid var(--line-strong)",
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
          1P 08
        </span>
        <span style={{ fontFamily: "var(--font-display)", fontSize: 11, color: "var(--grey-300)" }}>
          HI 12
        </span>
        <span
          style={{
            fontFamily: "var(--font-data)",
            fontSize: 10,
            letterSpacing: ".12em",
            color: "var(--text-muted)",
          }}
        >
          Session 043 · 20:00 → 23:00 · closed on time
        </span>
        <span style={{ marginLeft: "auto" }}>
          <Badge tone="live" dot>
            Window closed
          </Badge>
        </span>
      </div>

      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: 44,
          bottom: 56,
          display: "grid",
          gridTemplateColumns: "1fr 440px",
        }}
      >
        {/* the tally */}
        <div
          style={{
            padding: "30px 40px",
            display: "grid",
            gap: 22,
            alignContent: "start",
            minHeight: 0,
          }}
        >
          <div style={{ display: "flex", alignItems: "flex-end", gap: 22 }}>
            <span
              style={{
                fontFamily: "var(--font-display)",
                fontSize: 34,
                lineHeight: 1,
                color: "var(--phos-400)",
                textShadow: "var(--glow-text)",
              }}
            >
              SESSION CLEAR
            </span>
            <Term size={18} style={{ paddingBottom: 4 }}>
              you closed the window instead of it closing you.
            </Term>
          </div>

          <div style={{ display: "grid", gap: 2 }}>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 90px 120px",
                gap: 12,
                padding: "0 14px 8px",
                fontSize: 9,
                letterSpacing: ".18em",
                textTransform: "uppercase",
                color: "var(--text-disabled)",
              }}
            >
              <span>Tally</span>
              <span style={{ textAlign: "right" }}>Count</span>
              <span style={{ textAlign: "right" }}>Points</span>
            </div>

            {tally.map((row) => (
              <div
                key={row.label}
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 90px 120px",
                  gap: 12,
                  alignItems: "center",
                  padding: "12px 14px",
                  background: "var(--black-2)",
                  borderBottom: "1px solid var(--line-hairline)",
                }}
              >
                <span style={{ display: "grid", gap: 3 }}>
                  <Caps size={11} weight={700} color="var(--text-secondary)">
                    {row.label}
                  </Caps>
                  <span
                    style={{
                      fontFamily: "var(--font-terminal)",
                      fontSize: 15,
                      color: "var(--grey-500)",
                    }}
                  >
                    {row.note}
                  </span>
                </span>
                <span
                  style={{
                    fontFamily: "var(--font-data)",
                    fontSize: 16,
                    fontWeight: 700,
                    textAlign: "right",
                    color: "var(--text-body)",
                    fontVariantNumeric: "tabular-nums",
                  }}
                >
                  {row.count}
                </span>
                <span
                  style={{
                    fontFamily: "var(--font-data)",
                    fontSize: 16,
                    fontWeight: 700,
                    textAlign: "right",
                    fontVariantNumeric: "tabular-nums",
                    color: row.points.startsWith("-") ? "var(--arcade-red)" : "var(--phos-300)",
                  }}
                >
                  {row.points}
                </span>
              </div>
            ))}

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 90px 120px",
                gap: 12,
                alignItems: "center",
                padding: "16px 14px",
                marginTop: 8,
                background: "var(--phos-a08)",
                border: "1px solid var(--line-strong)",
                boxShadow: "var(--glow-sm)",
              }}
            >
              <span
                style={{
                  fontFamily: "var(--font-display)",
                  fontSize: 14,
                  color: "var(--phos-300)",
                }}
              >
                TOTAL
              </span>
              <span />
              <span
                style={{
                  fontFamily: "var(--font-data)",
                  fontSize: 22,
                  fontWeight: 700,
                  textAlign: "right",
                  color: "var(--phos-200)",
                  textShadow: "var(--glow-text)",
                  fontVariantNumeric: "tabular-nums",
                }}
              >
                {tallyTotal}
              </span>
            </div>
          </div>

          <div style={{ display: "flex", gap: 14 }}>
            <div
              style={{
                display: "grid",
                gap: 6,
                padding: "14px 18px",
                border: "1px solid var(--line-hairline)",
                background: "var(--black-2)",
              }}
            >
              <Caps>Session P&amp;L</Caps>
              <PnLValue value={2.4} size="lg" />
            </div>
            {SUMMARY.map((tile) => (
              <div
                key={tile.label}
                style={{
                  display: "grid",
                  gap: 6,
                  padding: "14px 18px",
                  border: "1px solid var(--line-hairline)",
                  background: "var(--black-2)",
                }}
              >
                <Caps>{tile.label}</Caps>
                <span
                  style={{
                    fontFamily: "var(--font-data)",
                    fontSize: 24,
                    fontWeight: 700,
                    color: tile.color,
                    fontVariantNumeric: "tabular-nums",
                  }}
                >
                  {tile.value}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* rank, meters, desk review */}
        <aside
          style={{
            borderLeft: "1px solid var(--line-strong)",
            background: "rgba(8,12,8,.94)",
            display: "grid",
            gridTemplateRows: "auto auto 1fr",
            minHeight: 0,
          }}
        >
          <div
            style={{
              padding: "24px 22px",
              borderBottom: "1px solid var(--line-hairline)",
              display: "grid",
              gap: 12,
              justifyItems: "center",
              textAlign: "center",
            }}
          >
            <Caps color="var(--phos-500)">Rank · process, not profit</Caps>
            <span
              style={{
                fontFamily: "var(--font-display)",
                fontSize: 72,
                lineHeight: 1,
                color: "var(--phos-400)",
                textShadow: "var(--glow-text)",
              }}
            >
              A
            </span>
            <Term>one rule bent, none broken.</Term>
          </div>

          <div
            style={{
              padding: "16px 20px",
              borderBottom: "1px solid var(--line-hairline)",
              display: "grid",
              gap: 12,
            }}
          >
            <Caps color="var(--phos-500)">Discipline meters</Caps>
            <MeterBar label="Rules kept" value={11} max={12} segments={12} showValue />
            <MeterBar label="Size discipline" value={9} max={10} segments={10} showValue />
            <MeterBar label="Patience" value={6} max={10} segments={10} tone="warn" showValue />
          </div>

          <div
            style={{
              padding: "16px 20px",
              display: "grid",
              gap: 8,
              alignContent: "start",
              background: "rgba(4,6,4,.7)",
              backgroundImage: "var(--veil-scanline)",
            }}
          >
            <Caps color="var(--status-agent)">Desk review · session-scribe</Caps>
            <Term color="var(--status-agent)">four fills, three inside plan.</Term>
            <Term color="var(--status-agent)">
              the 21:48 short had no level behind it. it cost -0.60R.
            </Term>
            <Term color="var(--status-agent)">
              you refused eight arms after 22:10 — the same hour that cost you -4.3R last month.
            </Term>
            <Term color="var(--status-agent)">
              patience is your weakest meter three sessions running.
            </Term>
          </div>
        </aside>
      </div>

      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          bottom: 0,
          height: 56,
          display: "flex",
          alignItems: "center",
          gap: 14,
          padding: "0 20px",
          background: "var(--black-1)",
          borderTop: "1px solid var(--line-strong)",
        }}
      >
        <PadHint button="a" label="Commit session" />
        <PadHint button="y" label="Ask desk" />
        <PadHint button="VIEW" label="Back to cabinet" />
        <span
          style={{
            marginLeft: "auto",
            fontFamily: "var(--font-terminal)",
            fontSize: 15,
            color: "var(--phos-600)",
          }}
        >
          &gt; the tally is written. it cannot be edited after commit.
        </span>
      </div>
    </Artboard>
  );
}
