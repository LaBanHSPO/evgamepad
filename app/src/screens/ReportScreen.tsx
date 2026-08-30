import { Artboard, Caps, ScreenFooter, ScreenHeader, Term } from "../components/primitives";
import { Button, Checkbox, GamepadKey } from "../ds";

/**
 * Report — the prototype's `is_report` artboard.
 *
 * The money appendix is off by default and can only be turned on by ticking it
 * here; the preview is a light print layout rather than a dark screenshot.
 */

const PERIODS = ["August 2026", "This week", "Custom range", "One session"];

const COUNTS = [
  { label: "Sessions", value: "14" },
  { label: "Trades", value: "38" },
  { label: "Sat-out nights", value: "5" },
];

const CONTENTS = [
  { label: "Process cover", checked: true },
  { label: "Month heatmap", checked: true },
  { label: "Process scores and adherence", checked: true },
  { label: "Playbook cut · trade count and adherence only", checked: true },
  {
    label: "Mistake types",
    checked: false,
    description: "execution-learning has no spec yet — this section will say so",
  },
];

/** The print heatmap uses paper greens, not the phosphor ramp. */
const PRINT_NIGHTS = [
  "#B9D6BF",
  "#8CC195",
  "#5FA96C",
  "#3E8F4C",
  "#2E7A3B",
  "#8CC195",
  "out",
  "#5FA96C",
  "#3E8F4C",
  "#B9D6BF",
  "out",
  "#2E7A3B",
  "#5FA96C",
  "#3E8F4C",
];

const PRINT_STATS = [
  { label: "Median process score", value: "82" },
  { label: "Adherence", value: "89%" },
  { label: "Stand-down rate", value: "58%" },
];

const PLAYBOOK_CUT = [
  { name: "orb", trades: "18 trades", adherence: "92% adherence" },
  { name: "retest", trades: "14 trades", adherence: "86% adherence" },
  { name: "unplanned", trades: "6 trades", adherence: "—" },
];

const printCaps = {
  fontSize: 9,
  letterSpacing: ".18em",
  textTransform: "uppercase",
  color: "#4A554A",
} as const;

