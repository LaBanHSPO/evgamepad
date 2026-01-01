# Phase 5.3: Visual Indicator Dashboard

**Duration:** 4 hours
**Priority:** P0
**Status:** Planned

---

## Objective

Show users exactly what AI sees via interactive chart overlays and visual explainability components.

**User Value:** "I can see the indicators on the chart and verify AI isn't hallucinating"

---

## Deliverables

1. `src/components/advisor/IndicatorOverlayChart.tsx` - TradingView-style chart with toggleable indicators
2. `src/components/advisor/ChainOfThoughtViewer.tsx` - Step-by-step reasoning display
3. `src/components/advisor/AccuracyMetricsPanel.tsx` - Performance statistics
4. `src/components/advisor/ProvenanceTimeline.tsx` - Data freshness tracker
5. Integration with `CapitalCompanionPanel.tsx`

---

## Component Specifications

### 1. Indicator Overlay Chart

**File:** `src/components/advisor/IndicatorOverlayChart.tsx`

**Features:**
- Lightweight Charts library (TradingView alternative)
- Candlestick price chart
- Toggleable indicator overlays:
  - Moving averages (EMA 21, 50, SMA 200)
  - Bollinger Bands
  - Volume bars
  - Support/Resistance levels
  - Pattern annotations (arrows, labels)
- Zoom/pan controls
- Real-time updates via Socket.IO

**Implementation:**
```tsx
import React, { useEffect, useRef, useState } from 'react';
import { createChart, IChartApi, ISeriesApi } from 'lightweight-charts';
import { useSocket } from '../../contexts/SocketContext';

interface IndicatorOverlayChartProps {
  symbol: string;
  timeframe: string;
  height?: number;
}

interface Indicator {
  name: string;
  enabled: boolean;
  color: string;
  series?: ISeriesApi<any>;
}

export const IndicatorOverlayChart: React.FC<IndicatorOverlayChartProps> = ({
  symbol,
  timeframe,
  height = 400
}) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const { socket } = useSocket();

  const [indicators, setIndicators] = useState<Indicator[]>([
    { name: 'EMA 21', enabled: true, color: '#2962FF' },
    { name: 'EMA 50', enabled: true, color: '#FF6D00' },
    { name: 'Bollinger Bands', enabled: false, color: '#9C27B0' },
    { name: 'Volume', enabled: true, color: '#26A69A' },
    { name: 'S/R Levels', enabled: true, color: '#EF5350' }
  ]);

  const [candleData, setCandleData] = useState<any[]>([]);
  const [technicalData, setTechnicalData] = useState<any>(null);

  // Initialize chart
  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height,
      layout: {
        background: { color: '#1E1E1E' },
        textColor: '#D9D9D9',
      },
      grid: {
        vertLines: { color: '#2B2B43' },
        horzLines: { color: '#2B2B43' },
      },
      timeScale: {
        borderColor: '#2B2B43',
      },
    });

    chartRef.current = chart;

    // Candlestick series
    const candleSeries = chart.addCandlestickSeries({
      upColor: '#26A69A',
      downColor: '#EF5350',
      borderVisible: false,
      wickUpColor: '#26A69A',
      wickDownColor: '#EF5350',
    });

    // Volume series
    const volumeSeries = chart.addHistogramSeries({
      color: '#26A69A',
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: 'volume',
    });

    chart.priceScale('volume').applyOptions({
      scaleMargins: {
        top: 0.8,
        bottom: 0,
      },
    });

    // Resize handler
    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [height]);

  // Fetch OHLCV data
  useEffect(() => {
    if (!socket) return;

    socket.emit('advisor:technical_summary', {
      symbol,
      timeframe,
      indicators: ['sma', 'ema', 'bb', 'volume']
    });

    socket.on('advisor:technical_result', (data: any) => {
      if (data.success) {
        setTechnicalData(data.data);
        // Update chart with OHLCV + indicators
        updateChart(data.data);
      }
    });

    return () => {
      socket.off('advisor:technical_result');
    };
  }, [socket, symbol, timeframe]);

  const updateChart = (data: any) => {
    // Update candlestick and indicator overlays
    // Implementation details...
  };

  const toggleIndicator = (name: string) => {
    setIndicators(prev =>
      prev.map(ind =>
        ind.name === name ? { ...ind, enabled: !ind.enabled } : ind
      )
    );
  };

  return (
    <div className="indicator-overlay-chart">
      <div className="chart-controls">
        {indicators.map(ind => (
          <button
            key={ind.name}
            className={`indicator-toggle ${ind.enabled ? 'active' : ''}`}
            onClick={() => toggleIndicator(ind.name)}
            style={{ borderColor: ind.color }}
          >
            {ind.name}
          </button>
        ))}
      </div>

      <div ref={chartContainerRef} className="chart-container" />

      <style jsx>{`
        .chart-controls {
          display: flex;
          gap: 8px;
          margin-bottom: 12px;
          flex-wrap: wrap;
        }
        .indicator-toggle {
          padding: 6px 12px;
          border-radius: 4px;
          border: 2px solid;
          background: transparent;
          color: white;
          cursor: pointer;
          opacity: 0.5;
          transition: opacity 0.2s;
        }
        .indicator-toggle.active {
          opacity: 1;
        }
        .chart-container {
          position: relative;
        }
      `}</style>
    </div>
  );
};
```

