"""
Pydantic models for AI Trading Advisor responses.
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class TechnicalIndicators(BaseModel):
    """Container for computed technical indicators."""
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    ema_9: Optional[float] = None
    ema_21: Optional[float] = None
    ema_50: Optional[float] = None
    rsi: Optional[float] = None
    macd: Optional[Dict[str, float]] = None
    bollinger: Optional[Dict[str, float]] = None
    atr: Optional[float] = None
    atr_pct: Optional[float] = None
    adx: Optional[Dict[str, float]] = None
    stochastic: Optional[Dict[str, float]] = None
    obv: Optional[int] = None

class SignalSummary(BaseModel):
    """Aggregated signal assessment."""
    signal: str = Field(..., description="Overall signal: bullish, bearish, neutral")
    confidence: float = Field(..., ge=0, le=1, description="Confidence 0-1")
    bullish_signals: int = 0
    bearish_signals: int = 0
    neutral_signals: int = 0
    reasoning: Dict[str, str] = Field(default_factory=dict)

class TechnicalSummaryResponse(BaseModel):
    """Response for advisor:technical_summary event."""
    success: bool = True
    symbol: str
    timeframe: str
    last_close: float
    last_time: str
    candles: int
    indicators: Dict[str, Any]
    signals: Dict[str, str]
    overall: SignalSummary
    cached: bool = False
    computed_at: datetime = Field(default_factory=datetime.utcnow)

class TechnicalSummaryRequest(BaseModel):
    """Request for advisor:technical_summary event."""
    symbol: str = Field(..., min_length=1, max_length=20)
    timeframe: str = Field(default="H1", pattern="^(M1|M5|M15|M30|H1|H4|D1|W1|MN1)$")
    indicators: Optional[List[str]] = None

class MultiTimeframeRequest(BaseModel):
    """Request for multi-timeframe analysis."""
    symbol: str = Field(..., min_length=1, max_length=20)
    timeframes: List[str] = Field(default=["H1", "H4", "D1"])
    indicators: Optional[List[str]] = None

class CandlestickPattern(BaseModel):
    """Single candlestick pattern detection."""
    name: str
    bias: str  # bullish, bearish, neutral
    strength: int
    candle_index: int
    candle_time: str
    price: float

class ChartPattern(BaseModel):
    """Chart pattern (double top, H&S, etc.)."""
    type: str
    bias: str
    confidence: float
    neckline: float
    target: float
    stop_loss: float
    formation: Dict[str, Any]

class SupportResistanceLevel(BaseModel):
    """Single S/R level."""
    price: float
    source: str  # pivot, fibonacci, swing
    type: str    # s1, r1, 0.618, swing_high, etc.

class PatternScanResponse(BaseModel):
    """Response for advisor:pattern_scan event."""
    success: bool = True
    symbol: str
    timeframe: str
    last_price: float
    candlestick_patterns: Dict[str, Any]
    chart_patterns: Dict[str, Any]
    support_resistance: Optional[Dict[str, Any]] = None
    cached: bool = False
    computed_at: datetime = Field(default_factory=datetime.utcnow)

class RiskAnalysisRequest(BaseModel):
    """Request for advisor:risk_analysis event."""
    symbol: Optional[str] = None
    account_balance: float = Field(..., gt=0)
    entry_price: float = Field(..., gt=0)
    stop_loss: float = Field(..., gt=0)
    take_profit: float = Field(..., gt=0)
    risk_profile: str = Field(default="moderate", pattern="^(conservative|moderate|aggressive)$")
    timeframe: str = Field(default="H1")

class PositionSizing(BaseModel):
    """Position sizing result."""
    method: str
    position_size: float
    risk_amount: float
    risk_percentage: float
    stop_distance: float
    stop_distance_pct: float

class RiskReward(BaseModel):
    """Risk/reward calculation result."""
    direction: str
    risk: float
    risk_pct: float
    reward: float
    reward_pct: float
    rr_ratio: float
    recommendation: str
    advice: str
    breakeven_win_rate: float

class RiskAnalysisResponse(BaseModel):
    """Response for advisor:risk_analysis event."""
    success: bool = True
    symbol: Optional[str] = None
    risk_profile: str
    risk_reward: Dict[str, Any]
    position_sizing: Dict[str, Any]
    recommendation: Dict[str, Any]
    computed_at: datetime = Field(default_factory=datetime.utcnow)

class PositionInput(BaseModel):
    """User-provided position data for portfolio analysis."""
    symbol: str = Field(..., min_length=1, max_length=20)
    entry_price: float = Field(..., gt=0)
    current_price: Optional[float] = None  # Optional, fetch if missing
    position_size: float = Field(..., gt=0)
    stop_loss: Optional[float] = None
    timeframe: str = Field(default="H1")

class PortfolioAnalysisRequest(BaseModel):
    """Request for portfolio analysis."""
    positions: List[PositionInput] = Field(..., min_length=1, max_length=10)
    account_balance: float = Field(..., gt=0)
    risk_profile: str = Field(default="conservative", pattern="^(conservative|moderate|aggressive)$")
    language: str = Field(default="vi", pattern="^(vi|en)$")

class HealthStatus(str):
    """Health status enum values."""
    HEALTHY = "HEALTHY"
    CAUTION = "CAUTION"
    DANGER = "DANGER"

class PortfolioHealth(BaseModel):
    """Portfolio health metrics."""
    score: int = Field(..., ge=0, le=100)
    status: str = Field(..., pattern="^(HEALTHY|CAUTION|DANGER)$")
    total_risk_exposure: float
    current_drawdown: float
    positions_at_risk: int

class PositionAnalysis(BaseModel):
    """Per-position analysis result."""
    symbol: str
    entry_price: float
    current_price: float
    position_size: float
    stop_loss: float
    pnl_pct: float
    pnl_amount: float
    r_multiple: float
    distance_to_stop_pct: float
    risk_status: str  # safe/approaching_stop/danger/caution
    recommendation: str  # HOLD/REDUCE/CLOSE
    technical_signal: str
    technical_confidence: float

class PortfolioAnalysisResponse(BaseModel):
    """Response for portfolio analysis."""
    success: bool = True
    portfolio_health: PortfolioHealth
    position_analysis: List[PositionAnalysis]
    ai_advice: Dict[str, Any]
    cached: bool = False
    computed_at: datetime = Field(default_factory=datetime.utcnow)
