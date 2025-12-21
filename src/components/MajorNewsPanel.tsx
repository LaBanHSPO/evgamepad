import { Newspaper, AlertCircle, TrendingUp, TrendingDown, Clock, ExternalLink } from "lucide-react";

const newsData = [
  {
    id: 1,
    title: "Fed signals potential rate pause in upcoming meeting",
    source: "Reuters",
    time: "5m ago",
    impact: "high",
    sentiment: "bullish",
    category: "MACRO",
    summary: "Federal Reserve officials hint at maintaining current rates, citing stable inflation data."
  },
  {
    id: 2,
    title: "BlackRock Bitcoin ETF sees $500M inflow",
    source: "Bloomberg",
    time: "18m ago",
    impact: "high",
    sentiment: "bullish",
    category: "INSTITUTIONAL",
    summary: "Record single-day inflow for IBIT as institutional demand continues to surge."
  },
  {
    id: 3,
    title: "SEC delays decision on Ethereum spot ETF",
    source: "CoinDesk",
    time: "45m ago",
    impact: "medium",
    sentiment: "bearish",
    category: "REGULATORY",
    summary: "Commission extends review period by 60 days, citing need for more public comment."
  },
  {
    id: 4,
    title: "Binance announces expansion into new markets",
    source: "The Block",
    time: "1h ago",
    impact: "medium",
    sentiment: "bullish",
    category: "EXCHANGE",
    summary: "Exchange receives regulatory approval in 3 new jurisdictions."
  },
  {
    id: 5,
    title: "Large whale moves 10,000 BTC to cold storage",
    source: "Whale Alert",
    time: "2h ago",
    impact: "low",
    sentiment: "bullish",
    category: "ON-CHAIN",
    summary: "Long-term holder signal as coins move off exchanges."
  }
];

export const MajorNewsPanel = () => {
  const getImpactColor = (impact: string) => {
    switch (impact) {
      case "high":
        return "bg-danger-red text-danger-red";
      case "medium":
        return "bg-primary text-primary";
      default:
        return "bg-muted-foreground text-muted-foreground";
    }
  };

  const getSentimentIcon = (sentiment: string) => {
    return sentiment === "bullish" ? (
      <TrendingUp className="w-4 h-4 text-terminal-green" />
    ) : (
      <TrendingDown className="w-4 h-4 text-danger-red" />
    );
  };

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      MACRO: "bg-blue-500/20 text-blue-400",
      INSTITUTIONAL: "bg-purple-500/20 text-purple-400",
      REGULATORY: "bg-orange-500/20 text-orange-400",
      EXCHANGE: "bg-cyan-500/20 text-cyan-400",
      "ON-CHAIN": "bg-green-500/20 text-green-400"
    };
    return colors[category] || "bg-muted text-muted-foreground";
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <div className="flex items-center gap-2">
          <Newspaper className="w-4 h-4 text-danger-red" />
          <h2 className="panel-title">MAJOR NEWS</h2>
        </div>
        <div className="flex items-center gap-2">
          <AlertCircle className="w-3 h-3 text-danger-red animate-pulse" />
          <span className="text-xs text-danger-red">HIGH IMPACT</span>
        </div>
      </div>

      <div className="space-y-3 max-h-[350px] overflow-y-auto scrollbar-thin scrollbar-thumb-primary/20">
        {newsData.map((news) => (
          <div
            key={news.id}
            className="p-3 rounded bg-panel-bg/30 border border-border/30 hover:border-primary/30 transition-all cursor-pointer group"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className={`text-xs px-2 py-0.5 rounded ${getCategoryColor(news.category)}`}>
                    {news.category}
                  </span>
                  <div className="flex items-center gap-1">
                    <div className={`w-2 h-2 rounded-full ${getImpactColor(news.impact)} bg-opacity-100`} />
                    <span className="text-xs text-muted-foreground">{news.impact.toUpperCase()}</span>
                  </div>
                </div>
                <h3 className="text-sm font-semibold text-foreground group-hover:text-primary transition-colors">
                  {news.title}
                </h3>
                <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{news.summary}</p>
              </div>
              <div className="flex flex-col items-end gap-2">
                {getSentimentIcon(news.sentiment)}
                <ExternalLink className="w-3 h-3 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
            </div>
            <div className="flex items-center justify-between mt-2 pt-2 border-t border-border/20">
              <span className="text-xs text-muted-foreground">{news.source}</span>
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                <Clock className="w-3 h-3" />
                {news.time}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-3 pt-3 border-t border-border/30 flex items-center justify-between">
        <div className="flex items-center gap-3 text-xs">
          <span className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full bg-danger-red" />
            <span className="text-muted-foreground">High: 2</span>
          </span>
          <span className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full bg-primary" />
            <span className="text-muted-foreground">Medium: 2</span>
          </span>
          <span className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full bg-muted-foreground" />
            <span className="text-muted-foreground">Low: 1</span>
          </span>
        </div>
        <span className="text-xs text-primary cursor-pointer hover:underline">View All News →</span>
      </div>
    </div>
  );
};
