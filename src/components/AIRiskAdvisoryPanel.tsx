import React from 'react';
import { AlertTriangle, CheckCircle, XCircle } from 'lucide-react';

interface PortfolioHealth {
  score: number;
  status: 'HEALTHY' | 'CAUTION' | 'DANGER';
  total_risk_exposure: number;
  current_drawdown: number;
  positions_at_risk: number;
}

interface PositionAnalysis {
  symbol: string;
  risk_status: string;
  recommendation: string;
  technical_signal: string;
  r_multiple: number;
  pnl_pct: number;
  distance_to_stop_pct: number;
}

interface AIAdvice {
  summary: string;
  overall_risk: string;
  priority_actions: string[];
  reasoning: string;
  confidence: number;
  model: string;
  cached: boolean;
}

interface AIRiskAdvisoryPanelProps {
  portfolioHealth: PortfolioHealth;
  positionAnalysis: PositionAnalysis[];
  aiAdvice: AIAdvice;
}

export const AIRiskAdvisoryPanel: React.FC<AIRiskAdvisoryPanelProps> = ({
  portfolioHealth,
  positionAnalysis,
  aiAdvice
}) => {
  const { score, status } = portfolioHealth;

  const textColorClass = {
    HEALTHY: 'text-terminal-green',
    CAUTION: 'text-yellow-500',
    DANGER: 'text-danger-red'
  }[status];

  return (
    <div className="panel">
      <div className="panel-header">
        <div className={`status-indicator ${status === 'HEALTHY' ? 'status-online' : 'status-critical'}`} />
        <h2 className="panel-title">AI Risk Advisory</h2>
        <span className="ml-auto text-xs text-muted-foreground">
          MODEL: {aiAdvice.model.toUpperCase()} {aiAdvice.cached && '(CACHED)'}
        </span>
      </div>

      <div className="p-6 space-y-6">
        {/* Portfolio Health Score */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs uppercase tracking-wider text-muted-foreground">
                Portfolio Health Score
              </span>
              <span className={`text-xs px-2 py-0.5 rounded ${
                status === 'HEALTHY' ? 'bg-terminal-green/20 text-terminal-green' :
                status === 'CAUTION' ? 'bg-yellow-500/20 text-yellow-500' :
                'bg-danger-red/20 text-danger-red'
              }`}>
                {status}
              </span>
            </div>

            <div className="text-center">
              <span className={`font-display text-4xl font-bold data-value ${textColorClass}`}>
                {score}/100
              </span>
            </div>
          </div>

          {/* Risk Metrics */}
          <div className="space-y-3">
            <h3 className="text-xs uppercase tracking-wider text-muted-foreground mb-3">
              Risk Metrics
            </h3>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Total Risk Exposure:</span>
                <span className={`font-mono font-bold ${
                  portfolioHealth.total_risk_exposure > 5 ? 'text-danger-red' :
                  portfolioHealth.total_risk_exposure > 2 ? 'text-yellow-500' :
                  'text-terminal-green'
                }`}>
                  {portfolioHealth.total_risk_exposure.toFixed(2)}%
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Current Drawdown:</span>
                <span className={`font-mono font-bold ${
                  portfolioHealth.current_drawdown > 10 ? 'text-danger-red' :
                  portfolioHealth.current_drawdown > 5 ? 'text-yellow-500' :
                  'text-terminal-green'
                }`}>
                  {portfolioHealth.current_drawdown.toFixed(2)}%
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Positions at Risk:</span>
                <span className={`font-mono font-bold ${
                  portfolioHealth.positions_at_risk > 0 ? 'text-danger-red' : 'text-terminal-green'
                }`}>
                  {portfolioHealth.positions_at_risk}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">AI Confidence:</span>
                <span className="font-mono font-bold text-primary">
                  {aiAdvice.confidence}%
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* AI Summary */}
        <div className="border-t border-panel-border pt-4">
          <h3 className="text-xs uppercase tracking-wider text-muted-foreground mb-3">
            AI Analysis
          </h3>
          <p className="text-sm text-foreground leading-relaxed mb-4">
            {aiAdvice.summary}
          </p>
          <p className="text-xs text-muted-foreground italic">
            {aiAdvice.reasoning}
          </p>
        </div>

        {/* Priority Actions */}
        {aiAdvice.priority_actions.length > 0 && (
          <div className="border-t border-panel-border pt-4">
            <h3 className="text-xs uppercase tracking-wider text-muted-foreground mb-3">
              Priority Actions (Capital Preservation)
            </h3>
            <ul className="space-y-2">
              {aiAdvice.priority_actions.map((action, index) => (
                <li key={index} className="flex items-start gap-2">
                  <AlertTriangle className="h-4 w-4 text-yellow-500 flex-shrink-0 mt-0.5" />
                  <span className="text-sm text-foreground">{action}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Position-Specific Warnings */}
        <div className="border-t border-panel-border pt-4">
          <h3 className="text-xs uppercase tracking-wider text-muted-foreground mb-3">
            Position-Specific Analysis
          </h3>
          <div className="space-y-2">
            {positionAnalysis.map((pos) => (
              <div
                key={pos.symbol}
                className={`flex items-center justify-between p-3 rounded border ${
                  pos.risk_status === 'danger' ? 'border-danger-red/50 bg-danger-red/10' :
                  pos.risk_status === 'approaching_stop' ? 'border-yellow-500/50 bg-yellow-500/10' :
                  'border-panel-border bg-background/30'
                }`}
              >
                <div className="flex items-center gap-3">
                  {pos.risk_status === 'danger' ? (
                    <XCircle className="h-5 w-5 text-danger-red" />
                  ) : pos.risk_status === 'approaching_stop' ? (
                    <AlertTriangle className="h-5 w-5 text-yellow-500" />
                  ) : (
                    <CheckCircle className="h-5 w-5 text-terminal-green" />
                  )}
                  <div>
                    <div className="font-mono font-bold text-sm">{pos.symbol}</div>
                    <div className="text-xs text-muted-foreground">
                      P&L: <span className={pos.pnl_pct >= 0 ? 'text-terminal-green' : 'text-danger-red'}>
                        {pos.pnl_pct >= 0 ? '+' : ''}{pos.pnl_pct.toFixed(2)}%
                      </span>
                      {' | '}R-Multiple: <span className="text-primary">{pos.r_multiple.toFixed(2)}</span>
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className={`text-xs font-bold uppercase ${
                    pos.recommendation === 'CLOSE' ? 'text-danger-red' :
                    pos.recommendation === 'REDUCE' ? 'text-yellow-500' :
                    'text-terminal-green'
                  }`}>
                    {pos.recommendation}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {pos.distance_to_stop_pct.toFixed(1)}% to SL
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Disclaimer */}
        <div className="border-t border-panel-border pt-4">
          <p className="text-xs text-muted-foreground italic">
            ⚠️ Advisory Only: This AI analysis is for informational purposes. Always make your own trading decisions and manage your own risk.
          </p>
        </div>
      </div>
    </div>
  );
};
