import { CodeRain } from "../components/CodeRain";
import { Artboard, Caps, PadHint, Term } from "../components/primitives";
import { bootChecks, bootLines } from "../data/arcade";
import { GamepadKey, MeterBar } from "../ds";
import { useCabinet } from "../journey/Cabinet";
import { BOOT_KEYS } from "../journey/graph";
import { MATRIX_ART } from "./art";

/** Boot sequence · connecting the pad — the prototype's `is_boot` artboard. */
export function BootScreen() {
  const cabinet = useCabinet();
  const handshake = cabinet?.state.handshake ?? [];
  const handshakeCount = handshake.length;
  return (
    <Artboard
      label="Boot sequence · connecting the pad"
      frameStyle={{
        width: 1440,
        height: 810,
        position: "relative",
        background: `#040604 url('${MATRIX_ART}') center/cover no-repeat`,
        border: "1px solid var(--line-strong)",
        boxShadow: "var(--glow-md)",
      }}
    >
      <div style={{ position: "absolute", inset: 0, background: "rgba(4,6,4,.78)" }} />
      <CodeRain opacity={0.14} fontSize={15} />
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage: "var(--veil-scanline)",
          opacity: 0.6,
          pointerEvents: "none",
        }}
      />

      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: 0,
          bottom: 56,
          display: "grid",
          gridTemplateColumns: "1fr 420px",
        }}
      >
        {/* cold-start log */}
        <div
          style={{
            padding: "34px 40px",
            display: "grid",
            gap: 20,
            alignContent: "start",
            background: "rgba(4,6,4,.72)",
            minHeight: 0,
          }}
        >
          <div style={{ display: "flex", alignItems: "baseline", gap: 16 }}>
            <span
              style={{
                fontFamily: "var(--font-display)",
                fontSize: 14,
                color: "var(--phos-400)",
                textShadow: "var(--glow-text)",
              }}
            >
              EV<span style={{ color: "var(--arcade-red)" }}>GAMEPAD</span>
            </span>
            <span
              style={{
                fontFamily: "var(--font-data)",
                fontSize: 11,
                letterSpacing: ".12em",
                color: "var(--text-muted)",
              }}
            >
              v0.43 · session 044 · 19:58:02
            </span>
          </div>
          <div style={{ display: "grid", gap: 5, alignContent: "start" }}>
            {bootLines.map((line) => (
              <span
                key={line.text}
                style={{
                  fontFamily: "var(--font-terminal)",
                  fontSize: 18,
                  lineHeight: 1.35,
                  color: line.color,
                }}
              >
                {line.text}
              </span>
            ))}
            <div style={{ display: "flex", alignItems: "center", gap: 8, paddingTop: 4 }}>
              <span
                style={{
                  fontFamily: "var(--font-terminal)",
                  fontSize: 18,
                  color: "var(--phos-300)",
                }}
              >
                &gt;
              </span>
              <i
                style={{
                  display: "inline-block",
                  width: 9,
                  height: 18,
                  background: "var(--phos-400)",
                  boxShadow: "var(--glow-xs)",
                  animation: "ev-blink 1s steps(1,end) infinite",
                }}
              />
            </div>
          </div>
        </div>

        {/* pre-flight + handshake */}
        <aside
          style={{
            borderLeft: "1px solid var(--line-strong)",
            background: "rgba(8,12,8,.94)",
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
              gap: 6,
            }}
          >
            <Caps color="var(--phos-500)">Pre-flight</Caps>
            <Term>six checks. all six or no coin.</Term>
          </div>

          <div
            style={{
              padding: "14px 18px",
              borderBottom: "1px solid var(--line-hairline)",
              display: "grid",
              gap: 8,
            }}
          >
            {bootChecks.map((check) => (
              <div
                key={check.label}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  padding: "8px 10px",
                  border: "1px solid var(--line-hairline)",
                  background: "var(--black-3)",
                }}
              >
                <span
                  style={{
                    fontFamily: "var(--font-data)",
                    fontSize: 13,
                    fontWeight: 700,
                    width: 14,
                    textAlign: "center",
                    color: check.ok ? "var(--phos-400)" : "var(--arcade-yellow)",
                  }}
                >
                  {check.ok ? "✓" : "!"}
                </span>
                <Caps size={10} weight={700} color="var(--text-secondary)">
                  {check.label}
                </Caps>
                <span
                  style={{
                    marginLeft: "auto",
                    fontFamily: "var(--font-data)",
                    fontSize: 11,
                    color: check.ok ? "var(--text-muted)" : "var(--arcade-yellow)",
                  }}
                >
                  {check.value}
                </span>
              </div>
            ))}
          </div>

          <div style={{ padding: "16px 18px", display: "grid", gap: 12, alignContent: "start" }}>
            <Caps color="var(--phos-500)">Pad handshake</Caps>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              {(["LT", "RT", "a", "b", "x", "y", "START"] as const).map((key) => (
                <GamepadKey
                  key={key}
                  button={key}
                  size="md"
                  pressed={handshake.includes(key.toLowerCase())}
                />
              ))}
            </div>
            <Term color="var(--phos-500)">
              press each key once. {handshakeCount}/{BOOT_KEYS.length} read.
            </Term>
            <MeterBar
              label="Handshake"
              value={Math.min(handshakeCount, BOOT_KEYS.length)}
              max={BOOT_KEYS.length}
              segments={BOOT_KEYS.length}
              showValue
            />
          </div>

          <div
            style={{
              borderTop: "1px solid var(--line-strong)",
              padding: 18,
              display: "grid",
              gap: 10,
              justifyItems: "center",
              background: "var(--phos-a08)",
            }}
          >
            <button
              type="button"
              onClick={() => cabinet?.emit("start")}
              style={{
                fontFamily: "var(--font-display)",
                fontSize: 16,
                color: "var(--phos-400)",
                textShadow: "var(--glow-text)",
                animation: "ev-blink 1s steps(1,end) infinite",
                background: "transparent",
                border: 0,
                cursor: "pointer",
                padding: 0,
              }}
            >
              READY PLAYER ONE
            </button>
            <Term style={{ textAlign: "center" }}>
              limits load next. you write them before the first chart.
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
        <PadHint button="START" label="Write limits" />
        <PadHint button="VIEW" label="Back to cabinet" />
        <span
          style={{
            marginLeft: "auto",
            fontFamily: "var(--font-terminal)",
            fontSize: 15,
            color: "var(--phos-600)",
          }}
        >
          &gt; nothing reaches the broker until the window opens.
        </span>
      </div>
    </Artboard>
  );
}