---

### 2. Chain-of-Thought Viewer

**File:** `src/components/advisor/ChainOfThoughtViewer.tsx`

```tsx
import React from 'react';

interface ReasoningStep {
  step_number: number;
  category: string;
  description: string;
  points_awarded: int;
  max_points: number;
  confidence: number;
}

interface ChainOfThoughtViewerProps {
  steps: ReasoningStep[];
  totalScore: number;
  maxScore: number;
  recommendation: string;
  reasoningSummary: string;
  risksIdentified: string[];
  dataGaps: string[];
}

export const ChainOfThoughtViewer: React.FC<ChainOfThoughtViewerProps> = ({
  steps,
  totalScore,
  maxScore,
  recommendation,
  reasoningSummary,
  risksIdentified,
  dataGaps
}) => {
  const getCategoryIcon = (category: string) => {
    const icons = {
      trend: '📈',
      momentum: '⚡',
      volume: '📊',
      pattern: '🔍',
      risk: '⚠️'
    };
    return icons[category] || '•';
  };

  const getScoreColor = (points: number, max: number) => {
    const ratio = points / max;
    if (ratio >= 0.8) return '#26A69A'; // Green
    if (ratio >= 0.5) return '#FFA726'; // Orange
    return '#EF5350'; // Red
  };

  return (
    <div className="cot-viewer">
      <div className="cot-header">
        <h3>Chain-of-Thought Reasoning</h3>
        <div className="score-badge">
          {totalScore}/{maxScore} points
        </div>
      </div>

      <div className="cot-summary">
        <strong>Recommendation:</strong> {recommendation}
        <br />
        {reasoningSummary}
      </div>

      <div className="cot-steps">
        {steps.map((step) => (
          <div key={step.step_number} className="cot-step">
            <div className="step-header">
              <span className="step-icon">{getCategoryIcon(step.category)}</span>
              <span className="step-title">
                Step {step.step_number}: {step.category.toUpperCase()}
              </span>
              <div
                className="step-score"
                style={{ color: getScoreColor(step.points_awarded, step.max_points) }}
              >
                {step.points_awarded}/{step.max_points}
              </div>
            </div>
            <div className="step-description">
              {step.description}
            </div>
            <div className="step-confidence">
              Confidence: {(step.confidence * 100).toFixed(0)}%
            </div>
          </div>
        ))}
      </div>

      {risksIdentified.length > 0 && (
        <div className="cot-risks">
          <h4>⚠️ Identified Risks</h4>
          <ul>
            {risksIdentified.map((risk, idx) => (
              <li key={idx}>{risk}</li>
            ))}
          </ul>
        </div>
      )}

      {dataGaps.length > 0 && (
        <div className="cot-gaps">
          <h4>ℹ️ Data Gaps</h4>
          <ul>
            {dataGaps.map((gap, idx) => (
              <li key={idx}>{gap}</li>
            ))}
          </ul>
        </div>
      )}

      <style jsx>{`
        .cot-viewer {
          background: #2A2A2A;
          border-radius: 8px;
          padding: 16px;
          color: #E0E0E0;
        }
        .cot-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }
        .score-badge {
          background: #3F51B5;
          padding: 4px 12px;
          border-radius: 12px;
          font-weight: bold;
        }
        .cot-summary {
          background: #1E1E1E;
          padding: 12px;
          border-radius: 4px;
          margin-bottom: 16px;
          line-height: 1.6;
        }
        .cot-step {
          background: #1E1E1E;
          padding: 12px;
          border-radius: 4px;
          margin-bottom: 8px;
        }
        .step-header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 8px;
        }
        .step-icon {
          font-size: 20px;
        }
        .step-title {
          flex: 1;
          font-weight: bold;
        }
        .step-score {
          font-weight: bold;
        }
        .step-description {
          margin-left: 28px;
          line-height: 1.5;
        }
        .step-confidence {
          margin-left: 28px;
          font-size: 12px;
          color: #999;
          margin-top: 4px;
        }
        .cot-risks, .cot-gaps {
          margin-top: 16px;
          padding: 12px;
          background: #1E1E1E;
          border-radius: 4px;
        }
        .cot-risks ul, .cot-gaps ul {
          margin: 8px 0 0 0;
          padding-left: 20px;
        }
      `}</style>
    </div>
  );
};
```

