import { SystemHeader } from "@/components/SystemHeader";
import { MarketOverviewPanel } from "@/components/MarketOverviewPanel";
import { PriceActionPanel } from "@/components/PriceActionPanel";
import { MarketSentimentPanel } from "@/components/MarketSentimentPanel";
import { KOLUpdatesPanel } from "@/components/KOLUpdatesPanel";
import { AIAnalysisPanel } from "@/components/AIAnalysisPanel";
import { MajorNewsPanel } from "@/components/MajorNewsPanel";

const Monitor1 = () => {
  return (
    <div className="min-h-screen bg-background text-foreground p-4 relative overflow-hidden">
      {/* Scanlines overlay */}
      <div className="scanlines" />
      
      {/* CRT flicker effect */}
      <div className="crt-flicker" />
      
      {/* Main content */}
      <div className="relative z-10 max-w-7xl mx-auto space-y-4">
        <SystemHeader monitorNumber={1} title="MARKET COMMANDER" />
        
        {/* Row 1: Market Overview & Sentiment */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <MarketOverviewPanel />
          <MarketSentimentPanel />
        </div>
        
        {/* Row 2: Price Action */}
        <PriceActionPanel />
        
        {/* Row 3: KOL Updates, AI Analysis, Major News */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <KOLUpdatesPanel />
          <AIAnalysisPanel />
          <MajorNewsPanel />
        </div>
      </div>
    </div>
  );
};

export default Monitor1;
