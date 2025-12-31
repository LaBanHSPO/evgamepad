# Phase 5.4: Integration & Testing

**Duration:** 2 hours
**Priority:** P0
**Status:** Planned

---

## Objective

Comprehensive testing, performance validation, documentation, and production deployment of Phase 5 explainability features.

---

## Deliverables

1. Integration tests (end-to-end flows)
2. Performance benchmarks
3. User documentation
4. API documentation updates
5. Deployment checklist
6. Rollback procedures

---

## Integration Testing

### End-to-End Test Scenarios

**File:** `backend/tests/integration/test_explainability_e2e.py`

```python
"""End-to-end integration tests for explainability layer."""
import pytest
from datetime import datetime


class TestExplainabilityE2E:
    """Test complete explainability flow."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_recommendation_with_explainability(self, test_client, db_pool):
        """
        Test full recommendation flow with explainability.

        Flow:
        1. Client requests recommendation
        2. Backend generates CoT explanation
        3. Backend tracks data provenance
        4. Response includes explainability data
        5. Client can request detailed explanation
        """
        # 1. Request recommendation
        response = await test_client.emit_and_wait(
            'advisor:recommendation',
            {
                'symbol': 'XAUUSD',
                'timeframe': 'H1',
                'user_profile': {'risk_tolerance': 'moderate'}
            },
            'advisor:recommendation_result'
        )

        assert response['success'] is True
        data = response['data']

        # Verify explainability included
        assert 'explainability' in data
        explainability = data['explainability']

        assert 'steps' in explainability
        assert len(explainability['steps']) >= 3  # Trend, Momentum, Volume

        assert 'total_score' in explainability
        assert 'confidence' in explainability
        assert 'risks_identified' in explainability

        # Verify provenance
        assert 'provenance' in data
        provenance = data['provenance']

        assert 'total_data_points' in provenance
        assert 'sources' in provenance
        assert 'oldest_data_age_seconds' in provenance

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_accuracy_tracking_flow(self, test_client, db_pool):
        """
        Test accuracy tracking workflow.

        Flow:
        1. Client records trade outcome
        2. Backend saves to database
        3. Materialized view refreshes
        4. Client requests accuracy report
        5. Backend returns performance metrics
        """
        # 1. Record outcome
        outcome_response = await test_client.emit_and_wait(
            'advisor:record_outcome',
            {
                'symbol': 'XAUUSD',
                'timeframe': 'H1',
                'signal': 'BUY',
                'confidence': 85,
                'entry_price': 2634.50,
                'exit_price': 2640.20,
                'exit_reason': 'take_profit'
            },
            'advisor:outcome_recorded'
        )

        assert outcome_response['success'] is True
        assert 'outcome_id' in outcome_response

        # 2. Request accuracy report
        report_response = await test_client.emit_and_wait(
            'advisor:accuracy_report',
            {
                'symbol': 'XAUUSD',
                'timeframe': 'H1',
                'days': 7
            },
            'advisor:accuracy_result'
        )

        assert report_response['success'] is True
        report = report_response['data']['report']

        assert 'total_trades' in report
        assert 'win_rate_pct' in report
        assert 'profit_factor' in report

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_visual_dashboard_data_flow(self, test_client):
        """
        Test data flow for visual dashboard components.

        Flow:
        1. Client requests technical summary
        2. Backend returns OHLCV + indicators
        3. Client requests explanation
        4. Backend returns CoT breakdown
        5. Client requests provenance details
        """
        # 1. Technical summary
        tech_response = await test_client.emit_and_wait(
            'advisor:technical_summary',
            {
                'symbol': 'XAUUSD',
                'timeframe': 'H1',
                'indicators': ['sma', 'ema', 'rsi', 'macd', 'bb']
            },
            'advisor:technical_result'
        )

        assert tech_response['success'] is True
        assert 'indicators' in tech_response['data']
        assert 'signals' in tech_response['data']

        # 2. Explanation
        explain_response = await test_client.emit_and_wait(
            'advisor:explain_recommendation',
            {
                'symbol': 'XAUUSD',
                'timeframe': 'H1'
            },
            'advisor:explanation_result'
        )

        assert explain_response['success'] is True
        assert 'explainability' in explain_response['data']
        assert 'provenance' in explain_response['data']
```

