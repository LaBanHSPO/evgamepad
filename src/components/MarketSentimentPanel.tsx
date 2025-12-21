import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts";
import { Brain, AlertTriangle, Shield, Zap } from "lucide-react";

const sentimentData = [
  { name: "Bullish", value: 62, color: "hsl(var(--terminal-green))" },
  { name: "Bearish", value: 28, color: "hsl(var(--danger-red))" },
  { name: "Neutral", value: 10, color: "hsl(var(--muted-foreground))" },
];

const indicators = [
  { label: "Fear & Greed", value: 72, status: "GREED", icon: Brain },
  { label: "Volatility Index", value: 23, status: "LOW", icon: Zap },
  { label: "Market Risk", value: 34, status: "MODERATE", icon: AlertTriangle },
  { label: "Trend Strength", value: 78, status: "STRONG", icon: Shield },
];

export const MarketSentimentPanel = () => {
  return (
    <div className="panel">
      <div className="panel-header">
        <div className="flex items-center gap-2">
          <Brain className="w-4 h-4 text-secondary" />
          <span className="panel-title">SENTIMENT ANALYSIS</span>
        </div>
        <div className="text-xs text-muted-foreground font-mono">
          AI CONFIDENCE: 94%
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* Pie Chart */}
        <div className="flex flex-col items-center">
          <div className="h-32 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={sentimentData}
                  cx="50%"
                  cy="50%"
                  innerRadius={35}
                  outerRadius={55}
                  dataKey="value"
                  strokeWidth={2}
                  stroke="hsl(var(--background))"
                >
                  {sentimentData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </div>
          
          {/* Legend */}
          <div className="flex gap-4 mt-2">
            {sentimentData.map((item) => (
              <div key={item.name} className="flex items-center gap-1 text-xs">
                <span
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: item.color }}
                />
                <span className="text-muted-foreground">{item.name}</span>
                <span className="font-mono text-foreground">{item.value}%</span>
              </div>
            ))}
          </div>
        </div>

        {/* Indicators */}
        <div className="space-y-2">
          {indicators.map((ind) => (
            <div
              key={ind.label}
              className="flex items-center justify-between bg-panel-bg/50 p-2 rounded border border-primary/10"
            >
              <div className="flex items-center gap-2">
                <ind.icon className="w-3 h-3 text-primary" />
                <span className="text-xs text-muted-foreground">{ind.label}</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-16 h-1.5 bg-background rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: `${ind.value}%`,
                      background:
                        ind.value > 60
                          ? "hsl(var(--terminal-green))"
                          : ind.value > 40
                          ? "hsl(var(--primary))"
                          : "hsl(var(--danger-red))",
                    }}
                  />
                </div>
                <span className="text-xs font-mono text-foreground w-12 text-right">
                  {ind.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-4 p-2 bg-terminal-green/10 border border-terminal-green/30 rounded">
        <div className="flex items-center gap-2 text-terminal-green text-sm">
          <span className="w-2 h-2 rounded-full bg-terminal-green animate-pulse" />
          <span className="font-mono">MARKET BIAS: BULLISH | RECOMMENDED: LONG POSITIONS</span>
        </div>
      </div>
    </div>
  );
};
