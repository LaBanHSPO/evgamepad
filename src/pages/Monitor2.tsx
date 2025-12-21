import { useState, useCallback, useEffect } from "react";
import { SystemHeader } from "@/components/SystemHeader";
import { GamepadQuickTrade } from "@/components/GamepadQuickTrade";
import { GamepadPositions } from "@/components/GamepadPositions";
import { GamepadControllerHints } from "@/components/GamepadControllerHints";

const Monitor2 = () => {
  const [activeSection, setActiveSection] = useState<"trade" | "positions">("trade");

  // Gamepad navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "ArrowLeft" || e.key === "q") {
        setActiveSection("trade");
      } else if (e.key === "ArrowRight" || e.key === "e") {
        setActiveSection("positions");
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <div className="min-h-screen bg-background text-foreground p-4 relative overflow-hidden">
      {/* Scanlines overlay */}
      <div className="scanlines" />
      
      {/* CRT flicker effect */}
      <div className="crt-flicker" />
      
      {/* Main content */}
      <div className="relative z-10 max-w-7xl mx-auto space-y-4">
        <SystemHeader monitorNumber={2} title="TRADE OPERATIONS" />
        
        {/* Section Tabs - Big gamepad-friendly buttons */}
        <div className="grid grid-cols-2 gap-4">
          <button
            onClick={() => setActiveSection("trade")}
            className={`gamepad-tile group ${
              activeSection === "trade" ? "gamepad-tile-active" : ""
            }`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="gamepad-button-hint">LB</div>
                <span className="text-xl font-display tracking-wider">QUICK TRADE</span>
              </div>
              {activeSection === "trade" && (
                <div className="w-3 h-3 rounded-full bg-terminal-green animate-pulse" />
              )}
            </div>
          </button>
          
          <button
            onClick={() => setActiveSection("positions")}
            className={`gamepad-tile group ${
              activeSection === "positions" ? "gamepad-tile-active" : ""
            }`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="gamepad-button-hint">RB</div>
                <span className="text-xl font-display tracking-wider">POSITIONS</span>
              </div>
              {activeSection === "positions" && (
                <div className="w-3 h-3 rounded-full bg-terminal-green animate-pulse" />
              )}
            </div>
          </button>
        </div>

        {/* Main Content Area */}
        <div className="min-h-[60vh]">
          {activeSection === "trade" ? (
            <GamepadQuickTrade />
          ) : (
            <GamepadPositions />
          )}
        </div>

        {/* Controller Hints Footer */}
        <GamepadControllerHints />
      </div>
    </div>
  );
};

export default Monitor2;
