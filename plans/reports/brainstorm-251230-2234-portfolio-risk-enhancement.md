# Brainstorm Report: Portfolio/Risk Management Screen Enhancement

**Date:** 2025-12-30
**Session:** 22:34
**Agent:** Solution Brainstormer
**Status:** Solution Agreed

---

## Problem Statement

User wants enhanced Portfolio/Risk Management screen (`src/pages/Portfolio.tsx`) that:
- **Primary Goal:** Capital preservation - users want to NOT lose money and protect principle
- **Leverages:** Socket.IO real-time updates + LLM analysis (Claude/DeepSeek)
- **Reference:** Capital Companion Smart Risk Management docs (R-Multiple framework, position sizing)
- **Current State:** Static display with hardcoded demo data (account balance 85%, risk exposure 1.5%, margin level, drawdown)

### User Requirements (from discovery):
1. **Real-time Metrics:** Portfolio-wide risk exposure, dynamic drawdown alerts, AI-powered position warnings
2. **LLM Approach:** On-demand advisory (user-initiated, not proactive)
3. **Trigger:** User-initiated only (no auto-LLM analysis, cost control)
4. **Risk Philosophy:** Capital preservation first (conservative protection over return optimization)

---

## Current System Analysis

### Existing Architecture (from codebase)

**Backend (Python):**
- Socket.IO server on port 8000
- AI Trading Advisor module with 4 phases:
  - Phase 01-03: Technical analysis, patterns, risk analysis
  - Phase 04: LLM integration (Claude 3.7 Sonnet primary, DeepSeek fallback)
- Existing events: `advisor:technical_summary`, `advisor:pattern_scan`, `advisor:risk_analysis`, `advisor:recommendation`
- Redis caching: 60s indicators, 300s patterns/AI summaries
- Data source: MT5 terminal for market data

**Frontend (React/TypeScript):**
- `SocketContext` established with connection management
- `RiskManagementPanel.tsx`: Static gauges for account balance, risk exposure
- `MissionLogPanel.tsx`: Trade history table
- No current Socket.IO event subscriptions for advisor module

**Gap Analysis:**
- ❌ No real-time portfolio data streaming
- ❌ No position P&L tracking
- ❌ No integration with existing advisor backend events
- ❌ No LLM advisory UI components
- ❌ No user-initiated risk analysis trigger

---

## Evaluated Approaches

### Approach 1: Full Portfolio Streaming Architecture (REJECTED)

**Description:** Stream all portfolio metrics via Socket.IO with continuous updates (positions, P&L, risk metrics every 1-5s).

**Pros:**
- True real-time monitoring
- Instant alert detection
- Best UX for active traders

