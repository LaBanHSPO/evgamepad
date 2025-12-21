import { TrendingUp, TrendingDown, DollarSign, Percent } from "lucide-react";

const positions = [
  {
    id: "POS-001",
    pair: "BTC/USD",
    type: "LONG",
    entry: "96,850.00",
    current: "97,842.50",
    size: "0.25",
    leverage: "10x",
    pnl: "+992.50",
    pnlPercent: "+10.25%",
    margin: "2,421.25",
    liquidation: "87,165.00",
  },
  {
    id: "POS-002",
    pair: "ETH/USD",
    type: "LONG",
    entry: "3,420.00",
    current: "3,456.78",
    size: "5.0",
    leverage: "5x",
    pnl: "+183.90",
    pnlPercent: "+1.08%",
    margin: "3,420.00",
    liquidation: "2,736.00",
  },
  {
    id: "POS-003",
    pair: "SOL/USD",
    type: "SHORT",
    entry: "192.50",
    current: "187.45",
    size: "50",
    leverage: "3x",
    pnl: "+252.50",
    pnlPercent: "+2.63%",
    margin: "3,208.33",
    liquidation: "256.67",
  },
];

const totalPnL = positions.reduce((acc, pos) => acc + parseFloat(pos.pnl.replace(/[+,]/g, "")), 0);
const totalMargin = positions.reduce((acc, pos) => acc + parseFloat(pos.margin.replace(/,/g, "")), 0);

export const PositionManagerPanel = () => {
  return (
    <div className="panel">
      <div className="panel-header">
        <div className="flex items-center gap-2">
          <DollarSign className="w-4 h-4 text-terminal-green" />
          <span className="panel-title">POSITION MANAGER</span>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-xs font-mono">
            <span className="text-muted-foreground">TOTAL P&L: </span>
            <span className={totalPnL >= 0 ? "text-terminal-green" : "text-danger-red"}>
              {totalPnL >= 0 ? "+" : ""}${totalPnL.toFixed(2)}
            </span>
          </div>
          <div className="text-xs font-mono">
            <span className="text-muted-foreground">MARGIN USED: </span>
            <span className="text-primary">${totalMargin.toLocaleString()}</span>
          </div>
        </div>
      </div>

      <div className="space-y-3">
        {positions.map((pos) => {
          const isLong = pos.type === "LONG";
          const isProfitable = pos.pnl.startsWith("+");

          return (
            <div
              key={pos.id}
              className={`p-3 rounded border ${
                isProfitable
                  ? "bg-terminal-green/5 border-terminal-green/30"
                  : "bg-danger-red/5 border-danger-red/30"
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-3">
                  <div
                    className={`flex items-center gap-1 px-2 py-0.5 rounded text-xs font-mono font-bold ${
                      isLong
                        ? "bg-terminal-green/20 text-terminal-green"
                        : "bg-danger-red/20 text-danger-red"
                    }`}
                  >
                    {isLong ? (
                      <TrendingUp className="w-3 h-3" />
                    ) : (
                      <TrendingDown className="w-3 h-3" />
                    )}
                    {pos.type}
                  </div>
                  <span className="text-primary font-bold">{pos.pair}</span>
                  <span className="text-xs text-secondary font-mono">{pos.leverage}</span>
                </div>

                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <div
                      className={`text-lg font-mono font-bold ${
                        isProfitable ? "text-terminal-green" : "text-danger-red"
                      }`}
                    >
                      ${pos.pnl}
                    </div>
                    <div
                      className={`text-xs font-mono ${
                        isProfitable ? "text-terminal-green/70" : "text-danger-red/70"
                      }`}
                    >
                      {pos.pnlPercent}
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <button className="px-3 py-1 text-xs font-mono bg-primary/20 text-primary rounded hover:bg-primary/30 transition-colors">
                      MODIFY
                    </button>
                    <button className="px-3 py-1 text-xs font-mono bg-danger-red/20 text-danger-red rounded hover:bg-danger-red/30 transition-colors">
                      CLOSE
                    </button>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-5 gap-4 text-xs">
                <div>
                  <span className="text-muted-foreground">ENTRY</span>
                  <div className="font-mono text-foreground">${pos.entry}</div>
                </div>
                <div>
                  <span className="text-muted-foreground">CURRENT</span>
                  <div className="font-mono text-foreground">${pos.current}</div>
                </div>
                <div>
                  <span className="text-muted-foreground">SIZE</span>
                  <div className="font-mono text-foreground">{pos.size}</div>
                </div>
                <div>
                  <span className="text-muted-foreground">MARGIN</span>
                  <div className="font-mono text-primary">${pos.margin}</div>
                </div>
                <div>
                  <span className="text-muted-foreground">LIQUIDATION</span>
                  <div className="font-mono text-danger-red">${pos.liquidation}</div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-3 pt-2 border-t border-primary/20 flex justify-between text-xs">
        <span className="text-muted-foreground">Active Positions: {positions.length}</span>
        <button className="text-danger-red hover:text-danger-red/80 font-mono transition-colors">
          CLOSE ALL POSITIONS
        </button>
      </div>
    </div>
  );
};
