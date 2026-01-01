/**
 * AI Advisor hook for technical analysis and recommendations
 * Provides technical summary, patterns, risk analysis, and AI recommendations
 */

import { useState, useEffect, useCallback } from 'react';
import { useSocket } from '@/context/SocketContext';

// ============================================================================
// Types
// ============================================================================

export interface TechnicalSummaryRequest {
  symbol: string;
  timeframe: string;
  indicators?: string[];
}

export interface TechnicalSummaryResult {
  symbol: string;
  timeframe: string;
  last_close: number;
  indicators: {
    sma_20?: number;
    sma_50?: number;
    sma_200?: number;
    rsi?: number;
    macd?: {
      macd: number;
      signal: number;
      histogram: number;
    };
    atr?: number;
    bollinger?: {
      upper: number;
      middle: number;
      lower: number;
    };
  };
  signals: {
    sma?: string;
    rsi?: string;
    macd?: string;
  };
  overall: {
    signal: string;
    confidence: number;
    strength: string;
  };
  cached: boolean;
  computed_at: string;
}

export interface MultiTimeframeRequest {
  symbol: string;
  timeframes: string[];
}

export interface MultiTimeframeResult {
  symbol: string;
  timeframes: Record<string, TechnicalSummaryResult>;
  alignment: {
    status: string;
    bullish_count: number;
    bearish_count: number;
    signals: Array<{
      timeframe: string;
      signal: string;
      confidence: number;
    }>;
  };
  power_zone: boolean;
  computed_at: string;
}

export interface PatternScanRequest {
  symbol: string;
  timeframe: string;
  include_sr?: boolean;
}

export interface PatternScanResult {
  symbol: string;
  timeframe: string;
  last_price: number;
  candlestick_patterns: Array<{
    name: string;
    signal: string;
    strength: string;
    index: number;
  }>;
  chart_patterns: Array<{
    name: string;
    type: string;
    signal: string;
    confidence: number;
  }>;
  support_resistance?: {
    pivot: number;
    support_levels: number[];
    resistance_levels: number[];
    nearest_support: number;
    nearest_resistance: number;
  };
  cached: boolean;
  computed_at: string;
}

export interface RiskAnalysisRequest {
  symbol?: string;
  account_balance: number;
  entry_price: number;
  stop_loss: number;
  take_profit: number;
  risk_profile?: string;
  timeframe?: string;
}

export interface RiskAnalysisResult {
  symbol?: string;
  risk_reward: {
    risk_amount: number;
    reward_amount: number;
    ratio: number;
    recommendation: string;
  };
  position_sizing: {
    max_volume: number;
    recommended_volume: number;
    risk_percentage: number;
  };
  recommendation: {
    action: string;
    notes: string;
  };
  computed_at: string;
}

export interface RecommendationRequest {
  symbol: string;
  timeframe: string;
  language?: string;
  risk_profile?: string;
}

export interface RecommendationResult {
  symbol: string;
  timeframe: string;
  language: string;
  recommendation: {
    action: string;
    confidence: number;
    entry_zone: number[];
    stop_loss: number;
    take_profit: number[];
    reasoning: string;
  };
  ai_summary: {
    market_context: string;
    key_factors: string[];
    risks: string[];
    personalized_advice: string;
  };
  provenance?: {
    data_sources: string[];
    model_used: string;
    generated_at: string;
  };
  explainability?: {
    steps: Array<{
      step: number;
      name: string;
      score: number;
      max_score: number;
      reasoning: string;
      data_used: string[];
    }>;
    total_score: number;
    max_score: number;
    confidence: number;
    recommendation: string;
    reasoning_summary: string;
    risks_identified: string[];
    data_gaps: string[];
  };
}

interface AdvisorError {
  success: false;
  error_code: string;
  message: string;
  details?: Record<string, unknown>;
}

// ============================================================================
// Hook
// ============================================================================

