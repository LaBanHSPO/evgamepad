import { useState, useEffect, useCallback } from "react";
import { TrendingUp, TrendingDown, Zap, Shield, Target } from "lucide-react";
import { useSocket } from "@/context/SocketContext";
import { toast } from "sonner";
import { sfxEmitter } from "@/services/sfx-event-emitter";

/**
 * Order result from Socket.IO
 */
interface OrderResult {
  success: boolean;
  order?: {
    ticket?: string | number;
    symbol?: string;
    price?: number;
    volume?: number;
    type?: number; // 0 = buy, 1 = sell
  };
  error?: string;
}

/**
 * Socket.IO error response
 */
interface SocketError {
  message?: string;
  error?: string;
}

const pairs = [
  // { symbol: "BTC/USD", price: "97,842.50", change: "+2.34%" },
  // { symbol: "ETH/USD", price: "3,456.78", change: "+1.87%" },
  // { symbol: "SOL/USD", price: "187.45", change: "+5.67%" },
  { symbol: "XAU/USD", price: "2,634.50", change: "-0.45%" },
];

const sizes = ["0.01", "0.05", "0.10", "0.25", "0.50"];

export const GamepadQuickTrade = () => {
  const [selectedPair, setSelectedPair] = useState(0);
  const [selectedSize, setSelectedSize] = useState(2);
  const [side, setSide] = useState<"BUY" | "SELL">("BUY");
  const [focusArea, setFocusArea] = useState<"pair" | "size" | "action">("pair");
  const [isProcessing, setIsProcessing] = useState(false);

  const { socket, isConnected } = useSocket();

  const handleTradeResponse = useCallback((data: OrderResult) => {
    setIsProcessing(false);
    console.log("Order response:", data);
    if (data.success) {
      toast.success(`Order Executed: ${data.order?.ticket || "Success"}`, {
        description: `${data.order?.symbol} @ ${data.order?.price}`,
        duration: 3000,
      });

      // Trigger SFX for successful trade
      const tradeAmount = data.order?.volume || 0;
      const tradeType = data.order?.type === 0 ? 'trade:buy' : 'trade:sell';
      sfxEmitter.emit({
        type: tradeType,
        metadata: {
          amount: tradeAmount,
          symbol: data.order?.symbol
        }
      });
    } else {
      toast.error("Order Failed", {
        description: data.error || "Unknown error",
        duration: 5000,
      });
    }
  }, []);

  const handleError = useCallback((err: SocketError) => {
    setIsProcessing(false);
    const msg = err?.message || err?.error || "Unknown error";
    toast.error("Trade Error", { description: msg });
  }, []);

  useEffect(() => {
    if (!socket) return;

    socket.on("order_result", handleTradeResponse);
    socket.on("error", handleError);

    return () => {
      socket.off("order_result", handleTradeResponse);
      socket.off("error", handleError);
    };
  }, [socket, handleTradeResponse, handleError]);

  const executeTrade = () => {
    if (!socket || !isConnected) {
      toast.error("Not Connected", { description: "Socket.IO server unreachable" });
      return;
    }

    if (isProcessing) return;

    const currentPair = pairs[selectedPair];
    const volume = parseFloat(sizes[selectedSize]);
    const symbol = currentPair.symbol.replace("/", "");

    setIsProcessing(true);
    const event = side === "BUY" ? "buy" : "sell";

    console.log(`Emitting ${event}: ${symbol} ${volume}`);

    socket.emit(event, {
      symbol: symbol,
      volume: volume,
      sl: 0.0,
      tp: 0.0,
    });
  };

  // Keyboard/gamepad navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case "ArrowUp":
          if (focusArea === "size") setFocusArea("pair");
          else if (focusArea === "action") setFocusArea("size");
          break;
        case "ArrowDown":
          if (focusArea === "pair") setFocusArea("size");
          else if (focusArea === "size") setFocusArea("action");
          break;
        case "ArrowLeft":
          if (focusArea === "pair" && selectedPair > 0) setSelectedPair(selectedPair - 1);
          if (focusArea === "size" && selectedSize > 0) setSelectedSize(selectedSize - 1);
          if (focusArea === "action") setSide("BUY");
          break;
        case "ArrowRight":
          if (focusArea === "pair" && selectedPair < pairs.length - 1) setSelectedPair(selectedPair + 1);
          if (focusArea === "size" && selectedSize < sizes.length - 1) setSelectedSize(selectedSize + 1);
          if (focusArea === "action") setSide("SELL");
          break;
        case "Enter": // A Button
          if (focusArea === "action") {
            executeTrade();
          }
          break;
        case "x": // X Button -> Set BUY
          setSide("BUY");
          setFocusArea("action");
          break;
        case "b": // B Button -> Set SELL (if not used for back)
          setSide("SELL");
          setFocusArea("action");
          break;
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [focusArea, selectedPair, selectedSize, side, socket, isConnected, isProcessing]);

  const currentPair = pairs[selectedPair];

  return (
    <div className="space-y-6">
      {/* Asset Selection - Big tiles */}
      <div className="panel">
        <div className="panel-header">
          <div className="flex items-center gap-2">
            <Target className="w-5 h-5 text-primary" />
            <span className="panel-title">SELECT ASSET</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="gamepad-button-hint text-xs">◄►</div>
            <span className="text-xs text-muted-foreground">D-PAD</span>
          </div>
        </div>

        <div className={`grid grid-cols-2 lg:grid-cols-4 gap-3 ${focusArea === "pair" ? "ring-2 ring-primary/50 rounded-lg p-2" : "p-2"}`}>
          {pairs.map((pair, index) => (
            <button
              key={pair.symbol}
              onClick={() => {
                setSelectedPair(index);
                setFocusArea("pair");
              }}
              className={`gamepad-tile-sm ${selectedPair === index ? "gamepad-tile-active" : ""
                }`}
            >
              <div className="text-lg font-display text-primary">{pair.symbol}</div>
              <div className="text-2xl font-mono font-bold mt-1">${pair.price}</div>
              <div className={`text-sm font-mono mt-1 ${pair.change.startsWith("+") ? "text-terminal-green" : "text-danger-red"
                }`}>
                {pair.change}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Size Selection - Slider-like big buttons */}
      <div className="panel">
        <div className="panel-header">
          <div className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-secondary" />
            <span className="panel-title">POSITION SIZE</span>
          </div>
          <div className="text-xl font-mono text-primary font-bold">
            {sizes[selectedSize]} {currentPair.symbol.split("/")[0]}
          </div>
        </div>

        <div className={`flex gap-2 ${focusArea === "size" ? "ring-2 ring-primary/50 rounded-lg p-2" : "p-2"}`}>
          {sizes.map((size, index) => (
            <button
              key={size}
              onClick={() => {
                setSelectedSize(index);
                setFocusArea("size");
              }}
              className={`flex-1 py-4 text-lg font-mono rounded-lg border-2 transition-all ${selectedSize === index
                ? "bg-primary/30 border-primary text-primary scale-105"
                : "bg-panel-bg/50 border-primary/20 text-muted-foreground hover:border-primary/50"
                }`}
            >
              {size}
            </button>
          ))}
        </div>
      </div>

      {/* Action Buttons - Massive gamepad-friendly */}
      <div className={`grid grid-cols-2 gap-6 ${focusArea === "action" ? "ring-2 ring-primary/50 rounded-lg p-3" : "p-1"}`}>
        <button
          onClick={() => {
            setSide("BUY");
            setFocusArea("action");
          }}
          className={`relative py-8 rounded-xl border-4 transition-all font-display text-2xl tracking-wider ${side === "BUY"
            ? "bg-terminal-green/20 border-terminal-green text-terminal-green scale-[1.02] shadow-[0_0_30px_rgba(34,197,94,0.3)]"
            : "bg-panel-bg/50 border-muted/30 text-muted-foreground hover:border-terminal-green/50"
            }`}
        >
          <div className="absolute top-2 left-3">
            <div className="gamepad-button-hint bg-terminal-green/20 text-terminal-green">X</div>
          </div>
          <TrendingUp className="w-10 h-10 mx-auto mb-2" />
          <div>BUY</div>
          <div className="text-sm font-mono mt-1 opacity-70">+{currentPair.price}</div>
        </button>

        <button
          onClick={() => {
            setSide("SELL");
            setFocusArea("action");
          }}
          className={`relative py-8 rounded-xl border-4 transition-all font-display text-2xl tracking-wider ${side === "SELL"
            ? "bg-danger-red/20 border-danger-red text-danger-red scale-[1.02] shadow-[0_0_30px_rgba(239,68,68,0.3)]"
            : "bg-panel-bg/50 border-muted/30 text-muted-foreground hover:border-danger-red/50"
            }`}
        >
          <div className="absolute top-2 left-3">
            <div className="gamepad-button-hint bg-danger-red/20 text-danger-red">B</div>
          </div>
          <TrendingDown className="w-10 h-10 mx-auto mb-2" />
          <div>SELL</div>
          <div className="text-sm font-mono mt-1 opacity-70">-{currentPair.price}</div>
        </button>
      </div>

      {/* Execute Button - The big one */}
      <button
        onClick={executeTrade}
        disabled={isProcessing}
        className={`w-full py-6 rounded-xl border-4 font-display text-3xl tracking-widest transition-all ${isProcessing ? "opacity-50 cursor-not-allowed" : ""} ${side === "BUY"
          ? "bg-terminal-green text-background border-terminal-green hover:scale-[1.01] shadow-[0_0_40px_rgba(34,197,94,0.4)]"
          : "bg-danger-red text-background border-danger-red hover:scale-[1.01] shadow-[0_0_40px_rgba(239,68,68,0.4)]"
          }`}
      >
        <div className="flex items-center justify-center gap-4">
          <div className="gamepad-button-hint bg-background/20 text-background border-background/30">A</div>
          <span>{isProcessing ? "EXECUTING..." : `EXECUTE ${side}`}</span>
        </div>
      </button>

      {/* Risk Info */}
      <div className="flex justify-center gap-8 text-sm font-mono">
        <div className="flex items-center gap-2">
          <Shield className="w-4 h-4 text-danger-red" />
          <span className="text-muted-foreground">RISK:</span>
          <span className="text-primary">$975.00</span>
        </div>
        <div className="flex items-center gap-2">
          <Zap className="w-4 h-4 text-terminal-green" />
          <span className="text-muted-foreground">LEVERAGE:</span>
          <span className="text-secondary">10x</span>
        </div>
      </div>

      {!isConnected && (
        <div className="text-center text-xs text-danger-red animate-pulse">
          DISCONNECTED FROM TRADING SERVER
        </div>
      )}
    </div>
  );
};
