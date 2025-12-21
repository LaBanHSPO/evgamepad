import { ArrowUpRight, ArrowDownRight, History } from "lucide-react";

interface Trade {
  id: string;
  time: string;
  pair: string;
  type: 'LONG' | 'SHORT';
  size: string;
  result: 'WIN' | 'LOSS';
  pnl: string;
}

const trades: Trade[] = [
  { id: 'T-0847', time: '14:32:18', pair: 'BTC/USD', type: 'LONG', size: '0.15', result: 'WIN', pnl: '+$234.50' },
  { id: 'T-0846', time: '13:15:42', pair: 'ETH/USD', type: 'SHORT', size: '2.40', result: 'WIN', pnl: '+$156.20' },
  { id: 'T-0845', time: '11:48:09', pair: 'BTC/USD', type: 'LONG', size: '0.10', result: 'LOSS', pnl: '-$89.00' },
  { id: 'T-0844', time: '10:22:31', pair: 'SOL/USD', type: 'LONG', size: '45.00', result: 'WIN', pnl: '+$312.80' },
  { id: 'T-0843', time: '09:05:55', pair: 'ETH/USD', type: 'LONG', size: '1.80', result: 'WIN', pnl: '+$178.40' },
  { id: 'T-0842', time: '08:41:12', pair: 'BTC/USD', type: 'SHORT', size: '0.08', result: 'LOSS', pnl: '-$45.20' },
  { id: 'T-0841', time: '07:18:33', pair: 'XRP/USD', type: 'LONG', size: '1500', result: 'WIN', pnl: '+$89.60' },
  { id: 'T-0840', time: '06:52:47', pair: 'BTC/USD', type: 'LONG', size: '0.12', result: 'WIN', pnl: '+$267.30' },
];

const MissionLogPanel = () => {
  const winCount = trades.filter(t => t.result === 'WIN').length;
  const totalTrades = trades.length;
  const winRate = ((winCount / totalTrades) * 100).toFixed(1);

  return (
    <div className="panel">
      <div className="panel-header">
        <div className="status-indicator status-online" />
        <History className="h-4 w-4 text-primary" />
        <h2 className="panel-title">Mission Log (Trade History)</h2>
        <div className="ml-auto flex items-center gap-4">
          <span className="text-xs text-muted-foreground">
            WIN RATE: <span className="text-terminal-green font-bold">{winRate}%</span>
          </span>
          <span className="text-xs text-muted-foreground">
            TOTAL: <span className="text-primary font-bold">{totalTrades}</span>
          </span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-panel-border bg-muted/30">
              <th className="px-4 py-2 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">ID</th>
              <th className="px-4 py-2 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">Time</th>
              <th className="px-4 py-2 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">Pair</th>
              <th className="px-4 py-2 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">Type</th>
              <th className="px-4 py-2 text-right text-xs font-bold uppercase tracking-wider text-muted-foreground">Size</th>
              <th className="px-4 py-2 text-center text-xs font-bold uppercase tracking-wider text-muted-foreground">Result</th>
              <th className="px-4 py-2 text-right text-xs font-bold uppercase tracking-wider text-muted-foreground">P&L</th>
            </tr>
          </thead>
          <tbody className="font-mono text-sm">
            {trades.map((trade, index) => (
              <tr 
                key={trade.id}
                className={`
                  border-b border-panel-border/50 transition-colors
                  ${index % 2 === 0 ? 'bg-background/30' : 'bg-muted/20'}
                  ${trade.result === 'WIN' ? 'bg-terminal-green/5' : ''}
                  hover:bg-primary/5
                `}
              >
                <td className="px-4 py-2 text-muted-foreground">{trade.id}</td>
                <td className="px-4 py-2 text-primary tabular-nums">{trade.time}</td>
                <td className="px-4 py-2 text-foreground font-bold">{trade.pair}</td>
                <td className="px-4 py-2">
                  <span className={`inline-flex items-center gap-1 ${
                    trade.type === 'LONG' ? 'text-terminal-green' : 'text-danger-red'
                  }`}>
                    {trade.type === 'LONG' ? (
                      <ArrowUpRight className="h-3 w-3" />
                    ) : (
                      <ArrowDownRight className="h-3 w-3" />
                    )}
                    {trade.type}
                  </span>
                </td>
                <td className="px-4 py-2 text-right tabular-nums text-foreground">{trade.size}</td>
                <td className="px-4 py-2 text-center">
                  <span className={`
                    inline-block px-2 py-0.5 rounded text-xs font-bold
                    ${trade.result === 'WIN' 
                      ? 'bg-terminal-green/20 text-terminal-green' 
                      : 'bg-danger-red/20 text-danger-red'
                    }
                  `}>
                    {trade.result}
                  </span>
                </td>
                <td className={`px-4 py-2 text-right font-bold tabular-nums ${
                  trade.result === 'WIN' ? 'text-terminal-green' : 'text-danger-red'
                }`}>
                  {trade.pnl}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Summary Footer */}
      <div className="px-4 py-3 border-t border-panel-border bg-muted/20 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <div className="text-xs">
            <span className="text-muted-foreground">Today's P&L: </span>
            <span className="text-terminal-green font-bold">+$1,104.60</span>
          </div>
          <div className="text-xs">
            <span className="text-muted-foreground">Avg Win: </span>
            <span className="text-terminal-green font-bold">$206.47</span>
          </div>
          <div className="text-xs">
            <span className="text-muted-foreground">Avg Loss: </span>
            <span className="text-danger-red font-bold">-$67.10</span>
          </div>
        </div>
        <div className="text-xs text-muted-foreground">
          Last Updated: <span className="text-primary">14:32:18 UTC</span>
        </div>
      </div>
    </div>
  );
};

export default MissionLogPanel;
