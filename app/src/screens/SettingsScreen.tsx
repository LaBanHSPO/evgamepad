import { Artboard, Caps, ScreenFooter, ScreenHeader, Term } from "../components/primitives";
import { Badge, Button, GamepadKey, Input, MeterBar, Switch, Tag } from "../ds";

/**
 * Settings — the prototype's `is_settings` artboard.
 *
 * Only safe preferences live here. The safety catches are named in the
 * "not in this interface" panel rather than shown as controls that might
 * look editable.
 */

const TIMEFRAMES = [
  { name: "M1", on: true },
  { name: "M5", on: true },
  { name: "M15", on: true },
  { name: "H1", on: false },
  { name: "H4", on: false },
];

const NOT_HERE = [
  "demo / live mode",
  "broker credentials",
  "gateway bind address",
  "AI tool permissions",
  "process-score axis weights",
];

const ACCOUNT = [
  { label: "cTrader demo", value: "#4028119" },
  { label: "gateway", value: "connected · 12 ms" },
];

const panel = {
  background: "var(--black-2)",
  padding: "18px 20px",
  display: "grid",
  gap: 16,
  alignContent: "start",
  minHeight: 0,
  overflow: "hidden",
} as const;

/** A switch with its explanatory label, the shape this screen repeats. */
function Toggle({ checked, children }: { checked: boolean; children: string }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 10,
        fontSize: 12,
        color: "var(--text-secondary)",
      }}
    >
      <Switch checked={checked} />
      <span>{children}</span>
    </div>
  );
}

