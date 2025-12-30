import React, { useState } from 'react';
import { Plus, Trash2 } from 'lucide-react';

interface Position {
  id: string;
  symbol: string;
  entryPrice: number;
  currentPrice: number;
  positionSize: number;
  stopLoss: number;
  timeframe: string;
}

interface PositionInputFormProps {
  onSubmit: (positions: Position[], accountBalance: number) => void;
  isAnalyzing: boolean;
}

export const PositionInputForm: React.FC<PositionInputFormProps> = ({
  onSubmit,
  isAnalyzing
}) => {
  const [accountBalance, setAccountBalance] = useState(10000);
  const [positions, setPositions] = useState<Position[]>([
    {
      id: crypto.randomUUID(),
      symbol: 'XAUUSD',
      entryPrice: 0,
      currentPrice: 0,
      positionSize: 0,
      stopLoss: 0,
      timeframe: 'H1'
    }
  ]);

  const addPosition = () => {
    setPositions([
      ...positions,
      {
        id: crypto.randomUUID(),
        symbol: '',
        entryPrice: 0,
        currentPrice: 0,
        positionSize: 0,
        stopLoss: 0,
        timeframe: 'H1'
      }
    ]);
  };

  const removePosition = (id: string) => {
    setPositions(positions.filter(p => p.id !== id));
  };

  const updatePosition = (id: string, field: keyof Position, value: string | number) => {
    setPositions(
      positions.map(p =>
        p.id === id ? { ...p, [field]: value } : p
      )
    );
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(positions, accountBalance);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Account Balance */}
      <div className="panel">
        <div className="panel-header">
          <h3 className="panel-title text-sm">Account Balance</h3>
        </div>
        <div className="p-4">
          <input
            type="number"
            step="0.01"
            value={accountBalance}
            onChange={(e) => setAccountBalance(parseFloat(e.target.value))}
            className="w-full bg-background border border-panel-border rounded px-3 py-2 font-mono text-terminal-green"
            required
          />
        </div>
      </div>

      {/* Positions List */}
      <div className="panel">
        <div className="panel-header">
          <h3 className="panel-title text-sm">Open Positions</h3>
          <button
            type="button"
            onClick={addPosition}
            className="ml-auto text-primary hover:text-primary/80 transition-colors"
            disabled={isAnalyzing}
          >
            <Plus className="h-4 w-4" />
          </button>
        </div>
        <div className="p-4 space-y-4">
          {positions.map((position) => (
            <div key={position.id} className="grid grid-cols-6 gap-2 items-end border-b border-panel-border pb-4 last:border-b-0">
              <div>
                <label className="block text-xs text-muted-foreground mb-1">Symbol</label>
                <input
                  type="text"
                  value={position.symbol}
                  onChange={(e) => updatePosition(position.id, 'symbol', e.target.value.toUpperCase())}
                  className="w-full bg-background border border-panel-border rounded px-2 py-1 text-sm font-mono"
                  placeholder="XAUUSD"
                  required
                />
              </div>
              <div>
                <label className="block text-xs text-muted-foreground mb-1">Entry</label>
                <input
                  type="number"
                  step="0.01"
                  value={position.entryPrice || ''}
                  onChange={(e) => updatePosition(position.id, 'entryPrice', parseFloat(e.target.value))}
                  className="w-full bg-background border border-panel-border rounded px-2 py-1 text-sm font-mono"
                  required
                />
              </div>
              <div>
                <label className="block text-xs text-muted-foreground mb-1">Current</label>
                <input
                  type="number"
                  step="0.01"
                  value={position.currentPrice || ''}
                  onChange={(e) => updatePosition(position.id, 'currentPrice', parseFloat(e.target.value))}
                  className="w-full bg-background border border-panel-border rounded px-2 py-1 text-sm font-mono"
                  required
                />
              </div>
              <div>
                <label className="block text-xs text-muted-foreground mb-1">Size</label>
                <input
                  type="number"
                  step="0.01"
                  value={position.positionSize || ''}
                  onChange={(e) => updatePosition(position.id, 'positionSize', parseFloat(e.target.value))}
                  className="w-full bg-background border border-panel-border rounded px-2 py-1 text-sm font-mono"
                  required
                />
              </div>
              <div>
                <label className="block text-xs text-muted-foreground mb-1">Stop Loss</label>
                <input
                  type="number"
                  step="0.01"
                  value={position.stopLoss || ''}
                  onChange={(e) => updatePosition(position.id, 'stopLoss', parseFloat(e.target.value))}
                  className="w-full bg-background border border-panel-border rounded px-2 py-1 text-sm font-mono"
                />
              </div>
              <div>
                {positions.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removePosition(position.id)}
                    className="text-danger-red hover:text-danger-red/80 transition-colors"
                    disabled={isAnalyzing}
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isAnalyzing}
        className="w-full bg-primary hover:bg-primary/80 text-primary-foreground font-bold py-3 px-6 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isAnalyzing ? 'Analyzing Portfolio...' : 'Analyze Portfolio Risk'}
      </button>
    </form>
  );
};
