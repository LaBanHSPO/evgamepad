"""
Tests for data provenance tracking module.
"""
import pytest
from datetime import datetime, timedelta, timezone

from app.advisor.data_provenance_tracker import (
    ProvenanceTracker,
    DataProvenance,
    DataSource,
    DataType,
    ValidationStatus
)


class TestDataProvenance:
    """Test DataProvenance dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        prov = DataProvenance(
            source=DataSource.PANDAS_TA,
            data_type=DataType.INDICATOR,
            fetched_at=datetime(2025, 12, 30, 10, 0, 0, tzinfo=timezone.utc),
            cache_hit=False,
            confidence=0.95,
            validation_status=ValidationStatus.VALIDATED,
            raw_value=28.5
        )

        result = prov.to_dict()

        assert result["source"] == "pandas-ta calculation"
        assert result["data_type"] == "indicator"
        assert result["cache_hit"] is False
        assert result["confidence"] == 0.95
        assert result["validation_status"] == "validated"
        assert result["raw_value"] == 28.5

    def test_age_calculation(self):
        """Test age calculation."""
        old_time = datetime.now(timezone.utc) - timedelta(minutes=10)

        prov = DataProvenance(
            source=DataSource.MT5,
            data_type=DataType.PRICE,
            fetched_at=old_time,
            cache_hit=False,
            confidence=1.0,
            validation_status=ValidationStatus.VALIDATED,
            raw_value=2634.50
        )

        assert prov.age_seconds > 590  # ~10 minutes
        assert prov.age_seconds < 610

    def test_is_stale_check(self):
        """Test stale data detection."""
        # Fresh data
        fresh = DataProvenance(
            source=DataSource.MT5,
            data_type=DataType.PRICE,
            fetched_at=datetime.now(timezone.utc),
            cache_hit=False,
            confidence=1.0,
            validation_status=ValidationStatus.VALIDATED,
            raw_value=2634.50
        )
        assert not fresh.is_stale(threshold_seconds=300)

        # Stale data
        stale = DataProvenance(
            source=DataSource.MT5,
            data_type=DataType.PRICE,
            fetched_at=datetime.now(timezone.utc) - timedelta(minutes=10),
            cache_hit=False,
            confidence=1.0,
            validation_status=ValidationStatus.VALIDATED,
            raw_value=2634.50
        )
        assert stale.is_stale(threshold_seconds=300)


class TestProvenanceTracker:
    """Test ProvenanceTracker class."""

    @pytest.fixture
    def tracker(self):
        return ProvenanceTracker()

    def test_track_indicator(self, tracker):
        """Test tracking technical indicator."""
        provenance = tracker.track(
            key="rsi",
            source=DataSource.PANDAS_TA,
            data_type=DataType.INDICATOR,
            value=28.5,
            confidence=1.0,
            validation_status=ValidationStatus.VALIDATED
        )

        assert provenance.source == DataSource.PANDAS_TA
        assert provenance.confidence == 1.0
        assert provenance.raw_value == 28.5
        assert not provenance.cache_hit

    def test_track_with_cache_hit(self, tracker):
        """Test tracking with cache hit."""
        provenance = tracker.track(
            key="macd",
            source=DataSource.REDIS_CACHE,
            data_type=DataType.INDICATOR,
            value={"macd": 1.2, "signal": 0.8},
            cache_hit=True,
            confidence=1.0,
            validation_status=ValidationStatus.VALIDATED
        )

        assert provenance.cache_hit is True
        assert provenance.source == DataSource.REDIS_CACHE

    def test_get_provenance(self, tracker):
        """Test retrieving provenance."""
        tracker.track(
            key="rsi",
            source=DataSource.PANDAS_TA,
            data_type=DataType.INDICATOR,
            value=28.5
        )

        retrieved = tracker.get("rsi")
        assert retrieved is not None
        assert retrieved.raw_value == 28.5

        # Non-existent key
        assert tracker.get("nonexistent") is None

    def test_get_all_provenance(self, tracker):
        """Test retrieving all provenance data."""
        tracker.track("rsi", DataSource.PANDAS_TA, DataType.INDICATOR, 28.5)
        tracker.track("macd", DataSource.PANDAS_TA, DataType.INDICATOR, 1.2)
        tracker.track("volume", DataSource.MT5, DataType.VOLUME, 15000000)

        all_prov = tracker.get_all()
        assert len(all_prov) == 3
        assert "rsi" in all_prov
        assert "macd" in all_prov
        assert "volume" in all_prov

    def test_to_summary(self, tracker):
        """Test generating summary."""
        # Add multiple data points from different sources
        tracker.track("rsi", DataSource.PANDAS_TA, DataType.INDICATOR, 28.5, confidence=1.0)
        tracker.track("macd", DataSource.PANDAS_TA, DataType.INDICATOR, 1.2, confidence=1.0)
        tracker.track("volume", DataSource.MT5, DataType.VOLUME, 15000000, confidence=0.9)
        tracker.track("cached_data", DataSource.REDIS_CACHE, DataType.PRICE, 2634.50, cache_hit=True, confidence=1.0)

        summary = tracker.to_summary()

        assert summary["total_data_points"] == 4
        assert len(summary["sources"]) == 3  # PANDAS_TA, MT5, REDIS_CACHE

        # Check pandas-ta summary
        pandas_ta = summary["sources"]["pandas-ta calculation"]
        assert pandas_ta["count"] == 2
        assert pandas_ta["cache_hits"] == 0
        assert pandas_ta["avg_confidence"] == 1.0

        # Check cache summary
        cache = summary["sources"]["Redis cache"]
        assert cache["count"] == 1
        assert cache["cache_hits"] == 1

    def test_summary_oldest_data(self, tracker):
        """Test oldest data age tracking."""
        # Track data with different ages
        tracker.track(
            "fresh",
            DataSource.PANDAS_TA,
            DataType.INDICATOR,
            1.0,
            fetched_at=datetime.now(timezone.utc)
        )

        old_time = datetime.now(timezone.utc) - timedelta(minutes=10)
        tracker.track(
            "old",
            DataSource.MT5,
            DataType.PRICE,
            2634.50,
            fetched_at=old_time
        )

        summary = tracker.to_summary()
        assert summary["oldest_data_age_seconds"] > 590  # ~10 minutes

    def test_complex_value_serialization(self, tracker):
        """Test serialization of complex values."""
        complex_value = {
            "macd": 1.2,
            "signal": 0.8,
            "histogram": 0.4
        }

        tracker.track(
            "macd_complex",
            DataSource.PANDAS_TA,
            DataType.INDICATOR,
            complex_value
        )

        prov = tracker.get("macd_complex")
        result = prov.to_dict()

        # Complex values should be converted to string
        assert isinstance(result["raw_value"], str)

    def test_validation_status_tracking(self, tracker):
        """Test different validation statuses."""
        # Validated data
        tracker.track(
            "validated",
            DataSource.PANDAS_TA,
            DataType.INDICATOR,
            1.0,
            validation_status=ValidationStatus.VALIDATED
        )

        # Unvalidated data
        tracker.track(
            "unvalidated",
            DataSource.PANDAS_TA,
            DataType.PATTERN,
            "pattern",
            validation_status=ValidationStatus.UNVALIDATED
        )

        # Conflicting data
        tracker.track(
            "conflicting",
            DataSource.TWELVEDATA,
            DataType.VOLUME,
            15000000,
            validation_status=ValidationStatus.CONFLICTING
        )

        validated = tracker.get("validated")
        assert validated.validation_status == ValidationStatus.VALIDATED

        conflicting = tracker.get("conflicting")
        assert conflicting.validation_status == ValidationStatus.CONFLICTING

    def test_empty_tracker_summary(self, tracker):
        """Test summary with no data."""
        summary = tracker.to_summary()

        assert summary["total_data_points"] == 0
        assert len(summary["sources"]) == 0
        assert summary["oldest_data_age_seconds"] == 0
