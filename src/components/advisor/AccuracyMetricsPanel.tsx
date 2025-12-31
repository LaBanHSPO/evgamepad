import React, { useEffect, useState } from 'react';
import { useSocket } from '@/context/SocketContext';
import { TrendingUp, TrendingDown, Target, DollarSign } from 'lucide-react';

interface AccuracyMetrics {
  period_days: number;
  total_trades: number;
  wins: number;
  losses: number;
  win_rate_pct: number;
  avg_pnl_pct: number;
  avg_win_pct?: number;
  avg_loss_pct?: number;
  profit_factor: number;
  avg_hold_hours?: number;
  recommendation: string;
}

interface AccuracyMetricsPanelProps {
  symbol?: string;
  timeframe?: string;
  signal?: string;
  periodDays?: number;
}

/**
 * Displays historical performance metrics and accuracy statistics
 */
export const AccuracyMetricsPanel: React.FC<AccuracyMetricsPanelProps> = ({
  symbol,
  timeframe,
  signal,
  periodDays = 30
}) => {
  const { socket } = useSocket();
  const [metrics, setMetrics] = useState<AccuracyMetrics | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!socket) return;

    setLoading(true);
    setError(null);

    socket.emit('advisor:accuracy_report', {
      symbol,
      timeframe,
      signal,
      days: periodDays
    });

    const handleAccuracyResult = (data: { success: boolean; data?: { report: AccuracyMetrics }; message?: string }) => {
      if (data.success && data.data && data.data.report) {
        // Validate report structure
        const report = data.data.report;
        if (
          typeof report.total_trades === 'number' &&
          typeof report.wins === 'number' &&
          typeof report.losses === 'number' &&
          typeof report.win_rate_pct === 'number' &&
          typeof report.avg_pnl_pct === 'number' &&
          typeof report.profit_factor === 'number'
        ) {
          setMetrics(report);
          setError(null);
        } else {
          setError('Invalid accuracy metrics format');
          console.error('Invalid report structure:', report);
        }
      } else {
        setError(data.message || 'Failed to fetch accuracy metrics');
      }
      setLoading(false);
    };

    const handleError = (errorData: { message: string }) => {
      setError(errorData.message);
      setLoading(false);
    };

    socket.on('advisor:accuracy_result', handleAccuracyResult);
    socket.on('advisor:error', handleError);

    return () => {
      socket.off('advisor:accuracy_result', handleAccuracyResult);
      socket.off('advisor:error', handleError);
    };
  }, [socket, symbol, timeframe, signal, periodDays]);

  const getWinRateColor = (rate: number): string => {
    if (rate >= 70) return '#26A69A';
    if (rate >= 60) return '#FFA726';
    if (rate >= 50) return '#FFD54F';
    return '#EF5350';
  };

  const getProfitFactorColor = (pf: number): string => {
    if (pf >= 2.0) return '#26A69A';
    if (pf >= 1.5) return '#FFA726';
    if (pf >= 1.0) return '#FFD54F';
    return '#EF5350';
  };

  if (loading) {
    return (
      <div className="bg-background/50 border border-border/50 rounded p-4">
        <div className="text-xs text-muted-foreground text-center">Loading accuracy metrics...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-danger-red/10 border border-danger-red/30 rounded p-4">
        <div className="text-xs text-danger-red">{error}</div>
      </div>
    );
  }

  if (!metrics || metrics.total_trades === 0) {
    return (
      <div className="bg-background/30 border border-border/50 rounded p-4">
        <div className="text-xs text-muted-foreground text-center">
          No historical trades for this configuration yet
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex justify-between items-center">
        <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
          <Target className="w-4 h-4 text-primary" />
          Historical Performance
        </h3>
        <span className="text-[10px] text-muted-foreground">
          Last {metrics.period_days} Days
        </span>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 gap-3">
        {/* Total Trades */}
        <div className="bg-background/50 border border-border/50 rounded p-3">
          <div className="text-[10px] text-muted-foreground mb-1">Total Trades</div>
          <div className="text-xl font-bold text-foreground">{metrics.total_trades}</div>
        </div>

        {/* Win Rate */}
        <div className="bg-background/50 border border-border/50 rounded p-3">
          <div className="text-[10px] text-muted-foreground mb-1">Win Rate</div>
          <div
            className="text-xl font-bold"
            style={{ color: getWinRateColor(metrics.win_rate_pct) }}
          >
            {metrics.win_rate_pct.toFixed(1)}%
          </div>
          <div className="text-[10px] text-muted-foreground mt-1">
            {metrics.wins}W / {metrics.losses}L
          </div>
        </div>

        {/* Avg P/L */}
        <div className="bg-background/50 border border-border/50 rounded p-3">
          <div className="text-[10px] text-muted-foreground mb-1 flex items-center gap-1">
            <DollarSign className="w-3 h-3" />
            Avg P/L
          </div>
          <div
            className="text-xl font-bold flex items-center gap-1"
            style={{ color: metrics.avg_pnl_pct > 0 ? '#26A69A' : '#EF5350' }}
          >
            {metrics.avg_pnl_pct > 0 ? (
              <TrendingUp className="w-4 h-4" />
            ) : (
              <TrendingDown className="w-4 h-4" />
            )}
            {metrics.avg_pnl_pct > 0 ? '+' : ''}
            {metrics.avg_pnl_pct.toFixed(2)}%
          </div>
        </div>

        {/* Profit Factor */}
        <div className="bg-background/50 border border-border/50 rounded p-3">
          <div className="text-[10px] text-muted-foreground mb-1">Profit Factor</div>
          <div
            className="text-xl font-bold"
            style={{ color: getProfitFactorColor(metrics.profit_factor) }}
          >
            {metrics.profit_factor.toFixed(2)}
          </div>
          <div className="text-[10px] text-muted-foreground mt-1">
            {metrics.profit_factor >= 2.0 ? 'Excellent' : metrics.profit_factor >= 1.5 ? 'Good' : metrics.profit_factor >= 1.0 ? 'Fair' : 'Poor'}
          </div>
        </div>
      </div>

      {/* Additional Stats */}
      {(metrics.avg_win_pct !== undefined || metrics.avg_loss_pct !== undefined || metrics.avg_hold_hours !== undefined) && (
        <div className="grid grid-cols-3 gap-2 text-xs">
          {metrics.avg_win_pct !== undefined && (
            <div className="bg-terminal-green/10 border border-terminal-green/30 rounded p-2">
              <div className="text-[10px] text-terminal-green/70 mb-0.5">Avg Win</div>
              <div className="text-xs font-bold text-terminal-green">+{metrics.avg_win_pct.toFixed(2)}%</div>
            </div>
          )}
          {metrics.avg_loss_pct !== undefined && (
            <div className="bg-danger-red/10 border border-danger-red/30 rounded p-2">
              <div className="text-[10px] text-danger-red/70 mb-0.5">Avg Loss</div>
              <div className="text-xs font-bold text-danger-red">-{metrics.avg_loss_pct.toFixed(2)}%</div>
            </div>
          )}
          {metrics.avg_hold_hours !== undefined && (
            <div className="bg-secondary/10 border border-secondary/30 rounded p-2">
              <div className="text-[10px] text-secondary/70 mb-0.5">Avg Hold</div>
              <div className="text-xs font-bold text-secondary">{metrics.avg_hold_hours.toFixed(1)}h</div>
            </div>
          )}
        </div>
      )}

      {/* Recommendation */}
      <div className="bg-primary/10 border border-primary/30 rounded p-3">
        <div className="text-xs font-bold text-primary mb-1">Assessment</div>
        <p className="text-xs text-foreground/80 leading-relaxed">{metrics.recommendation}</p>
      </div>
    </div>
  );
};