**Cons:**
- ❌ Over-engineered for user requirement (user-initiated analysis only)
- ❌ High backend complexity (need position tracking, P&L calculation engine)
- ❌ WebSocket bandwidth waste (most data doesn't change frequently)
- ❌ Requires MT5 integration for open positions (not currently implemented)
- ❌ Violates YAGNI - user doesn't need sub-second updates for capital preservation

**Verdict:** REJECTED - Too complex, doesn't match user's on-demand requirement

---

### Approach 2: Hybrid Static + On-Demand LLM Analysis (RECOMMENDED)

**Description:** Display real-time risk metrics via Socket.IO polling + user-triggered LLM portfolio analysis leveraging existing advisor events.

**Architecture:**

```
Portfolio Page Components:
┌──────────────────────────────────────────────────────────────┐
│  RiskManagementPanel (Enhanced)                              │
│  ├─ Real-time Metrics (Socket.IO subscriptions):            │
│  │  ├─ Portfolio-Wide Risk Exposure (% of capital at risk)  │
│  │  ├─ Current Drawdown Level (% from peak)                 │
│  │  └─ Active Position Count                                │
│  ├─ User Action Button: "Analyze Portfolio Risk"            │
│  └─ LLM Advisory Display (conditional render)               │
├──────────────────────────────────────────────────────────────┤
│  AI Risk Advisory Panel (NEW, renders on-demand)            │
│  ├─ Overall Portfolio Health Score (0-100)                  │
│  ├─ LLM-Generated Capital Preservation Advice               │
│  ├─ Position-Specific Warnings (AI-detected risks)          │
│  └─ Recommended Actions (reduce/close positions)            │
├──────────────────────────────────────────────────────────────┤
│  MissionLogPanel (Existing trade history)                   │
└──────────────────────────────────────────────────────────────┘
```

**Data Flow:**

```
1. Page Load:
   Client → emit portfolio:subscribe → Backend
   Backend → Stream risk metrics every 5-10s → Client
   Client → Update RiskManagementPanel gauges

2. User Clicks "Analyze Portfolio Risk":
   Client → emit advisor:portfolio_analysis {
     positions: [{symbol, entry, current, size, unrealized_pnl}],
     account_balance: 10000,
     risk_profile: "conservative",
     language: "vi"
   }
   Backend → Process multi-position risk analysis:
     ├─ For each position: advisor:risk_analysis
     ├─ Calculate portfolio-wide metrics
     ├─ Call LLM (Claude/DeepSeek) for capital preservation advice
     └─ Cache result (300s TTL)
   Backend → emit advisor:portfolio_result → Client
   Client → Render AI Risk Advisory Panel
```

**Backend Changes (NEW Event):**

```python
# backend/app/events/advisor_events.py
@sio.event
async def advisor_portfolio_analysis(sid: str, data: Dict[str, Any]):
    """
    Analyze entire portfolio for capital preservation.

    Request: {
        "positions": [
            {
                "symbol": "XAUUSD",
                "entry_price": 2100.50,
                "current_price": 2095.00,
                "position_size": 0.5,
                "unrealized_pnl": -2.75,
                "stop_loss": 2090.00,
                "timeframe": "H1"
            }
        ],
        "account_balance": 10000,
        "risk_profile": "conservative",
        "language": "vi"
    }

    Response: {
        "success": true,
        "portfolio_health": {
            "score": 65,  # 0-100
            "status": "CAUTION",  # HEALTHY/CAUTION/DANGER
            "total_risk_exposure": 3.2,  # % of capital
            "current_drawdown": 1.5,
            "positions_at_risk": 2
        },
        "position_analysis": [
            {
                "symbol": "XAUUSD",
                "risk_status": "approaching_stop",
                "recommendation": "Consider reducing position by 50%",
                "technical_signal": "bearish",
                "r_multiple": -0.5
            }
        ],
        "ai_advice": {
            "summary": "Portfolio approaching risk threshold...",
            "priority_actions": [
                "Close XAUUSD position to preserve capital",
                "Reduce overall exposure to 2%"
            ],
            "reasoning": "Technical analysis shows...",
            "model": "claude",
            "language": "vi"
        },
        "cached": false
    }
    """
```

**Frontend Components (NEW):**

```typescript
// src/components/AIRiskAdvisoryPanel.tsx
interface PortfolioAnalysisResult {
  portfolio_health: {
    score: number;
    status: 'HEALTHY' | 'CAUTION' | 'DANGER';
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
  }>;
  ai_advice: {
    summary: string;
    priority_actions: string[];
    reasoning: string;
    model: string;
    language: string;
  };
}

// User clicks button → emit advisor:portfolio_analysis
// On response → display AI advice panel with color-coded warnings
```

**Pros:**
- ✅ Matches user requirement: on-demand, user-initiated analysis
- ✅ Leverages existing advisor backend (minimal new code)
- ✅ Cost-efficient: LLM only called when user clicks (not per tick)
- ✅ Semantic caching reduces repeat analysis costs 75%
- ✅ Capital preservation focus: LLM prompt emphasizes downside protection
- ✅ Simple UX: Clear "Analyze" button, clear visual feedback
- ✅ Follows YAGNI/KISS: Only builds what's needed

**Cons:**
- ⚠️ Not truly real-time LLM (user must trigger, ~2-4s latency)
- ⚠️ Requires manual position data entry (if MT5 connection not available)
- ⚠️ Redis caching only effective if same portfolio analyzed repeatedly

**Implementation Complexity:** Medium (2-3 days)
- Backend: 1 new event handler, 1 new processor method, LLM prompt engineering
- Frontend: 1 new component, Socket.IO event integration, state management

---

### Approach 3: Risk Alert Subscription Model (REJECTED)

**Description:** Users configure risk thresholds (max drawdown, max exposure), backend monitors and alerts via Socket.IO when crossed.

**Pros:**
- Proactive protection
- No user action needed

**Cons:**
- ❌ User explicitly chose "user-initiated only" (not proactive)
- ❌ Requires background monitoring task (complexity)
- ❌ Needs persistent position tracking (not currently implemented)

**Verdict:** REJECTED - Doesn't match user requirement

---

## Final Recommended Solution

### Approach 2: Hybrid Static + On-Demand LLM Analysis

**Why this wins:**
1. **Aligns with user requirements:** User-initiated, cost-controlled, capital preservation focused
2. **Leverages existing system:** Uses established advisor events, Claude/DeepSeek integration, Redis caching
3. **YAGNI/KISS compliant:** Doesn't over-engineer, builds only what's needed
4. **DRY principle:** Reuses existing technical analysis, pattern detection, LLM infrastructure
5. **Cost-efficient:** LLM only called on user action (~$0.005/call with caching)

---

## Implementation Details

### Backend Components

**1. New Event Handler** (`advisor_events.py`):
```python
@sio.event
async def advisor_portfolio_analysis(sid, data):
    # Validate positions data
    # For each position: fetch technical analysis, risk metrics
    # Aggregate portfolio-wide risk exposure
    # Call LLM with capital preservation prompt
    # Return comprehensive analysis
```

**2. New Processor Method** (`advisor_processor.py`):
```python
async def process_portfolio_analysis(
    self, sid, positions, account_balance, risk_profile, language
):
    # Parallel analysis of all positions
    results = await asyncio.gather(*[
        self.analyze_position(pos) for pos in positions
    ])

    # Calculate portfolio metrics
    portfolio_health = self._calculate_portfolio_health(results)

    # LLM call with capital preservation prompt
    ai_advice = await self.ai_summarizer.generate_portfolio_advice(
        portfolio_health, results, risk_profile, language
    )

    # Cache result
    await self.redis_client.set_portfolio_analysis(
        cache_key, result, ttl=300
    )

    return result
```

**3. LLM Prompt Engineering** (capital preservation focus):
```python
PORTFOLIO_ANALYSIS_PROMPT = """
You are a conservative risk advisor focused on CAPITAL PRESERVATION.

Portfolio Status:
- Account Balance: {account_balance}
- Total Risk Exposure: {risk_exposure}% (Target: <2%)
- Current Drawdown: {drawdown}%
- Open Positions: {positions}

For each position, provide:
1. Risk assessment (SAFE/CAUTION/DANGER)
2. Technical signal deterioration analysis
3. Recommended action (HOLD/REDUCE/CLOSE)
4. Reasoning focused on protecting principle

Overall Portfolio Advice:
- Priority actions to reduce capital risk
- Position sizing recommendations
- Stop-loss adjustments

OUTPUT FORMAT: JSON with summary, priority_actions, reasoning
PRINCIPLE: Protect capital FIRST, profits SECOND.
"""
```

### Frontend Components

**1. Enhanced RiskManagementPanel** (`src/components/RiskManagementPanel.tsx`):
- Add "Analyze Portfolio Risk" button
- Socket.IO subscription for real-time metrics
- Conditional render of AI advisory result
- Loading state during LLM analysis (~2-4s)

**2. New AIRiskAdvisoryPanel** (`src/components/AIRiskAdvisoryPanel.tsx`):
- Portfolio health score gauge (0-100)
- Color-coded status (green/yellow/red)
- LLM-generated advice text
- Position-specific warnings table
- Priority actions checklist

**3. Socket.IO Integration** (`src/pages/Portfolio.tsx`):
```typescript
const { socket } = useSocket();
const [portfolioAnalysis, setPortfolioAnalysis] = useState(null);
const [isAnalyzing, setIsAnalyzing] = useState(false);

useEffect(() => {
  if (!socket) return;

  // Subscribe to portfolio metrics stream
  socket.emit('portfolio:subscribe');

  socket.on('portfolio:metrics', (data) => {
    // Update risk gauges
  });

  socket.on('advisor:portfolio_result', (data) => {
    setPortfolioAnalysis(data);
    setIsAnalyzing(false);
  });
}, [socket]);

const handleAnalyzeRisk = () => {
  setIsAnalyzing(true);
  socket.emit('advisor:portfolio_analysis', {
    positions: getCurrentPositions(),
    account_balance: accountBalance,
    risk_profile: 'conservative',
    language: 'vi'
  });
};
```

---

## Risk Assessment & Mitigation

### Technical Risks

| Risk | Severity | Mitigation |
|------|----------|-----------|
| LLM API failure (Claude/DeepSeek down) | Medium | Fallback to technical-only analysis, graceful error display |
| Socket.IO disconnection during analysis | Low | Reconnection logic exists, cache result server-side |
| Position data inaccuracy | Medium | Validate input data, clear UI instructions for manual entry |
| LLM hallucination (bad advice) | High | Strict prompt engineering, disclaimer text, human review emphasis |
| Cost overrun from repeated analysis | Low | Semantic caching (75% reduction), rate limiting (max 1 call/5s) |

### User Experience Risks

| Risk | Severity | Mitigation |
|------|----------|-----------|
| 2-4s latency unacceptable | Low | Loading spinner, optimistic UI, cache hit <500ms |
| LLM advice too complex/unclear | Medium | Prompt engineering for clarity, examples, simple language |
| Users over-rely on AI, ignore own judgment | High | Clear disclaimers, "advisory only" messaging, emphasize user responsibility |

---

## Success Metrics

### Technical Metrics
- LLM analysis latency: <3s (95th percentile)
- Cache hit rate: >60% (within 5-minute window)
- Socket.IO connection stability: >99.5% uptime
- Error rate: <1% (LLM failures handled gracefully)

### Business Metrics
- User engagement: % of portfolio page visitors who click "Analyze Risk"
- Capital preservation impact: Track if users act on LLM advice (reduce positions)
- Cost efficiency: LLM costs <$20/month (1000 analyses with caching)

### User Experience Metrics
- Time-to-insight: <5s from button click to actionable advice
- Advice clarity: User survey rating >4/5
- Perceived value: % of users who find advice useful for capital preservation

---

## Implementation Phases

### Phase 1: Backend Portfolio Analysis (2 days)
- [ ] Create `advisor:portfolio_analysis` event handler
- [ ] Implement `process_portfolio_analysis` in processor
- [ ] Engineer capital preservation LLM prompts (Vietnamese/English)
- [ ] Add portfolio analysis caching to Redis
- [ ] Write unit tests for multi-position aggregation
- [ ] Test with sample portfolio data

### Phase 2: Frontend Integration (1 day)
- [ ] Create `AIRiskAdvisoryPanel` component
- [ ] Enhance `RiskManagementPanel` with "Analyze" button
- [ ] Implement Socket.IO event subscriptions
- [ ] Add loading/error states
- [ ] Style with existing panel design system
- [ ] Test Socket.IO reconnection handling

### Phase 3: Testing & Refinement (1 day)
- [ ] End-to-end testing with real portfolio scenarios
- [ ] LLM prompt refinement based on output quality
- [ ] Performance optimization (caching, latency)
- [ ] User testing for advice clarity
- [ ] Documentation updates

**Total Estimated Time:** 4 days

---

## Alternative Considerations (Future)

### If Requirements Change Later

**If user wants proactive alerts:**
- Add threshold-based monitoring task
- Socket.IO push when risk limits exceeded
- Requires persistent position tracking

**If user wants automated position management:**
- CRITICAL: Requires explicit user confirmation for any trade actions
- Never auto-close positions without consent (legal/ethical)
- Implement "suggested action" workflow with approval step

**If cost becomes issue:**
- Switch to smaller LLM (Haiku instead of Sonnet)
- Increase cache TTL to 10-15 minutes
- Batch multiple analyses in single LLM call

---

## Dependencies & Prerequisites

### Existing Infrastructure (Ready)
- ✅ Socket.IO server (port 8000)
- ✅ Claude/DeepSeek LLM integration
- ✅ Redis caching with semantic cache
- ✅ Technical analysis engine
- ✅ Frontend Socket.IO context

### Missing Infrastructure (Need to build/clarify)
- ⚠️ Position data source: Where do current positions come from?
  - Option A: MT5 terminal integration (requires new data fetcher)
  - Option B: Manual user input (simpler, user enters positions)
  - **Recommendation:** Start with Option B (manual input), migrate to Option A later
- ⚠️ Account balance tracking: Real-time or user-provided?
  - **Recommendation:** User-provided for MVP, real-time later

---

## Open Questions

1. **Position Data Source:** Should we integrate MT5 for automatic position fetching, or require manual input?
   - **Recommendation:** Manual input for MVP (faster, simpler)

2. **Real-time Risk Metrics Stream:** Should backend push risk exposure/drawdown updates every 5-10s, or only when user refreshes?
   - **Recommendation:** Push every 10s (minimal complexity, better UX)

3. **Multi-Language Support:** User selected Vietnamese, but should English be available?
   - **Recommendation:** Support both (existing advisor supports vi/en)

4. **Risk Profile Storage:** Should user risk profile (conservative/moderate/aggressive) persist, or ask each time?
   - **Recommendation:** Store in localStorage, allow override per analysis

---

## Next Steps

1. **User Decision:** Proceed with Approach 2 (Hybrid Static + On-Demand)?
2. **Clarify:** Position data source (manual vs MT5 integration)?
3. **Create Implementation Plan:** Detailed task breakdown with `/plan` command?

---

## Final Decisions

1. ✅ **Position Data Source:** Manual input via form (MVP approach, can migrate to MT5 later)
2. ✅ **Real-time Metrics:** 10-second push updates for risk exposure/drawdown gauges
3. ✅ **Risk Profile:** Store in localStorage with per-analysis override option
4. ✅ **Implementation:** Proceeding with detailed implementation plan creation

## Unresolved Questions

None - all decisions finalized with user.
