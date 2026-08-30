import { Artboard, Caps, ScreenFooter, ScreenHeader, Term } from "../components/primitives";
import { Badge, Button, GamepadKey, Input, MeterBar } from "../ds";

/**
 * Size calculator — the prototype's `is_calc` artboard.
 *
 * The point of the screen is the pair of numbers: what the maths asks for, and
 * what the broker's step will actually accept. It can only stage a preview.
 */

const SAVED = [
  "capital and the time it was read",
  "risk level, instrument, entry, stop",
  "requested size and rounded size",
  "real money risk and the limits in force",
  "price at the moment of calculation",
];

const rowStyle = {
  display: "flex",
  justifyContent: "space-between",
  fontFamily: "var(--font-data)",
  fontSize: 11,
  color: "var(--text-secondary)",
} as const;

export function SizeCalculatorScreen() {
  return (
    <Artboard
      label="Size calculator"
      frameStyle={{
        width: 1440,
        height: 860,
        display: "grid",
        gridTemplateRows: "44px 34px 1fr 44px",
        background: "var(--surface-app)",
        border: "1px solid var(--line-hairline)",
      }}
    >
      <ScreenHeader title="Size calculator" meta="Session 042 · 21:18">
        <Badge tone="warn" dot>
          Opens locked
        </Badge>
      </ScreenHeader>

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
          Staging only
        </Caps>
        <Term>
          applying here writes a preview onto the HUD. it still takes LT+RT on the main screen to
          reach the broker.
        </Term>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "420px 1fr 340px",
          gap: 1,
          background: "var(--line-hairline)",
          minHeight: 0,
        }}
      >
        {/* inputs */}
        <div
          style={{
            background: "var(--black-2)",
            padding: "18px 20px",
            display: "grid",
            gap: 14,
            alignContent: "start",
          }}
        >
          <Caps size={10} weight={700} color="var(--phos-300)">
            Inputs
          </Caps>

          <div
            style={{
              display: "grid",
              gap: 6,
              padding: 12,
              background: "var(--black-3)",
              border: "1px solid var(--line-hairline)",
            }}
          >
            <div
              style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}
            >
              <Caps size={9} color="var(--text-muted)">
                Capital in use
              </Caps>
              <span style={{ fontFamily: "var(--font-data)", fontSize: 16, fontWeight: 700 }}>
                10 000.00
              </span>
            </div>
            <span
              style={{ fontFamily: "var(--font-data)", fontSize: 10, color: "var(--text-disabled)" }}
            >
              read from the broker at 21:17:52
            </span>
          </div>

          <Input
            label="Risk per trade"
            value="1.0"
            suffix="%"
            align="right"
            hint="100.00 of capital"
          />
          <Input label="Instrument" value="XAUUSD" />
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <Input label="Entry" value="2461.38" align="right" />
            <Input label="Stop" value="2455.60" align="right" />
          </div>

          <div style={{ ...rowStyle, paddingTop: 4, borderTop: "1px solid var(--line-hairline)" }}>
            <Caps size={10} color="var(--text-muted)">
              Stop distance
            </Caps>
            5.78 · 578 points
          </div>
          <div style={rowStyle}>
            <Caps size={10} color="var(--text-muted)">
              Price at calculation
            </Caps>
            2461.38 · 21:18:04
          </div>
        </div>

        {/* result */}
        <div
          style={{
            background: "var(--black-2)",
            padding: "18px 20px",
            display: "grid",
            gap: 16,
            alignContent: "start",
          }}
        >
          <Caps size={10} weight={700} color="var(--phos-300)">
            Result
          </Caps>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: 1,
              background: "var(--line-hairline)",
            }}
          >
            <div
              style={{ background: "var(--surface-well)", padding: 14, display: "grid", gap: 6 }}
            >
              <Caps color="var(--text-muted)">Requested</Caps>
              <span
                style={{
                  fontFamily: "var(--font-data)",
                  fontSize: 26,
                  fontWeight: 700,
                  color: "var(--text-body)",
                }}
              >
                0.173
              </span>
              <span
                style={{ fontFamily: "var(--font-data)", fontSize: 10, color: "var(--text-muted)" }}
              >
                lots · exact maths
              </span>
            </div>
            <div
              style={{ background: "var(--surface-well)", padding: 14, display: "grid", gap: 6 }}
            >
              <Caps color="var(--phos-300)">Rounded to broker step</Caps>
              <span
                style={{
                  fontFamily: "var(--font-data)",
                  fontSize: 26,
                  fontWeight: 700,
                  color: "var(--phos-400)",
                  textShadow: "var(--glow-text)",
                }}
              >
                0.17
              </span>
              <span
                style={{ fontFamily: "var(--font-data)", fontSize: 10, color: "var(--text-muted)" }}
              >
                step 0.01 · minimum 0.01
              </span>
            </div>
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
            <div style={{ ...rowStyle, fontSize: 12 }}>
              <Caps size={10} color="var(--text-muted)">
                Real risk at 0.17
              </Caps>
              <span>98.26 · 0.98%</span>
            </div>
            <div style={{ ...rowStyle, fontSize: 12 }}>
              <Caps size={10} color="var(--text-muted)">
                In risk units
              </Caps>
              <span style={{ color: "var(--arcade-red)" }}>-1.00R</span>
            </div>
            <Term>
              rounding down costs you 1.74 of intended risk. the number shown is the one that will
              actually be sent.
            </Term>
          </div>

          <div
            style={{
              display: "grid",
              gap: 10,
              padding: 14,
              border: "1px solid var(--line-strong)",
              background: "var(--phos-a08)",
            }}
          >
            <Caps size={10} weight={700} color="var(--phos-300)">
              Against your limits
            </Caps>
            <MeterBar label="Max size 0.50" value={17} max={50} segments={10} showValue />
            <MeterBar
              label="Loss cap after a stop"
              value={21}
              max={30}
              segments={10}
              tone="warn"
              showValue
            />
            <Term color="var(--phos-500)">
              inside every declared limit. positions would go 2 of 2 — you would have to close one
              first.
            </Term>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <Button variant="primary" size="md">
              Stage on the HUD
            </Button>
            <Button variant="ghost" size="md">
              Discard
            </Button>
            <Caps size={10} color="var(--text-muted)" style={{ marginLeft: "auto" }}>
              Nothing is sent from here
            </Caps>
          </div>
        </div>

        {/* what gets kept */}
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
          <Caps size={10} weight={700} color="var(--phos-300)">
            Saved with the trade
          </Caps>
          <div
            style={{
              display: "grid",
              gap: 8,
              padding: 14,
              background: "var(--black-3)",
              border: "1px solid var(--line-hairline)",
            }}
          >
            {SAVED.map((line) => (
              <Term key={line}>{line}</Term>
            ))}
          </div>
          <span
            style={{
              fontSize: 14,
              lineHeight: 1.5,
              color: "var(--text-secondary)",
              maxWidth: "64ch",
            }}
          >
            Every one of those is kept so that months later you can see what you knew when you sized
            the trade, not just what you sized it to.
          </span>
          <div
            style={{
              display: "grid",
              gap: 8,
              padding: 14,
              border: "1px solid rgba(255,212,0,.4)",
              background: "rgba(255,212,0,.06)",
            }}
          >
            <Caps color="var(--arcade-yellow)">If the stop is invalid</Caps>
            <Term>
              wrong side of price, or too close, is blocked at the preview with the reason — before
              it can ever be confirmed.
            </Term>
          </div>
        </div>
      </div>

      <ScreenFooter>
        <GamepadKey button="b" size="sm" label="Back to session" />
        <Caps size={10} color="var(--text-muted)">
          Confirm the staged preview with LT+RT on the main screen
        </Caps>
      </ScreenFooter>
    </Artboard>
  );
}
