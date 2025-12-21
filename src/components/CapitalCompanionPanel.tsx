import { useState, useEffect } from "react";
import { Brain, CheckCircle, AlertCircle } from "lucide-react";

const terminalLines = [
  { text: "> Initializing Capital Companion v2.4.1...", delay: 0 },
  { text: "> System Core: ONLINE", delay: 400 },
  { text: "> Analyzing Market Structure...", delay: 800 },
  { text: "", delay: 1000 },
  { text: "> ═══════════════════════════════════════", delay: 1200 },
  { text: "> MARKET ANALYSIS REPORT", delay: 1400 },
  { text: "> ═══════════════════════════════════════", delay: 1600 },
  { text: "", delay: 1800 },
  { text: "> Trend Detection: BULLISH (H4 Timeframe)", delay: 2000, type: 'success' },
  { text: "> Momentum: Strong upward pressure detected", delay: 2400 },
  { text: "> Volume Profile: Above average (127%)", delay: 2800 },
  { text: "", delay: 3000 },
  { text: "> Key Levels Identified:", delay: 3200 },
  { text: ">   Support Found: $96,500", delay: 3400, type: 'info' },
  { text: ">   Resistance: $98,200", delay: 3600, type: 'info' },
  { text: ">   Stop Loss Zone: $95,800", delay: 3800, type: 'warning' },
  { text: "", delay: 4000 },
  { text: "> ═══════════════════════════════════════", delay: 4200 },
  { text: "> RISK ASSESSMENT", delay: 4400 },
  { text: "> ═══════════════════════════════════════", delay: 4600 },
  { text: "", delay: 4800 },
  { text: "> Position Size Calculation: 0.15 BTC", delay: 5000 },
  { text: "> Risk/Reward Ratio: 1:2.8", delay: 5200, type: 'success' },
  { text: "> Account Risk: 1.5% (Within Limits)", delay: 5400, type: 'success' },
  { text: "", delay: 5600 },
  { text: "> RISK CHECK: ████████████████████ PASSED", delay: 5800, type: 'success' },
  { text: "", delay: 6000 },
  { text: "> Recommendation: LONG Entry Approved", delay: 6200, type: 'success' },
  { text: "> Confidence Level: 78%", delay: 6400 },
  { text: "", delay: 6600 },
  { text: "> Awaiting trader confirmation...", delay: 6800 },
];

const CapitalCompanionPanel = () => {
  const [displayedLines, setDisplayedLines] = useState<typeof terminalLines>([]);
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    terminalLines.forEach((line, index) => {
      setTimeout(() => {
        setDisplayedLines(prev => [...prev, line]);
        if (index === terminalLines.length - 1) {
          setIsComplete(true);
        }
      }, line.delay);
    });
  }, []);

  const getLineColor = (type?: string) => {
    switch (type) {
      case 'success': return 'text-terminal-green';
      case 'warning': return 'text-primary';
      case 'info': return 'text-safe-blue';
      case 'error': return 'text-danger-red';
      default: return 'text-amber/80';
    }
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <div className={`status-indicator ${isComplete ? 'status-online' : 'status-warning'}`} />
        <Brain className="h-4 w-4 text-primary" />
        <h2 className="panel-title">Capital Companion Logic</h2>
        <span className="ml-auto text-xs text-muted-foreground">
          AI DECISION ENGINE
        </span>
      </div>

      <div className="p-4">
        <div 
          className="bg-background/50 border border-panel-border rounded-sm p-4 h-64 overflow-y-auto font-mono text-sm"
          style={{
            backgroundImage: 'linear-gradient(transparent 50%, rgba(0,0,0,0.1) 50%)',
            backgroundSize: '100% 4px'
          }}
        >
          {displayedLines.map((line, index) => (
            <div 
              key={index} 
              className={`${getLineColor(line.type)} leading-relaxed`}
              style={{ textShadow: '0 0 5px currentColor' }}
            >
              {line.text || '\u00A0'}
            </div>
          ))}
          {!isComplete && (
            <span className="text-primary cursor-blink" />
          )}
        </div>

        {/* Status Footer */}
        <div className="mt-4 flex items-center justify-between border-t border-panel-border pt-4">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-terminal-green" />
              <span className="text-xs text-muted-foreground">All Systems Nominal</span>
            </div>
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-primary animate-pulse" />
              <span className="text-xs text-primary">1 Action Pending</span>
            </div>
          </div>
          
          <div className="text-xs text-muted-foreground">
            Analysis ID: <span className="text-primary font-bold">CC-2024-1221-0847</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CapitalCompanionPanel;
