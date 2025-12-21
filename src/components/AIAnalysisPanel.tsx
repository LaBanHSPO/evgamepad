import { Brain, Zap, Target, AlertTriangle, CheckCircle, Loader2 } from "lucide-react";
import { useState, useEffect } from "react";

const analysisData = {
  marketPhase: "Accumulation",
  trend: "Bullish",
  confidence: 78,
  signals: [
    { type: "bullish", text: "RSI divergence detected on H4", priority: "high" },
    { type: "bullish", text: "Volume increasing on upward moves", priority: "medium" },
    { type: "neutral", text: "Price consolidating near resistance", priority: "medium" },
    { type: "bearish", text: "Funding rate elevated (0.045%)", priority: "low" }
  ],
  recommendation: "ACCUMULATE",
  keyLevels: {
    support: [96500, 95200, 93800],
    resistance: [98500, 100000, 102500]
  },
  riskLevel: "MODERATE"
};

export const AIAnalysisPanel = () => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [lastUpdate, setLastUpdate] = useState("Just now");

  useEffect(() => {
    const interval = setInterval(() => {
      setIsAnalyzing(true);
      setTimeout(() => setIsAnalyzing(false), 2000);
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  const getSignalIcon = (type: string) => {
    switch (type) {
      case "bullish":
        return <CheckCircle className="w-3 h-3 text-terminal-green" />;
      case "bearish":
        return <AlertTriangle className="w-3 h-3 text-danger-red" />;
      default:
        return <Target className="w-3 h-3 text-primary" />;
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "high":
        return "bg-danger-red/20 text-danger-red";
      case "medium":
        return "bg-primary/20 text-primary";
      default:
        return "bg-muted text-muted-foreground";
    }
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <div className="flex items-center gap-2">
          <Brain className="w-4 h-4 text-secondary" />
          <h2 className="panel-title">AI ANALYSIS</h2>
        </div>
        <div className="flex items-center gap-2">
          {isAnalyzing ? (
            <>
              <Loader2 className="w-3 h-3 text-secondary animate-spin" />
              <span className="text-xs text-secondary">ANALYZING...</span>
            </>
          ) : (
            <>
              <Zap className="w-3 h-3 text-terminal-green" />
              <span className="text-xs text-terminal-green">READY</span>
            </>
          )}
        </div>
      </div>

      {/* Market Phase & Trend */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        <div className="bg-panel-bg/50 rounded p-3 border border-border/30">
          <span className="text-xs text-muted-foreground block mb-1">PHASE</span>
          <span className="text-sm font-bold text-primary">{analysisData.marketPhase}</span>
        </div>
        <div className="bg-panel-bg/50 rounded p-3 border border-border/30">
          <span className="text-xs text-muted-foreground block mb-1">TREND</span>
          <span className="text-sm font-bold text-terminal-green">{analysisData.trend}</span>
        </div>
        <div className="bg-panel-bg/50 rounded p-3 border border-border/30">
          <span className="text-xs text-muted-foreground block mb-1">CONFIDENCE</span>
          <span className="text-sm font-bold text-foreground">{analysisData.confidence}%</span>
        </div>
      </div>

      {/* AI Recommendation */}
      <div className="bg-terminal-green/10 border border-terminal-green/30 rounded p-3 mb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Target className="w-5 h-5 text-terminal-green" />
            <span className="text-sm text-muted-foreground">AI Recommendation:</span>
          </div>
          <span className="text-lg font-bold text-terminal-green tracking-wider">
            {analysisData.recommendation}
          </span>
        </div>
        <div className="mt-2 flex items-center gap-4 text-xs">
          <span className="text-muted-foreground">
            Risk Level: <span className="text-primary font-semibold">{analysisData.riskLevel}</span>
          </span>
        </div>
      </div>

      {/* Signals */}
      <div className="mb-4">
        <h3 className="text-xs text-muted-foreground mb-2 flex items-center gap-2">
          <Zap className="w-3 h-3" />
          ACTIVE SIGNALS
        </h3>
        <div className="space-y-2">
          {analysisData.signals.map((signal, idx) => (
            <div
              key={idx}
              className="flex items-center justify-between bg-panel-bg/30 rounded px-3 py-2 border border-border/20"
            >
              <div className="flex items-center gap-2">
                {getSignalIcon(signal.type)}
                <span className="text-sm text-foreground/90">{signal.text}</span>
              </div>
              <span className={`text-xs px-2 py-0.5 rounded ${getPriorityColor(signal.priority)}`}>
                {signal.priority.toUpperCase()}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Key Levels */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-terminal-green/5 border border-terminal-green/20 rounded p-2">
          <span className="text-xs text-terminal-green block mb-1">SUPPORT LEVELS</span>
          <div className="flex flex-wrap gap-1">
            {analysisData.keyLevels.support.map((level, idx) => (
              <span key={idx} className="text-xs bg-terminal-green/20 text-terminal-green px-2 py-0.5 rounded">
                ${level.toLocaleString()}
              </span>
            ))}
          </div>
        </div>
        <div className="bg-danger-red/5 border border-danger-red/20 rounded p-2">
          <span className="text-xs text-danger-red block mb-1">RESISTANCE LEVELS</span>
          <div className="flex flex-wrap gap-1">
            {analysisData.keyLevels.resistance.map((level, idx) => (
              <span key={idx} className="text-xs bg-danger-red/20 text-danger-red px-2 py-0.5 rounded">
                ${level.toLocaleString()}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-3 pt-3 border-t border-border/30 text-xs text-muted-foreground flex justify-between">
        <span>Last analysis: {lastUpdate}</span>
        <button 
          onClick={() => {
            setIsAnalyzing(true);
            setTimeout(() => {
              setIsAnalyzing(false);
              setLastUpdate("Just now");
            }, 2000);
          }}
          className="text-primary hover:underline"
        >
          Refresh Analysis →
        </button>
      </div>
    </div>
  );
};
