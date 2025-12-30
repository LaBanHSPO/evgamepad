"""
Data provenance tracking for explainability.
Every signal, indicator, pattern tagged with source metadata.
"""
import logging
from typing import Any, Dict, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class DataSource(Enum):
    """Data source types."""
    MT5 = "MT5 Terminal"
    TWELVEDATA = "TwelveData API"
    PANDAS_TA = "pandas-ta calculation"
    CLAUDE_API = "Claude API"
    DEEPSEEK_API = "DeepSeek API"
    REDIS_CACHE = "Redis cache"
    USER_INPUT = "User input"


class DataType(Enum):
    """Data type categories."""
    PRICE = "price"
    VOLUME = "volume"
    INDICATOR = "indicator"
    PATTERN = "pattern"
    LLM_SUMMARY = "llm_summary"
    RISK_METRIC = "risk_metric"
    USER_PREFERENCE = "user_preference"


class ValidationStatus(Enum):
    """Validation status of data."""
    VALIDATED = "validated"          # Cross-checked with multiple sources
    UNVALIDATED = "unvalidated"      # Single source, not verified
    CONFLICTING = "conflicting"      # Multiple sources disagree
    STALE = "stale"                  # Data older than threshold


@dataclass
class DataProvenance:
    """Metadata for every piece of data used in recommendation."""

    source: DataSource
    data_type: DataType
    fetched_at: datetime
    cache_hit: bool
    confidence: float  # 0.0-1.0
    validation_status: ValidationStatus
    raw_value: Any
    computed_value: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "source": self.source.value,
            "data_type": self.data_type.value,
            "fetched_at": self.fetched_at.isoformat(),
            "age_seconds": (datetime.now(timezone.utc) - self.fetched_at).total_seconds(),
            "cache_hit": self.cache_hit,
            "confidence": round(self.confidence, 2),
            "validation_status": self.validation_status.value,
            "raw_value": self.raw_value if isinstance(self.raw_value, (int, float, str, bool, type(None))) else str(self.raw_value),
            "computed_value": self.computed_value
        }

    @property
    def age_seconds(self) -> float:
        """Calculate data age in seconds."""
        return (datetime.now(timezone.utc) - self.fetched_at).total_seconds()

    def is_stale(self, threshold_seconds: int = 300) -> bool:
        """Check if data is stale (default: 5 minutes)."""
        return self.age_seconds > threshold_seconds


class ProvenanceTracker:
    """Tracks data provenance throughout recommendation pipeline."""

    def __init__(self):
        self.provenance_map: Dict[str, DataProvenance] = {}

    def track(
        self,
        key: str,
        source: DataSource,
        data_type: DataType,
        value: Any,
        fetched_at: Optional[datetime] = None,
        cache_hit: bool = False,
        confidence: float = 1.0,
        validation_status: ValidationStatus = ValidationStatus.UNVALIDATED
    ) -> DataProvenance:
        """
        Track a data point with provenance metadata.

        Args:
            key: Unique identifier (e.g., "rsi", "macd_histogram", "volume_validation")
            source: Where data came from
            data_type: Type of data
            value: The actual value
            fetched_at: When data was fetched (defaults to now)
            cache_hit: Whether data came from cache
            confidence: Confidence in data quality (0-1)
            validation_status: Validation state

        Returns:
            DataProvenance object
        """
        provenance = DataProvenance(
            source=source,
            data_type=data_type,
            fetched_at=fetched_at or datetime.now(timezone.utc),
            cache_hit=cache_hit,
            confidence=confidence,
            validation_status=validation_status,
            raw_value=value
        )

        self.provenance_map[key] = provenance
        logger.debug(f"Tracked provenance for {key}: {source.value} ({data_type.value})")

        return provenance

    def get(self, key: str) -> Optional[DataProvenance]:
        """Retrieve provenance for a key."""
        return self.provenance_map.get(key)

    def get_all(self) -> Dict[str, DataProvenance]:
        """Get all tracked provenance data."""
        return self.provenance_map

    def to_summary(self) -> Dict[str, Any]:
        """Generate summary of all provenance data."""
        sources = {}
        for prov in self.provenance_map.values():
            source_name = prov.source.value
            if source_name not in sources:
                sources[source_name] = {
                    "count": 0,
                    "cache_hits": 0,
                    "avg_confidence": 0.0,
                    "oldest_age_seconds": 0
                }

            sources[source_name]["count"] += 1
            if prov.cache_hit:
                sources[source_name]["cache_hits"] += 1
            sources[source_name]["avg_confidence"] += prov.confidence
            sources[source_name]["oldest_age_seconds"] = max(
                sources[source_name]["oldest_age_seconds"],
                prov.age_seconds
            )

        # Calculate averages
        for source_data in sources.values():
            if source_data["count"] > 0:
                source_data["avg_confidence"] = round(
                    source_data["avg_confidence"] / source_data["count"],
                    2
                )

        return {
            "total_data_points": len(self.provenance_map),
            "sources": sources,
            "oldest_data_age_seconds": max(
                (p.age_seconds for p in self.provenance_map.values()),
                default=0
            )
        }
