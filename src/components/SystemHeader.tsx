import { Activity, Shield, Wifi } from "lucide-react";

const SystemHeader = () => {
  const currentTime = new Date().toLocaleTimeString('en-US', { 
    hour12: false, 
    hour: '2-digit', 
    minute: '2-digit', 
    second: '2-digit' 
  });

  return (
    <header className="border-b border-panel-border bg-muted/30 px-6 py-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-primary" />
            <h1 className="font-display text-lg font-bold tracking-wider text-primary glow-text">
              MONITOR 3
            </h1>
          </div>
          <span className="text-xs text-muted-foreground tracking-widest">
            SYSTEM ENGINEER
          </span>
        </div>

        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <Activity className="h-4 w-4 text-terminal-green animate-pulse" />
            <span className="text-xs text-terminal-green">ONLINE</span>
          </div>
          
          <div className="flex items-center gap-2">
            <Wifi className="h-4 w-4 text-primary" />
            <span className="text-xs text-muted-foreground">UPLINK: STABLE</span>
          </div>

          <div className="font-mono text-sm text-primary tabular-nums">
            {currentTime}
          </div>
        </div>
      </div>
    </header>
  );
};

export default SystemHeader;
