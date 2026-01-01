import { useState, useEffect, useCallback } from 'react';
import { useSocket } from '@/context/SocketContext';

export interface Position {
  symbol: string;
  entry_price: number;
  current_price?: number;
  position_size: number;
  stop_loss?: number;
  timeframe: string;
}

export interface PortfolioAnalysisResult {
  portfolio_health: {
    score: number;
    status: string;
    total_risk_exposure: number;
    current_drawdown: number;
    positions_at_risk: number;
  };
  position_analysis: Array<{
    symbol: string;
    entry_price: number;
    current_price: number;
    position_size: number;
    stop_loss: number;
    pnl_pct: number;
    pnl_amount: number;
    r_multiple: number;
    distance_to_stop_pct: number;
    risk_status: string;
    recommendation: string;
    technical_signal: string;
    technical_confidence: number;
  }>;
  ai_advice: {
    overall_assessment: string;
    capital_preservation_tips: string[];
    risk_warnings: string[];
    opportunities: string[];
    model_used: string;
    language: string;
  };
  cached: boolean;
  computed_at: string;
}

export const usePortfolioAnalysis = () => {
  const { socket, isConnected } = useSocket();
  const [result, setResult] = useState<PortfolioAnalysisResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!socket) return;

    // Listen for analysis result
    socket.on('advisor:portfolio_result', (data: { success: boolean; data?: PortfolioAnalysisResult; message?: string }) => {
      console.log('[usePortfolioAnalysis] Result:', data);
      if (data.success && data.data) {
        setResult(data.data);
        setError(null);
      } else {
        setError(data.message || 'Analysis failed');
      }
      setIsAnalyzing(false);
    });

    // Listen for errors
    socket.on('advisor:error', (data: { message?: string; error_code?: string }) => {
      console.error('[usePortfolioAnalysis] Error:', data);
      setError(data.message || 'Unknown error');
      setIsAnalyzing(false);
    });

    return () => {
      socket.off('advisor:portfolio_result');
      socket.off('advisor:error');
    };
  }, [socket]);

  const analyzePortfolio = useCallback(
    (
      positions: Position[],
      accountBalance: number,
      riskProfile: string = 'moderate',
      language: string = 'en'
    ): Promise<PortfolioAnalysisResult> => {
      return new Promise((resolve, reject) => {
        if (!socket || !isConnected) {
          reject(new Error('Socket not connected'));
          return;
        }

        setIsAnalyzing(true);
        setError(null);
        setResult(null);

        const handleResult = (data: { success: boolean; data?: PortfolioAnalysisResult }) => {
          socket.off('advisor:portfolio_result', handleResult);
          socket.off('advisor:error', handleError);

          if (data.success && data.data) {
            setResult(data.data);
            resolve(data.data);
          } else {
            const errorMsg = 'Portfolio analysis failed';
            setError(errorMsg);
            reject(new Error(errorMsg));
          }
          setIsAnalyzing(false);
        };

        const handleError = (data: { message?: string }) => {
          socket.off('advisor:portfolio_result', handleResult);
          socket.off('advisor:error', handleError);
          const errorMsg = data.message || 'Unknown error';
          setError(errorMsg);
          reject(new Error(errorMsg));
          setIsAnalyzing(false);
        };

        socket.once('advisor:portfolio_result', handleResult);
        socket.once('advisor:error', handleError);

        socket.emit('advisor_portfolio_analysis', {
          positions,
          account_balance: accountBalance,
          risk_profile: riskProfile,
          language
        });
      });
    },
    [socket, isConnected]
  );

  const clearResult = useCallback(() => {
    setResult(null);
    setError(null);
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    result,
    isAnalyzing,
    error,
    analyzePortfolio,
    clearResult,
    clearError,
    isConnected
  };
};
