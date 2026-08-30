import { Artboard, Caps, ScreenFooter, ScreenHeader, Term } from "../components/primitives";
import { Badge, Button, GamepadKey, MeterBar } from "../ds";

/**
 * Gamepad — the prototype's `is_pad` artboard.
 *
 * The two safety pairs are drawn locked and stay that way: LT+RT to send, and
 * LB+RB to flatten. Everything else rebinds.
 */

const BINDINGS = [
  { key: "a", size: "sm" as const, action: "Close selected position", context: "session" },
  { key: "b", size: "sm" as const, action: "Cancel arm · counts as a stand-down", context: "armed" },
  {
    key: "x",
    size: "sm" as const,
    action: "Open replay",
    context: "journal",
    /** mid-rebind: this row is waiting for a key press */
    listening: true,
  },
  { key: "y", size: "sm" as const, action: "Ask the desk · record memo", context: "any" },
  { key: "START", size: "sm" as const, action: "Safe menu · cancels the arm on open", context: "any" },
  { key: "VIEW", size: "sm" as const, action: "Lock · unlock the session", context: "any" },
];

const CONNECTION = [
  { label: "Transport", value: "2.4G dongle", dim: false },
  { label: "Fallback", value: "USB cable", dim: false },
  { label: "Bluetooth", value: "unsupported on this OS", dim: true },
];

const BIND_COLUMNS = "44px 1fr 110px 90px";