---

## Performance Benchmarks

### Target Metrics

| Component | Metric | Target | Critical |
|-----------|--------|--------|----------|
| CoT Generation | Latency | < 200ms | < 500ms |
| Provenance Tracking | Overhead | < 50ms | < 100ms |
| Accuracy Query | Response | < 100ms | < 300ms |
| Visual Dashboard | Load Time | < 1s | < 2s |
| Database Write | Throughput | > 100 ops/s | > 50 ops/s |
| Materialized View Refresh | Duration | < 2s | < 5s |

### Benchmark Tests

**File:** `backend/tests/performance/test_explainability_performance.py`

```python
"""Performance benchmarks for explainability layer."""
import pytest
import asyncio
from time import time


class TestExplainabilityPerformance:
    """Performance tests for explainability components."""

    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_cot_generation_latency(self, cot_engine, sample_technical_data):
        """Benchmark: CoT generation should be < 200ms."""
        start = time()

        result = cot_engine.generate_explanation(
            technical_data=sample_technical_data,
            pattern_data=None,
            risk_data=None,
            volume_validation=None,
            current_price=2634.50
        )

        duration_ms = (time() - start) * 1000

        assert duration_ms < 200, f"CoT generation took {duration_ms:.2f}ms (target: < 200ms)"
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_accuracy_query_performance(self, accuracy_tracker):
        """Benchmark: Accuracy report query should be < 100ms."""
        start = time()

        report = await accuracy_tracker.get_accuracy_report(
            symbol="XAUUSD",
            timeframe="H1",
            days=30
        )

        duration_ms = (time() - start) * 1000

        assert duration_ms < 100, f"Accuracy query took {duration_ms:.2f}ms (target: < 100ms)"
        assert report is not None

    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_database_write_throughput(self, accuracy_tracker):
        """Benchmark: Should handle > 100 outcome records/sec."""
        num_records = 100
        start = time()

        tasks = [
            accuracy_tracker.record_outcome(
                symbol="XAUUSD",
                timeframe="H1",
                signal="BUY",
                confidence=85,
                entry_price=2634.50 + i * 0.1,
                exit_price=2640.20 + i * 0.1
            )
            for i in range(num_records)
        ]

        await asyncio.gather(*tasks)

        duration = time() - start
        throughput = num_records / duration

        assert throughput > 100, f"Throughput: {throughput:.1f} ops/s (target: > 100 ops/s)"
```

---

## Documentation Updates

### 1. User Guide

**File:** `docs/explainability-user-guide.md`

