"""
Data models for accuracy tracking system.

Phase 5.2: Accuracy Tracking System
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class RecordOutcomeRequest(BaseModel):
    """Request to record trade outcome."""

    symbol: str = Field(..., description="Trading symbol (e.g., XAUUSD)")
    timeframe: str = Field(default="H1", description="Timeframe (H1, H4, D1, etc.)")
    signal: str = Field(..., pattern="^(BUY|SELL|HOLD)$", description="Trade signal")
    confidence: float = Field(ge=0, le=100, description="Confidence score 0-100")
    entry_price: float = Field(gt=0, description="Entry price")
    exit_price: float = Field(gt=0, description="Exit price")
    stop_loss: Optional[float] = Field(default=None, description="Stop loss price")
    take_profit: Optional[float] = Field(default=None, description="Take profit price")
    exit_reason: str = Field(default="manual", description="Reason for exit")
    entry_at: Optional[datetime] = Field(default=None, description="Entry timestamp")
    exit_at: Optional[datetime] = Field(default=None, description="Exit timestamp")
    recommendation_id: Optional[UUID] = Field(default=None, description="Link to recommendation")

    @field_validator('signal')
    @classmethod
    def validate_signal(cls, v: str) -> str:
        """Validate signal is uppercase."""
        return v.upper()


class AccuracyReportRequest(BaseModel):
    """Request for accuracy performance report."""

    symbol: Optional[str] = Field(default=None, description="Filter by symbol")
    timeframe: Optional[str] = Field(default=None, description="Filter by timeframe")
    signal: Optional[str] = Field(default=None, pattern="^(BUY|SELL|HOLD)?$", description="Filter by signal")
    days: int = Field(default=30, ge=1, le=365, description="Number of days to analyze")
    user_id: Optional[UUID] = Field(default=None, description="Filter by user ID")

    @field_validator('signal')
    @classmethod
    def validate_signal(cls, v: Optional[str]) -> Optional[str]:
        """Validate signal is uppercase if provided."""
        return v.upper() if v else None


class AccuracyMetrics(BaseModel):
    """Accuracy performance metrics."""

    period_days: int = Field(..., description="Analysis period in days")
    symbol: Optional[str] = Field(default=None, description="Filtered symbol")
    timeframe: Optional[str] = Field(default=None, description="Filtered timeframe")
    signal: Optional[str] = Field(default=None, description="Filtered signal")
    total_trades: int = Field(..., description="Total number of trades")
    wins: int = Field(..., description="Number of winning trades")
    losses: int = Field(..., description="Number of losing trades")
    break_evens: int = Field(..., description="Number of break-even trades")
    win_rate_pct: float = Field(..., description="Win rate percentage")
    avg_pnl_pct: float = Field(..., description="Average P/L percentage")
    avg_win_pct: float = Field(..., description="Average winning trade percentage")
    avg_loss_pct: float = Field(..., description="Average losing trade percentage")
    profit_factor: float = Field(..., description="Profit factor (wins/losses)")
    sharpe_ratio: Optional[float] = Field(default=None, description="Sharpe ratio")
    best_trade_pct: float = Field(..., description="Best trade percentage")
    worst_trade_pct: float = Field(..., description="Worst trade percentage")
    avg_hold_hours: float = Field(..., description="Average hold time in hours")
    recommendation: str = Field(..., description="Text recommendation based on performance")

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "period_days": 30,
                "symbol": "XAUUSD",
                "timeframe": "H1",
                "signal": "BUY",
                "total_trades": 50,
                "wins": 35,
                "losses": 15,
                "break_evens": 0,
                "win_rate_pct": 70.0,
                "avg_pnl_pct": 2.5,
                "avg_win_pct": 4.2,
                "avg_loss_pct": 1.8,
                "profit_factor": 2.33,
                "sharpe_ratio": 1.39,
                "best_trade_pct": 12.5,
                "worst_trade_pct": -5.2,
                "avg_hold_hours": 4.5,
                "recommendation": "Excellent - High confidence trades"
            }
        }


class BestPerformingConfig(BaseModel):
    """Best-performing configuration (symbol/timeframe/signal combination)."""

    symbol: str = Field(..., description="Trading symbol")
    timeframe: str = Field(..., description="Timeframe")
    signal: str = Field(..., description="Signal type")
    total_trades: int = Field(..., description="Number of trades")
    win_rate_pct: float = Field(..., description="Win rate percentage")
    avg_pnl_pct: float = Field(..., description="Average P/L percentage")
    profit_factor: float = Field(..., description="Profit factor")

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "symbol": "XAUUSD",
                "timeframe": "H4",
                "signal": "BUY",
                "total_trades": 25,
                "win_rate_pct": 76.0,
                "avg_pnl_pct": 3.2,
                "profit_factor": 2.8
            }
        }


class OutcomeRecordResponse(BaseModel):
    """Response after recording outcome."""

    success: bool = Field(..., description="Whether operation succeeded")
    outcome_id: Optional[str] = Field(default=None, description="UUID of created outcome")
    message: str = Field(..., description="Status message")


class AccuracyReportResponse(BaseModel):
    """Response containing accuracy report."""

    success: bool = Field(..., description="Whether operation succeeded")
    data: Optional[dict] = Field(default=None, description="Report data")

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "report": {
                        "period_days": 30,
                        "total_trades": 50,
                        "win_rate_pct": 70.0,
                        "profit_factor": 2.33
                    },
                    "best_performing": [
                        {
                            "symbol": "XAUUSD",
                            "timeframe": "H4",
                            "signal": "BUY",
                            "total_trades": 25,
                            "win_rate_pct": 76.0
                        }
                    ]
                }
            }
        }
