import { useState } from "react";
import type { CSSProperties } from "react";
import { BgmProvider } from "./components/bgm";
import { AgentDeskScreen } from "./screens/AgentDeskScreen";
import { AttractScreen } from "./screens/AttractScreen";
import { BootScreen } from "./screens/BootScreen";
import { CityFireScreen } from "./screens/CityFireScreen";
import { DataScreen } from "./screens/DataScreen";
import { Deck } from "./deck/Deck";
import { GamepadScreen } from "./screens/GamepadScreen";
import { HistoryScreen } from "./screens/HistoryScreen";
import { JournalScreen } from "./screens/JournalScreen";
import { LiveHudScreen } from "./screens/LiveHudScreen";
import { MatrixHudScreen } from "./screens/MatrixHudScreen";
import { PhilosophyScreen } from "./screens/PhilosophyScreen";
import { PreSessionScreen } from "./screens/PreSessionScreen";
import { ProcessScoreScreen } from "./screens/ProcessScoreScreen";
import { ReplayScreen } from "./screens/ReplayScreen";
import { ReportScreen } from "./screens/ReportScreen";
import { SessionClearScreen } from "./screens/SessionClearScreen";
import { SessionHudScreen, HUD_STATES, type HudState } from "./screens/SessionHudScreen";
import { SessionOverScreen } from "./screens/SessionOverScreen";
import { SettingsScreen } from "./screens/SettingsScreen";
import { SizeCalculatorScreen } from "./screens/SizeCalculatorScreen";
import { TradeDetailScreen } from "./screens/TradeDetailScreen";

/**
 * Click-through shell — the prototype's sidebar, in the order the design chat
 * settled on: the run of a real session, then setup and reference.
 */

type ScreenId =
  | "title"
  | "boot"
  | "pre"
  | "session"
  | "live"
  | "deck"
  | "artmatrix"
  | "artcontra"
  | "desk"
  | "detail"
  | "calc"
  | "clear"
  | "over"
  | "report"
  | "journal"
  | "replay"
  | "history"
  | "score"
  | "pad"
  | "data"
  | "settings"
  | "philosophy";

const GROUPS: {
  heading: string;
  short: string;
  items: { id: ScreenId; label: string }[];
}[] = [
  {
    heading: "1 · Before the session",
    short: "1",
    items: [
      { id: "title", label: "Attract screen" },
      { id: "boot", label: "Boot sequence" },
      { id: "pre", label: "Pre-session" },
    ],
  },
  {
    heading: "2 · In session",
    short: "2",
    items: [
      { id: "live", label: "Live HUD (real gateway)" },
      { id: "deck", label: "Deck (real gateway)" },
      { id: "session", label: "Session HUD" },
      { id: "artmatrix", label: "HUD on matrix art" },
      { id: "artcontra", label: "Fire on city art" },
      { id: "desk", label: "Agent desk" },
      { id: "detail", label: "Trade detail" },
      { id: "calc", label: "Size calculator" },
    ],
  },
  {
    heading: "3 · After the session",
    short: "3",
    items: [
      { id: "clear", label: "Session clear" },
      { id: "over", label: "Session over" },
      { id: "report", label: "Report" },
      { id: "journal", label: "Journal" },
      { id: "replay", label: "Replay" },
      { id: "history", label: "History" },
      { id: "score", label: "Process score" },
    ],
  },
  {
    heading: "4 · Setup & reference",
    short: "4",
    items: [
      { id: "pad", label: "Gamepad" },
      { id: "data", label: "Data" },
      { id: "settings", label: "Settings" },
      { id: "philosophy", label: "Philosophy" },
    ],
  },
];

const SCREENS: Record<Exclude<ScreenId, "session">, () => JSX.Element> = {
  // The two surfaces wired to the real gateway; the rest are the design prototype.
  live: LiveHudScreen,
  deck: Deck,
  title: AttractScreen,
  boot: BootScreen,
  pre: PreSessionScreen,
  artmatrix: MatrixHudScreen,
  artcontra: CityFireScreen,
  desk: AgentDeskScreen,
  detail: TradeDetailScreen,
  calc: SizeCalculatorScreen,
  clear: SessionClearScreen,
  over: SessionOverScreen,
  report: ReportScreen,
  journal: JournalScreen,
  replay: ReplayScreen,
  history: HistoryScreen,
  score: ProcessScoreScreen,
  pad: GamepadScreen,
  data: DataScreen,
  settings: SettingsScreen,
  philosophy: PhilosophyScreen,
};

const RAIL = 48;
const OPEN = 216;

const navStyle = (active: boolean): CSSProperties => ({
  display: "flex",
  alignItems: "center",
  gap: 10,
  height: 32,
  padding: "0 12px 0 16px",
  width: OPEN,
  boxSizing: "border-box",
  textAlign: "left",
  border: 0,
  borderLeft: `2px solid ${active ? "var(--phos-400)" : "transparent"}`,
  background: active ? "var(--surface-selected)" : "transparent",
  color: active ? "var(--phos-300)" : "var(--text-secondary)",
  fontFamily: "var(--font-core)",
  fontSize: 11,
  fontWeight: 700,
  letterSpacing: ".12em",
  textTransform: "uppercase",
  cursor: "pointer",
  ...(active ? { textShadow: "var(--glow-text)" } : null),
});

