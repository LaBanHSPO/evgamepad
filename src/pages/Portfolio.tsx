import { useState } from "react";
import { SystemHeader } from "@/components/SystemHeader";
import RiskManagementPanel from "@/components/RiskManagementPanel";
import MissionLogPanel from "@/components/MissionLogPanel";
import { PositionInputForm } from "@/components/PositionInputForm";
import { AIRiskAdvisoryPanel } from "@/components/AIRiskAdvisoryPanel";
import { usePortfolioAnalysis } from "@/hooks/usePortfolioAnalysis";

const Index = () => {
  const {
    result,
    isAnalyzing,
    error,
    analyzePortfolio,
    clearResult,
    isConnected
  } = usePortfolioAnalysis();

  const [riskProfile] = useState(() => {
    return localStorage.getItem('riskProfile') || 'conservative';
  });

  const handleAnalyze = (positions: Array<{
    id: string;
    symbol: string;
    entryPrice: number;
    currentPrice: number;
    positionSize: number;
    stopLoss: number;
    timeframe: string;
  }>, accountBalance: number) => {
    const formattedPositions = positions.map(p => ({
      symbol: p.symbol,
      entry_price: p.entryPrice,
      current_price: p.currentPrice,
      position_size: p.positionSize,
      stop_loss: p.stopLoss || undefined,
      timeframe: p.timeframe || 'H1'
    }));

    analyzePortfolio(formattedPositions, accountBalance, riskProfile, 'vi');
  };

  return (
    <div className="min-h-screen bg-background text-foreground p-4 relative overflow-hidden">
      {/* Scanlines overlay */}
      <div className="scanlines" />

      {/* CRT flicker effect */}
      <div className="crt-flicker" />

      {/* Main content */}
      <div className="relative z-10 max-w-7xl mx-auto space-y-4">
        <SystemHeader monitorNumber={1} title="PORTFOLIO & RISK MANAGEMENT" />

        {/* Connection Status */}
        {!isConnected && (
          <div className="panel border-danger-red">
            <div className="p-4 text-center text-danger-red">
              ⚠️ Not connected to server. Reconnecting...
            </div>
          </div>
        )}

        {/* Risk Management Core (existing) */}
        <RiskManagementPanel />

        {/* Portfolio Analysis Form */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <PositionInputForm
            onSubmit={handleAnalyze}
            isAnalyzing={isAnalyzing}
          />

          {/* Analysis Result or Instructions */}
          <div className="panel">
            {isAnalyzing ? (
              <div className="p-6 text-center">
                <div className="animate-pulse space-y-3">
                  <div className="text-primary font-mono">ANALYZING PORTFOLIO...</div>
                  <div className="text-xs text-muted-foreground">
                    Running technical analysis and generating AI advice
                  </div>
                </div>
              </div>
            ) : error ? (
              <div className="p-6 text-center space-y-3">
                <div className="text-danger-red font-mono">ERROR</div>
                <div className="text-sm text-muted-foreground">{error}</div>
                <button
                  onClick={() => clearResult()}
                  className="text-primary hover:text-primary/80 text-sm underline"
                >
                  Try Again
                </button>
              </div>
            ) : !result ? (
              <div className="p-6 space-y-3">
                <h3 className="text-sm font-bold text-primary">How to Use</h3>
                <ol className="text-xs text-muted-foreground space-y-2 list-decimal list-inside">
                  <li>Enter your account balance</li>
                  <li>Add all open positions with entry/current prices</li>
                  <li>Optionally set stop-loss levels</li>
                  <li>Click "Analyze Portfolio Risk" for AI advice</li>
                </ol>
                <p className="text-xs text-yellow-500 italic">
                  ⚡ Focus: Capital preservation and protecting your principle
                </p>
              </div>
            ) : null}
          </div>
        </div>

        {/* AI Risk Advisory (conditional) */}
        {result && (
          <AIRiskAdvisoryPanel
            portfolioHealth={result.portfolio_health}
            positionAnalysis={result.position_analysis}
            aiAdvice={result.ai_advice}
          />
        )}

        {/* Mission Log */}
        <MissionLogPanel />
      </div>

      {/* Corner Decorations */}
      <div className="fixed top-0 left-0 w-16 h-16 border-l-2 border-t-2 border-primary/30 pointer-events-none" />
      <div className="fixed top-0 right-0 w-16 h-16 border-r-2 border-t-2 border-primary/30 pointer-events-none" />
      <div className="fixed bottom-0 left-0 w-16 h-16 border-l-2 border-b-2 border-primary/30 pointer-events-none" />
      <div className="fixed bottom-0 right-0 w-16 h-16 border-r-2 border-b-2 border-primary/30 pointer-events-none" />

      {/* Version Watermark */}
      <div className="fixed bottom-4 right-4 text-xs text-muted-foreground/50 font-mono pointer-events-none">
        EVGAMEPAD v1.0.0
      </div>
    </div>
  );
};

export default Index;
