/**
 * Fixed screen data, transcribed from the prototype's `renderVals()`.
 * The prototype's own footer says it: screens are real, data is fixed.
 */

/** Colour for an R-multiple cell: red for a loss, phosphor for a gain, muted for "—". */
export const rColor = (v: string) =>
  v.startsWith("-")
    ? "var(--pnl-down)"
    : v.startsWith("+")
      ? "var(--pnl-up)"
      : "var(--text-muted)";

export interface HiScore {
  rank: string;
  name: string;
  score: string;
  r: string;
}

/** Attract screen — ranked by stand-downs, not profit. */
export const hiScores: HiScore[] = [
  { rank: "1ST", name: "S-031 · 12 refused", score: "12", r: "+4.20R" },
  { rank: "2ND", name: "S-039 · 11 refused", score: "11", r: "+1.10R" },
  { rank: "3RD", name: "S-043 · 08 refused", score: "08", r: "+2.40R" },
  { rank: "4TH", name: "S-036 · 07 refused", score: "07", r: "-0.40R" },
  { rank: "5TH", name: "S-028 · 06 refused", score: "06", r: "+0.90R" },
  { rank: "6TH", name: "S-044 · 03 refused", score: "03", r: "-3.10R" },
];

const P = "var(--phos-400)";
const D = "var(--phos-600)";
const G = "var(--grey-300)";
const M = "var(--status-agent)";
const Y = "var(--arcade-yellow)";

export interface BootLine {
  text: string;
  color: string;
}

/** Boot sequence — 14 phosphor log lines. */
export const bootLines: BootLine[] = [
  { text: "> evgamepad terminal 0.43 — cold start", color: D },
  { text: "> phosphor buffer ok · 1440x810 · 60hz", color: D },
  { text: "> mounting journal store … 43 sessions, 512 fills", color: G },
  { text: "> loading rule set rev 11 … 12 rules, 0 conflicts", color: G },
  { text: "> rule 4 caps size at 0.50 lots per position", color: P },
  { text: "> rule 9 goes close-only at -3.00R", color: P },
  { text: "> broker socket … connected · xauusd 2455.90 · spread 0.22", color: G },
  { text: "> clock drift 41ms — inside tolerance", color: D },
  { text: "> scanning input devices …", color: G },
  { text: "> pad detected: generic hid, 14 bindings restored", color: P },
  { text: "> risk-warden online. reading the last four sessions.", color: M },
  { text: "> session-scribe online. it writes, you sign.", color: M },
  { text: "> warning: window opens in 2m 14s. limits not written yet.", color: Y },
  { text: "> awaiting player.", color: P },
];

export interface BootCheck {
  label: string;
  value: string;
  ok: boolean;
}

/** Boot sequence — six pre-flight checks. All six or no coin. */
export const bootChecks: BootCheck[] = [
  { label: "Pad", value: "connected", ok: true },
  { label: "Broker feed", value: "live · 22ms", ok: true },
  { label: "Rule set", value: "rev 11", ok: true },
  { label: "Journal store", value: "writable", ok: true },
  { label: "Clock", value: "drift 41ms", ok: true },
  { label: "Session limits", value: "not written", ok: false },
];

export interface TallyRow {
  label: string;
  note: string;
  count: string;
  points: string;
}

/** Session clear — points scored on behaviour, not on money. */
export const tally: TallyRow[] = [
  { label: "Rules kept", note: "11 of 12 · rule 7 bent at 21:48", count: "11", points: "+2 200" },
  { label: "Arms refused", note: "clutch held, trigger released", count: "8", points: "+1 600" },
  { label: "Plan followed", note: "three fills of four inside thesis", count: "3", points: "+600" },
  {
    label: "Journalled at the fill",
    note: "no back-filling after the close",
    count: "4",
    points: "+400",
  },
  { label: "Size drift", note: "0.20 → 0.30 on the second entry", count: "1", points: "-300" },
  { label: "Revenge window", note: "one entry inside 60s of a stop", count: "1", points: "-150" },
];

export const tallyTotal = "4 350";

export interface OverRow {
  time: string;
  what: string;
  r: string;
}

/** Session over — where the -3.10R went. */
export const overRows: OverRow[] = [
  { time: "20:41", what: "long 0.20 · stopped", r: "-1.00R" },
  { time: "21:02", what: "long 0.30 · stopped", r: "-1.10R" },
  { time: "21:19", what: "short 0.30 · scratched", r: "-0.10R" },
  { time: "21:34", what: "long 0.50 · stopped", r: "-0.90R" },
  { time: "21:36", what: "arm blocked · rule 4", r: "—" },
];
