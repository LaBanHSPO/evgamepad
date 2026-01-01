/**
 * Example component demonstrating Socket.IO AI Advisor features
 * Shows how to use useAdvisor and usePortfolioAnalysis hooks
 */

import React, { useState } from 'react';
import { useAdvisor } from '@/hooks/useAdvisor';
import { usePortfolioAnalysis, type Position } from '@/hooks/usePortfolioAnalysis';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

export const AdvisorExample: React.FC = () => {
  const advisor = useAdvisor();
  const portfolio = usePortfolioAnalysis();

  const [symbol, setSymbol] = useState('XAUUSD');
  const [timeframe, setTimeframe] = useState('H1');
  const [technicalResult, setTechnicalResult] = useState<any>(null);
  const [recommendationResult, setRecommendationResult] = useState<any>(null);
  const [patternResult, setPatternResult] = useState<any>(null);

  // Handlers
  const handleTechnicalAnalysis = async () => {
    try {
      const result = await advisor.getTechnicalSummary({
        symbol,
        timeframe,
      });
      setTechnicalResult(result);
      console.log('Technical analysis:', result);
    } catch (err) {
      console.error('Technical analysis failed:', err);
    }
  };

  const handleMultiTimeframe = async () => {
    try {
      const result = await advisor.getMultiTimeframeAnalysis({
        symbol,
        timeframes: ['H1', 'H4', 'D1'],
      });
      console.log('Multi-timeframe:', result);
      alert(`Alignment: ${result.alignment.status} | Power Zone: ${result.power_zone ? 'Yes' : 'No'}`);
    } catch (err) {
      console.error('Multi-timeframe failed:', err);
    }
  };

  const handlePatternScan = async () => {
    try {
      const result = await advisor.getPatternScan({
        symbol,
        timeframe,
        include_sr: true,
      });
      setPatternResult(result);
      console.log('Pattern scan:', result);
    } catch (err) {
      console.error('Pattern scan failed:', err);
    }
  };

  const handleRiskAnalysis = async () => {
    try {
      const result = await advisor.getRiskAnalysis({
        symbol,
        account_balance: 10000,
        entry_price: 2634.50,
        stop_loss: 2625.00,
        take_profit: 2645.00,
        risk_profile: 'moderate',
        timeframe,
      });
      console.log('Risk analysis:', result);
      alert(`Risk/Reward Ratio: ${result.risk_reward.ratio.toFixed(2)} | Recommended Volume: ${result.position_sizing.recommended_volume}`);
    } catch (err) {
      console.error('Risk analysis failed:', err);
    }
  };

  const handleGetRecommendation = async () => {
    try {
      const result = await advisor.getRecommendation({
        symbol,
        timeframe,
        language: 'en',
        risk_profile: 'moderate',
      });
      setRecommendationResult(result);
      console.log('AI Recommendation:', result);
    } catch (err) {
      console.error('Recommendation failed:', err);
    }
  };

  const handlePortfolioAnalysis = async () => {
    const positions: Position[] = [
      {
        symbol: 'XAUUSD',
        entry_price: 2630.50,
        current_price: 2634.00,
        position_size: 0.5,
        stop_loss: 2625.00,
        timeframe: 'H1',
      },
      {
        symbol: 'EURUSD',
        entry_price: 1.1000,
        position_size: 0.1,
        stop_loss: 1.0950,
        timeframe: 'H1',
      },
    ];

    try {
      const result = await portfolio.analyzePortfolio(
        positions,
        10000,  // account balance
        'moderate',
        'en'
      );
      console.log('Portfolio analysis:', result);
    } catch (err) {
      console.error('Portfolio analysis failed:', err);
    }
  };

  return (
    <div className="space-y-4 p-4">
      {/* Connection Status */}
      <Card>
        <CardHeader>
          <CardTitle>AI Advisor Socket Connection</CardTitle>
          <CardDescription>
            Status: {advisor.isConnected ?
              <Badge variant="default" className="ml-2">Connected</Badge> :
              <Badge variant="destructive" className="ml-2">Disconnected</Badge>
            }
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Error Display */}
      {(advisor.error || portfolio.error) && (
        <Alert variant="destructive">
          <AlertDescription>
            {advisor.error || portfolio.error}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                advisor.clearError();
                portfolio.clearError();
              }}
              className="ml-2"
            >
              Dismiss
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Input Controls */}
      <Card>
        <CardHeader>
          <CardTitle>Analysis Parameters</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="symbol">Symbol</Label>
              <Input
                id="symbol"
                placeholder="XAUUSD"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              />
            </div>
            <div>
              <Label htmlFor="timeframe">Timeframe</Label>
              <Input
                id="timeframe"
                placeholder="H1"
                value={timeframe}
                onChange={(e) => setTimeframe(e.target.value.toUpperCase())}
              />
              <p className="text-xs text-muted-foreground mt-1">
                M1, M5, M15, M30, H1, H4, D1, W1, MN1
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Analysis Tabs */}
      <Tabs defaultValue="technical" className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="technical">Technical</TabsTrigger>
          <TabsTrigger value="patterns">Patterns</TabsTrigger>
          <TabsTrigger value="risk">Risk</TabsTrigger>
          <TabsTrigger value="ai">AI Rec</TabsTrigger>
          <TabsTrigger value="portfolio">Portfolio</TabsTrigger>
        </TabsList>

        {/* Technical Analysis Tab */}
        <TabsContent value="technical">
          <Card>
            <CardHeader>
              <CardTitle>Technical Analysis</CardTitle>
              <CardDescription>Get indicators and signals</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Button onClick={handleTechnicalAnalysis} disabled={advisor.loading}>
                  {advisor.loading ? 'Analyzing...' : 'Get Technical Summary'}
                </Button>
                <Button onClick={handleMultiTimeframe} disabled={advisor.loading} variant="outline">
                  Multi-Timeframe
                </Button>
              </div>

              {technicalResult && (
                <div className="mt-4 p-4 border rounded-lg space-y-2">
                  <h3 className="font-semibold">Results</h3>
                  <p><strong>Last Price:</strong> {technicalResult.last_close}</p>
                  <p><strong>Overall Signal:</strong> <Badge>{technicalResult.overall.signal}</Badge></p>
                  <p><strong>Confidence:</strong> {technicalResult.overall.confidence}%</p>
                  <p><strong>RSI:</strong> {technicalResult.indicators.rsi?.toFixed(2)}</p>
                  <p><strong>SMA(20):</strong> {technicalResult.indicators.sma_20?.toFixed(2)}</p>
                  <p><strong>Cached:</strong> {technicalResult.cached ? 'Yes' : 'No'}</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Pattern Scan Tab */}
        <TabsContent value="patterns">
          <Card>
            <CardHeader>
              <CardTitle>Pattern Detection</CardTitle>
              <CardDescription>Candlestick patterns and support/resistance</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Button onClick={handlePatternScan} disabled={advisor.loading}>
                {advisor.loading ? 'Scanning...' : 'Scan Patterns'}
              </Button>

              {patternResult && (
                <div className="mt-4 p-4 border rounded-lg space-y-3">
                  <div>
                    <h3 className="font-semibold">Candlestick Patterns</h3>
                    {patternResult.candlestick_patterns.map((p: any, i: number) => (
                      <Badge key={i} variant="outline" className="mr-2 mt-2">
                        {p.name} ({p.signal})
                      </Badge>
                    ))}
                  </div>

                  {patternResult.support_resistance && (
                    <div>
                      <h3 className="font-semibold">Support/Resistance</h3>
                      <p><strong>Nearest Support:</strong> {patternResult.support_resistance.nearest_support}</p>
                      <p><strong>Nearest Resistance:</strong> {patternResult.support_resistance.nearest_resistance}</p>
                      <p><strong>Pivot:</strong> {patternResult.support_resistance.pivot}</p>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Risk Analysis Tab */}
        <TabsContent value="risk">
          <Card>
            <CardHeader>
              <CardTitle>Risk Analysis</CardTitle>
              <CardDescription>Position sizing and risk/reward calculation</CardDescription>
            </CardHeader>
            <CardContent>
              <Button onClick={handleRiskAnalysis} disabled={advisor.loading}>
                {advisor.loading ? 'Analyzing...' : 'Calculate Risk'}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* AI Recommendation Tab */}
        <TabsContent value="ai">
          <Card>
            <CardHeader>
              <CardTitle>AI Recommendation</CardTitle>
              <CardDescription>Get comprehensive AI-powered trading advice</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Button onClick={handleGetRecommendation} disabled={advisor.loading}>
                {advisor.loading ? 'Generating...' : 'Get AI Recommendation'}
              </Button>

              {recommendationResult && (
                <div className="mt-4 p-4 border rounded-lg space-y-3">
                  <div>
                    <h3 className="font-semibold text-lg">
                      <Badge className="mr-2">{recommendationResult.recommendation.action}</Badge>
                      Confidence: {recommendationResult.recommendation.confidence}%
                    </h3>
                  </div>

                  <div>
                    <p><strong>Entry Zone:</strong> {recommendationResult.recommendation.entry_zone.join(' - ')}</p>
                    <p><strong>Stop Loss:</strong> {recommendationResult.recommendation.stop_loss}</p>
                    <p><strong>Take Profit:</strong> {recommendationResult.recommendation.take_profit.join(' / ')}</p>
                  </div>

                  <div>
                    <h4 className="font-semibold">Market Context</h4>
                    <p className="text-sm">{recommendationResult.ai_summary.market_context}</p>
                  </div>

                  <div>
                    <h4 className="font-semibold">Key Factors</h4>
                    <ul className="list-disc list-inside text-sm">
                      {recommendationResult.ai_summary.key_factors.map((f: string, i: number) => (
                        <li key={i}>{f}</li>
                      ))}
                    </ul>
                  </div>

                  {recommendationResult.ai_summary.risks.length > 0 && (
                    <div>
                      <h4 className="font-semibold text-destructive">Risks</h4>
                      <ul className="list-disc list-inside text-sm">
                        {recommendationResult.ai_summary.risks.map((r: string, i: number) => (
                          <li key={i}>{r}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Portfolio Analysis Tab */}
        <TabsContent value="portfolio">
          <Card>
            <CardHeader>
              <CardTitle>Portfolio Risk Management</CardTitle>
              <CardDescription>Analyze multiple positions for capital preservation</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Button onClick={handlePortfolioAnalysis} disabled={portfolio.isAnalyzing}>
                {portfolio.isAnalyzing ? 'Analyzing...' : 'Analyze Portfolio'}
              </Button>

              {portfolio.result && (
                <div className="mt-4 p-4 border rounded-lg space-y-3">
                  <div>
                    <h3 className="font-semibold text-lg">
                      Portfolio Health: <Badge variant={portfolio.result.portfolio_health.status === 'HEALTHY' ? 'default' : 'destructive'}>
                        {portfolio.result.portfolio_health.status}
                      </Badge>
                    </h3>
                    <p><strong>Score:</strong> {portfolio.result.portfolio_health.score}/100</p>
                    <p><strong>Risk Exposure:</strong> {portfolio.result.portfolio_health.total_risk_exposure.toFixed(2)}%</p>
                    <p><strong>Positions at Risk:</strong> {portfolio.result.portfolio_health.positions_at_risk}</p>
                  </div>

                  <div>
                    <h4 className="font-semibold">AI Assessment</h4>
                    <p className="text-sm">{portfolio.result.ai_advice.overall_assessment}</p>
                  </div>

                  {portfolio.result.ai_advice.capital_preservation_tips.length > 0 && (
                    <div>
                      <h4 className="font-semibold">Recommendations</h4>
                      <ul className="list-disc list-inside text-sm">
                        {portfolio.result.ai_advice.capital_preservation_tips.map((tip, i) => (
                          <li key={i}>{tip}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <div>
                    <h4 className="font-semibold">Position Analysis</h4>
                    {portfolio.result.position_analysis.map((pos, i) => (
                      <div key={i} className="mt-2 p-2 border rounded text-sm">
                        <p><strong>{pos.symbol}</strong> | <Badge variant="outline">{pos.recommendation}</Badge></p>
                        <p>P&L: {pos.pnl_pct.toFixed(2)}% | R-Multiple: {pos.r_multiple.toFixed(2)}x</p>
                        <p>Risk Status: <Badge variant={pos.risk_status === 'safe' ? 'default' : 'destructive'}>{pos.risk_status}</Badge></p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};
