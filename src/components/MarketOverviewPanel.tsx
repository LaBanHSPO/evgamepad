import { TrendingUp, TrendingDown, Activity } from "lucide-react";

const marketData = [
  { pair: "BTC/USD", price: "97,842.50", change: "+2.34%", trend: "up", volume: "2.4B" },
  { pair: "ETH/USD", price: "3,456.78", change: "+1.87%", trend: "up", volume: "1.2B" },
  { pair: "EUR/USD", price: "1.0845", change: "-0.12%", trend: "down", volume: "890M" },
  { pair: "GBP/USD", price: "1.2634", change: "+0.08%", trend: "up", volume: "456M" },
  { pair: "XAU/USD", price: "2,634.50", change: "-0.45%", trend: "down", volume: "234M" },
  { pair: "SOL/USD", price: "187.45", change: "+5.67%", trend: "up", volume: "567M" },
];

export const MarketOverviewPanel = () => {
  return (
    <div className="panel">
      <div className="panel-header">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-primary animate-pulse" />
          <span className="panel-title">LIVE MARKET FEED</span>
        </div>
        <div className="status-indicator online">
          <span className="w-2 h-2 rounded-full bg-terminal-green animate-pulse" />
          <span className="text-xs">STREAMING</span>
        </div>
      </div>

      <div className="space-y-1">
        {/* Header row */}
        <div className="grid grid-cols-5 gap-2 text-xs text-muted-foreground px-2 py-1 border-b border-primary/20">
          <span>PAIR</span>
          <span className="text-right">PRICE</span>
          <span className="text-right">CHANGE</span>
          <span className="text-right">VOLUME</span>
          <span className="text-center">TREND</span>
        </div>

        {/* Data rows */}
        {marketData.map((item, index) => (
          <div
            key={item.pair}
            className={`grid grid-cols-5 gap-2 text-sm px-2 py-2 font-mono transition-colors hover:bg-primary/10 ${
              index % 2 === 0 ? "bg-panel-bg/50" : "bg-background/50"
            }`}
          >
            <span className="text-primary font-bold">{item.pair}</span>
            <span className="text-right text-foreground">{item.price}</span>
            <span
              className={`text-right ${
                item.trend === "up" ? "text-terminal-green" : "text-danger-red"
              }`}
            >
              {item.change}
            </span>
            <span className="text-right text-muted-foreground">{item.volume}</span>
            <div className="flex justify-center">
              {item.trend === "up" ? (
                <TrendingUp className="w-4 h-4 text-terminal-green" />
              ) : (
                <TrendingDown className="w-4 h-4 text-danger-red" />
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-3 pt-2 border-t border-primary/20 flex justify-between text-xs text-muted-foreground">
        <span>Last Update: {new Date().toLocaleTimeString()}</span>
        <span className="text-terminal-green">● 6 PAIRS ACTIVE</span>
      </div>
    </div>
  );
};
