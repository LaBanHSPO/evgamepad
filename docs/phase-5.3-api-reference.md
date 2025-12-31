# Phase 5.3 - Visual Indicator Dashboard API Reference

**Date:** 2025-12-31
**Phase:** 5.3 - Visual Indicator Dashboard (Frontend)
**Version:** 1.0.0
**Status:** Completed

---

## Overview

Phase 5.3 adds a comprehensive visual explainability layer to the Capital Companion Panel. Users can now:

1. **See What AI Sees** - Interactive technical indicator overlay chart
2. **Understand Reasoning** - Step-by-step chain-of-thought breakdown
3. **Verify Performance** - Historical accuracy metrics for specific configurations
4. **Check Data Freshness** - Data provenance timeline showing source freshness

This phase focuses on **frontend UI/UX components** that consume existing backend events and data.

---

## Frontend Components

### 1. IndicatorOverlayChart Component

**File:** `src/components/advisor/IndicatorOverlayChart.tsx`

**Purpose:** Display candlestick chart with toggleable technical indicators

**Props:**
```typescript
interface IndicatorOverlayChartProps {
  symbol: string;        // Trading symbol (e.g., "XAUUSD")
  timeframe: string;     // Timeframe (e.g., "H1", "D1")
  height?: number;       // Chart height in pixels (default: 400)
}
```

**Technical Details:**
- Uses Recharts for chart rendering (responsive, mobile-friendly)
- Candlestick visualization via LineChart (simplified from full candlestick library)
- Support/Resistance lines rendered as ReferenceLine components
- Colors: Candlesticks (up=#26A69A, down=#EF5350), EMAs (blue/orange), BBands (teal), S/R (green/red)

**Socket.IO Integration:**
- Event: `advisor:technical_summary` (request)
- Event: `advisor:technical_result` (response)

---

### 2. ChainOfThoughtViewer Component

**File:** `src/components/advisor/ChainOfThoughtViewer.tsx`

**Purpose:** Display step-by-step reasoning breakdown with scoring

**Key Features:**
- 5-step reasoning display (Trend, Momentum, Volume, Pattern, Risk)
- Point-based scoring (0-12 total)
- Category icons from lucide-react
- Color-coded recommendation (BUY=green, SELL=red, HOLD=orange)
- Risk identification and data gaps sections
- Confidence percentage per step

**Visual Scoring:**
- Green (#26A69A) if ratio >= 80%
- Orange (#FFA726) if ratio >= 50%
- Red (#EF5350) if ratio < 50%

---

### 3. AccuracyMetricsPanel Component

**File:** `src/components/advisor/AccuracyMetricsPanel.tsx`

**Purpose:** Display historical performance metrics

**Metrics Displayed:**
- Total trades count
- Win rate % with W/L breakdown
- Avg P/L % (with trending icons)
- Profit factor with quality assessment
- Optional: Avg Win/Loss, Avg Hold Hours

**Socket.IO Integration:**
- Event: `advisor:accuracy_report` (request)
- Event: `advisor:accuracy_result` (response)
- Supports filtering by symbol, timeframe, signal, period

**Color Thresholds:**
- Win Rate: Green ≥70%, Orange ≥60%, Yellow ≥50%, Red <50%
- Profit Factor: Green ≥2.0, Orange ≥1.5, Yellow ≥1.0, Red <1.0

---

### 4. ProvenanceTimeline Component

**File:** `src/components/advisor/ProvenanceTimeline.tsx`

**Purpose:** Display data source freshness and provenance

**Data Sources Tracked:**
- MT5 (Database icon)
- TwelveData/API (Cloud icon)
- pandas-ta (Activity icon)
- Claude/DeepSeek/LLM (Bot icon)
- Redis/Cache (RefreshCw icon)

**Freshness Indicators:**
- Fresh: < 1 min (green)
- Acceptable: < 5 min (orange)
- Warning: < 1 hour (yellow)
- Stale: >= 1 hour (red)

**Overall Status Indicators:**
- ✅ All data fresh
- ✅ Freshness acceptable
- ⚠️ Some data stale
- ❌ Data requires refresh

---

## Integration: CapitalCompanionPanel

**New Functionality:**
- "Show/Hide Details" toggle button
- Three view modes: chat, pinned, explainability
- Explainability view displays all 4 components in sequence

**State Management:**
- cotData: Chain-of-thought reasoning
- provenanceData: Data source freshness
- showExplainability: UI toggle state
- currentSymbol, currentTimeframe: Context for chart

---

## Socket.IO Events

### 1. advisor:explain_recommendation

**Direction:** Client → Server

**Request:**
```json
{
  "symbol": "XAUUSD",
  "timeframe": "H1"
}
```

---

### 2. advisor:explanation_result

**Direction:** Server → Client

**Response:**
```json
{
  "success": true,
  "data": {
    "explainability": {
      "steps": [...],
      "total_score": 11,
      "max_score": 12,
      "recommendation": "STRONG_BUY",
      "reasoning_summary": "...",
      "risks_identified": [...],
      "data_gaps": [...]
    },
    "provenance": {
      "total_data_points": 127,
      "sources": {...},
      "oldest_data_age_seconds": 120,
      "cache_hit_rate": 72.4
    }
  }
}
```

---

## Component Files

| File | Purpose | Status |
|------|---------|--------|
| src/components/advisor/IndicatorOverlayChart.tsx | Technical indicator chart | NEW |
| src/components/advisor/ChainOfThoughtViewer.tsx | Reasoning breakdown | NEW |
| src/components/advisor/AccuracyMetricsPanel.tsx | Performance metrics | NEW |
| src/components/advisor/ProvenanceTimeline.tsx | Data freshness tracker | NEW |
| src/components/CapitalCompanionPanel.tsx | Main panel integration | UPDATED |

---

**Last Updated:** 2025-12-31
**Version:** 1.0.0 (Stable)
