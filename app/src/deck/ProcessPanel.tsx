import { PlaybookStats } from "./PlaybookStats";
import type { PlaybookRow } from "./PlaybookStats";
import { ScoreRadar } from "./ScoreRadar";
import type { ScoreView } from "./ScoreRadar";
import { TiltRetro } from "./TiltRetro";
import type { TiltRetroView } from "./TiltRetro";
import type { ProcessView } from "./types";
import { percent, show, signed } from "./types";

/**
 * The default panel.
 *
 * Nothing here is a dollar figure, and nothing here is a streak or a badge. Standing down counts
 * upward, a dead tape is stated as a fact about the night rather than a verdict on the player,
 * and the check-in is plotted against adherence rather than against money.
 */
export function ProcessPanel({ view, score, playbooks, tilt, distribution }: {
  view: ProcessView | null;
  score?: ScoreView | null;
  playbooks?: PlaybookRow[];
  tilt?: TiltRetroView | null;
  distribution?: MonthScores[];
}): JSX.Element {
  if (view === null) return <p>loading the process figures…</p>;

  const { current, delta, month, previousMonth } = view.months;

  return (
    <>
      <section style={panel}>
        <h2 style={heading}>Process Score · last evening</h2>
        <ScoreRadar view={score ?? null} />
        <p style={note}>
          Computed at session close, from process only. The evening it rates highest is the one
          where the tape offered nothing and you correctly did nothing.
        </p>
      </section>
      <section style={panel}>
        <h2 style={heading}>This month{month ? ` · ${month}` : ""}</h2>
        <div style={grid}>
          <Stat label="Adherence" value={percent(current.adherence)}
                delta={delta.adherence} deltaFormat="percent" />
          <Stat label="Declined per session" value={show(current.declinedRate)}
                delta={delta.declinedRate} />
          <Stat label="Check-in average" value={show(current.checkinAverage, 1)}
                delta={delta.checkinAverage} />
          <Stat label="Opportunity quality" value={show(current.opportunityQuality)}
                delta={delta.opportunityQuality} />
        </div>
        <p style={note}>
          {previousMonth
            ? `compared with ${previousMonth}`
            : "no previous month yet — deltas appear once there is one"}
        </p>
      </section>

      <section style={panel}>
        <h2 style={heading}>Where adherence goes</h2>
        {Object.keys(current.adherenceByRule).length === 0 ? (
          <p style={note}>no fires this month, so there is nothing to score</p>
        ) : (
          <ul style={{ margin: 0, paddingLeft: 18 }}>
            {Object.entries(current.adherenceByRule).map(([rule, value]) => (
              <li key={rule}>
                {rule.replace(/_/g, " ")} — {percent(value)}
              </li>
            ))}
          </ul>
        )}
      </section>

      {view.latestSession ? (
        <section style={panel}>
          <h2 style={heading}>Last evening</h2>
          <div style={grid}>
            <Stat label="Check-in before" value={show(view.latestSession.checkinPre, 0)} />
            <Stat label="Check-in after" value={show(view.latestSession.checkinPost, 0)} />
            <Stat label="Trades declined" value={String(view.latestSession.declined)} />
            <Stat label="Tape" value={show(view.latestSession.opportunityQuality)} />
          </div>
          <p style={note}>{view.latestSession.verdict}</p>
          {/* Player text, rendered as a text child so React escapes it. Never raw HTML. */}
          {view.latestSession.note ? <blockquote style={quote}>{view.latestSession.note}</blockquote> : null}
        </section>
      ) : null}

      <section style={panel}>
        <h2 style={heading}>Score by month</h2>
        <ScoreDistribution months={distribution ?? []} />
      </section>

      <section style={panel}>
        <h2 style={heading}>By playbook</h2>
        <PlaybookStats rows={playbooks ?? []} />
      </section>

      <section style={panel}>
        <h2 style={heading}>Tilt, last evening</h2>
        <TiltRetro view={tilt ?? null} />
      </section>

      <section style={panel}>
        <h2 style={heading}>All time</h2>
        <div style={grid}>
          <Stat label="Sessions" value={String(view.allTime.sessions)} />
          <Stat label="Fires" value={String(view.allTime.fires)} />
          <Stat label="Declined" value={String(view.allTime.declined)} />
          <Stat label="Adherence" value={percent(view.allTime.adherence)} />
        </div>
      </section>
    </>
  );
}

/** One month's scores. A distribution with n — deliberately not a streak or a "days since". */
export interface MonthScores {
  month: string;
  n: number;
  mean: number;
  min: number;
  max: number;
  scores: number[];
}

function ScoreDistribution({ months }: { months: MonthScores[] }): JSX.Element {
  if (months.length === 0) return <p style={note}>no scored evenings yet</p>;
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {months.map((entry) => (
        <div key={entry.month} style={{ display: "flex", gap: 12, alignItems: "center" }}>
          <span style={{ width: 64, opacity: 0.75, fontSize: 12 }}>{entry.month}</span>
          {/* The spread of the month's evenings, so a good month reads as a shape rather than as
              a number to defend. */}
          <span style={{ position: "relative", flex: 1, height: 18 }}>
            <span style={spread(entry)} />
            {entry.scores.map((value, index) => (
              <span key={`${value}-${index}`} style={{ ...dot, left: `${value}%` }} />
            ))}
          </span>
          <span style={{ fontFamily: "var(--font-data)", fontSize: 13 }}>
            {entry.mean.toFixed(0)}
          </span>
          <span style={{ opacity: 0.6, fontSize: 12 }}>n={entry.n}</span>
        </div>
      ))}
    </div>
  );
}

const spread = (entry: MonthScores): React.CSSProperties => ({
  position: "absolute",
  top: 8,
  left: `${entry.min}%`,
  width: `${Math.max(0.5, entry.max - entry.min)}%`,
  height: 2,
  background: "var(--phos-600, #063)",
});

const dot: React.CSSProperties = {
  position: "absolute",
  top: 5,
  width: 6,
  height: 6,
  marginLeft: -3,
  borderRadius: "50%",
  background: "var(--phos-300)",
};

function Stat({ label, value, delta, deltaFormat }: {
  label: string;
  value: string;
  delta?: number | null;
  deltaFormat?: "percent";
}): JSX.Element {
  const rendered =
    delta === undefined || delta === null
      ? null
      : deltaFormat === "percent"
        ? `${delta >= 0 ? "+" : ""}${(delta * 100).toFixed(1)}%`
        : signed(delta);
  return (
    <div>
      <div style={{ opacity: 0.7, fontSize: 12 }}>{label}</div>
      <div style={{ fontSize: 26, fontFamily: "var(--font-data)" }}>{value}</div>
      {rendered ? <div style={{ fontSize: 12, opacity: 0.8 }}>{rendered} vs last month</div> : null}
    </div>
  );
}

const panel: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 10,
  padding: 14,
  border: "var(--border-hairline)",
  background: "var(--black-2)",
};

const heading: React.CSSProperties = { margin: 0, fontSize: 14, letterSpacing: "0.08em" };
const grid: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
  gap: 16,
};
const note: React.CSSProperties = { margin: 0, opacity: 0.75, fontSize: 13 };
const quote: React.CSSProperties = {
  margin: 0,
  paddingLeft: 12,
  borderLeft: "2px solid var(--phos-600)",
  opacity: 0.9,
};
