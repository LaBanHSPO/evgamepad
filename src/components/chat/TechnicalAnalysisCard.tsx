import React from 'react';
import { TrendingUp, TrendingDown, Activity, Pin } from 'lucide-react';
import { Button } from '@/components/ui/button';

export interface TechnicalAnalysisData {
    symbol: string;
    timeframe: string;
    last_close: number;
    indicators: {
        rsi: number;
        macd: {
            macd: number;
            signal: number;
            histogram: number;
        };
        adx: number;
    };
    signals: {
        rsi: string;
        macd: string;
        trend: string;
    };
    support_resistance: {
        nearest_support: number;
        nearest_resistance: number;
    };
}

interface TechnicalAnalysisCardProps {
    data: TechnicalAnalysisData;
    onPin?: (data: any) => void;
}

export const TechnicalAnalysisCard: React.FC<TechnicalAnalysisCardProps> = ({ data, onPin }) => {
    const isBullish = data.signals.trend === 'bullish';
    const trendColor = isBullish ? 'text-terminal-green' : 'text-danger-red';

    return (
        <div className="bg-background/80 border border-border rounded-lg p-3 my-2 w-full max-w-sm text-xs font-mono">
            <div className="flex justify-between items-start mb-2 border-b border-border/50 pb-2">
                <div>
                    <div className="font-bold flex items-center gap-2">
                        <Activity className="w-3 h-3 text-primary" />
                        <span className="text-foreground">{data.symbol} ({data.timeframe})</span>
                    </div>
                    <div className="text-lg font-bold text-foreground tracking-wider mt-0.5">
                        {data.last_close.toFixed(2)}
                    </div>
                </div>
                <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6 text-muted-foreground hover:text-secondary"
                    onClick={() => onPin && onPin(data)}
                >
                    <Pin className="w-3 h-3" />
                </Button>
            </div>

            <div className="grid grid-cols-2 gap-2 mb-2">
                <div className="bg-background/50 p-1.5 rounded border border-border/30">
                    <span className="text-muted-foreground block text-[10px] uppercase">RSI (14)</span>
                    <div className="flex justify-between items-end">
                        <span className="font-semibold">{data.indicators.rsi.toFixed(1)}</span>
                        <span className={`text-[10px] ${data.signals.rsi === 'oversold' ? 'text-terminal-green' : data.signals.rsi === 'overbought' ? 'text-danger-red' : 'text-muted-foreground'}`}>
                            {data.signals.rsi}
                        </span>
                    </div>
                </div>
                <div className="bg-background/50 p-1.5 rounded border border-border/30">
                    <span className="text-muted-foreground block text-[10px] uppercase">Trend</span>
                    <div className="flex justify-between items-end">
                        <span className={`font-semibold ${trendColor}`}>{data.signals.trend.toUpperCase()}</span>
                        {isBullish ? <TrendingUp className={`w-3 h-3 ${trendColor}`} /> : <TrendingDown className={`w-3 h-3 ${trendColor}`} />}
                    </div>
                </div>
            </div>

            <div className="space-y-1 text-[10px]">
                <div className="flex justify-between">
                    <span className="text-muted-foreground">MACD</span>
                    <span className={data.indicators.macd.macd > data.indicators.macd.signal ? 'text-terminal-green' : 'text-danger-red'}>
                        {data.indicators.macd.macd.toFixed(3)}
                    </span>
                </div>
                <div className="flex justify-between">
                    <span className="text-muted-foreground">Support</span>
                    <span className="text-foreground">{data.support_resistance.nearest_support?.toFixed(2) || 'N/A'}</span>
                </div>
                <div className="flex justify-between">
                    <span className="text-muted-foreground">Resistance</span>
                    <span className="text-foreground">{data.support_resistance.nearest_resistance?.toFixed(2) || 'N/A'}</span>
                </div>
            </div>
        </div>
    );
};
