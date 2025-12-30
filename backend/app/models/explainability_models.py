"""Data models for explainability layer."""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class ProvenanceMetadata(BaseModel):
    """Metadata for data provenance."""
    source: str
    data_type: str
    fetched_at: datetime
    age_seconds: float
    cache_hit: bool
    confidence: float = Field(ge=0.0, le=1.0)
    validation_status: str


class ReasoningStepResponse(BaseModel):
    """Single reasoning step in CoT."""
    step_number: int
    category: str
    description: str
    indicators_used: List[str]
    points_awarded: int
    max_points: int
    confidence: float
    provenance_keys: List[str]


class ChainOfThoughtResponse(BaseModel):
    """Complete CoT explanation."""
    steps: List[ReasoningStepResponse]
    total_score: int
    max_score: int
    confidence: float
    confidence_pct: int
    recommendation: str
    reasoning_summary: str
    risks_identified: List[str]
    data_gaps: List[str]


class ExplainRecommendationRequest(BaseModel):
    """Request for recommendation explanation."""
    symbol: str
    timeframe: str = "H1"
    recommendation_id: Optional[str] = None


class ExplainRecommendationResponse(BaseModel):
    """Response with explanation."""
    symbol: str
    timeframe: str
    explainability: ChainOfThoughtResponse
    provenance: Dict[str, Any]
