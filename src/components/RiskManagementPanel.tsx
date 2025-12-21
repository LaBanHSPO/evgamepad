import { useMemo } from "react";
import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts";
import { TrendingUp, AlertTriangle } from "lucide-react";

const RiskManagementPanel = () => {
  const accountBalance = 85;
  const riskExposure = 1.5;
  const maxRisk = 5;
  
  const isRiskSafe = riskExposure <= 2;

  const gaugeData = useMemo(() => {
    const percentage = (riskExposure / maxRisk) * 100;
    return [
      { value: percentage, name: "exposure" },
      { value: 100 - percentage, name: "remaining" },
    ];
  }, [riskExposure, maxRisk]);

  return (
    <div className="panel">
      <div className="panel-header">
        <div className="status-indicator status-online" />
        <h2 className="panel-title">Risk Management Core</h2>
        <span className="ml-auto text-xs text-muted-foreground">
          MODULE: RM-CORE-01
        </span>
      </div>

      <div className="p-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Account Balance Health Bar */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-terminal-green" />
                <span className="text-xs uppercase tracking-wider text-muted-foreground">
                  Account Balance
                </span>
              </div>
              <span className="font-display text-xl font-bold text-terminal-green data-value">
                {accountBalance}%
              </span>
            </div>
            
            <div className="relative h-6 bg-muted rounded-sm overflow-hidden border border-panel-border">
              <div 
                className="absolute inset-y-0 left-0 rounded-sm transition-all duration-1000"
                style={{ 
                  width: `${accountBalance}%`,
                  background: 'linear-gradient(90deg, hsl(200, 80%, 50%), hsl(142, 70%, 45%))',
                  boxShadow: '0 0 15px hsl(142 70% 45% / 0.5)'
                }}
              />
              {/* Grid lines */}
              <div className="absolute inset-0 flex">
                {[...Array(10)].map((_, i) => (
                  <div 
                    key={i} 
                    className="flex-1 border-r border-background/30 last:border-r-0"
                  />
                ))}
              </div>
            </div>
            
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>0%</span>
              <span>CRITICAL</span>
              <span>OPTIMAL</span>
              <span>100%</span>
            </div>
          </div>

          {/* Risk Exposure Gauge */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertTriangle className={`h-4 w-4 ${isRiskSafe ? 'text-terminal-green' : 'text-danger-red'}`} />
                <span className="text-xs uppercase tracking-wider text-muted-foreground">
                  Risk Exposure
                </span>
              </div>
              <span className={`text-xs px-2 py-0.5 rounded ${isRiskSafe ? 'bg-terminal-green/20 text-terminal-green' : 'bg-danger-red/20 text-danger-red'}`}>
                {isRiskSafe ? 'SAFE ZONE' : 'DANGER'}
              </span>
            </div>

            <div className="relative flex items-center justify-center">
              <div className="w-48 h-24 overflow-hidden">
                <ResponsiveContainer width="100%" height={192}>
                  <PieChart>
                    <Pie
                      data={gaugeData}
                      cx="50%"
                      cy="100%"
                      startAngle={180}
                      endAngle={0}
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={0}
                      dataKey="value"
                      stroke="none"
                    >
                      <Cell 
                        fill={isRiskSafe ? "hsl(142, 70%, 45%)" : "hsl(0, 84%, 50%)"} 
                        style={{ 
                          filter: `drop-shadow(0 0 10px ${isRiskSafe ? 'hsl(142, 70%, 45%)' : 'hsl(0, 84%, 50%)'})`
                        }}
                      />
                      <Cell fill="hsl(0, 0%, 15%)" />
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
              </div>
              
              {/* Center Value */}
              <div className="absolute bottom-0 text-center">
                <span className={`font-display text-2xl font-bold data-value ${isRiskSafe ? 'text-terminal-green' : 'text-danger-red'}`}>
                  {riskExposure}%
                </span>
              </div>
            </div>

            <div className="flex justify-between text-xs text-muted-foreground px-4">
              <span>0%</span>
              <span className="text-terminal-green">2% MAX SAFE</span>
              <span>{maxRisk}%</span>
            </div>
          </div>
        </div>

        {/* Status Indicators */}
        <div className="mt-6 grid grid-cols-4 gap-4 border-t border-panel-border pt-4">
          {[
            { label: 'MARGIN LEVEL', value: '1,245%', status: 'safe' },
            { label: 'DRAWDOWN', value: '3.2%', status: 'safe' },
            { label: 'OPEN POSITIONS', value: '3', status: 'warning' },
            { label: 'EQUITY', value: '$12,847', status: 'safe' },
          ].map((item) => (
            <div key={item.label} className="text-center">
              <p className="text-xs text-muted-foreground mb-1">{item.label}</p>
              <p className={`font-display text-sm font-bold ${
                item.status === 'safe' ? 'text-terminal-green' : 
                item.status === 'warning' ? 'text-primary' : 'text-danger-red'
              }`}>
                {item.value}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default RiskManagementPanel;
