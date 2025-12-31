import React from 'react';
import { TrendingUp, Zap, BarChart3, Search, ShieldAlert } from 'lucide-react';

interface ReasoningStep {
  step_number: number;
  category: string;
  description: string;
  points_awarded: number;
  max_points: number;
  confidence: number;
  indicators_used?: string[];
}

interface ChainOfThoughtViewerProps {
  steps: ReasoningStep[];
  totalScore: number;
  maxScore: number;
  recommendation: string;
  reasoningSummary: string;
  risksIdentified: string[];
  dataGaps: string[];
}

/**
 * Displays step-by-step chain-of-thought reasoning for AI recommendations
 */
export const ChainOfThoughtViewer: React.FC<ChainOfThoughtViewerProps> = ({
  steps,
  totalScore,
  maxScore,
  recommendation,
  reasoningSummary,
  risksIdentified,
  dataGaps
}) => {
  const getCategoryIcon = (category: string) => {
    const iconMap: Record<string, React.ReactNode> = {
      trend: <TrendingUp className="w-4 h-4" />,
      momentum: <Zap className="w-4 h-4" />,
      volume: <BarChart3 className="w-4 h-4" />,
      pattern: <Search className="w-4 h-4" />,
      risk: <ShieldAlert className="w-4 h-4" />
    };
    return iconMap[category.toLowerCase()] || <span>•</span>;
  };

  const getScoreColor = (points: number, max: number): string => {
    const ratio = points / max;
    if (ratio >= 0.8) return '#26A69A'; // Green
    if (ratio >= 0.5) return '#FFA726'; // Orange
    return '#EF5350'; // Red
  };

  const getRecommendationColor = (rec: string): string => {
    if (rec.includes('BUY')) return '#26A69A';
    if (rec.includes('SELL')) return '#EF5350';
    return '#FFA726';
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h3 className="text-sm font-bold text-foreground">Chain-of-Thought Reasoning</h3>
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">Score:</span>
          <div className="px-3 py-1 bg-primary/20 rounded-full text-xs font-bold text-primary">
            {totalScore}/{maxScore}
          </div>
        </div>
      </div>

      {/* Summary */}
      <div className="bg-background/50 border border-border/50 rounded p-3">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-xs font-bold text-muted-foreground">Recommendation:</span>
          <span
            className="text-sm font-bold"
            style={{ color: getRecommendationColor(recommendation) }}
          >
            {recommendation}
          </span>
        </div>
        <p className="text-xs text-foreground/80 leading-relaxed">{reasoningSummary}</p>
      </div>

      {/* Reasoning Steps */}
      <div className="space-y-2">
        {steps.map((step) => (
          <div
            key={step.step_number}
            className="bg-background/30 border border-border/50 rounded p-3 hover:bg-background/50 transition-colors"
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2">
                <div className="text-primary">
                  {getCategoryIcon(step.category)}
                </div>
                <span className="text-xs font-bold text-foreground">
                  Step {step.step_number}: {step.category.toUpperCase()}
                </span>
              </div>
              <div
                className="text-xs font-bold"
                style={{ color: getScoreColor(step.points_awarded, step.max_points) }}
              >
                {step.points_awarded}/{step.max_points}
              </div>
            </div>

            <p className="text-xs text-foreground/70 leading-relaxed ml-6">
              {step.description}
            </p>

            <div className="flex items-center justify-between ml-6 mt-2">
              <div className="text-[10px] text-muted-foreground">
                Confidence: {(step.confidence * 100).toFixed(0)}%
              </div>
              {step.indicators_used && step.indicators_used.length > 0 && (
                <div className="text-[10px] text-muted-foreground">
                  Using: {step.indicators_used.join(', ')}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Risks */}
      {risksIdentified.length > 0 && (
        <div className="bg-danger-red/10 border border-danger-red/30 rounded p-3">
          <h4 className="text-xs font-bold text-danger-red mb-2 flex items-center gap-1.5">
            <ShieldAlert className="w-3 h-3" />
            Identified Risks
          </h4>
          <ul className="space-y-1">
            {risksIdentified.map((risk, idx) => (
              <li key={idx} className="text-xs text-danger-red/80 leading-relaxed pl-4 relative">
                <span className="absolute left-0">•</span>
                {risk}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Data Gaps */}
      {dataGaps.length > 0 && (
        <div className="bg-secondary/10 border border-secondary/30 rounded p-3">
          <h4 className="text-xs font-bold text-secondary mb-2 flex items-center gap-1.5">
            ℹ️ Data Gaps
          </h4>
          <ul className="space-y-1">
            {dataGaps.map((gap, idx) => (
              <li key={idx} className="text-xs text-muted-foreground leading-relaxed pl-4 relative">
                <span className="absolute left-0">•</span>
                {gap}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
