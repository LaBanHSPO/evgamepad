"""
User profile and preferences for personalized recommendations.
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class RiskTolerance(str, Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"

class UserProfile(BaseModel):
    """User trading profile and preferences."""
    user_id: str
    risk_tolerance: RiskTolerance = RiskTolerance.MODERATE
    preferred_timeframes: List[str] = Field(default=["H1", "H4", "D1"])
    preferred_indicators: List[str] = Field(default=["RSI", "MACD", "SMA"])
    watchlist: List[str] = Field(default=[])
    max_position_risk: float = Field(default=0.02, ge=0.005, le=0.10)
    language: str = Field(default="vi", pattern="^(vi|en)$")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class UserProfileUpdate(BaseModel):
    """Update model for user profile."""
    risk_tolerance: Optional[RiskTolerance] = None
    preferred_timeframes: Optional[List[str]] = None
    preferred_indicators: Optional[List[str]] = None
    watchlist: Optional[List[str]] = None
    max_position_risk: Optional[float] = None
    language: Optional[str] = None

class RecommendationRequest(BaseModel):
    """Request for personalized recommendation."""
    symbol: str = Field(..., min_length=1, max_length=20)
    timeframe: str = Field(default="H1")
    language: str = Field(default="vi", pattern="^(vi|en)$")
    include_technical: bool = True
    include_patterns: bool = True
    include_sr: bool = True
    include_ai_summary: bool = True

class RecommendationResponse(BaseModel):
    """Response for recommendation request."""
    success: bool = True
    symbol: str
    overall_signal: Dict[str, Any]
    technical_signal: Optional[Dict[str, Any]] = None
    pattern_signal: Optional[Dict[str, Any]] = None
    targets: Dict[str, Any]
    ai_summary: Optional[Dict[str, Any]] = None
    recommendation: Dict[str, Any]
    generated_at: datetime = Field(default_factory=datetime.utcnow)