export function ReportScreen() {
  return (
    <Artboard
      label="Report"
      frameStyle={{
        width: 1440,
        height: 860,
        display: "grid",
        gridTemplateRows: "44px 34px 1fr 44px",
        background: "var(--surface-app)",
        border: "1px solid var(--line-hairline)",
      }}
    >
      <ScreenHeader
        title="Report"
        meta="Out-of-session surface · mouse and keyboard"
        right={
          <Button variant="secondary" size="sm">
            Save as PDF
          </Button>
        }
      />

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 12,
          padding: "0 16px",
          background: "var(--phos-a08)",
          borderBottom: "1px solid var(--line-hairline)",
        }}
      >
        <Caps size={11} weight={700} color="var(--phos-300)">
          Opened from the safe menu
        </Caps>
        <Term>
          your arm was cancelled and new opens are locked while this is open. closing positions is
          not.
        </Term>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "300px 360px 1fr",
          gap: 1,
          background: "var(--line-hairline)",
          minHeight: 0,
        }}
      >
        {/* period */}
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
            Period
          </Caps>
          <div style={{ display: "grid", gap: 6 }}>
            {PERIODS.map((p, i) => {
              const on = i === 0;
              return (
                <span
                  key={p}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    height: 30,
                    padding: "0 12px",
                    borderLeft: `2px solid ${on ? "var(--phos-400)" : "transparent"}`,
                    background: on ? "var(--surface-selected)" : undefined,
                    color: on ? "var(--phos-300)" : "var(--text-secondary)",
                    fontSize: 11,
                    fontWeight: 700,
                    letterSpacing: ".12em",
                    textTransform: "uppercase",
                  }}
                >
                  {p}
                </span>
              );
            })}
          </div>

          <div
            style={{
              display: "grid",
              gap: 8,
              padding: 12,
              background: "var(--black-3)",
              border: "1px solid var(--line-hairline)",
            }}
          >
            {COUNTS.map((c) => (
              <div
                key={c.label}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  fontFamily: "var(--font-data)",
                  fontSize: 11,
                  color: "var(--text-secondary)",
                }}
              >
                <Caps size={10} color="var(--text-muted)">
                  {c.label}
                </Caps>
                {c.value}
              </div>
            ))}
            <Term color="var(--grey-500)">
              every aggregate prints its session count beside it.
            </Term>
          </div>

          <Term color="var(--grey-500)">
            a custom range lists session-level numbers only — nothing here invents an aggregate.
          </Term>
        </div>

        {/* contents */}
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
            Contents
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
            {CONTENTS.map((c) => (
              <Checkbox
                key={c.label}
                checked={c.checked}
                label={c.label}
                description={c.description}
              />
            ))}
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
            <Checkbox
              checked={false}
              label="Outcome appendix · money"
              description="R expectancy, MFE/MAE, setup table, win rate"
            />
            <Term color="var(--arcade-yellow)">
              off unless you tick it now. no setting can turn this on for you.
            </Term>
            <Term>leave it off and the file contains no currency figure at all.</Term>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <Button variant="primary" size="md">
              Build report
            </Button>
            <Caps size={10} color="var(--text-muted)">
              Rendered in this browser
            </Caps>
          </div>
        </div>

        {/* print preview */}
        <div
          style={{
            background: "var(--black-1)",
            padding: "18px 20px",
            display: "grid",
            gap: 10,
            alignContent: "start",
            minHeight: 0,
            overflow: "hidden",
          }}
        >
          <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between" }}>
            <Caps size={10} weight={700} color="var(--phos-300)">
              Preview · print layout
            </Caps>
            <Caps color="var(--text-muted)">Light for paper, not a dark screenshot</Caps>
          </div>

          <div
            style={{
              background: "#F4F6F4",
              color: "#101410",
              padding: "22px 24px",
              display: "grid",
              gap: 16,
              border: "1px solid var(--line-neutral)",
              fontFamily: "var(--font-core)",
              minHeight: 0,
              overflow: "hidden",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "baseline",
                justifyContent: "space-between",
                borderBottom: "1px solid rgba(16,20,16,.2)",
                paddingBottom: 10,
              }}
            >
              <span
                style={{
                  fontSize: 13,
                  fontWeight: 700,
                  letterSpacing: ".18em",
                  textTransform: "uppercase",
                }}
              >
                Process report · august 2026
              </span>
              <span style={{ fontFamily: "var(--font-data)", fontSize: 11, color: "#4A554A" }}>
                14 sessions
              </span>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 14 }}>
              {PRINT_STATS.map((s) => (
                <div key={s.label} style={{ display: "grid", gap: 4 }}>
                  <span style={printCaps}>{s.label}</span>
                  <span
                    style={{ fontFamily: "var(--font-data)", fontSize: 22, fontWeight: 700 }}
                  >
                    {s.value}
                  </span>
                </div>
              ))}
            </div>

            <div style={{ display: "grid", gap: 6 }}>
              <span style={printCaps}>Nights</span>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(14,1fr)", gap: 4 }}>
                {PRINT_NIGHTS.map((n, i) => (
                  <span
                    key={i}
                    style={
                      n === "out"
                        ? { height: 26, background: "#F4F6F4", border: "1px dashed #8A968A" }
                        : { height: 26, background: n }
                    }
                  />
                ))}
              </div>
              <span style={{ fontSize: 10, color: "#4A554A" }}>
                Dashed nights were sat out on purpose — valid data, not missing data.
              </span>
            </div>

            <div style={{ display: "grid", gap: 6 }}>
              <span style={printCaps}>Playbook cut</span>
              {PLAYBOOK_CUT.map((row, i) => (
                <div
                  key={row.name}
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 70px 90px",
                    gap: 8,
                    fontFamily: "var(--font-data)",
                    fontSize: 11,
                    borderBottom:
                      i === PLAYBOOK_CUT.length - 1 ? undefined : "1px solid rgba(16,20,16,.15)",
                    paddingBottom: i === PLAYBOOK_CUT.length - 1 ? undefined : 4,
                  }}
                >
                  <span>{row.name}</span>
                  <span>{row.trades}</span>
                  <span>{row.adherence}</span>
                </div>
              ))}
            </div>

            <div
              style={{
                display: "grid",
                gap: 4,
                borderTop: "1px solid rgba(16,20,16,.2)",
                paddingTop: 10,
              }}
            >
              <span style={{ fontSize: 10, color: "#4A554A" }}>
                No outcome appendix in this build — no currency figure appears in this file.
              </span>
              <span style={{ fontSize: 10, color: "#4A554A" }}>
                Demo only. Not advice. Entertainment, not alpha.
              </span>
            </div>
          </div>
        </div>
      </div>

      <ScreenFooter>
        <GamepadKey button="b" size="sm" label="Back to session" />
        <Caps size={10} color="var(--text-muted)">
          Weights version 3 · older months recalculated with it
        </Caps>
      </ScreenFooter>
    </Artboard>
  );
}
