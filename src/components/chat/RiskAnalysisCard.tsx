import React from 'react';
import { ShieldCheck, Pin, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';

export interface RiskAnalysisData {
    symbol: string;
    entry_price: number;
    stop_loss: number;
    take_profit: number;
    timeframe: string;
    risk_reward: {
        ratio: number;
        is_acceptable: boolean;
    };
    position_sizing: {
        units: number;
        risk_amount: number;
    };
    recommendation: {
        action: 'BUY' | 'SELL' | 'HOLD';
    };
}

interface RiskAnalysisCardProps {
    data: RiskAnalysisData;
    onPin?: (data: any) => void;
}

export const RiskAnalysisCard: React.FC<RiskAnalysisCardProps> = ({ data, onPin }) => {
    const rrColor = data.risk_reward.is_acceptable ? 'text-terminal-green' : 'text-danger-red';
    const actionColor = data.recommendation.action === 'BUY' ? 'text-terminal-green' : data.recommendation.action === 'SELL' ? 'text-danger-red' : 'text-secondary';

    return (
        <div className="bg-background/80 border border-border rounded-lg p-3 my-2 w-full max-w-sm text-xs font-mono">
            <div className="flex justify-between items-start mb-2 border-b border-border/50 pb-2">
                <div className="flex items-center gap-2">
                    <ShieldCheck className="w-3 h-3 text-secondary" />
                    <span className="font-bold text-foreground">Risk Calculator</span>
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

            <div className="flex justify-between items-center mb-3">
                <span className="text-muted-foreground">Action</span>
                <span className={`font-bold text-sm ${actionColor} border border-current px-2 py-0.5 rounded`}>
                    {data.recommendation.action}
                </span>
            </div>

            <div className="grid grid-cols-3 gap-2 mb-2 text-center">
                <div className="bg-background/50 p-1.5 rounded border border-border/30">
                    <span className="text-muted-foreground block text-[9px] uppercase">Entry</span>
                    <span className="font-semibold">{data.entry_price.toFixed(2)}</span>
                </div>
                <div className="bg-background/50 p-1.5 rounded border border-border/30">
                    <span className="text-muted-foreground block text-[9px] uppercase">Stop</span>
                    <span className="font-semibold text-danger-red">{data.stop_loss.toFixed(2)}</span>
                </div>
                <div className="bg-background/50 p-1.5 rounded border border-border/30">
                    <span className="text-muted-foreground block text-[9px] uppercase">Target</span>
                    <span className="font-semibold text-terminal-green">{data.take_profit.toFixed(2)}</span>
                </div>
            </div>

            <div className="border-t border-border/30 pt-2 space-y-1">
                <div className="flex justify-between">
                    <span className="text-muted-foreground">R/R Ratio</span>
                    <span className={`font-bold ${rrColor}`}>{data.risk_reward.ratio.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                    <span className="text-muted-foreground">Pos Size</span>
                    <span className="font-semibold">{data.position_sizing.units.toFixed(2)} units</span>
                </div>
                <div className="flex justify-between">
                    <span className="text-muted-foreground">Risk Amt</span>
                    <span className="font-semibold text-danger-red">${data.position_sizing.risk_amount.toFixed(2)}</span>
                </div>
            </div>

            {!data.risk_reward.is_acceptable && (
                <div className="mt-2 text-[10px] text-danger-red flex items-center gap-1">
                    <AlertTriangle className="w-3 h-3" />
                    <span>R/R is below recommended threshold</span>
                </div>
            )}
        </div>
    );
};