---

### 3. Accuracy Metrics Panel

**File:** `src/components/advisor/AccuracyMetricsPanel.tsx`

```tsx
import React, { useEffect, useState } from 'react';
import { useSocket } from '../../contexts/SocketContext';

interface AccuracyMetrics {
  period_days: number;
  total_trades: number;
  wins: number;
  losses: number;
  win_rate_pct: number;
  avg_pnl_pct: number;
  profit_factor: number;
  recommendation: string;
}

export const AccuracyMetricsPanel: React.FC<{
  symbol?: string;
  timeframe?: string;
  signal?: string;
}> = ({ symbol, timeframe, signal }) => {
  const { socket } = useSocket();
  const [metrics, setMetrics] = useState<AccuracyMetrics | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!socket) return;

    setLoading(true);
    socket.emit('advisor:accuracy_report', {
      symbol,
      timeframe,
      signal,
      days: 30
    });

    socket.on('advisor:accuracy_result', (data: any) => {
      if (data.success) {
        setMetrics(data.data.report);
        setLoading(false);
      }
    });

    return () => {
      socket.off('advisor:accuracy_result');
    };
  }, [socket, symbol, timeframe, signal]);

  if (loading) {
    return <div className="loading">Loading accuracy metrics...</div>;
  }

  if (!metrics || metrics.total_trades === 0) {
    return (
      <div className="no-data">
        No historical trades for this configuration
      </div>
    );
  }

  const getWinRateColor = (rate: number) => {
    if (rate >= 70) return '#26A69A';
    if (rate >= 60) return '#FFA726';
    if (rate >= 50) return '#FFD54F';
    return '#EF5350';
  };

  return (
    <div className="accuracy-panel">
      <h3>📊 Historical Performance (Last {metrics.period_days} Days)</h3>

      <div className="metrics-grid">
        <div className="metric">
          <div className="metric-label">Total Trades</div>
          <div className="metric-value">{metrics.total_trades}</div>
        </div>

        <div className="metric">
          <div className="metric-label">Win Rate</div>
          <div
            className="metric-value"
            style={{ color: getWinRateColor(metrics.win_rate_pct) }}
          >
            {metrics.win_rate_pct.toFixed(1)}%
          </div>
          <div className="metric-detail">
            {metrics.wins}W / {metrics.losses}L
          </div>
        </div>

        <div className="metric">
          <div className="metric-label">Avg P/L</div>
          <div
            className="metric-value"
            style={{ color: metrics.avg_pnl_pct > 0 ? '#26A69A' : '#EF5350' }}
          >
            {metrics.avg_pnl_pct > 0 ? '+' : ''}{metrics.avg_pnl_pct.toFixed(2)}%
          </div>
        </div>

        <div className="metric">
          <div className="metric-label">Profit Factor</div>
          <div className="metric-value">{metrics.profit_factor.toFixed(2)}</div>
        </div>
      </div>

      <div className="recommendation-box">
        <strong>Assessment:</strong> {metrics.recommendation}
      </div>

      <style jsx>{`
        .accuracy-panel {
          background: #2A2A2A;
          border-radius: 8px;
          padding: 16px;
          color: #E0E0E0;
        }
        .metrics-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
          gap: 16px;
          margin: 16px 0;
        }
        .metric {
          background: #1E1E1E;
          padding: 12px;
          border-radius: 4px;
          text-align: center;
        }
        .metric-label {
          font-size: 12px;
          color: #999;
          margin-bottom: 4px;
        }
        .metric-value {
          font-size: 24px;
          font-weight: bold;
        }
        .metric-detail {
          font-size: 12px;
          color: #999;
          margin-top: 4px;
        }
        .recommendation-box {
          background: #3F51B5;
          padding: 12px;
          border-radius: 4px;
          margin-top: 16px;
        }
      `}</style>
    </div>
  );
};
```

---

### 4. Provenance Timeline

**File:** `src/components/advisor/ProvenanceTimeline.tsx`

