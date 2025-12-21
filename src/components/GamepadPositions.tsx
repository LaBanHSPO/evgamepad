import { useState, useEffect } from "react";
import { TrendingUp, TrendingDown, DollarSign, X, Edit3 } from "lucide-react";

const positions = [
  {
    id: "POS-001",
    pair: "BTC/USD",
    type: "LONG",
    entry: "96,850.00",
    current: "97,842.50",
    size: "0.25",
    pnl: "+992.50",
    pnlPercent: "+10.25%",
  },
  {
    id: "POS-002",
    pair: "ETH/USD",
    type: "LONG",
    entry: "3,420.00",
    current: "3,456.78",
    size: "5.0",
    pnl: "+183.90",
    pnlPercent: "+1.08%",
  },
  {
    id: "POS-003",
    pair: "SOL/USD",
    type: "SHORT",
    entry: "192.50",
    current: "187.45",
    size: "50",
    pnl: "+252.50",
    pnlPercent: "+2.63%",
  },
];

export const GamepadPositions = () => {
  const [selectedPosition, setSelectedPosition] = useState(0);
  const [actionMode, setActionMode] = useState<"select" | "action">("select");
  const [selectedAction, setSelectedAction] = useState(0);

  const totalPnL = positions.reduce(
    (acc, pos) => acc + parseFloat(pos.pnl.replace(/[+,]/g, "")),
    0
  );

  // Keyboard/gamepad navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (actionMode === "select") {
        switch (e.key) {
          case "ArrowUp":
            if (selectedPosition > 0) setSelectedPosition(selectedPosition - 1);
            break;
          case "ArrowDown":
            if (selectedPosition < positions.length - 1) setSelectedPosition(selectedPosition + 1);
            break;
          case "Enter":
          case " ":
            setActionMode("action");
            break;
        }
      } else {
        switch (e.key) {
          case "ArrowLeft":
            setSelectedAction(0);
            break;
          case "ArrowRight":
            setSelectedAction(1);
            break;
          case "Escape":
            setActionMode("select");
            break;
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [actionMode, selectedPosition, selectedAction]);

  return (
    <div className="space-y-4">
      {/* Total P&L Header */}
      <div className="panel">
        <div className="flex items-center justify-between p-4">
          <div className="flex items-center gap-3">
            <DollarSign className="w-8 h-8 text-terminal-green" />
            <div>
              <div className="text-sm text-muted-foreground font-mono">TOTAL UNREALIZED P&L</div>
              <div className="text-4xl font-mono font-bold text-terminal-green">
                +${totalPnL.toFixed(2)}
              </div>
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm text-muted-foreground font-mono">ACTIVE POSITIONS</div>
            <div className="text-4xl font-display text-primary">{positions.length}</div>
          </div>
        </div>
      </div>

      {/* Position Cards - Big gamepad-friendly */}
      <div className="space-y-3">
        {positions.map((pos, index) => {
          const isLong = pos.type === "LONG";
          const isProfitable = pos.pnl.startsWith("+");
          const isSelected = selectedPosition === index;

          return (
            <button
              key={pos.id}
              onClick={() => {
                setSelectedPosition(index);
                setActionMode("action");
              }}
              className={`w-full text-left gamepad-position-card ${
                isSelected ? "gamepad-position-card-active" : ""
              } ${isProfitable ? "border-terminal-green/30" : "border-danger-red/30"}`}
            >
              <div className="flex items-center justify-between">
                {/* Left: Position Info */}
                <div className="flex items-center gap-4">
                  <div
                    className={`flex items-center justify-center w-16 h-16 rounded-xl ${
                      isLong ? "bg-terminal-green/20" : "bg-danger-red/20"
                    }`}
                  >
                    {isLong ? (
                      <TrendingUp className={`w-8 h-8 text-terminal-green`} />
                    ) : (
                      <TrendingDown className={`w-8 h-8 text-danger-red`} />
                    )}
                  </div>

                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-2xl font-display text-primary">{pos.pair}</span>
                      <span
                        className={`px-2 py-0.5 rounded text-sm font-mono ${
                          isLong
                            ? "bg-terminal-green/20 text-terminal-green"
                            : "bg-danger-red/20 text-danger-red"
                        }`}
                      >
                        {pos.type}
                      </span>
                    </div>
                    <div className="text-sm text-muted-foreground font-mono mt-1">
                      SIZE: {pos.size} | ENTRY: ${pos.entry}
                    </div>
                  </div>
                </div>

                {/* Right: P&L */}
                <div className="text-right">
                  <div
                    className={`text-3xl font-mono font-bold ${
                      isProfitable ? "text-terminal-green" : "text-danger-red"
                    }`}
                  >
                    ${pos.pnl}
                  </div>
                  <div
                    className={`text-lg font-mono ${
                      isProfitable ? "text-terminal-green/70" : "text-danger-red/70"
                    }`}
                  >
                    {pos.pnlPercent}
                  </div>
                </div>

                {/* Selection indicator */}
                {isSelected && (
                  <div className="ml-4">
                    <div className="w-4 h-4 rounded-full bg-primary animate-pulse" />
                  </div>
                )}
              </div>

              {/* Action buttons when selected */}
              {isSelected && actionMode === "action" && (
                <div className="flex gap-4 mt-4 pt-4 border-t border-primary/20">
                  <button
                    className={`flex-1 py-4 rounded-lg border-2 font-display text-lg transition-all flex items-center justify-center gap-3 ${
                      selectedAction === 0
                        ? "bg-primary/20 border-primary text-primary"
                        : "bg-panel-bg/50 border-muted/30 text-muted-foreground"
                    }`}
                  >
                    <div className="gamepad-button-hint">X</div>
                    <Edit3 className="w-5 h-5" />
                    <span>MODIFY</span>
                  </button>
                  <button
                    className={`flex-1 py-4 rounded-lg border-2 font-display text-lg transition-all flex items-center justify-center gap-3 ${
                      selectedAction === 1
                        ? "bg-danger-red/20 border-danger-red text-danger-red"
                        : "bg-panel-bg/50 border-muted/30 text-muted-foreground"
                    }`}
                  >
                    <div className="gamepad-button-hint bg-danger-red/20 text-danger-red">B</div>
                    <X className="w-5 h-5" />
                    <span>CLOSE</span>
                  </button>
                </div>
              )}
            </button>
          );
        })}
      </div>

      {/* Close All Button */}
      <button className="w-full py-5 rounded-xl border-2 border-danger-red/50 bg-danger-red/10 text-danger-red font-display text-xl tracking-wider hover:bg-danger-red/20 transition-all flex items-center justify-center gap-3">
        <div className="gamepad-button-hint bg-danger-red/20 text-danger-red">Y</div>
        <span>CLOSE ALL POSITIONS</span>
      </button>
    </div>
  );
};