export const useAdvisor = () => {
  const { socket, isConnected } = useSocket();

  // State
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // ============================================================================
  // Event Handlers
  // ============================================================================

  useEffect(() => {
    if (!socket) return;

    // Error handling
    socket.on('advisor:error', (data: AdvisorError) => {
      console.error('[useAdvisor] Error:', data);
      setError(data.message);
      setLoading(false);
    });

    return () => {
      socket.off('advisor:error');
    };
  }, [socket]);

  // ============================================================================
  // Operations
  // ============================================================================

  const getTechnicalSummary = useCallback(
    (request: TechnicalSummaryRequest): Promise<TechnicalSummaryResult> => {
      return new Promise((resolve, reject) => {
        if (!socket || !isConnected) {
          reject(new Error('Socket not connected'));
          return;
        }

        setLoading(true);
        setError(null);

        const handleResult = (data: { success: boolean; data?: TechnicalSummaryResult }) => {
          socket.off('advisor:technical_result', handleResult);
          socket.off('advisor:error', handleError);

          if (data.success && data.data) {
            resolve(data.data);
          } else {
            reject(new Error('Technical analysis failed'));
          }
          setLoading(false);
        };

        const handleError = (data: AdvisorError) => {
          socket.off('advisor:technical_result', handleResult);
          socket.off('advisor:error', handleError);
          reject(new Error(data.message));
          setLoading(false);
        };

        socket.once('advisor:technical_result', handleResult);
        socket.once('advisor:error', handleError);

        socket.emit('advisor_technical_summary', request);
      });
    },
    [socket, isConnected]
  );

  const getMultiTimeframeAnalysis = useCallback(
    (request: MultiTimeframeRequest): Promise<MultiTimeframeResult> => {
      return new Promise((resolve, reject) => {
        if (!socket || !isConnected) {
          reject(new Error('Socket not connected'));
          return;
        }

        setLoading(true);
        setError(null);

        const handleResult = (data: { success: boolean; data?: MultiTimeframeResult }) => {
          socket.off('advisor:multi_timeframe_result', handleResult);
          socket.off('advisor:error', handleError);

          if (data.success && data.data) {
            resolve(data.data);
          } else {
            reject(new Error('Multi-timeframe analysis failed'));
          }
          setLoading(false);
        };

        const handleError = (data: AdvisorError) => {
          socket.off('advisor:multi_timeframe_result', handleResult);
          socket.off('advisor:error', handleError);
          reject(new Error(data.message));
          setLoading(false);
        };

        socket.once('advisor:multi_timeframe_result', handleResult);
        socket.once('advisor:error', handleError);

        socket.emit('advisor_multi_timeframe', request);
      });
    },
    [socket, isConnected]
  );

  const getPatternScan = useCallback(
    (request: PatternScanRequest): Promise<PatternScanResult> => {
      return new Promise((resolve, reject) => {
        if (!socket || !isConnected) {
          reject(new Error('Socket not connected'));
          return;
        }

        setLoading(true);
        setError(null);

        const handleResult = (data: { success: boolean; data?: PatternScanResult }) => {
          socket.off('advisor:pattern_result', handleResult);
          socket.off('advisor:error', handleError);

          if (data.success && data.data) {
            resolve(data.data);
          } else {
            reject(new Error('Pattern scan failed'));
          }
          setLoading(false);
        };

        const handleError = (data: AdvisorError) => {
          socket.off('advisor:pattern_result', handleResult);
          socket.off('advisor:error', handleError);
          reject(new Error(data.message));
          setLoading(false);
        };

        socket.once('advisor:pattern_result', handleResult);
        socket.once('advisor:error', handleError);

        socket.emit('advisor_pattern_scan', request);
      });
    },
    [socket, isConnected]
  );

  const getRiskAnalysis = useCallback(
    (request: RiskAnalysisRequest): Promise<RiskAnalysisResult> => {
      return new Promise((resolve, reject) => {
        if (!socket || !isConnected) {
          reject(new Error('Socket not connected'));
          return;
        }

        setLoading(true);
        setError(null);

        const handleResult = (data: { success: boolean; data?: RiskAnalysisResult }) => {
          socket.off('advisor:risk_result', handleResult);
          socket.off('advisor:error', handleError);

          if (data.success && data.data) {
            resolve(data.data);
          } else {
            reject(new Error('Risk analysis failed'));
          }
          setLoading(false);
        };

        const handleError = (data: AdvisorError) => {
          socket.off('advisor:risk_result', handleResult);
          socket.off('advisor:error', handleError);
          reject(new Error(data.message));
          setLoading(false);
        };

        socket.once('advisor:risk_result', handleResult);
        socket.once('advisor:error', handleError);

        socket.emit('advisor_risk_analysis', request);
      });
    },
    [socket, isConnected]
  );

  const getRecommendation = useCallback(
    (request: RecommendationRequest): Promise<RecommendationResult> => {
      return new Promise((resolve, reject) => {
        if (!socket || !isConnected) {
          reject(new Error('Socket not connected'));
          return;
        }

        setLoading(true);
        setError(null);

        const handleResult = (data: { success: boolean; data?: RecommendationResult }) => {
          socket.off('advisor:recommendation_result', handleResult);
          socket.off('advisor:error', handleError);

          if (data.success && data.data) {
            resolve(data.data);
          } else {
            reject(new Error('Recommendation failed'));
          }
          setLoading(false);
        };

        const handleError = (data: AdvisorError) => {
          socket.off('advisor:recommendation_result', handleResult);
          socket.off('advisor:error', handleError);
          reject(new Error(data.message));
          setLoading(false);
        };

        socket.once('advisor:recommendation_result', handleResult);
        socket.once('advisor:error', handleError);

        socket.emit('advisor_recommendation', request);
      });
    },
    [socket, isConnected]
  );

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    // State
    isConnected,
    loading,
    error,

    // Operations
    getTechnicalSummary,
    getMultiTimeframeAnalysis,
    getPatternScan,
    getRiskAnalysis,
    getRecommendation,
    clearError,
  };
};