```tsx
import React from 'react';

interface ProvenanceData {
  total_data_points: number;
  sources: {
    [key: string]: {
      count: number;
      cache_hits: number;
      avg_confidence: number;
      oldest_age_seconds: number;
    };
  };
  oldest_data_age_seconds: number;
}

export const ProvenanceTimeline: React.FC<{
  provenance: ProvenanceData;
}> = ({ provenance }) => {
  const formatAge = (seconds: number): string => {
    if (seconds < 60) return `${Math.floor(seconds)}s ago`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    return `${Math.floor(seconds / 3600)}h ago`;
  };

  const getAgeColor = (seconds: number): string => {
    if (seconds < 60) return '#26A69A'; // Fresh (< 1min)
    if (seconds < 300) return '#FFA726'; // Acceptable (< 5min)
    return '#EF5350'; // Stale (> 5min)
  };

  return (
    <div className="provenance-timeline">
      <h4>🔍 Data Sources ({provenance.total_data_points} data points)</h4>

      <div className="sources-list">
        {Object.entries(provenance.sources).map(([source, data]) => (
          <div key={source} className="source-item">
            <div className="source-header">
              <span className="source-name">{source}</span>
              <span
                className="source-age"
                style={{ color: getAgeColor(data.oldest_age_seconds) }}
              >
                {formatAge(data.oldest_age_seconds)}
              </span>
            </div>
            <div className="source-stats">
              <span>{data.count} points</span>
              <span>•</span>
              <span>{data.cache_hits}/{data.count} cached</span>
              <span>•</span>
              <span>{(data.avg_confidence * 100).toFixed(0)}% confidence</span>
            </div>
          </div>
        ))}
      </div>

      <style jsx>{`
        .provenance-timeline {
          background: #2A2A2A;
          border-radius: 8px;
          padding: 16px;
          color: #E0E0E0;
          margin-top: 16px;
        }
        .sources-list {
          margin-top: 12px;
        }
        .source-item {
          background: #1E1E1E;
          padding: 12px;
          border-radius: 4px;
          margin-bottom: 8px;
        }
        .source-header {
          display: flex;
          justify-content: space-between;
          font-weight: bold;
          margin-bottom: 4px;
        }
        .source-stats {
          font-size: 12px;
          color: #999;
          display: flex;
          gap: 8px;
        }
      `}</style>
    </div>
  );
};
```

---

## Integration with CapitalCompanionPanel

**File:** `src/components/CapitalCompanionPanel.tsx`

```tsx
import { IndicatorOverlayChart } from './advisor/IndicatorOverlayChart';
import { ChainOfThoughtViewer } from './advisor/ChainOfThoughtViewer';
import { AccuracyMetricsPanel } from './advisor/AccuracyMetricsPanel';
import { ProvenanceTimeline } from './advisor/ProvenanceTimeline';

// Add to existing panel
export const CapitalCompanionPanel: React.FC = () => {
  const [showExplainability, setShowExplainability] = useState(false);
  const [cotData, setCotData] = useState(null);
  const [provenance, setProvenance] = useState(null);

  // ... existing code ...

  return (
    <div className="capital-companion-panel">
      {/* Existing recommendation display */}

      {/* NEW: Explainability toggle */}
      <button onClick={() => setShowExplainability(!showExplainability)}>
        {showExplainability ? 'Hide' : 'Show'} Details
      </button>

      {showExplainability && (
        <div className="explainability-section">
          <IndicatorOverlayChart symbol={symbol} timeframe={timeframe} />

          {cotData && (
            <ChainOfThoughtViewer
              steps={cotData.steps}
              totalScore={cotData.total_score}
              maxScore={cotData.max_score}
              recommendation={cotData.recommendation}
              reasoningSummary={cotData.reasoning_summary}
              risksIdentified={cotData.risks_identified}
              dataGaps={cotData.data_gaps}
            />
          )}

          <AccuracyMetricsPanel
            symbol={symbol}
            timeframe={timeframe}
            signal={recommendation?.signal}
          />

          {provenance && <ProvenanceTimeline provenance={provenance} />}
        </div>
      )}
    </div>
  );
};
```

---

## Dependencies

**Package additions to `package.json`:**
```json
{
  "dependencies": {
    "lightweight-charts": "^4.1.0"
  }
}
```

---

## Acceptance Criteria

- [ ] Indicator overlay chart displays candlesticks + 5 indicators
- [ ] Toggleable indicators (show/hide)
- [ ] Chain-of-thought viewer shows all 5 steps
- [ ] Accuracy metrics panel displays win rate, profit factor
- [ ] Provenance timeline shows data freshness
- [ ] Real-time updates via Socket.IO
- [ ] Responsive design (mobile-friendly)
- [ ] Performance: Chart renders < 1s

---

## Next Steps

Proceed to Phase 5.4: Integration & Testing
