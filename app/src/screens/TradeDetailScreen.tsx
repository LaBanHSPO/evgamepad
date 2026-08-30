import { Artboard, Caps, ScreenFooter, ScreenHeader, Term } from "../components/primitives";
import { Badge, Button, GamepadKey, Tag } from "../ds";

/** Trade detail — the prototype's `is_detail` artboard. */

const FACTS = [
  { label: "Opened", value: "20:57:03 · 2458.10", color: "var(--text-body)" },
  { label: "Closed", value: "21:34:48 · 2473.00", color: "var(--text-body)" },
  { label: "Side · size", value: "LONG 0.20", color: "var(--side-long)" },
  { label: "Exit reason", value: "target hit", color: "var(--text-body)" },
  { label: "MFE · MAE", value: "+2.60R · -0.40R", color: "var(--text-body)" },
  { label: "Fill latency", value: "71 ms", color: "var(--text-body)" },
];

const RULE_LINES = [
  { text: "pass · size inside rule 4 · 0.20 of 0.50", color: "var(--phos-500)" },
  { text: "pass · stop set before entry", color: "var(--phos-500)" },
  { text: "fail · entry 41s after the signal bar closed · rule 7 says 20s", color: "var(--arcade-red)" },
  { text: 'dropped · "waited for the retest" — self-assessed, unanswered', color: "var(--grey-500)" },
];

