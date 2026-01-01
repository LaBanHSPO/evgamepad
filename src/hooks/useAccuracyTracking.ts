/**
 * Accuracy Tracking hook for recording trade outcomes and performance metrics
 * Phase 5.2 feature - requires PostgreSQL database
 */

import { useState, useEffect, useCallback } from 'react';
import { useSocket } from '@/context/SocketContext';

// ============================================================================
// Types
// ============================================================================

export interface TradeOutcome {
  symbol: string;
  timeframe: string;
  signal: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  entry_price: number;
  exit_price: number;
  stop_loss?: number;
  take_profit?: number;
  exit_reason?: 'manual' | 'stop_loss' | 'take_profit';
  entry_at?: string;  // ISO 8601 timestamp
  exit_at?: string;   // ISO 8601 timestamp
}

export interface RecordOutcomeResult {
  success: boolean;
  outcome_id: string;
  message: string;
}

export interface AccuracyReportRequest {
  symbol?: string;
  timeframe?: string;
  signal?: 'BUY' | 'SELL' | 'HOLD';
  days?: number;
}

export interface AccuracyReport {
  period_days: number;
  symbol?: string;
  timeframe?: string;
  signal?: string;
  total_trades: number;
  wins: number;
  losses: number;
  break_evens: number;
  win_rate_pct: number;
  avg_pnl_pct: number;
  profit_factor: number;
  recommendation: string;
}

export interface BestPerformingConfig {
  symbol: string;
  timeframe: string;
  signal: string;
  win_rate_pct: number;
  total_trades: number;
}

export interface AccuracyReportResult {
  report: AccuracyReport;
  best_performing: BestPerformingConfig[];
}

export interface ExplainabilityRequest {
  symbol: string;
  timeframe: string;
  recommendation_id?: string;
}

export interface ExplainabilityResult {
  symbol: string;
  timeframe: string;
  explainability: {
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
  provenance: {
    data_sources: string[];
    timestamp: string;
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

export const useAccuracyTracking = () => {
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
      console.error('[useAccuracyTracking] Error:', data);
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

  const recordOutcome = useCallback(
    (outcome: TradeOutcome): Promise<RecordOutcomeResult> => {
      return new Promise((resolve, reject) => {
        if (!socket || !isConnected) {
          reject(new Error('Socket not connected'));
          return;
        }

        setLoading(true);
        setError(null);

        const handleResult = (data: RecordOutcomeResult) => {
          socket.off('advisor:outcome_recorded', handleResult);
          socket.off('advisor:error', handleError);

          if (data.success) {
            resolve(data);
          } else {
            reject(new Error('Failed to record outcome'));
          }
          setLoading(false);
        };

        const handleError = (data: AdvisorError) => {
          socket.off('advisor:outcome_recorded', handleResult);
          socket.off('advisor:error', handleError);
          reject(new Error(data.message));
          setLoading(false);
        };

        socket.once('advisor:outcome_recorded', handleResult);
        socket.once('advisor:error', handleError);

        socket.emit('advisor_record_outcome', outcome);
      });
    },
    [socket, isConnected]
  );

  const getAccuracyReport = useCallback(
    (request: AccuracyReportRequest = {}): Promise<AccuracyReportResult> => {
      return new Promise((resolve, reject) => {
        if (!socket || !isConnected) {
          reject(new Error('Socket not connected'));
          return;
        }

        setLoading(true);
        setError(null);

        const handleResult = (data: { success: boolean; data?: AccuracyReportResult }) => {
          socket.off('advisor:accuracy_result', handleResult);
          socket.off('advisor:error', handleError);

          if (data.success && data.data) {
            resolve(data.data);
          } else {
            reject(new Error('Failed to get accuracy report'));
          }
          setLoading(false);
        };

        const handleError = (data: AdvisorError) => {
          socket.off('advisor:accuracy_result', handleResult);
          socket.off('advisor:error', handleError);
          reject(new Error(data.message));
          setLoading(false);
        };

        socket.once('advisor:accuracy_result', handleResult);
        socket.once('advisor:error', handleError);

        socket.emit('advisor_accuracy_report', request);
      });
    },
    [socket, isConnected]
  );

  const getExplainability = useCallback(
    (request: ExplainabilityRequest): Promise<ExplainabilityResult> => {
      return new Promise((resolve, reject) => {
        if (!socket || !isConnected) {
          reject(new Error('Socket not connected'));
          return;
        }

        setLoading(true);
        setError(null);

        const handleResult = (data: { success: boolean; data?: ExplainabilityResult }) => {
          socket.off('advisor:explanation_result', handleResult);
          socket.off('advisor:error', handleError);

          if (data.success && data.data) {
            resolve(data.data);
          } else {
            reject(new Error('Failed to get explainability data'));
          }
          setLoading(false);
        };

        const handleError = (data: AdvisorError) => {
          socket.off('advisor:explanation_result', handleResult);
          socket.off('advisor:error', handleError);
          reject(new Error(data.message));
          setLoading(false);
        };

        socket.once('advisor:explanation_result', handleResult);
        socket.once('advisor:error', handleError);

        socket.emit('advisor_explain_recommendation', request);
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
    recordOutcome,
    getAccuracyReport,
    getExplainability,
    clearError,
  };
};
