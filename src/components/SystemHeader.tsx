import { Activity, Shield, Wifi, Volume2 } from "lucide-react";
import { useState } from "react";
import { MonitorNav } from "./MonitorNav";
import { AudioSettingsModal } from "./AudioSettingsModal";
import { Button } from "./ui/button";

interface SystemHeaderProps {
  monitorNumber: number;
  title: string;
}

export const SystemHeader = ({ monitorNumber, title }: SystemHeaderProps) => {
  const [isAudioSettingsOpen, setIsAudioSettingsOpen] = useState(false);

  const currentTime = new Date().toLocaleTimeString('en-US', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });

  return (
    <header className="border-b border-primary/30 bg-panel-bg/50 px-4 py-3 rounded-t">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-primary" />
            <h1 className="font-display text-lg font-bold tracking-wider text-primary">
              MONITOR {monitorNumber}
            </h1>
          </div>
          <span className="text-xs text-muted-foreground tracking-widest">
            {title}
          </span>
        </div>

        <MonitorNav />

        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <Activity className="h-4 w-4 text-terminal-green animate-pulse" />
            <span className="text-xs text-terminal-green">ONLINE</span>
          </div>

          <div className="flex items-center gap-2">
            <Wifi className="h-4 w-4 text-primary" />
            <span className="text-xs text-muted-foreground">UPLINK: STABLE</span>
          </div>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsAudioSettingsOpen(true)}
            className="h-8 w-8 p-0"
            title="Audio Settings"
          >
            <Volume2 className="h-4 w-4" />
          </Button>

          <div className="font-mono text-sm text-primary tabular-nums">
            {currentTime}
          </div>
        </div>
      </div>

      <AudioSettingsModal
        open={isAudioSettingsOpen}
        onOpenChange={setIsAudioSettingsOpen}
      />
    </header>
  );
};

export default SystemHeader;