```markdown
# Explainability Layer User Guide

## Overview

The explainability layer provides transparency into AI trading recommendations through:
- **Chain-of-Thought Reasoning** - See step-by-step logic
- **Data Provenance** - Verify data sources and freshness
- **Accuracy Tracking** - Review historical performance
- **Visual Validation** - See indicators on charts

## Reading Chain-of-Thought Explanations

### Scoring System

Recommendations scored 0-12 points across 5 categories:

1. **Trend Analysis** (0-3 points)
   - EMA alignment
   - ADX trend strength
   - Trend direction

2. **Momentum Signals** (0-3 points)
   - RSI oversold/overbought
   - MACD crossovers
   - Momentum direction

3. **Volume Validation** (0-2 points)
   - Broker vs market volume comparison
   - Fake pump detection
   - Volume divergence warnings

4. **Pattern Confirmation** (0-2 points)
   - Bullish/bearish candlestick patterns
   - Chart patterns

5. **Risk Assessment** (0-2 points)
   - Risk/Reward ratio
   - Position sizing limits

### Confidence Levels

- **10-12 points**: 80-100% confidence (STRONG signal)
- **7-9 points**: 60-79% confidence (MODERATE signal)
- **4-6 points**: 40-59% confidence (WEAK signal)
- **0-3 points**: 0-39% confidence (NO TRADE)

## Understanding Accuracy Metrics

### Key Metrics

- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Average win ÷ Average loss
  - > 2.0 = Excellent
  - 1.5-2.0 = Good
  - < 1.5 = Poor

- **Sharpe Ratio**: Return relative to risk (higher is better)

### Filtering

View accuracy by:
- Symbol (e.g., XAUUSD only)
- Timeframe (e.g., H4 only)
- Signal type (e.g., BUY signals only)
- Time period (7, 30, 90 days)

## Using Visual Dashboard

### Indicator Overlays

Toggle indicators on/off:
- EMAs (21, 50)
- Bollinger Bands
- Volume bars
- Support/Resistance levels

### Data Freshness

Check provenance timeline to see:
- Data age (green < 1min, orange < 5min, red > 5min)
- Cache hits (faster responses)
- Source confidence (MT5, TwelveData, pandas-ta)

## Recording Trade Outcomes

To improve accuracy tracking:

1. After entering trade, note:
   - Entry price
   - Stop loss
   - Take profit

2. After exiting trade:
   - Record outcome via "Record Result" button
   - Exit price
   - Exit reason (TP hit, SL hit, manual)

3. Review accuracy:
   - Check "Performance" tab
   - See which timeframes/signals perform best
```

### 2. API Documentation

**File:** `docs/advisor-api-specification.md` (additions)

