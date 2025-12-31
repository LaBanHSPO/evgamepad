import React, { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';
import { useSocket } from '@/context/SocketContext';
import { Button } from '@/components/ui/button';

interface IndicatorOverlayChartProps {
  symbol: string;
  timeframe: string;
  height?: number;
}

interface Indicator {
  name: string;
  enabled: boolean;
  color: string;
  dataKey: string;
}

interface OHLCVDataPoint {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  ema21?: number;
  ema50?: number;
  sma200?: number;
  bb_upper?: number;
  bb_lower?: number;
  bb_middle?: number;
}

interface TechnicalResultData {
  success: boolean;
  data?: {
    symbol: string;
    timeframe: string;
    current_price?: number;
    indicators?: {
      ema_21?: number;
      ema_50?: number;
      sma_200?: number;
      bollinger_bands?: {
        upper?: number;
        middle?: number;
        lower?: number;
      };
    };
    support_resistance?: {
      support?: number[];
      resistance?: number[];
    };
  };
}

interface TechnicalData {
  current_price?: number;
  indicators?: {
    ema_21?: number;
    ema_50?: number;
    sma_200?: number;
    bollinger_bands?: {
      upper?: number;
      middle?: number;
      lower?: number;
    };
  };
  support_resistance?: {
    support?: number[];
    resistance?: number[];
  };
}

/**
 * TradingView-style chart with toggleable technical indicators
 */
export const IndicatorOverlayChart: React.FC<IndicatorOverlayChartProps> = ({
  symbol,
  timeframe,
  height = 400
}) => {
  const { socket } = useSocket();
  const [indicators, setIndicators] = useState<Indicator[]>([
    { name: 'EMA 21', enabled: true, color: '#2962FF', dataKey: 'ema21' },
    { name: 'EMA 50', enabled: true, color: '#FF6D00', dataKey: 'ema50' },
    { name: 'SMA 200', enabled: false, color: '#9C27B0', dataKey: 'sma200' },
    { name: 'BB Upper', enabled: false, color: '#26A69A', dataKey: 'bb_upper' },
    { name: 'BB Lower', enabled: false, color: '#26A69A', dataKey: 'bb_lower' }
  ]);

  const [chartData, setChartData] = useState<OHLCVDataPoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [supportResistance, setSupportResistance] = useState<{support: number[], resistance: number[]}>({
    support: [],
    resistance: []
  });

  // Fetch technical data when component mounts or symbol/timeframe changes
  useEffect(() => {
    if (!socket) return;

    setLoading(true);
    socket.emit('advisor:technical_summary', {
      symbol,
      timeframe,
      indicators: ['sma', 'ema', 'bb', 'volume']
    });

    socket.on('advisor:technical_result', handleTechnicalResult);

    return () => {
      socket.off('advisor:technical_result', handleTechnicalResult);
    };
  }, [socket, symbol, timeframe]);

  const handleTechnicalResult = (data: TechnicalResultData) => {
    if (data.success && data.data) {
      // Transform technical data into chart format
      const technicalData = data.data;

      // Extract OHLCV data if available
      // For this demo, we'll create mock data based on the technical indicators
      // In production, you'd fetch actual OHLCV data from MT5
      const mockOHLCV = generateMockOHLCV(technicalData);
      setChartData(mockOHLCV);

      // Extract support/resistance if available
      if (technicalData.support_resistance) {
        setSupportResistance({
          support: technicalData.support_resistance.support || [],
          resistance: technicalData.support_resistance.resistance || []
        });
      }

      setLoading(false);
    }
  };

  // Generate mock OHLCV data based on technical indicators
  const generateMockOHLCV = (technicalData: TechnicalData): OHLCVDataPoint[] => {
    const data: OHLCVDataPoint[] = [];
    const basePrice = technicalData.current_price || 2000;
    const now = new Date();

    for (let i = 50; i >= 0; i--) {
      const time = new Date(now.getTime() - i * 60 * 60 * 1000);
      const volatility = 0.01;
      const trend = (50 - i) * 0.1;
      const noise = (Math.random() - 0.5) * basePrice * volatility;

      const close = basePrice + trend + noise;
      const open = close - (Math.random() - 0.5) * basePrice * volatility * 0.5;
      const high = Math.max(open, close) + Math.random() * basePrice * volatility * 0.5;
      const low = Math.min(open, close) - Math.random() * basePrice * volatility * 0.5;

      data.push({
        time: time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
        open,
        high,
        low,
        close,
        volume: Math.random() * 1000 + 500,
        ema21: technicalData.indicators?.ema_21 ? close * 0.998 : undefined,
        ema50: technicalData.indicators?.ema_50 ? close * 0.995 : undefined,
        sma200: technicalData.indicators?.sma_200 ? close * 0.99 : undefined,
        bb_upper: technicalData.indicators?.bollinger_bands?.upper || undefined,
        bb_middle: technicalData.indicators?.bollinger_bands?.middle || undefined,
        bb_lower: technicalData.indicators?.bollinger_bands?.lower || undefined
      });
    }

    return data;
  };

  const toggleIndicator = (name: string) => {
    setIndicators(prev =>
      prev.map(ind =>
        ind.name === name ? { ...ind, enabled: !ind.enabled } : ind
      )
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 bg-background/50 rounded border border-border/50">
        <div className="text-muted-foreground text-sm">Loading chart data...</div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Indicator Toggles */}
      <div className="flex flex-wrap gap-2">
        {indicators.map(ind => (
          <Button
            key={ind.name}
            variant="outline"
            size="sm"
            onClick={() => toggleIndicator(ind.name)}
            className={`h-7 text-xs transition-opacity ${ind.enabled ? 'opacity-100 border-2' : 'opacity-50'}`}
            style={{ borderColor: ind.enabled ? ind.color : undefined }}
          >
            <span className="w-2 h-2 rounded-full mr-1.5" style={{ backgroundColor: ind.color }} />
            {ind.name}
          </Button>
        ))}
      </div>

      {/* Chart */}
      <div className="bg-background/30 rounded border border-border/50 p-4">
        <ResponsiveContainer width="100%" height={height}>
          <LineChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2B2B43" />
            <XAxis
              dataKey="time"
              stroke="#666"
              style={{ fontSize: '10px' }}
              tick={{ fill: '#999' }}
            />
            <YAxis
              stroke="#666"
              style={{ fontSize: '10px' }}
              tick={{ fill: '#999' }}
              domain={['auto', 'auto']}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1E1E1E',
                border: '1px solid #2B2B43',
                borderRadius: '4px',
                fontSize: '11px'
              }}
            />
            <Legend wrapperStyle={{ fontSize: '11px' }} />

            {/* Price Line */}
            <Line
              type="monotone"
              dataKey="close"
              stroke="#E0E0E0"
              strokeWidth={2}
              dot={false}
              name="Price"
            />

            {/* Indicators */}
            {indicators.map(ind =>
              ind.enabled && (
                <Line
                  key={ind.dataKey}
                  type="monotone"
                  dataKey={ind.dataKey}
                  stroke={ind.color}
                  strokeWidth={1.5}
                  dot={false}
                  name={ind.name}
                />
              )
            )}

            {/* Support/Resistance Levels */}
            {supportResistance.support.map((level, idx) => (
              <ReferenceLine key={`support-${idx}`} y={level} stroke="#26A69A" strokeDasharray="3 3" />
            ))}
            {supportResistance.resistance.map((level, idx) => (
              <ReferenceLine key={`resistance-${idx}`} y={level} stroke="#EF5350" strokeDasharray="3 3" />
            ))}
          </LineChart>
        </ResponsiveContainer>

        <div className="text-xs text-muted-foreground mt-2 text-center">
          {symbol} • {timeframe} • {chartData.length} candles
        </div>
      </div>
    </div>
  );
};
