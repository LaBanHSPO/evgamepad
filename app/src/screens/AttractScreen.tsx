import { BgmControl } from "../components/bgm";
import { CodeRain } from "../components/CodeRain";
import { Artboard, Caps, DemoNotice, PadHint, Term } from "../components/primitives";
import { hiScores, rColor } from "../data/arcade";
import { MATRIX_ART } from "./art";

/** Attract screen · cabinet idle — the prototype's `is_title` artboard. */
export function AttractScreen() {
  return (
    <Artboard
      label="Attract screen · cabinet idle"
      frameStyle={{
        width: 1440,
        height: 810,
        position: "relative",
        background: `#040604 url('${MATRIX_ART}') center/cover no-repeat`,
        border: "1px solid var(--line-strong)",
        boxShadow: "var(--glow-md)",
      }}
    >
      <div style={{ position: "absolute", inset: 0, background: "rgba(4,6,4,.62)" }} />
      <CodeRain opacity={0.3} fontSize={16} />
      <div style={{ position: "absolute", inset: 0, background: "var(--veil-vignette)" }} />
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage: "var(--veil-scanline)",
          opacity: 0.5,
          pointerEvents: "none",
        }}
      />

      {/* cabinet status strip */}
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: 0,
          height: 34,
          display: "flex",
          alignItems: "center",
          gap: 20,
          padding: "0 20px",
          background: "rgba(4,6,4,.86)",
          borderBottom: "1px solid var(--line-hairline)",
        }}
      >
        <Caps color="var(--phos-500)">Cabinet idle · no session open</Caps>
        <span
          style={{
            fontFamily: "var(--font-data)",
            fontSize: 10,
            letterSpacing: ".12em",
            color: "var(--text-muted)",
          }}
        >
          2026-08-30 · 19:44 · broker feed live
        </span>
        <Caps style={{ marginLeft: "auto" }}>Window opens 20:00</Caps>
      </div>

      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: 34,
          bottom: 56,
          display: "grid",
          gridTemplateColumns: "1fr 380px",
        }}
      >
        {/* wordmark + coin slot */}
        <div
          style={{
            display: "grid",
            alignContent: "center",
            justifyItems: "center",
            gap: 26,
            padding: "0 40px",
            textAlign: "center",
          }}
        >
          <div style={{ display: "grid", gap: 14, justifyItems: "center" }}>
            <span
              style={{
                fontFamily: "var(--font-display)",
                fontSize: 52,
                lineHeight: 1,
                color: "var(--phos-400)",
                textShadow: "var(--glow-text)",
              }}
            >
              EV
              <span style={{ color: "var(--arcade-red)", textShadow: "2px 2px 0 #000" }}>
                GAMEPAD
              </span>
            </span>
            <Caps size={11} weight={700} color="var(--text-secondary)">
              A trading journal you drive with a pad
            </Caps>
          </div>
          <div
            style={{
              width: 220,
              height: 1,
              background: "var(--line-strong)",
              boxShadow: "var(--glow-xs)",
            }}
          />
          <span
            style={{
              fontFamily: "var(--font-display)",
              fontSize: 18,
              color: "var(--arcade-yellow)",
              textShadow: "2px 2px 0 #000",
              animation: "ev-blink 1s steps(1,end) infinite",
            }}
          >
            INSERT COIN
          </span>
          <div
            style={{
              display: "grid",
              gap: 10,
              justifyItems: "start",
              padding: "18px 26px",
              background: "rgba(8,12,8,.9)",
              border: "1px solid var(--line-strong)",
              boxShadow: "var(--sprite-shadow-lg)",
            }}
          >
            {[
              { key: "1 PLAYER", copy: "you, the pad and your rule set.", dim: false },
              { key: "2 PLAYER", copy: "the agent desk reads every fill with you.", dim: false },
              { key: "REBIND", copy: "14 bindings mapped · pad connected", dim: true },
            ].map((row) => (
              <div key={row.key} style={{ display: "flex", alignItems: "center", gap: 14 }}>
                <span
                  style={{
                    fontFamily: "var(--font-display)",
                    fontSize: 12,
                    color: row.dim ? "var(--text-disabled)" : "var(--phos-300)",
                  }}
                >
                  {row.key}
                </span>
                <Term color={row.dim ? "var(--grey-500)" : "var(--grey-300)"}>{row.copy}</Term>
              </div>
            ))}
          </div>
          <Term color="var(--phos-500)">the coin is the session. one per night.</Term>
        </div>

        {/* hi-score board */}
        <aside
          style={{
            borderLeft: "1px solid var(--line-strong)",
            background: "rgba(8,12,8,.92)",
            display: "grid",
            gridTemplateRows: "auto 1fr auto",
            minHeight: 0,
          }}
        >
          <div
            style={{
              padding: "16px 18px",
              borderBottom: "1px solid var(--line-hairline)",
              display: "grid",
              gap: 6,
              justifyItems: "center",
            }}
          >
            <span
              style={{
                fontFamily: "var(--font-display)",
                fontSize: 12,
                color: "var(--arcade-yellow)",
                textShadow: "2px 2px 0 #000",
              }}
            >
              HI-SCORE
            </span>
            <Caps>Stand-downs, not profit</Caps>
          </div>
          <div style={{ padding: "14px 18px", display: "grid", gap: 2, alignContent: "start" }}>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "26px 1fr 58px 58px",
                gap: 8,
                padding: "0 2px 8px",
                fontSize: 9,
                letterSpacing: ".18em",
                textTransform: "uppercase",
                color: "var(--text-disabled)",
              }}
            >
              <span>#</span>
              <span>Session</span>
              <span style={{ textAlign: "right" }}>Score</span>
              <span style={{ textAlign: "right" }}>Result</span>
            </div>
            {hiScores.map((row, i) => {
              const top = i === 0;
              return (
                <div
                  key={row.rank}
                  style={{
                    display: "grid",
                    gridTemplateColumns: "26px 1fr 58px 58px",
                    gap: 8,
                    alignItems: "center",
                    height: 30,
                    paddingRight: 2,
                    paddingLeft: top ? 8 : 2,
                    borderLeft: top ? "2px solid var(--phos-400)" : 0,
                    background: top ? "var(--phos-a08)" : "transparent",
                    borderBottom: "1px solid var(--line-hairline)",
                  }}
                >
                  <span
                    style={{
                      fontFamily: "var(--font-display)",
                      fontSize: 10,
                      color: "var(--text-muted)",
                    }}
                  >
                    {row.rank}
                  </span>
                  <span
                    style={{
                      fontFamily: "var(--font-data)",
                      fontSize: 12,
                      color: "var(--text-secondary)",
                    }}
                  >
                    {row.name}
                  </span>
                  <span
                    style={{
                      fontFamily: "var(--font-data)",
                      fontSize: 12,
                      fontWeight: 700,
                      textAlign: "right",
                      color: "var(--phos-300)",
                      fontVariantNumeric: "tabular-nums",
                    }}
                  >
                    {row.score}
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
              );
            })}
          </div>
          <div
            style={{
              borderTop: "1px solid var(--line-hairline)",
              padding: "14px 18px",
              display: "grid",
              gap: 8,
              background: "rgba(4,6,4,.7)",
              backgroundImage: "var(--veil-scanline)",
            }}
          >
            <Caps color="var(--phos-500)">Attract log</Caps>
            <Term color="var(--phos-500)">43 sessions logged · 512 fills</Term>
            <Term color="var(--status-agent)">risk-warden idle. it wakes with the window.</Term>
          </div>
        </aside>
      </div>

      {/* footer */}
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
        <PadHint button="START" label="Open session" />
        <PadHint button="y" label="Read last review" />
        <PadHint button="VIEW" label="Rebind" />
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 12,
            padding: "6px 12px",
            border: "1px solid var(--line-hairline)",
          }}
        >
          <BgmControl showTrack grouped />
        </div>
        <DemoNotice />
      </div>
    </Artboard>
  );
}
