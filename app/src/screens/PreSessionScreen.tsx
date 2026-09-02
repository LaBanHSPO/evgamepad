import { Artboard, Caps, DemoNotice, Term } from "../components/primitives";
import { Badge, Checkbox, GamepadKey, Input, Tag } from "../ds";

/** Pre-session · before you unlock — the prototype's `is_pre` artboard. */

const READINESS = [
  { label: "Slept enough to sit still for three hours", checked: true },
  { label: "Read tonight's event list", checked: true },
  { label: "Pad, dongle and Chrome focus checked", checked: true },
  {
    label: "Not here to win back yesterday",
    checked: false,
    description: "left blank — noted, not judged",
  },
  { label: "Plan written before the first chart", checked: true },
];

const panel = {
  background: "var(--black-2)",
  padding: "18px 20px",
  display: "grid",
  alignContent: "start",
  minHeight: 0,
} as const;

export function PreSessionScreen() {
  return (
    <Artboard
      label="Pre-session"
      frameStyle={{
        width: 1440,
        height: 860,
        display: "grid",
        gridTemplateRows: "44px auto 1fr 44px",
        background: "var(--surface-app)",
        border: "1px solid var(--line-hairline)",
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
          Before you unlock
        </Caps>
        <span
          style={{
            fontFamily: "var(--font-data)",
            fontSize: 10,
            letterSpacing: ".12em",
            color: "var(--text-muted)",
          }}
        >
          Session 043 · 2026-08-30 · 19:52
        </span>
        <Badge tone="info" dot>
          Broker ready
        </Badge>
        <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 12 }}>
          <Caps size={10} color="var(--text-muted)">
            Demo account · XAUUSD feed live
          </Caps>
        </div>
      </header>

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 12,
          height: 34,
          padding: "0 16px",
          background: "var(--phos-a08)",
          borderBottom: "1px solid var(--line-hairline)",
        }}
      >
        <Caps size={11} weight={700} color="var(--phos-300)">
          Tightening applies now · loosening applies next session
        </Caps>
        <Term>you are writing these while you are still calm. that is the whole trick.</Term>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "400px 400px 1fr",
          gap: 1,
          background: "var(--line-hairline)",
          minHeight: 0,
        }}
      >
        {/* enforced limits */}
        <div style={{ ...panel, gap: 16 }}>
          <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
            <Caps size={10} weight={700} color="var(--phos-300)">
              Session limits
            </Caps>
            <Badge tone="live">Enforced</Badge>
          </div>
          <Term>the gateway refuses anything past these. it does not ask twice.</Term>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <Input label="Window opens" value="20:00" align="right" />
            <Input label="Window closes" value="23:00" align="right" />
          </div>
          <Input
            label="Max size per position"
            value="0.50"
            suffix="lots"
            align="right"
            hint="broker step 0.01 · minimum 0.01"
          />
          <Input label="Max open positions" value="2" align="right" />
          <Input
            label="Max session loss"
            value="-3.00"
            suffix="R"
            align="right"
            hint="at -3.00R the session goes close-only"
          />
          <div style={{ height: 1, background: "var(--line-hairline)" }} />
          <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
            <Caps size={10} weight={700} color="var(--arcade-yellow)">
              News guard
            </Caps>
            <Badge tone="warn">Advisory</Badge>
          </div>
          <Input
            label="Warn before an event"
            value="15"
            suffix="min"
            align="right"
            hint="warns, never refuses — the call stays yours"
          />
        </div>

        {/* readiness */}
        <div style={{ ...panel, gap: 14 }}>
          <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
            <Caps size={10} weight={700} color="var(--phos-300)">
              Readiness
            </Caps>
            <Badge tone="neutral">Advisory · never blocks</Badge>
          </div>
          <Term>leave all five blank and you can still unlock. it is a mirror, not a gate.</Term>
          <div
            style={{
              display: "grid",
              gap: 12,
              padding: 14,
              background: "var(--black-3)",
              border: "1px solid var(--line-hairline)",
            }}
          >
            {READINESS.map((row) => (
              <Checkbox
                key={row.label}
                checked={row.checked}
                label={row.label}
                description={row.description}
              />
            ))}
          </div>

          <div style={{ display: "grid", gap: 10 }}>
            <Caps>Check-in · how you feel walking in</Caps>
            <div style={{ display: "flex", gap: 6 }}>
              {[1, 2, 3, 4, 5].map((n) => {
                const on = n === 4;
                return (
                  <span
                    key={n}
                    style={{
                      flex: 1,
                      textAlign: "center",
                      padding: "10px 0",
                      fontFamily: "var(--font-data)",
                      fontSize: 16,
                      color: on ? "var(--phos-300)" : "var(--text-muted)",
                      border: `1px solid ${on ? "var(--line-strong)" : "var(--line-neutral)"}`,
                      background: on ? "var(--phos-a08)" : undefined,
                      boxShadow: on ? "var(--glow-xs)" : undefined,
                    }}
                  >
                    {n}
                  </span>
                );
              })}
              <span
                style={{
                  flex: 1.4,
                  textAlign: "center",
                  padding: "10px 0",
                  fontSize: 10,
                  letterSpacing: ".18em",
                  textTransform: "uppercase",
                  color: "var(--text-disabled)",
                  border: "1px dashed var(--grey-700)",
                }}
              >
                Skip
              </span>
            </div>
          </div>

          <div
            style={{
              display: "grid",
              gap: 8,
              padding: 14,
              background: "var(--black-3)",
              borderLeft: "2px solid var(--status-agent)",
              borderTop: "1px solid var(--line-hairline)",
              borderRight: "1px solid var(--line-hairline)",
              borderBottom: "1px solid var(--line-hairline)",
            }}
          >
            <Caps>Desk session plan · read only, kept separate from your words</Caps>
            <Term color="var(--status-agent)">
              two events tonight: 21:30 dxy prints, 23:00 asia open.
            </Term>
            <Term color="var(--status-agent)">
              tape read: range, opportunity quality normal.
            </Term>
          </div>
        </div>

        {/* the plan, in your words */}
        <div style={{ ...panel, gap: 14, overflow: "hidden" }}>
          <Caps size={10} weight={700} color="var(--phos-300)">
            Tonight&apos;s plan · your words
          </Caps>

          <div style={{ display: "grid", gap: 6 }}>
            <Caps>Thesis</Caps>
            <div
              style={{
                padding: 12,
                minHeight: 76,
                background: "var(--surface-well)",
                boxShadow: "var(--inset-well)",
                fontSize: 14,
                lineHeight: 1.5,
                color: "var(--text-body)",
              }}
            >
              Gold has held 2455 twice today. I want one buy from a retest with the London low
              intact, and nothing else. If it breaks 2455 and closes below, I am done for the night.
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <div style={{ display: "grid", gap: 6 }}>
              <Caps>Watching</Caps>
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                <Tag>xauusd</Tag>
                <Tag color="var(--arcade-cyan)">eurusd</Tag>
              </div>
            </div>
            <div style={{ display: "grid", gap: 6 }}>
              <Caps>Setups allowed</Caps>
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                <Tag>orb</Tag>
                <Tag>retest</Tag>
              </div>
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <Input label="Level that matters" value="2455.00" align="right" />
            <Input label="Invalidation" value="close below 2455" />
          </div>

          <div style={{ display: "grid", gap: 6 }}>
            <Caps>What a good night looks like</Caps>
            <div
              style={{
                padding: 12,
                background: "var(--surface-well)",
                boxShadow: "var(--inset-well)",
                fontSize: 14,
                lineHeight: 1.5,
                color: "var(--text-body)",
              }}
            >
              One trade taken by the rules, or none taken at all. Standing down on a broken thesis
              counts as a win.
            </div>
          </div>

          <Term color="var(--grey-500)">
            this text freezes at your first fill. anything added later is kept and marked as added
            later.
          </Term>
        </div>
      </div>

      <footer
        style={{
          display: "flex",
          alignItems: "center",
          gap: 16,
          padding: "0 16px",
          borderTop: "1px solid var(--line-hairline)",
          background: "var(--black-1)",
        }}
      >
        <GamepadKey button="START" size="sm" label="Lock limits · start session" />
        <GamepadKey button="b" size="sm" label="Back" />
        <DemoNotice />
      </footer>
    </Artboard>
  );
}
