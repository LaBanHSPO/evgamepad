import { SystemHeader } from "@/components/SystemHeader";
import { ActiveOrdersPanel } from "@/components/ActiveOrdersPanel";
import { PositionManagerPanel } from "@/components/PositionManagerPanel";
import { OrderEntryPanel } from "@/components/OrderEntryPanel";

const Monitor2 = () => {
  return (
    <div className="min-h-screen bg-background text-foreground p-4 relative overflow-hidden">
      {/* Scanlines overlay */}
      <div className="scanlines" />
      
      {/* CRT flicker effect */}
      <div className="crt-flicker" />
      
      {/* Main content */}
      <div className="relative z-10 max-w-7xl mx-auto space-y-4">
        <SystemHeader monitorNumber={2} title="TRADE OPERATIONS" />
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2">
            <ActiveOrdersPanel />
          </div>
          <OrderEntryPanel />
        </div>
        
        <PositionManagerPanel />
      </div>
    </div>
  );
};

export default Monitor2;
