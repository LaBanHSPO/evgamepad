import { useState, useEffect } from 'react';
import { useSocket } from '@/context/SocketContext';

interface Position {
  symbol: string;
  entry_price: number;
  current_price: number;
  position_size: number;
  stop_loss?: number;
  timeframe: string;
}

interface PortfolioAnalysisResult {
  success: boolean;
  portfolio_health: {
    score: number;
    status: string;
    total_risk_exposure: number;
    current_drawdown: number;
    positions_at_risk: number;
  };
  position_analysis: Array<{
    symbol: string;
    risk_status: string;
    recommendation: string;
    technical_signal: string;
    r_multiple: number;
    pnl_pct: number;
    distance_to_stop_pct: number;
  }>;
  ai_advice: {
    summary: string;
    overall_risk: string;
    priority_actions: string[];
    reasoning: string;
    confidence: number;
    model: string;
    cached: boolean;
  };
  cached: boolean;
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
      console.log('Portfolio analysis result:', data);
      if (data.success && data.data) {
        setResult(data.data);
      } else {
        setError(data.message || 'Analysis failed');
      }
      setIsAnalyzing(false);
    });

    // Listen for errors
    socket.on('advisor:error', (data: { message?: string }) => {
      console.error('Portfolio analysis error:', data);
      setError(data.message || 'Unknown error');
      setIsAnalyzing(false);
    });

    return () => {
      socket.off('advisor:portfolio_result');
      socket.off('advisor:error');
    };
  }, [socket]);

  const analyzePortfolio = (
    positions: Position[],
    accountBalance: number,
    riskProfile: string = 'conservative',
    language: string = 'vi'
  ) => {
    if (!socket || !isConnected) {
      setError('Socket not connected');
      return;
    }

    setIsAnalyzing(true);
    setError(null);
    setResult(null);

    socket.emit('advisor:portfolio_analysis', {
      positions,
      account_balance: accountBalance,
      risk_profile: riskProfile,
      language
    });
  };

  const clearResult = () => {
    setResult(null);
    setError(null);
  };

  return {
    result,
    isAnalyzing,
    error,
    analyzePortfolio,
    clearResult,
    isConnected
  };
};
