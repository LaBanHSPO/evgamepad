import { Artboard, Caps, PadHint, Term } from "../components/primitives";
import { overRows, rColor } from "../data/arcade";
import { Badge, Button, MeterBar, PnLValue } from "../ds";
import { CITY_ART } from "./art";

/** Session over · loss cap hit — the prototype's `is_over` artboard. */
export function SessionOverScreen() {
  return (
    <Artboard
      label="Session over · loss cap hit"
      frameStyle={{
        width: 1440,
        height: 810,
        position: "relative",
        background: `#040604 url('${CITY_ART}') center/cover no-repeat`,
        border: "1px solid var(--arcade-red-dim)",
        boxShadow: "0 0 0 1px rgba(232,32,42,.18)",
      }}
    >
      <div style={{ position: "absolute", inset: 0, background: "rgba(4,6,4,.8)" }} />
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage: "var(--veil-scanline)",
          opacity: 0.6,
        }}
      />
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(120% 80% at 50% 50%, rgba(232,32,42,.10), rgba(4,6,4,.92) 70%)",
        }}
      />

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
          background: "rgba(4,6,4,.92)",
          borderBottom: "1px solid var(--arcade-red-dim)",
        }}
      >
        <span
          style={{
            fontFamily: "var(--font-display)",
            fontSize: 11,
            color: "var(--arcade-red)",
            textShadow: "2px 2px 0 #000",
          }}
        >
          1P 03
        </span>
        <span style={{ fontFamily: "var(--font-display)", fontSize: 11, color: "var(--grey-500)" }}>
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
          Session 044 · stopped 21:36 · 1h 24m of window unused
        </span>
        <span style={{ marginLeft: "auto" }}>
          <Badge tone="down" dot>
            Close only
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
          gridTemplateColumns: "1fr 420px",
        }}
      >
        <div
          style={{
            display: "grid",
            alignContent: "center",
            justifyItems: "center",
            gap: 24,
            padding: "0 40px",
            textAlign: "center",
          }}
        >
          <span
            style={{
              fontFamily: "var(--font-display)",
              fontSize: 46,
              lineHeight: 1.1,
              color: "var(--arcade-red)",
              textShadow: "3px 3px 0 #000",
            }}
          >
            SESSION OVER
          </span>

          <div style={{ display: "flex", alignItems: "baseline", gap: 14 }}>
            <Caps size={10} weight={700} color="var(--text-muted)">
              Loss cap
            </Caps>
            <PnLValue value={-3.1} size="lg" />
            <span
              style={{ fontFamily: "var(--font-data)", fontSize: 14, color: "var(--text-muted)" }}
            >
              of -3.00R written at 19:58
            </span>
          </div>

          {/* sized by its content, as the centred column in the prototype does */}
          <MeterBar
            value={30}
            max={30}
            segments={10}
            tone="danger"
            label="Loss meter · full"
            showValue
          />

          <div
            style={{
              display: "grid",
              gap: 14,
              justifyItems: "center",
              padding: "22px 34px",
              background: "rgba(8,12,8,.94)",
              border: "1px solid var(--arcade-red-dim)",
              boxShadow: "var(--sprite-shadow-lg)",
            }}
          >
            <span
              style={{
                fontFamily: "var(--font-display)",
                fontSize: 20,
                color: "var(--grey-500)",
              }}
            >
              CONTINUE?
            </span>
            <span
              style={{
                fontFamily: "var(--font-display)",
                fontSize: 44,
                lineHeight: 1,
                color: "var(--grey-700)",
              }}
            >
              —
            </span>
            <Term size={17} color="var(--arcade-yellow)">
              there is no continue. the coin was tonight&apos;s.
            </Term>
            <Term>next window opens tomorrow 20:00. the gateway is closed until then.</Term>
          </div>

          <Term color="var(--phos-500)">
            two positions were flattened for you. nothing is open.
          </Term>
        </div>

        <aside
          style={{
            borderLeft: "1px solid var(--arcade-red-dim)",
            background: "rgba(8,12,8,.94)",
            display: "grid",
            gridTemplateRows: "auto 1fr auto",
            minHeight: 0,
          }}
        >
          <div
            style={{
              padding: "16px 20px",
              borderBottom: "1px solid var(--line-hairline)",
              display: "grid",
              gap: 8,
            }}
          >
            <Caps color="var(--arcade-red)">Where it went</Caps>
            {overRows.map((row) => (
              <div
                key={row.time}
                style={{
                  display: "grid",
                  gridTemplateColumns: "52px 1fr 64px",
                  gap: 10,
                  alignItems: "center",
                  padding: "8px 0",
                  borderBottom: "1px solid var(--line-hairline)",
                }}
              >
                <span
                  style={{
                    fontFamily: "var(--font-data)",
                    fontSize: 11,
                    color: "var(--text-muted)",
                  }}
                >
                  {row.time}
                </span>
                <span
                  style={{
                    fontFamily: "var(--font-data)",
                    fontSize: 12,
                    color: "var(--text-secondary)",
                  }}
                >
                  {row.what}
                </span>
                <span
                  style={{
                    fontFamily: "var(--font-data)",
                    fontSize: 12,
                    fontWeight: 700,
                    textAlign: "right",
                    fontVariantNumeric: "tabular-nums",
                    color: rColor(row.r),
                  }}
                >
                  {row.r}
                </span>
              </div>
            ))}
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
            <Caps color="var(--status-agent)">risk-warden · closing statement</Caps>
            <Term color="var(--status-agent)">
              three of the last four fills were inside 90 seconds of each other.
            </Term>
            <Term color="var(--status-agent)">
              sizes went 0.20 → 0.30 → 0.50 while the thesis stayed the same.
            </Term>
            <Term color="var(--status-agent)">i blocked the fifth. it would have been 0.80.</Term>
            <Term color="var(--status-agent)">
              same pattern cost you -7.20R across four sessions.
            </Term>
          </div>

          <div
            style={{
              borderTop: "1px solid var(--line-strong)",
              padding: "16px 20px",
              display: "grid",
              gap: 10,
            }}
          >
            <Caps color="var(--phos-500)">Before you close the app</Caps>
            <div
              style={{
                padding: 12,
                background: "var(--surface-well)",
                boxShadow: "var(--inset-well)",
                fontSize: 13,
                lineHeight: 1.5,
                color: "var(--text-body)",
                minHeight: 64,
              }}
            >
              Write one line about the third entry. Not an excuse — what you saw.
            </div>
            <Button variant="ghost" size="sm" fullWidth>
              Write and lock
            </Button>
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
          borderTop: "1px solid var(--arcade-red-dim)",
        }}
      >
        <PadHint button="a" label="Write note" />
        <PadHint button="RT" label="Fire · disabled" dim />
        <PadHint button="VIEW" label="Back to cabinet" />
        <span
          style={{
            marginLeft: "auto",
            fontFamily: "var(--font-terminal)",
            fontSize: 15,
            color: "var(--phos-600)",
          }}
        >
          &gt; the cap did its job. that is the whole point of writing it early.
        </span>
      </div>
    </Artboard>
  );
}