```markdown
## New Events (Phase 5: Explainability)

### advisor:explain_recommendation

Get chain-of-thought explanation for recommendation.

**Request:**
```json
{
  "symbol": "XAUUSD",
  "timeframe": "H1"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "symbol": "XAUUSD",
    "timeframe": "H1",
    "explainability": {
      "steps": [
        {
          "step_number": 1,
          "category": "trend",
          "description": "...",
          "points_awarded": 2,
          "max_points": 3,
          "confidence": 0.67
        }
      ],
      "total_score": 10,
      "max_score": 12,
      "confidence": 0.83,
      "recommendation": "BUY",
      "reasoning_summary": "...",
      "risks_identified": [],
      "data_gaps": []
    },
    "provenance": {
      "total_data_points": 15,
      "sources": {...},
      "oldest_data_age_seconds": 12
    }
  }
}
```

### advisor:record_outcome

Record trade outcome for accuracy tracking.

**Request:**
```json
{
  "symbol": "XAUUSD",
  "timeframe": "H1",
  "signal": "BUY",
  "confidence": 85,
  "entry_price": 2634.50,
  "exit_price": 2640.20,
  "stop_loss": 2625.50,
  "take_profit": 2645.00,
  "exit_reason": "take_profit",
  "entry_at": "2025-12-30T10:00:00Z",
  "exit_at": "2025-12-30T14:30:00Z"
}
```

**Response:**
```json
{
  "success": true,
  "outcome_id": "uuid",
  "message": "Trade outcome recorded successfully"
}
```

### advisor:accuracy_report

Get historical performance metrics.

**Request:**
```json
{
  "symbol": "XAUUSD",
  "timeframe": "H1",
  "signal": "BUY",
  "days": 30
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "report": {
      "period_days": 30,
      "total_trades": 45,
      "wins": 31,
      "losses": 14,
      "win_rate_pct": 68.9,
      "avg_pnl_pct": 1.85,
      "profit_factor": 2.13,
      "recommendation": "Good - Reliable performance"
    },
    "best_performing": [...]
  }
}
```
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] All unit tests passing (80+ tests)
- [ ] Integration tests passing (3+ scenarios)
- [ ] Performance benchmarks met
- [ ] Database migration tested on staging
- [ ] Feature flags configured
- [ ] Documentation updated
- [ ] Code review completed

### Deployment Steps

1. **Database Migration**
   ```bash
   # Backup production database
   pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

   # Run migration
   psql $DATABASE_URL < backend/app/database/migrations/005_recommendation_outcomes.sql

   # Verify tables created
   psql $DATABASE_URL -c "\d recommendation_outcomes"
   psql $DATABASE_URL -c "\d recommendation_accuracy"
   ```

2. **Backend Deployment**
   ```bash
   # Enable feature flags (gradual rollout)
   export ENABLE_EXPLAINABILITY=true
   export ENABLE_PROVENANCE_TRACKING=true
   export ENABLE_ACCURACY_TRACKING=true

   # Deploy backend
   git checkout main
   git pull origin main
   docker-compose up -d --build backend
   ```

3. **Frontend Deployment**
   ```bash
   # Install dependencies
   npm install lightweight-charts

   # Build frontend
   npm run build

   # Deploy
   docker-compose up -d --build frontend
   ```

4. **Smoke Tests**
   - [ ] Request recommendation with explainability
   - [ ] Record trade outcome
   - [ ] Request accuracy report
   - [ ] View visual dashboard
   - [ ] Check database for outcomes

### Monitoring

**Metrics to Track:**
- CoT generation latency (avg, p95, p99)
- Database write throughput
- Materialized view refresh duration
- Frontend component load times
- Error rates for new events

**Alerts:**
- CoT latency > 500ms for 5 minutes
- Database write failures > 5%
- Accuracy query > 300ms
- Frontend errors > 1%

---

## Rollback Procedures

### If Issues Detected

1. **Disable Feature Flags**
   ```bash
   export ENABLE_EXPLAINABILITY=false
   export ENABLE_PROVENANCE_TRACKING=false
   export ENABLE_ACCURACY_TRACKING=false

   # Restart services
   docker-compose restart backend
   ```

2. **Rollback Database (if needed)**
   ```bash
   # Drop new tables
   psql $DATABASE_URL -c "DROP TABLE IF EXISTS recommendation_outcomes CASCADE"
   psql $DATABASE_URL -c "DROP MATERIALIZED VIEW IF EXISTS recommendation_accuracy CASCADE"

   # Restore from backup if needed
   psql $DATABASE_URL < backup_YYYYMMDD.sql
   ```

3. **Rollback Code**
   ```bash
   git revert <commit-hash>
   docker-compose up -d --build
   ```

---

## Post-Deployment

### Week 1: Monitoring

- [ ] Review performance metrics daily
- [ ] Check error logs
- [ ] Monitor database growth
- [ ] Collect user feedback

### Week 2: Optimization

- [ ] Identify performance bottlenecks
- [ ] Optimize slow queries
- [ ] Tune caching strategies
- [ ] Address user-reported issues

### Week 3: Gradual Rollout

- [ ] 10% users (internal testing)
- [ ] 50% users (beta testing)
- [ ] 100% users (full rollout)
- [ ] Remove feature flags

---

## Acceptance Criteria

- [ ] All 80+ unit tests passing
- [ ] Integration tests passing
- [ ] Performance benchmarks met
- [ ] Documentation complete
- [ ] Database migration successful
- [ ] Feature flags working
- [ ] Smoke tests passed
- [ ] Monitoring configured
- [ ] Rollback tested

---

## Success Metrics (30 Days Post-Launch)

### Technical
- [ ] CoT generation < 200ms (95th percentile)
- [ ] Accuracy queries < 100ms (95th percentile)
- [ ] Zero data loss in outcome tracking
- [ ] Database growth within projections

### User Experience
- [ ] 70%+ users view explainability details
- [ ] 50+ outcomes recorded per week
- [ ] User trust score improvement (survey)
- [ ] Reduced support tickets for "why this recommendation?"

### Quality
- [ ] Zero critical bugs
- [ ] < 0.1% error rate on new events
- [ ] No hallucinations detected
- [ ] Provenance data 100% accurate

---

**Phase 5 Complete:** Ready for production deployment 🚀
