import { Suspense, lazy, useReducer } from "react";
import type { CSSProperties } from "react";
import { Analytics } from "@vercel/analytics/react";
import { BgmProvider } from "./components/bgm";
import { AgentDeskScreen } from "./screens/AgentDeskScreen";
import { AttractScreen } from "./screens/AttractScreen";
import { BootScreen } from "./screens/BootScreen";
import { CityFireScreen } from "./screens/CityFireScreen";
import { DataScreen } from "./screens/DataScreen";
import { Deck } from "./deck/Deck";
import { SystemPrinciples } from "./journal/SystemPrinciples";
import { ReportBuilder } from "./reports/ReportBuilder";
import { Settings as LiveSettings } from "./settings/Settings";

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
import { SessionHudScreen, HUD_STATES } from "./screens/SessionHudScreen";
import { SessionOverScreen } from "./screens/SessionOverScreen";
import { SettingsScreen } from "./screens/SettingsScreen";
import { SizeCalculatorScreen } from "./screens/SizeCalculatorScreen";
import { TradeDetailScreen } from "./screens/TradeDetailScreen";
import { CabinetProvider, useCabinetInput } from "./journey/Cabinet";
import { initialJourney, reduceJourney } from "./journey/reducer";
import type { ScreenId } from "./journey/types";
import { GameOverlay } from "./overlay/GameOverlay";

/**
 * Playable cabinet. START walks the evening; Menu lists every screen; the rail still warps
 * for design review. Matrix / city artboards poll `/api/arcade`. Live HUD / journal / replay /
 * deck talk to the gateway when it is up.
 */

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
      { id: "reportlive", label: "Report (real gateway)" },
      { id: "report", label: "Report" },
      { id: "journallive", label: "Journal (real gateway)" },
      { id: "journal", label: "Journal" },
      { id: "replaylive", label: "Replay (real gateway)" },
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
      { id: "settingslive", label: "Settings (real gateway)" },
      { id: "settings", label: "Settings" },
      { id: "systemlive", label: "System (real gateway)" },
      { id: "philosophy", label: "Philosophy" },
    ],
  },
];

// `session`, `replaylive` and `journallive` are rendered by hand below: one takes a HUD state and
// the others need a way to hand a cid onward, and none of them fits a zero-argument component.
const SCREENS: Record<Exclude<ScreenId, "session" | "replaylive" | "journallive">,
                      () => JSX.Element> = {
  // Live HUD / deck / journal keep the socket. Matrix and city poll `/api/arcade`.
  live: LiveHudScreen,
  deck: Deck,
  systemlive: SystemPrinciples,
  settingslive: LiveSettings,
  reportlive: ReportBuilder,
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

/**
 * Replay is the only screen that needs a charting library, and most evenings never open it. Loading
 * it on demand keeps ~60 KB gzipped off the HUD's critical path; the chunk is cached by the service
 * worker on first fetch like every other hashed asset.
 */
const Replay = lazy(() => import("./replay/Replay").then((m) => ({ default: m.Replay })));

/** The journal is a large surface and most sessions open the HUD instead; it loads on demand. */
const Journal = lazy(() => import("./journal/Journal").then((m) => ({ default: m.Journal })));

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

function CabinetListeners(): null {
  useCabinetInput();
  return null;
}

export default function App() {
  const [journey, dispatch] = useReducer(reduceJourney, undefined, initialJourney);
  const screen = journey.screen;
  const hud = journey.hud;

  return (
    <CabinetProvider state={journey} dispatch={dispatch}>
      <CabinetListeners />
      <GameOverlay />
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
                    onClick={() => dispatch({ type: "warp", screen: item.id })}
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
                        onClick={() => dispatch({ type: "warp", screen: "session", hud: state.id })}
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
              <span className="ev-nav-label">Play</span>
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
              &gt; START walks the evening. Menu lists every screen.
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
          ) : screen === "journallive" ? (
            // The journal hands a cid to the replay route, which is the review loop the phases
            // were building toward: dashboard -> trade -> the tape it happened on.
            <Suspense fallback={<p style={{ fontFamily: "var(--font-terminal)", color: "var(--phos-400)" }}>&gt; loading the journal…</p>}>
              <Journal
                onReplay={(cid) => dispatch({ type: "replay", cid })}
              />
            </Suspense>
          ) : screen === "replaylive" ? (
            // Mounting replay unmounts the live HUD, taking its agent, poller and socket with it —
            // which is why no order can be placed from this route. B goes back to the journal.
            <Suspense fallback={<p style={{ fontFamily: "var(--font-terminal)", color: "var(--phos-400)" }}>&gt; loading the tape…</p>}>
              <Replay
                cid={journey.replayCid ?? undefined}
                onExit={() => dispatch({ type: "input", action: "back" })}
              />
            </Suspense>
          ) : (
            (() => {
              const Screen = SCREENS[screen];
              return <Screen />;
            })()
          )}
        </main>
      </div>
      </BgmProvider>
      <Analytics />
    </CabinetProvider>
  );
}