const CHECKLIST = [
  "Did you wait for the retest to complete?",
  "Was the London low still intact when you fired?",
  "Would you take this again tomorrow?",
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

export function TradeDetailScreen() {
  return (
    <Artboard
      label="Trade detail"
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
        title="Trade detail"
        meta="cid 8836 · session 042 · 2026-08-29"
        right={
          <Button variant="secondary" size="sm">
            Open replay
          </Button>
        }
      >
        <Badge tone="up">Closed +2.40R</Badge>
      </ScreenHeader>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 1,
          background: "var(--line-hairline)",
          minHeight: 0,
        }}
      >
        {/* what the broker says */}
        <div style={panel}>
          <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
            <Caps size={10} weight={700} color="var(--phos-300)">
              Broker facts
            </Caps>
            <Badge tone="info">Source of truth</Badge>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(2,1fr)",
              gap: 1,
              background: "var(--line-hairline)",
            }}
          >
            {FACTS.map((f) => (
              <div
                key={f.label}
                style={{
                  background: "var(--surface-well)",
                  padding: 10,
                  display: "grid",
                  gap: 4,
                }}
              >
                <Caps color="var(--text-muted)">{f.label}</Caps>
                <span style={{ fontFamily: "var(--font-data)", fontSize: 14, color: f.color }}>
                  {f.value}
                </span>
              </div>
            ))}
          </div>

          <div style={{ display: "grid", gap: 8 }}>
            <Caps>Protection edits</Caps>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "70px 1fr 90px",
                gap: 8,
                fontFamily: "var(--font-data)",
                fontSize: 11,
                color: "var(--text-secondary)",
                borderBottom: "1px solid var(--line-hairline)",
                paddingBottom: 6,
              }}
            >
              <span>21:12</span>
              <span>sl 2455.60 → 2458.10</span>
              <span style={{ textAlign: "right", color: "var(--phos-400)" }}>to entry</span>
            </div>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "70px 1fr 90px",
                gap: 8,
                fontFamily: "var(--font-data)",
                fontSize: 11,
                color: "var(--text-secondary)",
              }}
            >
              <span>21:26</span>
              <span>sl 2458.10 → 2464.00</span>
              <span style={{ textAlign: "right", color: "var(--phos-400)" }}>+0.80R locked</span>
            </div>
          </div>

          <div style={{ display: "grid", gap: 10 }}>
            <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
              <Caps size={10} weight={700} color="var(--phos-300)">
                Rule score
              </Caps>
              <span
                style={{
                  fontFamily: "var(--font-data)",
                  fontSize: 16,
                  fontWeight: 700,
                  color: "var(--phos-400)",
                }}
              >
                10 / 11
              </span>
              {/* the unverifiable rule leaves the denominator rather than counting as a failure */}
              <Badge tone="neutral">1 rule unverifiable</Badge>
            </div>
            <Term>
              frozen at the moment you fired. later checklist answers add to it; they never rewrite
              it.
            </Term>
            <div
              style={{
                display: "grid",
                gap: 6,
                padding: 12,
                background: "var(--black-3)",
                border: "1px solid var(--line-hairline)",
              }}
            >
              {RULE_LINES.map((line) => (
                <Term key={line.text} color={line.color}>
                  {line.text}
                </Term>
              ))}
            </div>
          </div>
        </div>

        {/* what you said */}
        <div style={panel}>
          <div style={{ display: "grid", gap: 8 }}>
            <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
              <Caps size={10} weight={700} color="var(--phos-300)">
                Plan snapshot
              </Caps>
              <Badge tone="neutral">Immutable</Badge>
            </div>
            <div
              style={{
                padding: 12,
                background: "var(--surface-well)",
                boxShadow: "var(--inset-well)",
                fontSize: 14,
                lineHeight: 1.5,
              }}
            >
              One long from a retest with the London low intact, and nothing else. Invalidation:
              close below 2455.
            </div>
          </div>

          <div style={{ display: "grid", gap: 8 }}>
            <Caps>Voice memo · recorded at entry 20:56:41</Caps>
            <div
              style={{
                padding: 12,
                border: "1px solid var(--line-hairline)",
                background: "var(--black-3)",
                display: "grid",
                gap: 10,
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <Button variant="secondary" size="sm" icon="play">
                  Play
                </Button>
                <span
                  style={{
                    fontFamily: "var(--font-data)",
                    fontSize: 11,
                    color: "var(--text-muted)",
                  }}
                >
                  0:14
                </span>
                <div
                  style={{
                    flex: 1,
                    height: 8,
                    background: "var(--surface-well)",
                    border: "1px solid var(--line-hairline)",
                    display: "flex",
                  }}
                >
                  <span style={{ width: "34%", background: "var(--phos-500)" }} />
                </div>
                <Button variant="ghost" size="sm">
                  Delete
                </Button>
              </div>
              <Term color="var(--text-terminal)">
                &quot;second touch of 2455, London low still holding, taking the retest with a tight
                stop.&quot;
              </Term>
              <Caps size={10}>Stored on this machine · deletable any time</Caps>
            </div>
          </div>

          <div style={{ display: "grid", gap: 8 }}>
            <Caps>Review memo · recorded 22:52, after the close</Caps>
            <div
              style={{
                padding: 12,
                borderLeft: "2px solid var(--arcade-cyan)",
                borderTop: "1px solid var(--line-hairline)",
                borderRight: "1px solid var(--line-hairline)",
                borderBottom: "1px solid var(--line-hairline)",
                background: "var(--black-3)",
              }}
            >
              <Term color="var(--text-terminal)">
                &quot;i was two minutes early. the retest hadn&apos;t finished.&quot;
              </Term>
            </div>
          </div>

          <div style={{ display: "grid", gap: 8 }}>
            <Caps>Tags</Caps>
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
              <Tag>retest</Tag>
              <Tag color="var(--arcade-yellow)">early entry</Tag>
              <Tag color="var(--arcade-cyan)">xauusd</Tag>
            </div>
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
            <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
              <Caps size={10} weight={700} color="var(--arcade-yellow)">
                Checklist · 3 taps
              </Caps>
              <Caps color="var(--text-muted)">Queued since 21:34 · skipping costs nothing</Caps>
            </div>
            <div style={{ display: "grid", gap: 10 }}>
              {CHECKLIST.map((q) => (
                <div key={q} style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <span style={{ flex: 1, fontSize: 14, lineHeight: 1.4 }}>{q}</span>
                  <Button variant="secondary" size="sm">
                    Yes
                  </Button>
                  <Button variant="ghost" size="sm">
                    No
                  </Button>
                </div>
              ))}
            </div>
            <Term>
              unanswered rules drop out of the denominator. they are never counted as failures.
            </Term>
          </div>
        </div>
      </div>

      <ScreenFooter>
        <GamepadKey button="x" size="sm" label="Open replay" />
        <GamepadKey button="y" size="sm" label="Record memo" />
        <GamepadKey button="b" size="sm" label="Back to journal" />
      </ScreenFooter>
    </Artboard>
  );
}
