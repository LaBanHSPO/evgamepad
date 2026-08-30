import { Artboard, Caps, ScreenFooter, ScreenHeader, Term } from "../components/primitives";
import { AgentMessage, Badge, Button, GamepadKey, Input, Tag } from "../ds";

/** Agent desk — the prototype's `is_desk` artboard. The desk reads; it never places. */

const CONTEXT = [
  { text: "spread 0.24", color: "var(--text-secondary)" },
  { text: "session 1:12 left", color: "var(--text-secondary)" },
  { text: "dxy prints in 18:04", color: "var(--arcade-yellow)" },
  { text: "method: range", color: "var(--text-secondary)" },
  { text: "news fetched 2h ago", color: "var(--text-secondary)" },
];

const DESK_NAV = [
  { label: "Ask", active: true, count: null as string | null, countColor: "" },
  { label: "News", active: false, count: "2", countColor: "var(--arcade-yellow)" },
  { label: "Method", active: false, count: null, countColor: "" },
  { label: "Signals", active: false, count: "4", countColor: "var(--text-muted)" },
];

const CREW = [
  { name: "sentinel", online: true },
  { name: "risk-warden", online: true },
  { name: "coach · offline", online: false },
];

export function AgentDeskScreen() {
  return (
    <Artboard
      label="Agent desk"
      frameStyle={{
        width: 1440,
        height: 860,
        display: "grid",
        gridTemplateRows: "44px 40px auto 1fr 44px",
        background: "var(--surface-app)",
        border: "1px solid var(--line-hairline)",
      }}
    >
      <ScreenHeader
        title="Agent desk"
        meta="Session 042 · 21:12"
        right={
          <Button variant="danger" size="sm">
            Flatten all
          </Button>
        }
      >
        <Badge tone="warn" dot>
          Opens locked
        </Badge>
      </ScreenHeader>

      {/* context strip — machine facts, not AI */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 20,
          padding: "0 16px",
          borderBottom: "1px solid var(--line-hairline)",
          background: "var(--black-3)",
        }}
      >
        <Caps>Context strip · not AI</Caps>
        {CONTEXT.map((c) => (
          <span
            key={c.text}
            style={{ fontFamily: "var(--font-data)", fontSize: 11, color: c.color }}
          >
            {c.text}
          </span>
        ))}
        <Caps size={10} color="var(--phos-300)" style={{ marginLeft: "auto" }}>
          Still live · updates without the coach
        </Caps>
      </div>

      {/* the read-only boundary, stated as a banner rather than a footnote */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 12,
          height: 34,
          padding: "0 16px",
          background: "rgba(255,212,0,.08)",
          borderBottom: "1px solid rgba(255,212,0,.4)",
        }}
      >
        <Caps size={11} weight={700} color="var(--arcade-yellow)">
          Arm cancelled on open
        </Caps>
        <Term>
          the desk cannot place, close or modify anything. closing and emergency exit still work
          from the pad.
        </Term>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "216px 1fr 380px",
          gap: 1,
          background: "var(--line-hairline)",
          minHeight: 0,
        }}
      >
        <nav
          style={{
            background: "var(--black-2)",
            padding: "10px 0",
            display: "grid",
            gap: 2,
            alignContent: "start",
          }}
        >
          {/* padding goes on the caps element itself — a wrapper would inherit
              the body line-height and push the list down */}
          <Caps style={{ padding: "6px 12px" }}>Desk</Caps>
          {DESK_NAV.map((item) => (
            <div
              key={item.label}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: item.count ? "space-between" : undefined,
                height: 32,
                padding: "0 12px",
                borderLeft: `2px solid ${item.active ? "var(--phos-400)" : "transparent"}`,
                background: item.active ? "var(--surface-selected)" : undefined,
                color: item.active ? "var(--phos-300)" : "var(--text-secondary)",
                fontSize: 11,
                fontWeight: 700,
                letterSpacing: ".12em",
                textTransform: "uppercase",
              }}
            >
              {item.label}
              {item.count ? (
                <span style={{ fontFamily: "var(--font-data)", color: item.countColor }}>
                  {item.count}
                </span>
              ) : null}
            </div>
          ))}

          <Caps style={{ padding: "14px 12px 6px" }}>Crew</Caps>
          {CREW.map((member) => (
            <div
              key={member.name}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                height: 26,
                padding: "0 12px",
                fontFamily: "var(--font-data)",
                fontSize: 11,
                color: member.online ? "var(--text-secondary)" : "var(--text-disabled)",
              }}
            >
              <i
                style={{
                  width: 5,
                  height: 5,
                  borderRadius: 999,
                  background: member.online ? "var(--phos-400)" : "var(--grey-700)",
                  boxShadow: member.online ? "0 0 6px var(--phos-400)" : undefined,
                }}
              />
              {member.name}
            </div>
          ))}
        </nav>

        {/* the conversation */}
        <section
          style={{
            background: "var(--black-2)",
            backgroundImage: "var(--veil-scanline)",
            display: "grid",
            gridTemplateRows: "1fr auto",
            minHeight: 0,
          }}
        >
          <div
            style={{
              padding: "18px 20px",
              display: "grid",
              gap: 14,
              alignContent: "start",
              minHeight: 0,
              overflow: "hidden",
            }}
          >
            <AgentMessage author="user" time="21:09">
              Is my long still valid if 2455 gives way on this candle?
            </AgentMessage>
            {/* One clause per line — the system's rule for agent output. */}
            <AgentMessage author="agent" name="risk-warden" time="21:09">
              <span style={{ display: "block" }}>
                &gt; your plan says a close below 2455 ends the night.
              </span>
              <span style={{ display: "block" }}>
                &gt; price is 2461.38, the level held twice today.
              </span>
              <span style={{ display: "block" }}>
                &gt; you are 2 of 2 positions and -1.10R into a -3.00R cap.
              </span>
            </AgentMessage>

            <div
              style={{
                padding: 14,
                border: "1px solid var(--line-neutral)",
                background: "var(--black-3)",
                display: "grid",
                gap: 8,
              }}
            >
              <Caps size={11} weight={700}>
                Coach offline
              </Caps>
              <Term color="var(--grey-500)">
                the arguing voice is unavailable — provider key rejected at 20:58.
              </Term>
              <Term color="var(--grey-500)">
                context strip, chart lens and the order path are unaffected. it will come back on
                its own.
              </Term>
            </div>

            <Term color="var(--grey-500)">
              your notes and memos are read as material here, never as instructions.
            </Term>
          </div>

          <div
            style={{
              borderTop: "1px solid var(--line-hairline)",
              padding: "12px 20px",
              display: "flex",
              alignItems: "center",
              gap: 12,
              background: "var(--black-2)",
            }}
          >
            <div style={{ flex: 1, minWidth: 0 }}>
              <Input value="" placeholder="ask the desk — it can read everything and place nothing" />
            </div>
            <Button variant="secondary" size="md">
              Ask desk
            </Button>
          </div>
        </section>

        {/* events, signals, sources */}
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
          <div style={{ display: "grid", gap: 10 }}>
            <Caps>Tonight&apos;s events</Caps>
            <div
              style={{
                display: "grid",
                gap: 8,
                padding: 12,
                border: "1px solid rgba(255,212,0,.4)",
                background: "rgba(255,212,0,.06)",
              }}
            >
              <div
                style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}
              >
                <Caps size={11} weight={700} color="var(--arcade-yellow)" style={{ letterSpacing: ".12em" }}>
                  DXY prints
                </Caps>
                <span
                  style={{
                    fontFamily: "var(--font-data)",
                    fontSize: 11,
                    color: "var(--arcade-yellow)",
                  }}
                >
                  18:04
                </span>
              </div>
              <span
                style={{ fontFamily: "var(--font-data)", fontSize: 10, color: "var(--text-muted)" }}
              >
                high impact · 21:30 · guard 15 min
              </span>
            </div>
            <div
              style={{
                display: "grid",
                gap: 8,
                padding: 12,
                border: "1px solid var(--line-hairline)",
              }}
            >
              <div
                style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}
              >
                <Caps size={11} weight={700} color="var(--text-secondary)" style={{ letterSpacing: ".12em" }}>
                  Asia open
                </Caps>
                <span
                  style={{
                    fontFamily: "var(--font-data)",
                    fontSize: 11,
                    color: "var(--text-muted)",
                  }}
                >
                  1:48
                </span>
              </div>
              <span
                style={{ fontFamily: "var(--font-data)", fontSize: 10, color: "var(--text-muted)" }}
              >
                medium impact · 23:00
              </span>
            </div>
          </div>

          <div style={{ display: "grid", gap: 10 }}>
            <Caps>External signals · read only</Caps>
            <div
              style={{
                display: "grid",
                gap: 6,
                padding: 12,
                background: "var(--black-3)",
                border: "1px solid var(--line-hairline)",
              }}
            >
              <Term color="var(--arcade-cyan)">21:02 tradingview: xauusd range break watch</Term>
              <Term color="var(--arcade-cyan)">20:44 tradingview: eurusd momentum fade</Term>
              <Term color="var(--grey-500)">
                a signal is a note. it cannot arm, fire or size anything.
              </Term>
            </div>
          </div>

          <div style={{ display: "grid", gap: 10 }}>
            <Caps>Sources · max 5 domains</Caps>
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
              <Tag color="var(--arcade-cyan)">forexfactory</Tag>
              <Tag color="var(--arcade-cyan)">reuters</Tag>
              <Tag color="var(--arcade-cyan)">ctrader</Tag>
            </div>
            <Term color="var(--grey-500)">no social accounts by default. english sources only.</Term>
          </div>
        </aside>
      </div>

      <ScreenFooter>
        <GamepadKey button="y" size="sm" label="Ask agent" />
        <GamepadKey button="b" size="sm" label="Back to session" />
        <GamepadKey button="a" size="sm" label="Close selected" />
      </ScreenFooter>
    </Artboard>
  );
}
