import { SystemHeader } from "@/components/SystemHeader";
import RiskManagementPanel from "@/components/RiskManagementPanel";
import CapitalCompanionPanel from "@/components/CapitalCompanionPanel";
import MissionLogPanel from "@/components/MissionLogPanel";

const Index = () => {
  return (
    <div className="min-h-screen bg-background text-foreground p-4 relative overflow-hidden">
      {/* Scanlines overlay */}
      <div className="scanlines" />
      
      {/* CRT flicker effect */}
      <div className="crt-flicker" />
      
      {/* Main content */}
      <div className="relative z-10 max-w-7xl mx-auto space-y-4">
        <SystemHeader monitorNumber={3} title="SYSTEM ENGINEER" />
        
        {/* Top Panel: Risk Management Core */}
        <RiskManagementPanel />
        
        {/* Middle Panel: Capital Companion Logic */}
        <CapitalCompanionPanel />
        
        {/* Bottom Panel: Mission Log */}
        <MissionLogPanel />
      </div>

      {/* Corner Decorations */}
      <div className="fixed top-0 left-0 w-16 h-16 border-l-2 border-t-2 border-primary/30 pointer-events-none" />
      <div className="fixed top-0 right-0 w-16 h-16 border-r-2 border-t-2 border-primary/30 pointer-events-none" />
      <div className="fixed bottom-0 left-0 w-16 h-16 border-l-2 border-b-2 border-primary/30 pointer-events-none" />
      <div className="fixed bottom-0 right-0 w-16 h-16 border-r-2 border-b-2 border-primary/30 pointer-events-none" />

      {/* Version Watermark */}
      <div className="fixed bottom-4 right-4 text-xs text-muted-foreground/50 font-mono pointer-events-none">
        TRADING COMMAND CENTER v3.1.4
      </div>
    </div>
  );
};

export default Index;
