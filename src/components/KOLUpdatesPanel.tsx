import { Users, MessageCircle, TrendingUp, TrendingDown, Minus, ExternalLink } from "lucide-react";

const kolUpdates = [
  {
    id: 1,
    name: "CryptoKing",
    handle: "@cryptoking",
    avatar: "CK",
    message: "BTC looking strong at 97k support. Expecting breakout to 100k soon. Long positions loaded.",
    sentiment: "bullish",
    time: "2m ago",
    followers: "1.2M",
    reliability: 87
  },
  {
    id: 2,
    name: "TradeMaster",
    handle: "@trademaster",
    avatar: "TM",
    message: "ETH/BTC ratio showing weakness. Rotating some ETH to BTC for now.",
    sentiment: "neutral",
    time: "8m ago",
    followers: "890K",
    reliability: 92
  },
  {
    id: 3,
    name: "WhaleAlert",
    handle: "@whalealert",
    avatar: "WA",
    message: "⚠️ Large BTC transfer detected: 5,000 BTC moved to exchange. Potential sell pressure incoming.",
    sentiment: "bearish",
    time: "15m ago",
    followers: "2.1M",
    reliability: 95
  },
  {
    id: 4,
    name: "DeFiGuru",
    handle: "@defiguru",
    avatar: "DG",
    message: "SOL ecosystem heating up. Multiple airdrops incoming. Accumulating SOL here.",
    sentiment: "bullish",
    time: "23m ago",
    followers: "567K",
    reliability: 78
  }
];

export const KOLUpdatesPanel = () => {
  const getSentimentIcon = (sentiment: string) => {
    switch (sentiment) {
      case "bullish":
        return <TrendingUp className="w-4 h-4 text-terminal-green" />;
      case "bearish":
        return <TrendingDown className="w-4 h-4 text-danger-red" />;
      default:
        return <Minus className="w-4 h-4 text-muted-foreground" />;
    }
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case "bullish":
        return "border-l-terminal-green bg-terminal-green/5";
      case "bearish":
        return "border-l-danger-red bg-danger-red/5";
      default:
        return "border-l-muted-foreground bg-muted/5";
    }
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <div className="flex items-center gap-2">
          <Users className="w-4 h-4 text-primary" />
          <h2 className="panel-title">KOL UPDATES</h2>
        </div>
        <div className="flex items-center gap-2">
          <MessageCircle className="w-3 h-3 text-terminal-green animate-pulse" />
          <span className="text-xs text-terminal-green">LIVE FEED</span>
        </div>
      </div>

      <div className="space-y-3 max-h-[300px] overflow-y-auto scrollbar-thin scrollbar-thumb-primary/20">
        {kolUpdates.map((kol) => (
          <div
            key={kol.id}
            className={`p-3 rounded border-l-2 ${getSentimentColor(kol.sentiment)} transition-all hover:bg-muted/10`}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-primary/20 border border-primary/40 flex items-center justify-center text-xs font-bold text-primary">
                  {kol.avatar}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-foreground">{kol.name}</span>
                    {getSentimentIcon(kol.sentiment)}
                  </div>
                  <span className="text-xs text-muted-foreground">{kol.handle} • {kol.followers}</span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <div className="text-xs">
                  <span className="text-muted-foreground">Trust: </span>
                  <span className={kol.reliability >= 85 ? "text-terminal-green" : kol.reliability >= 70 ? "text-primary" : "text-danger-red"}>
                    {kol.reliability}%
                  </span>
                </div>
                <ExternalLink className="w-3 h-3 text-muted-foreground cursor-pointer hover:text-primary" />
              </div>
            </div>
            <p className="text-sm text-foreground/80 mt-2 leading-relaxed">{kol.message}</p>
            <span className="text-xs text-muted-foreground mt-1 block">{kol.time}</span>
          </div>
        ))}
      </div>

      <div className="mt-3 pt-3 border-t border-border/30 flex items-center justify-between text-xs text-muted-foreground">
        <span>Tracking 24 KOLs</span>
        <span className="text-primary cursor-pointer hover:underline">View All →</span>
      </div>
    </div>
  );
};
