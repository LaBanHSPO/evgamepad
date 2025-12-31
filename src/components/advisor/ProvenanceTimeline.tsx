import React from 'react';
import { Database, Cloud, Activity, Bot, RefreshCw } from 'lucide-react';

interface SourceData {
  count: number;
  cache_hits: number;
  avg_confidence: number;
  oldest_age_seconds: number;
}

interface ProvenanceData {
  total_data_points: number;
  sources: Record<string, SourceData>;
  oldest_data_age_seconds: number;
  cache_hit_rate?: number;
}

interface ProvenanceTimelineProps {
  provenance: ProvenanceData;
}

/**
 * Displays data source freshness and provenance information
 */
export const ProvenanceTimeline: React.FC<ProvenanceTimelineProps> = ({ provenance }) => {
  const formatAge = (seconds: number): string => {
    if (seconds < 60) return `${Math.floor(seconds)}s ago`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
  };

  const getAgeColor = (seconds: number): string => {
    if (seconds < 60) return '#26A69A'; // Fresh (< 1min)
    if (seconds < 300) return '#FFA726'; // Acceptable (< 5min)
    if (seconds < 3600) return '#FFD54F'; // Warning (< 1hr)
    return '#EF5350'; // Stale (> 1hr)
  };

  const getSourceIcon = (source: string) => {
    const sourceLower = source.toLowerCase();
    if (sourceLower.includes('mt5')) return <Database className="w-4 h-4" />;
    if (sourceLower.includes('twelvedata') || sourceLower.includes('api')) return <Cloud className="w-4 h-4" />;
    if (sourceLower.includes('pandas') || sourceLower.includes('ta')) return <Activity className="w-4 h-4" />;
    if (sourceLower.includes('claude') || sourceLower.includes('deepseek') || sourceLower.includes('llm')) return <Bot className="w-4 h-4" />;
    if (sourceLower.includes('redis') || sourceLower.includes('cache')) return <RefreshCw className="w-4 h-4" />;
    return <Database className="w-4 h-4" />;
  };

  const cacheHitRate = provenance.cache_hit_rate ||
    (provenance.total_data_points > 0
      ? (Object.values(provenance.sources).reduce((sum, src) => sum + src.cache_hits, 0) / provenance.total_data_points) * 100
      : 0);

  return (
    <div className="space-y-3">
      <div className="flex justify-between items-center">
        <h4 className="text-sm font-bold text-foreground flex items-center gap-2">
          <RefreshCw className="w-4 h-4 text-primary" />
          Data Sources
        </h4>
        <span className="text-[10px] text-muted-foreground">
          {provenance.total_data_points} data points
        </span>
      </div>

      {/* Cache Hit Rate */}
      {cacheHitRate > 0 && (
        <div className="bg-background/50 border border-border/50 rounded p-2">
          <div className="flex justify-between items-center">
            <span className="text-[10px] text-muted-foreground">Cache Hit Rate</span>
            <span className="text-xs font-bold text-terminal-green">
              {cacheHitRate.toFixed(1)}%
            </span>
          </div>
          <div className="mt-1 h-1.5 bg-background rounded-full overflow-hidden">
            <div
              className="h-full bg-terminal-green transition-all"
              style={{ width: `${cacheHitRate}%` }}
            />
          </div>
        </div>
      )}

      {/* Sources List */}
      <div className="space-y-2">
        {Object.entries(provenance.sources).map(([source, data]) => (
          <div
            key={source}
            className="bg-background/30 border border-border/50 rounded p-3 hover:bg-background/50 transition-colors"
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2">
                <div className="text-primary">
                  {getSourceIcon(source)}
                </div>
                <span className="text-xs font-bold text-foreground">{source}</span>
              </div>
              <span
                className="text-xs font-bold"
                style={{ color: getAgeColor(data.oldest_age_seconds) }}
              >
                {formatAge(data.oldest_age_seconds)}
              </span>
            </div>

            <div className="grid grid-cols-3 gap-2 text-[10px]">
              <div>
                <span className="text-muted-foreground">Points:</span>{' '}
                <span className="font-bold text-foreground">{data.count}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Cached:</span>{' '}
                <span className="font-bold text-terminal-green">
                  {data.cache_hits}/{data.count}
                </span>
              </div>
              <div>
                <span className="text-muted-foreground">Confidence:</span>{' '}
                <span className="font-bold text-foreground">
                  {(data.avg_confidence * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Overall Freshness */}
      <div className="bg-background/50 border border-border/50 rounded p-3">
        <div className="flex justify-between items-center">
          <span className="text-xs text-muted-foreground">Oldest Data Age</span>
          <span
            className="text-xs font-bold"
            style={{ color: getAgeColor(provenance.oldest_data_age_seconds) }}
          >
            {formatAge(provenance.oldest_data_age_seconds)}
          </span>
        </div>
        <div className="mt-2 text-[10px] text-muted-foreground">
          {provenance.oldest_data_age_seconds < 60 && '✅ All data is fresh'}
          {provenance.oldest_data_age_seconds >= 60 && provenance.oldest_data_age_seconds < 300 && '✅ Data freshness acceptable'}
          {provenance.oldest_data_age_seconds >= 300 && provenance.oldest_data_age_seconds < 3600 && '⚠️ Some data may be stale'}
          {provenance.oldest_data_age_seconds >= 3600 && '❌ Data requires refresh'}
        </div>
      </div>
    </div>
  );
};