export function GamepadScreen() {
  return (
    <Artboard
      label="Gamepad"
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
        title="Gamepad"
        right={
          <Button variant="ghost" size="sm">
            Reset defaults
          </Button>
        }
      >
        <Badge tone="live" dot>
          8BitDo · dongle
        </Badge>
        <span
          style={{
            fontFamily: "var(--font-data)",
            fontSize: 10,
            letterSpacing: ".12em",
            color: "var(--text-muted)",
          }}
        >
          poll 8 ms · battery 74% · rumble ok
        </span>
      </ScreenHeader>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 460px",
          gap: 1,
          background: "var(--line-hairline)",
          minHeight: 0,
        }}
      >
        {/* bindings */}
        <div
          style={{
            background: "var(--black-2)",
            padding: "18px 20px",
            display: "grid",
            gap: 14,
            alignContent: "start",
            minHeight: 0,
            overflow: "hidden",
          }}
        >
          <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
            <Caps size={10} weight={700} color="var(--arcade-red)">
              Safety pairs · locked
            </Caps>
            <Caps color="var(--text-muted)">Not rebindable by design</Caps>
          </div>

          <div style={{ display: "grid", gap: 10 }}>
            {[
              { a: "LT", b: "RT", label: "Send order · apply protection edit" },
              { a: "LB", b: "RB", label: "Emergency flatten · works without the HUD" },
            ].map((pair) => (
              <div
                key={pair.label}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 14,
                  padding: 12,
                  border: "1px solid var(--arcade-red-dim)",
                  background: "rgba(232,32,42,.06)",
                }}
              >
                <GamepadKey button={pair.a} size="md" />
                <span style={{ color: "var(--text-disabled)" }}>+</span>
                <GamepadKey button={pair.b} size="md" />
                <span
                  style={{
                    flex: 1,
                    fontSize: 12,
                    fontWeight: 700,
                    letterSpacing: ".12em",
                    textTransform: "uppercase",
                  }}
                >
                  {pair.label}
                </span>
                <Badge tone="down">Locked</Badge>
              </div>
            ))}
          </div>

          <div style={{ height: 1, background: "var(--line-hairline)", margin: "4px 0" }} />
          <Caps size={10} weight={700} color="var(--phos-300)">
            Rebindable
          </Caps>

          <div style={{ display: "grid", gap: 8 }}>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: BIND_COLUMNS,
                gap: 12,
                alignItems: "center",
                fontSize: 9,
                letterSpacing: ".18em",
                textTransform: "uppercase",
                color: "var(--text-disabled)",
              }}
            >
              <span>Key</span>
              <span>Action</span>
              <span>Context</span>
              <span />
            </div>

            {BINDINGS.map((row, i) => {
              const last = i === BINDINGS.length - 1;
              return (
                <div
                  key={row.action}
                  style={{
                    display: "grid",
                    gridTemplateColumns: BIND_COLUMNS,
                    gap: 12,
                    alignItems: "center",
                    padding: "8px 0",
                    borderBottom: last ? undefined : "1px solid var(--line-hairline)",
                    background: row.listening ? "rgba(255,212,0,.06)" : undefined,
                  }}
                >
                  <GamepadKey button={row.key} size={row.size} />
                  <span style={{ fontSize: 12 }}>{row.action}</span>
                  <span
                    style={{
                      fontFamily: "var(--font-data)",
                      fontSize: 10,
                      color: row.listening ? "var(--arcade-yellow)" : "var(--text-muted)",
                    }}
                  >
                    {row.context}
                  </span>
                  <Button variant={row.listening ? "secondary" : "ghost"} size="sm">
                    {row.listening ? "Listening" : "Rebind"}
                  </Button>
                </div>
              );
            })}
          </div>

          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 12,
              padding: 12,
              border: "1px solid rgba(255,212,0,.4)",
              background: "rgba(255,212,0,.06)",
            }}
          >
            <Caps size={11} weight={700} color="var(--arcade-yellow)">
              Conflict
            </Caps>
            <Term>
              X is already open replay in journal. press another key, or confirm to move replay to
              LB.
            </Term>
          </div>
        </div>

        {/* live pad test */}
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
            Live pad test
          </Caps>
          <Term>press anything — nothing here reaches the broker.</Term>

          <div
            style={{
              display: "grid",
              gap: 14,
              padding: 16,
              background: "var(--black-3)",
              border: "1px solid var(--line-hairline)",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <div style={{ display: "flex", gap: 8 }}>
                <GamepadKey button="LB" size="md" />
                <GamepadKey button="LT" size="md" pressed />
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                <GamepadKey button="RT" size="md" />
                <GamepadKey button="RB" size="md" />
              </div>
            </div>

            <div
              style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}
            >
              {/* d-pad */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(3,22px)",
                  gap: 4,
                  justifyItems: "center",
                }}
              >
                <span />
                <GamepadKey button="up" size="sm" />
                <span />
                <GamepadKey button="left" size="sm" />
                <span />
                <GamepadKey button="right" size="sm" />
                <span />
                <GamepadKey button="down" size="sm" />
                <span />
              </div>
              {/* face buttons */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(3,26px)",
                  gap: 4,
                  justifyItems: "center",
                }}
              >
                <span />
                <GamepadKey button="y" size="sm" />
                <span />
                <GamepadKey button="x" size="sm" pressed />
                <span />
                <GamepadKey button="b" size="sm" />
                <span />
                <GamepadKey button="a" size="sm" />
                <span />
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              <div style={{ display: "grid", gap: 6 }}>
                <Caps color="var(--text-muted)">Left stick</Caps>
                <MeterBar value={34} max={100} segments={10} tone="info" />
                <span
                  style={{
                    fontFamily: "var(--font-data)",
                    fontSize: 10,
                    color: "var(--text-muted)",
                  }}
                >
                  x -0.34 · y 0.02 · deadzone 0.12
                </span>
              </div>
              <div style={{ display: "grid", gap: 6 }}>
                <Caps color="var(--text-muted)">Right stick</Caps>
                <MeterBar value={0} max={100} segments={10} tone="info" />
                <span
                  style={{
                    fontFamily: "var(--font-data)",
                    fontSize: 10,
                    color: "var(--text-muted)",
                  }}
                >
                  centred · drift 0.00
                </span>
              </div>
            </div>

            <Term color="var(--phos-500)">sticks change previews only. they can never submit.</Term>
          </div>

          <div style={{ display: "grid", gap: 10 }}>
            <Caps>Connection</Caps>
            {CONNECTION.map((row) => (
              <div
                key={row.label}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  fontFamily: "var(--font-data)",
                  fontSize: 11,
                  color: row.dim ? "var(--text-disabled)" : "var(--text-secondary)",
                }}
              >
                <Caps size={10} color="var(--text-muted)">
                  {row.label}
                </Caps>
                {row.value}
              </div>
            ))}
            <Term color="var(--grey-500)">
              lose the pad mid-session and the arm cancels instantly. the on-screen flatten stays.
            </Term>
          </div>
        </div>
      </div>

      <ScreenFooter>
        <GamepadKey button="b" size="sm" label="Back" />
        <Caps size={10} color="var(--text-muted)">
          Changes apply immediately · no order can be sent from this screen
        </Caps>
      </ScreenFooter>
    </Artboard>
  );
}