export function SettingsScreen() {
  return (
    <Artboard
      label="Settings"
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
        title="Settings"
        meta="Changes apply immediately"
        right={<Badge tone="info">Demo account · read-only identity</Badge>}
      />

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr 380px",
          gap: 1,
          background: "var(--line-hairline)",
          minHeight: 0,
        }}
      >
        {/* session */}
        <div style={panel}>
          <Caps size={10} weight={700} color="var(--phos-300)">
            Session
          </Caps>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <Input label="Evening starts" value="20:00" align="right" />
            <Input label="Evening ends" value="23:00" align="right" />
          </div>
          <Input label="Timezone" value="Asia/Ho_Chi_Minh" />

          <div style={{ display: "grid", gap: 8 }}>
            <Caps>Instruments · from the server&apos;s allowed list</Caps>
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
              {["xauusd", "eurusd", "gbpusd", "usdjpy"].map((s) => (
                <Tag key={s}>{s}</Tag>
              ))}
            </div>
            <Term color="var(--grey-500)">
              a symbol outside the allowed list is refused with the reason.
            </Term>
          </div>

          <div style={{ display: "grid", gap: 8 }}>
            <Caps>Chart timeframes</Caps>
            <div style={{ display: "flex", gap: 4 }}>
              {TIMEFRAMES.map((tf) => (
                <span
                  key={tf.name}
                  style={{
                    flex: 1,
                    textAlign: "center",
                    padding: "6px 0",
                    fontSize: 10,
                    color: tf.on ? "var(--phos-300)" : "var(--text-muted)",
                    border: `1px solid ${tf.on ? "var(--line-strong)" : "var(--line-neutral)"}`,
                    background: tf.on ? "var(--phos-a08)" : undefined,
                  }}
                >
                  {tf.name}
                </span>
              ))}
            </div>
          </div>

          <div
            style={{
              display: "grid",
              gap: 10,
              padding: 12,
              background: "var(--black-3)",
              border: "1px solid var(--line-hairline)",
            }}
          >
            <Caps>Report defaults</Caps>
            <Toggle checked>open on the process cover</Toggle>
            <Term color="var(--arcade-yellow)">
              the outcome appendix is not listed here on purpose. it starts off every time you build
              a report.
            </Term>
          </div>
        </div>

        {/* pad, voice, storage */}
        <div style={panel}>
          <Caps size={10} weight={700} color="var(--phos-300)">
            Pad, voice, storage
          </Caps>

          <div
            style={{
              display: "grid",
              gap: 12,
              padding: 14,
              background: "var(--black-3)",
              border: "1px solid var(--line-hairline)",
            }}
          >
            <Toggle checked>rumble on fills and rejections</Toggle>
            <MeterBar
              label="Stick deadzone"
              value={12}
              max={30}
              segments={10}
              showValue
              tone="info"
            />
            <Toggle checked>hold to talk · bound to LB</Toggle>
            <Input label="Microphone" value="Yeti Nano · USB" />
            <Toggle checked={false}>read coach lines aloud</Toggle>
          </div>

          <div
            style={{
              display: "grid",
              gap: 10,
              padding: 14,
              border: "1px solid rgba(255,212,0,.4)",
              background: "rgba(255,212,0,.06)",
            }}
          >
            <Caps color="var(--arcade-yellow)">Storage</Caps>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                fontFamily: "var(--font-data)",
                fontSize: 11,
                color: "var(--text-secondary)",
              }}
            >
              <span>free space</span>
              <span>41.2 GB · ~20 sessions</span>
            </div>
            <Toggle checked={false}>auto-delete old entries — off, and staying off</Toggle>
            <Term>
              the journal is kept indefinitely. retention is unresolved in the docs, so nothing
              deletes itself.
            </Term>
          </div>

          <div style={{ display: "grid", gap: 8 }}>
            <Caps>Edited elsewhere · one editor each</Caps>
            {["Playbook rules", "Philosophy and principles"].map((label) => (
              <div
                key={label}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  padding: 10,
                  background: "var(--black-3)",
                  border: "1px solid var(--line-hairline)",
                }}
              >
                <span style={{ flex: 1, fontSize: 12 }}>{label}</span>
                <Button variant="ghost" size="sm">
                  Open
                </Button>
              </div>
            ))}
          </div>
        </div>

        {/* what is deliberately absent */}
        <div style={panel}>
          <Caps size={10} weight={700} color="var(--arcade-red)">
            Not in this interface
          </Caps>
          <div
            style={{
              display: "grid",
              gap: 10,
              padding: 14,
              border: "1px solid var(--arcade-red-dim)",
              background: "rgba(232,32,42,.06)",
            }}
          >
            <span style={{ fontSize: 14, lineHeight: 1.5, maxWidth: "64ch" }}>
              These live outside the database. If one is wrong the product refuses to start, which
              is why there is no control for them here — not even a read-only one that might look
              editable.
            </span>
            <div style={{ display: "grid", gap: 6 }}>
              {NOT_HERE.map((item) => (
                <Term key={item}>{item}</Term>
              ))}
            </div>
          </div>

          <div style={{ display: "grid", gap: 10 }}>
            <Caps>Account</Caps>
            <div
              style={{
                display: "grid",
                gap: 6,
                padding: 14,
                background: "var(--black-3)",
                border: "1px solid var(--line-hairline)",
              }}
            >
              {ACCOUNT.map((row) => (
                <div
                  key={row.label}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    fontFamily: "var(--font-data)",
                    fontSize: 11,
                    color: "var(--text-secondary)",
                  }}
                >
                  <span>{row.label}</span>
                  <span>{row.value}</span>
                </div>
              ))}
              <Term color="var(--grey-500)">read-only. no second account can be added.</Term>
            </div>
          </div>

          <div style={{ display: "grid", gap: 10 }}>
            <Caps>No import exists</Caps>
            <Term>
              no cTrader history, no MT5, no CSV. every row in your journal is something you did
              with the pad.
            </Term>
          </div>
        </div>
      </div>

      <ScreenFooter>
        <GamepadKey button="b" size="sm" label="Back to session" />
        <Caps size={10} color="var(--text-muted)">
          A refused change keeps the old value and says why
        </Caps>
      </ScreenFooter>
    </Artboard>
  );
}
