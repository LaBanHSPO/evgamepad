import { SystemHeader } from "@/components/SystemHeader";
import { MarketOverviewPanel } from "@/components/MarketOverviewPanel";
import { PriceActionPanel } from "@/components/PriceActionPanel";
import { MarketSentimentPanel } from "@/components/MarketSentimentPanel";
import { KOLUpdatesPanel } from "@/components/KOLUpdatesPanel";
import { AIAnalysisPanel } from "@/components/AIAnalysisPanel";
import { MajorNewsPanel } from "@/components/MajorNewsPanel";
import CapitalCompanionPanel from "@/components/CapitalCompanionPanel";

const Plan = () => {
  return (
    <div className="min-h-screen bg-background text-foreground relative">
      {/* Scanlines overlay */}
      <div className="scanlines" />

      {/* CRT flicker effect */}
      <div className="crt-flicker" />

      {/* Main content */}
      <div className="relative z-10 max-w-7xl mx-auto">
        <div className="p-4 pb-0">
          <SystemHeader monitorNumber={2} title="PLAN" />
        </div>

        <div className="p-4 space-y-4">
          {/* Row 1: Market Overview & Sentiment */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <MarketOverviewPanel />
            <MarketSentimentPanel />
          </div>
        </div>

        {/* Top: Capital Companion Logic - Sticky */}
        <div className="sticky top-0 z-50 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 p-4 border-b border-border/50 shadow-md">
          <CapitalCompanionPanel />
        </div>

        <div className="p-4 space-y-4">


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
    </div>
  );
};

export default Plan;
