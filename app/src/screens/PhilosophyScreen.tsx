import { Artboard, Caps, ScreenFooter, ScreenHeader, Term } from "../components/primitives";
import { Badge, Button, GamepadKey } from "../ds";

/**
 * Philosophy — the prototype's `is_philosophy` artboard.
 *
 * The trader's own words, verbatim. The coach may argue with them in the rail;
 * it can never edit them.
 */

const PRINCIPLES = [
  "The stop goes in before the entry. Always. No exception has ever been worth it.",
  "One setup a night is enough. The second one is usually boredom wearing the first one's clothes.",
  "If I cannot say why out loud in one sentence, I do not take it.",
  "Losing on a good decision is the cost of the game. Winning on a bad one is a debt.",
  "When I want to trade to feel better, I close the tab.",
];

const EDITS = [
  { when: "2026-08-11 22:40", what: "principle 05 added" },
  { when: "2026-07-28 23:02", what: "rewrote how I want to play" },
  { when: "2026-07-02 21:15", what: "first written" },
];

export function PhilosophyScreen() {
  return (
    <Artboard
      label="Philosophy"
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
        title="Philosophy"
        meta="Out-of-session · last edited 2026-08-11"
        right={
          <Button variant="ghost" size="sm">
            Edit
          </Button>
        }
      >
        <Badge tone="neutral">Your words, stored verbatim</Badge>
      </ScreenHeader>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 420px",
          gap: 1,
          background: "var(--line-hairline)",
          minHeight: 0,
        }}
      >
        <div
          style={{
            background: "var(--black-2)",
            backgroundImage: "var(--veil-scanline)",
            padding: "34px 44px",
            display: "grid",
            gap: 26,
            alignContent: "start",
            minHeight: 0,
            overflow: "hidden",
          }}
        >
          <span
            style={{
              fontFamily: "var(--font-display)",
              fontSize: 16,
              lineHeight: 1.6,
              color: "var(--phos-400)",
              textShadow: "var(--glow-text)",
              maxWidth: "24ch",
            }}
          >
            PLAY THE LONG GAME
          </span>

          <div style={{ display: "grid", gap: 14, maxWidth: "64ch" }}>
            <Caps>How I want to play</Caps>
            <span
              style={{
                fontSize: 16,
                lineHeight: 1.6,
                color: "var(--text-body)",
                textWrap: "pretty" as never,
              }}
            >
              The market is not mine to control. My decisions are. I am here to make choices I will
              be proud of in the morning, and most of those choices are the ones where I did nothing
              at all.
            </span>
            <span
              style={{
                fontSize: 16,
                lineHeight: 1.6,
                color: "var(--text-body)",
                textWrap: "pretty" as never,
              }}
            >
              A night where I sat on my hands and wrote down why is a good night. A night where I
              made money by breaking my own rules is a bad night that happened to pay.
            </span>
          </div>

          <div style={{ display: "grid", gap: 12, maxWidth: "64ch" }}>
            <Caps>Principles · in my own order</Caps>
            <div style={{ display: "grid", gap: 10 }}>
              {PRINCIPLES.map((text, i) => (
                <div
                  key={text}
                  style={{
                    display: "flex",
                    gap: 14,
                    paddingLeft: 12,
                    // the first principle carries the brighter keyline
                    borderLeft: `2px solid ${i === 0 ? "var(--phos-400)" : "var(--phos-600)"}`,
                  }}
                >
                  <span
                    style={{
                      fontFamily: "var(--font-data)",
                      fontSize: 14,
                      color: "var(--phos-400)",
                    }}
                  >
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  <span style={{ fontSize: 15, lineHeight: 1.5 }}>{text}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <aside
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
          <div
            style={{
              display: "grid",
              gap: 10,
              padding: 14,
              background: "var(--black-3)",
              border: "1px solid var(--line-hairline)",
            }}
          >
            <Caps>Where this text is used</Caps>
            <Term>read by you before a hard night</Term>
            <Term>read by the desk as material, never as instructions</Term>
            <Term color="var(--arcade-red)">never editable by the desk, in any circumstance</Term>
          </div>

          <div
            style={{
              display: "grid",
              gap: 10,
              padding: 14,
              border: "1px solid var(--line-hairline)",
            }}
          >
            <Caps>Not here</Caps>
            <span
              style={{
                fontSize: 14,
                lineHeight: 1.5,
                color: "var(--text-secondary)",
                maxWidth: "64ch",
              }}
            >
              No reminder to review this, no &quot;days since last edit&quot;, no completion meter.
              It is a page, not a habit to keep.
            </span>
          </div>

          <div style={{ display: "grid", gap: 10 }}>
            <Caps>Edit history</Caps>
            {EDITS.map((e, i) => (
              <div
                key={e.when}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  fontFamily: "var(--font-data)",
                  fontSize: 11,
                  color: "var(--text-secondary)",
                  borderBottom: i === EDITS.length - 1 ? undefined : "1px solid var(--line-hairline)",
                  paddingBottom: i === EDITS.length - 1 ? undefined : 6,
                }}
              >
                <span>{e.when}</span>
                <span>{e.what}</span>
              </div>
            ))}
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
            <Caps color="var(--status-agent)">coach · may argue, may not edit</Caps>
            <Term color="var(--status-agent)">
              principle 02 and your orb playbook disagree on double entries. worth a look, not a
              change I can make.
            </Term>
          </div>
        </aside>
      </div>

      <ScreenFooter>
        <GamepadKey button="b" size="sm" label="Back" />
        <Caps size={10} color="var(--text-muted)">
          One editor for this text · settings only links here
        </Caps>
      </ScreenFooter>
    </Artboard>
  );
}