const headingStyle: CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 10,
  fontSize: 9,
  letterSpacing: ".18em",
  textTransform: "uppercase",
  color: "var(--text-disabled)",
};

/* The dot column sits under the rail's centre line, so items stay readable
   as markers while the labels are clipped away. */
const dotStyle = (active: boolean): CSSProperties => ({
  flex: "none",
  width: 8,
  height: 8,
  borderRadius: 1,
  border: `1px solid ${active ? "var(--phos-400)" : "var(--text-disabled)"}`,
  background: active ? "var(--phos-400)" : "transparent",
  ...(active ? { boxShadow: "var(--glow-text)" } : null),
});

const shortStyle: CSSProperties = {
  flex: "none",
  width: 8,
  textAlign: "center",
};

export default function App() {
  const [screen, setScreen] = useState<ScreenId>("title");
  const [hud, setHud] = useState<HudState>("live");

  return (
    <BgmProvider>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: `${RAIL}px 1fr`,
          minHeight: "100vh",
          background: "var(--surface-app)",
          fontFamily: "var(--font-core)",
          color: "var(--text-body)",
        }}
      >
        <nav
          className="ev-nav"
          style={{
            borderRight: "1px solid var(--line-hairline)",
            background: "var(--black-2)",
            display: "grid",
            gridTemplateRows: "44px 1fr auto",
            alignContent: "start",
            position: "fixed",
            left: 0,
            top: 0,
            height: "100vh",
            zIndex: 30,
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              padding: "0 12px",
              borderBottom: "1px solid var(--line-hairline)",
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
              EV
              <span className="ev-nav-label" style={{ color: "var(--arcade-red)" }}>
                GAMEPAD
              </span>
            </span>
          </div>

          <div
            className="ev-nav-scroll"
            style={{
              padding: "10px 0",
              display: "grid",
              gap: 2,
              alignContent: "start",
            }}
          >
            {GROUPS.map((group, gi) => (
              <div key={group.heading} style={{ display: "grid", gap: 2 }}>
                <div
                  style={{ ...headingStyle, padding: gi === 0 ? "6px 12px 6px 18px" : "14px 12px 6px 18px" }}
                >
                  <span className="ev-nav-short" style={shortStyle}>
                    {group.short}
                  </span>
                  <span className="ev-nav-label">{group.heading}</span>
                </div>
                {group.items.map((item) => (
                  <button
                    key={item.id}
                    className="ev-nav-item"
                    onClick={() => setScreen(item.id)}
                    style={navStyle(screen === item.id)}
                    title={item.label}
                  >
                    <span style={dotStyle(screen === item.id)} />
                    <span className="ev-nav-label">{item.label}</span>
                  </button>
                ))}

                {/* the HUD's six states hang off the in-session group */}
                {gi === 1 ? (
                  <>
                    <div style={{ ...headingStyle, padding: "14px 12px 6px 18px" }}>
                      <span className="ev-nav-short" style={shortStyle}>
                        S
                      </span>
                      <span className="ev-nav-label">Session state</span>
                    </div>
                    {HUD_STATES.map((state) => (
                      <button
                        key={state.id}
                        className="ev-nav-item"
                        onClick={() => {
                          setScreen("session");
                          setHud(state.id);
                        }}
                        style={navStyle(screen === "session" && hud === state.id)}
                        title={state.label}
                      >
                        <span style={dotStyle(screen === "session" && hud === state.id)} />
                        <span className="ev-nav-label">{state.label}</span>
                      </button>
                    ))}
                  </>
                ) : null}
              </div>
            ))}
          </div>

          <div
            style={{
              borderTop: "1px solid var(--line-hairline)",
              padding: 12,
              display: "grid",
              gap: 6,
            }}
          >
            <span style={{ ...headingStyle, padding: "0 0 0 6px" }}>
              <span className="ev-nav-short" style={shortStyle}>
                &gt;
              </span>
              <span className="ev-nav-label">Click-through</span>
            </span>
            <span
              className="ev-nav-label"
              style={{
                width: OPEN - 24,
                fontFamily: "var(--font-terminal)",
                fontSize: 15,
                color: "var(--phos-600)",
              }}
            >
              &gt; screens are real, data is fixed.
            </span>
          </div>
        </nav>

        <main
          style={{
            /* the rail is fixed, so main claims the second column explicitly */
            gridColumn: 2,
            padding: 20,
            overflow: "auto",
            display: "grid",
            justifyItems: "start",
            alignContent: "start",
            gap: 12,
          }}
        >
          {screen === "session" ? (
            <SessionHudScreen state={hud} />
          ) : (
            (() => {
              const Screen = SCREENS[screen];
              return <Screen />;
            })()
          )}
        </main>
      </div>
    </BgmProvider>
  );
}
