import { useState } from "react";
import { Send, Shield, Zap } from "lucide-react";

export const OrderEntryPanel = () => {
  const [orderType, setOrderType] = useState<"MARKET" | "LIMIT">("LIMIT");
  const [side, setSide] = useState<"BUY" | "SELL">("BUY");
  const [price, setPrice] = useState("97,500.00");
  const [size, setSize] = useState("0.10");
  const [stopLoss, setStopLoss] = useState("");
  const [takeProfit, setTakeProfit] = useState("");

  return (
    <div className="panel h-full">
      <div className="panel-header">
        <div className="flex items-center gap-2">
          <Send className="w-4 h-4 text-primary" />
          <span className="panel-title">ORDER ENTRY</span>
        </div>
        <div className="text-xs font-mono text-terminal-green">BTC/USD</div>
      </div>

      <div className="space-y-4">
        {/* Order Type Toggle */}
        <div className="grid grid-cols-2 gap-2">
          {(["MARKET", "LIMIT"] as const).map((type) => (
            <button
              key={type}
              onClick={() => setOrderType(type)}
              className={`py-2 text-sm font-mono rounded border transition-colors ${
                orderType === type
                  ? "bg-primary/20 border-primary text-primary"
                  : "bg-panel-bg border-primary/20 text-muted-foreground hover:border-primary/50"
              }`}
            >
              {type}
            </button>
          ))}
        </div>

        {/* Buy/Sell Toggle */}
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={() => setSide("BUY")}
            className={`py-3 text-sm font-mono font-bold rounded transition-colors ${
              side === "BUY"
                ? "bg-terminal-green/20 border-2 border-terminal-green text-terminal-green"
                : "bg-panel-bg border border-primary/20 text-muted-foreground hover:border-terminal-green/50"
            }`}
          >
            LONG / BUY
          </button>
          <button
            onClick={() => setSide("SELL")}
            className={`py-3 text-sm font-mono font-bold rounded transition-colors ${
              side === "SELL"
                ? "bg-danger-red/20 border-2 border-danger-red text-danger-red"
                : "bg-panel-bg border border-primary/20 text-muted-foreground hover:border-danger-red/50"
            }`}
          >
            SHORT / SELL
          </button>
        </div>

        {/* Price Input (for LIMIT orders) */}
        {orderType === "LIMIT" && (
          <div>
            <label className="block text-xs text-muted-foreground mb-1">PRICE (USD)</label>
            <input
              type="text"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              className="w-full bg-panel-bg border border-primary/30 rounded px-3 py-2 font-mono text-foreground focus:border-primary focus:outline-none"
            />
          </div>
        )}

        {/* Size Input */}
        <div>
          <label className="block text-xs text-muted-foreground mb-1">SIZE (BTC)</label>
          <input
            type="text"
            value={size}
            onChange={(e) => setSize(e.target.value)}
            className="w-full bg-panel-bg border border-primary/30 rounded px-3 py-2 font-mono text-foreground focus:border-primary focus:outline-none"
          />
          <div className="flex gap-2 mt-2">
            {["25%", "50%", "75%", "100%"].map((pct) => (
              <button
                key={pct}
                className="flex-1 py-1 text-xs font-mono bg-panel-bg border border-primary/20 rounded hover:border-primary/50 text-muted-foreground hover:text-primary transition-colors"
              >
                {pct}
              </button>
            ))}
          </div>
        </div>

        {/* Stop Loss / Take Profit */}
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="block text-xs text-muted-foreground mb-1 flex items-center gap-1">
              <Shield className="w-3 h-3 text-danger-red" />
              STOP LOSS
            </label>
            <input
              type="text"
              value={stopLoss}
              onChange={(e) => setStopLoss(e.target.value)}
              placeholder="96,000.00"
              className="w-full bg-panel-bg border border-danger-red/30 rounded px-2 py-1.5 font-mono text-sm text-foreground focus:border-danger-red focus:outline-none placeholder:text-muted-foreground/50"
            />
          </div>
          <div>
            <label className="block text-xs text-muted-foreground mb-1 flex items-center gap-1">
              <Zap className="w-3 h-3 text-terminal-green" />
              TAKE PROFIT
            </label>
            <input
              type="text"
              value={takeProfit}
              onChange={(e) => setTakeProfit(e.target.value)}
              placeholder="100,000.00"
              className="w-full bg-panel-bg border border-terminal-green/30 rounded px-2 py-1.5 font-mono text-sm text-foreground focus:border-terminal-green focus:outline-none placeholder:text-muted-foreground/50"
            />
          </div>
        </div>

        {/* Submit Button */}
        <button
          className={`w-full py-3 font-mono font-bold rounded transition-all ${
            side === "BUY"
              ? "bg-terminal-green text-background hover:bg-terminal-green/80"
              : "bg-danger-red text-background hover:bg-danger-red/80"
          }`}
        >
          {side === "BUY" ? "EXECUTE LONG" : "EXECUTE SHORT"}
        </button>

        {/* Risk Warning */}
        <div className="text-xs text-center text-muted-foreground font-mono">
          EST. RISK: <span className="text-primary">$975.00</span> (1% ACCOUNT)
        </div>
      </div>
    </div>
  );
};
