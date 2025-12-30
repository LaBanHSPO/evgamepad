import React from 'react';
import { Target, Pin, CheckCircle2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

export interface PatternAnalysisData {
    symbol: string;
    timeframe: string;
    candlestick_patterns: {
        detected: Array<{
            name: string;
            title: string;
            description: string;
        }>;
        bullish_patterns: string[];
        bearish_patterns: string[];
    };
    chart_patterns: {
        patterns: Array<{
            name: string;
            confidence: number;
        }>;
    };
}

interface PatternAnalysisCardProps {
    data: PatternAnalysisData;
    onPin?: (data: any) => void;
}

export const PatternAnalysisCard: React.FC<PatternAnalysisCardProps> = ({ data, onPin }) => {
    const patterns = [
        ...(data.candlestick_patterns.detected || []),
        ...(data.chart_patterns.patterns || [])
    ];

    return (
        <div className="bg-background/80 border border-border rounded-lg p-3 my-2 w-full max-w-sm text-xs font-mono">
            <div className="flex justify-between items-start mb-2 border-b border-border/50 pb-2">
                <div className="flex items-center gap-2">
                    <Target className="w-3 h-3 text-secondary" />
                    <span className="font-bold text-foreground">Pattern Scan</span>
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

            {patterns.length === 0 ? (
                <div className="text-muted-foreground italic py-2 text-center">No distinct patterns detected</div>
            ) : (
                <div className="space-y-2">
                    {patterns.map((p, idx) => (
                        <div key={idx} className="bg-background/50 p-2 rounded border border-border/30 flex items-start gap-2">
                            <CheckCircle2 className="w-3 h-3 text-terminal-green mt-0.5 shrink-0" />
                            <div>
                                <div className="font-semibold text-foreground">{p.title || p.name}</div>
                                {p.description && <div className="text-[10px] text-muted-foreground leading-tight mt-0.5">{p.description}</div>}
                            </div>
                        </div>
                    ))}
                </div>
            )}

            <div className="mt-2 flex gap-1 flex-wrap">
                {data.candlestick_patterns.bullish_patterns?.length > 0 && (
                    <Badge variant="outline" className="border-terminal-green/50 text-terminal-green text-[10px] h-5">Bullish Bias</Badge>
                )}
                {data.candlestick_patterns.bearish_patterns?.length > 0 && (
                    <Badge variant="outline" className="border-danger-red/50 text-danger-red text-[10px] h-5">Bearish Bias</Badge>
                )}
            </div>
        </div>
    );
};
