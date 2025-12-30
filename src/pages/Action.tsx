import { useState, useCallback, useEffect } from "react";
import { SystemHeader } from "@/components/SystemHeader";
import { GamepadQuickTrade } from "@/components/GamepadQuickTrade";
import { GamepadPositions } from "@/components/GamepadPositions";
import { GamepadControllerHints } from "@/components/GamepadControllerHints";

import { SocketProvider } from "@/context/SocketContext";

const Action = () => {
  const [activeSection, setActiveSection] = useState<"main" | "history">("main");

  // Gamepad navigation (mapped to q/w/e)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Use q/w/e for tab switching
      if (e.key === "q") {
        setActiveSection("main");
      } else if (e.key === "w") {
        setActiveSection("history");
      };
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <SocketProvider>
      <div className="min-h-screen bg-background text-foreground p-4 relative overflow-hidden">
        {/* Scanlines overlay */}
        <div className="scanlines" />

        {/* CRT flicker effect */}
        <div className="crt-flicker" />

        {/* Main content */}
        <div className="relative z-10 max-w-7xl mx-auto space-y-4">
          <SystemHeader monitorNumber={3} title="ACTIONS" />

          {/* Section Tabs - Big gamepad-friendly buttons */}
          <div className="grid grid-cols-3 gap-4">
            <button
              onClick={() => setActiveSection("main")}
              className={`gamepad-tile group ${activeSection === "main" ? "gamepad-tile-active" : ""
                }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="gamepad-button-hint">Q</div>
                  <span className="text-xl font-display tracking-wider">ENTER</span>
                </div>
                {activeSection === "main" && (
                  <div className="w-3 h-3 rounded-full bg-terminal-green animate-pulse" />
                )}
              </div>
            </button>

            <button
              onClick={() => setActiveSection("history")}
              className={`gamepad-tile group ${activeSection === "history" ? "gamepad-tile-active" : ""
                }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="gamepad-button-hint">E</div>
                  <span className="text-xl font-display tracking-wider">ORDERS</span>
                </div>
                {activeSection === "history" && (
                  <div className="w-3 h-3 rounded-full bg-terminal-green animate-pulse" />
                )}
              </div>
            </button>
          </div>

          {/* Main Content Area */}
          <div className="min-h-[60vh]">
            {activeSection === "history" ? (
              <GamepadPositions />
            ) : activeSection === "main" ? (
              <GamepadQuickTrade />
            ) : (
              <GamepadQuickTrade />
            )}
          </div>

          {/* Controller Hints Footer */}
          <GamepadControllerHints />
        </div>
      </div>
    </SocketProvider>
  );
};

export default Action;
