import SystemHeader from "@/components/SystemHeader";
import RiskManagementPanel from "@/components/RiskManagementPanel";
import CapitalCompanionPanel from "@/components/CapitalCompanionPanel";
import MissionLogPanel from "@/components/MissionLogPanel";

const Index = () => {
  return (
    <div className="min-h-screen bg-background scanlines crt-flicker">
      <SystemHeader />
      
      <main className="p-4 lg:p-6 space-y-4">
        {/* Top Panel: Risk Management Core */}
        <RiskManagementPanel />
        
        {/* Middle Panel: Capital Companion Logic */}
        <CapitalCompanionPanel />
        
        {/* Bottom Panel: Mission Log */}
        <MissionLogPanel />
      </main>

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
