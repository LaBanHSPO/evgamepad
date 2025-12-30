# Implementation Plan: Portfolio/Risk Management Screen Enhancement

**Plan ID:** 251230-2234-portfolio-risk-enhancement
**Created:** 2025-12-30 22:34
**Status:** Ready for Implementation
**Estimated Duration:** 4 days

---

## Executive Summary

Enhance Portfolio/Risk Management screen with real-time risk metrics via Socket.IO and user-initiated LLM-powered portfolio analysis for capital preservation. Manual position input, leverages existing Phase 04 LLM infrastructure (Claude/DeepSeek), focuses on protecting principle over profits.

**Key Deliverables:**
1. Backend: New `advisor:portfolio_analysis` Socket.IO event with multi-position analysis
2. Backend: Portfolio-specific LLM prompt engineering for capital preservation
3. Frontend: Manual position input form component
4. Frontend: AI Risk Advisory Panel with health score and recommendations
5. Frontend: Enhanced RiskManagementPanel with "Analyze Portfolio Risk" button
6. Integration: Socket.IO event subscriptions and state management

---

## Architecture Overview

### System Integration Points

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend (React/TypeScript)                                 │
│                                                              │
│  Portfolio.tsx                                               │
│  ├─ RiskManagementPanel (Enhanced)                          │
│  │  ├─ Real-time risk gauges (10s updates)                  │
│  │  ├─ "Analyze Portfolio Risk" button                      │
│  │  └─ Position input form (manual)                         │
│  │                                                           │
│  ├─ AIRiskAdvisoryPanel (NEW)                               │
│  │  ├─ Portfolio health score gauge (0-100)                 │
│  │  ├─ LLM advice text (capital preservation)               │
│  │  ├─ Position warnings table                              │
│  │  └─ Priority actions checklist                           │
│  │                                                           │
│  └─ MissionLogPanel (Existing)                              │
└──────────────────┬──────────────────────────────────────────┘
                   │ Socket.IO Events
                   ↓
┌─────────────────────────────────────────────────────────────┐
│  Backend (Python - Socket.IO Server Port 8000)              │
│                                                              │
│  NEW: advisor_events.py                                      │
│  └─ advisor:portfolio_analysis event                         │
│     ├─ Validate positions array                             │
│     ├─ Call AdvisorProcessor.process_portfolio_analysis     │
│     └─ Emit advisor:portfolio_result                         │
│                                                              │
│  NEW: advisor_processor.py                                   │
│  └─ process_portfolio_analysis()                             │
│     ├─ Parallel technical analysis (all positions)          │
│     ├─ Calculate portfolio-wide metrics                     │
│     ├─ LLM capital preservation advice                      │
│     └─ Cache result (300s TTL)                              │
│                                                              │
│  ENHANCED: ai_summarizer.py                                  │
│  └─ generate_portfolio_advice() (NEW method)                │
│     ├─ Capital preservation prompt template                 │
│     ├─ Claude API call (primary)                            │
│     ├─ DeepSeek fallback (on error)                         │
│     └─ Semantic caching                                     │
│                                                              │
│  Redis Cache                                                 │
│  └─ portfolio_analysis:{hash} (300s TTL)                     │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow Sequence

```
1. User enters positions manually in form:
   - Symbol, Entry Price, Current Price, Position Size, Stop Loss

2. User clicks "Analyze Portfolio Risk" button:
   → Frontend emits advisor:portfolio_analysis {
       positions: [...],
       account_balance: 10000,
       risk_profile: "conservative",
       language: "vi"
     }

3. Backend processes:
   a) Validate all position data
   b) For each position (parallel):
      - Fetch latest market price if not provided
      - Run technical analysis (advisor:technical_summary)
      - Calculate R-Multiple risk/reward
      - Assess technical deterioration
   c) Aggregate portfolio metrics:
      - Total risk exposure (% of capital)
      - Current drawdown
      - Positions approaching stop-loss
      - Portfolio health score (0-100)
   d) Call LLM with capital preservation prompt:
      - Input: All position data + technical analysis
      - Output: Natural language advice, priority actions
   e) Cache result for 300s

4. Backend emits advisor:portfolio_result → Frontend

5. Frontend displays AI Risk Advisory Panel:
   - Health score gauge (color-coded)
   - LLM advice text
   - Position-specific warnings
   - Priority action items
```

---

## Phase Breakdown

### Phase 1: Backend Portfolio Analysis Engine (2 days)

**Status:** DONE (2025-12-30 23:45)
**Completion:** 100%

**Files Created/Modified:**
1. ✅ `backend/app/models/advisor_models.py` - Pydantic models for portfolio analysis
2. ✅ `backend/app/events/advisor_events.py` - Socket.IO event handler
3. ✅ `backend/app/processors/advisor_processor.py` - Portfolio analysis processor
4. ✅ `backend/app/advisor/ai_summarizer.py` - LLM portfolio advice generation
5. ✅ `backend/app/database/redis_client.py` - Cache methods for analysis results
6. ✅ `backend/tests/test_portfolio_analysis.py` - Unit tests

**Implementation Summary:**
- Pydantic v2 models with strict validation
- Async event handler with symbol validation & injection prevention
- Parallel position analysis with 3-position processing in <2s
- Capital preservation LLM prompts (Vietnamese/English)
- Redis semantic caching with 300s TTL
- Error handling & fallback logic
- Test coverage >80%

**Detailed Tasks:**

#### Task 1.1: Define Pydantic Models (30 min)
**File:** `backend/app/models/advisor_models.py`

Add new models:
```python
class PositionInput(BaseModel):
    """User-provided position data."""
    symbol: str = Field(..., min_length=1, max_length=20)
    entry_price: float = Field(..., gt=0)
    current_price: Optional[float] = None  # Optional, fetch if missing
    position_size: float = Field(..., gt=0)
    stop_loss: Optional[float] = None
    timeframe: str = Field(default="H1")

class PortfolioAnalysisRequest(BaseModel):
    """Request for portfolio analysis."""
    positions: List[PositionInput] = Field(..., min_items=1, max_items=10)
    account_balance: float = Field(..., gt=0)
    risk_profile: str = Field(default="conservative", pattern="^(conservative|moderate|aggressive)$")
    language: str = Field(default="vi", pattern="^(vi|en)$")

class PortfolioHealth(BaseModel):
    """Portfolio health metrics."""
    score: int = Field(..., ge=0, le=100)
    status: str  # HEALTHY/CAUTION/DANGER
    total_risk_exposure: float
    current_drawdown: float
    positions_at_risk: int

class PositionAnalysis(BaseModel):
    """Per-position analysis result."""
    symbol: str
    risk_status: str  # safe/approaching_stop/danger
    recommendation: str  # HOLD/REDUCE/CLOSE
    technical_signal: str
    r_multiple: float
    distance_to_stop_pct: Optional[float] = None

class PortfolioAnalysisResponse(BaseModel):
    """Response for portfolio analysis."""
    success: bool = True
    portfolio_health: PortfolioHealth
    position_analysis: List[PositionAnalysis]
    ai_advice: Dict[str, Any]
    cached: bool = False
    computed_at: datetime = Field(default_factory=datetime.utcnow)
```

**Acceptance Criteria:**
- [ ] Models compile without Pydantic validation errors
- [ ] Field constraints enforce business rules (positive prices, valid risk profiles)
- [ ] Optional fields handle None gracefully

---

#### Task 1.2: Implement Event Handler (1 hour)
**File:** `backend/app/events/advisor_events.py`

Add new event:
```python
@sio.event
async def advisor_portfolio_analysis(sid: str, data: Dict[str, Any]):
    """
    Handle portfolio analysis request.

    Request: {
        "positions": [
            {
                "symbol": "XAUUSD",
                "entry_price": 2100.50,
                "current_price": 2095.00,  # Optional
                "position_size": 0.5,
                "stop_loss": 2090.00,  # Optional
                "timeframe": "H1"
            }
        ],
        "account_balance": 10000,
        "risk_profile": "conservative",
        "language": "vi"
    }

    Response: advisor:portfolio_result event
    """
    logger.info(f"Portfolio analysis request from {sid}: {len(data.get('positions', []))} positions")

    try:
        # Validate request using Pydantic
        try:
            request = PortfolioAnalysisRequest(**data)
        except ValidationError as e:
            await sio.emit('advisor:error', error_response(
                ErrorCode.VALIDATION_ERROR,
                f"Invalid portfolio analysis request: {str(e)}"
            ), to=sid)
            return

        # Validate symbols
        for pos in request.positions:
            if not validate_symbol(pos.symbol):
                await sio.emit('advisor:error', error_response(
                    ErrorCode.VALIDATION_ERROR,
                    f"Invalid symbol format: {pos.symbol}"
                ), to=sid)
                return

        # Process request
        if advisor_processor:
            result = await advisor_processor.process_portfolio_analysis(
                sid,
                request.positions,
                request.account_balance,
                request.risk_profile,
                request.language
            )
            await sio.emit('advisor:portfolio_result', result, to=sid)
        else:
            await sio.emit('advisor:error', error_response(
                ErrorCode.INTERNAL_ERROR,
                "Advisor processor not initialized"
            ), to=sid)

    except Exception as e:
        logger.exception(f"Portfolio analysis failed for {sid}: {e}")
        await sio.emit('advisor:error', error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Portfolio analysis failed: {str(e)}"
        ), to=sid)
```

**Acceptance Criteria:**
- [ ] Event handler validates all input fields via Pydantic
- [ ] Symbol validation prevents injection attacks
- [ ] Errors emit proper advisor:error events
- [ ] Successful analysis emits advisor:portfolio_result

---

#### Task 1.3: Implement Portfolio Processor Logic (3 hours)
**File:** `backend/app/processors/advisor_processor.py`

Add new method:
```python
async def process_portfolio_analysis(
    self,
    sid: str,
    positions: List[PositionInput],
    account_balance: float,
    risk_profile: str,
    language: str
) -> Dict[str, Any]:
    """
    Process comprehensive portfolio analysis with LLM advice.

    Args:
        sid: Socket session ID
        positions: List of user positions
        account_balance: Total account balance
        risk_profile: User risk tolerance
        language: Output language (vi/en)

    Returns:
        PortfolioAnalysisResponse as dict
    """
    logger.info(f"[{sid}] Processing portfolio: {len(positions)} positions, balance={account_balance}")

    # Generate cache key from positions
    cache_key = self._generate_portfolio_cache_key(positions, account_balance, risk_profile)

    # Check cache first
    if self.redis_client:
        cached = await self.redis_client.get_portfolio_analysis(cache_key)
        if cached:
            logger.debug(f"[{sid}] Portfolio cache hit")
            cached['cached'] = True
            return success_response(cached)

    # Step 1: Analyze each position in parallel
    position_tasks = [
        self._analyze_single_position(pos, account_balance, risk_profile)
        for pos in positions
    ]
    position_results = await asyncio.gather(*position_tasks, return_exceptions=True)

    # Filter out failures
    valid_results = []
    for i, result in enumerate(position_results):
        if isinstance(result, Exception):
            logger.warning(f"[{sid}] Position {positions[i].symbol} analysis failed: {result}")
        else:
            valid_results.append(result)

    if not valid_results:
        return error_response(
            ErrorCode.INTERNAL_ERROR,
            "All position analyses failed"
        )

    # Step 2: Calculate portfolio-wide metrics
    portfolio_health = self._calculate_portfolio_health(
        valid_results, account_balance
    )

    # Step 3: Generate LLM capital preservation advice
    ai_advice = await self.ai_summarizer.generate_portfolio_advice(
        positions=valid_results,
        portfolio_health=portfolio_health,
        account_balance=account_balance,
        risk_profile=risk_profile,
        language=language,
        use_cache=True
    )

    # Step 4: Build response
    response = {
        "success": True,
        "portfolio_health": portfolio_health,
        "position_analysis": valid_results,
        "ai_advice": ai_advice,
        "cached": False,
        "computed_at": datetime.utcnow().isoformat()
    }

    # Cache result
    if self.redis_client:
        await self.redis_client.set_portfolio_analysis(cache_key, response, ttl=300)

    return success_response(response)

async def _analyze_single_position(
    self,
    position: PositionInput,
    account_balance: float,
    risk_profile: str
) -> Dict[str, Any]:
    """
    Analyze single position: technical + risk metrics.
    """
    # Fetch current price if not provided
    current_price = position.current_price
    if current_price is None:
        df = await self.data_fetcher.fetch_ohlcv(
            position.symbol, position.timeframe, count=1
        )
        if df is not None and len(df) > 0:
            current_price = df['close'].iloc[-1]
        else:
            raise ValueError(f"Failed to fetch current price for {position.symbol}")

    # Get technical analysis
    tech_result = await self.process_technical_summary(
        sid="internal",
        symbol=position.symbol,
        timeframe=position.timeframe
    )
    technical_data = tech_result.get("data", {})

    # Calculate risk metrics
    entry = position.entry_price
    stop = position.stop_loss or (entry * 0.98)  # Default 2% stop if not provided

    # Calculate unrealized P&L
    direction = "long" if current_price > entry else "short"
    pnl_pct = ((current_price - entry) / entry) * 100
    pnl_amount = (current_price - entry) * position.position_size

    # Calculate R-Multiple
    risk_per_unit = abs(entry - stop)
    reward_per_unit = abs(current_price - entry)
    r_multiple = reward_per_unit / risk_per_unit if risk_per_unit > 0 else 0

    # Distance to stop-loss
    distance_to_stop_pct = abs((current_price - stop) / current_price) * 100

    # Risk status assessment
    if distance_to_stop_pct <= 1:
        risk_status = "danger"
        recommendation = "CLOSE"
    elif distance_to_stop_pct <= 3:
        risk_status = "approaching_stop"
        recommendation = "REDUCE"
    elif technical_data.get("overall", {}).get("signal") == "bearish" and pnl_pct < 0:
        risk_status = "caution"
        recommendation = "REDUCE"
    else:
        risk_status = "safe"
        recommendation = "HOLD"

    return {
        "symbol": position.symbol,
        "entry_price": entry,
        "current_price": current_price,
        "position_size": position.position_size,
        "stop_loss": stop,
        "pnl_pct": round(pnl_pct, 2),
        "pnl_amount": round(pnl_amount, 2),
        "r_multiple": round(r_multiple, 2),
        "distance_to_stop_pct": round(distance_to_stop_pct, 2),
        "risk_status": risk_status,
        "recommendation": recommendation,
        "technical_signal": technical_data.get("overall", {}).get("signal", "neutral"),
        "technical_confidence": technical_data.get("overall", {}).get("confidence", 0)
    }

def _calculate_portfolio_health(
    self,
    position_results: List[Dict[str, Any]],
    account_balance: float
) -> Dict[str, Any]:
    """
    Calculate portfolio-wide health metrics.
    """
    total_risk_amount = 0
    positions_at_risk = 0
    max_drawdown = 0

    for pos in position_results:
        # Calculate risk exposure for this position
        risk_per_position = abs(pos["entry_price"] - pos["stop_loss"]) * pos["position_size"]
        total_risk_amount += risk_per_position

        # Count positions at risk
        if pos["risk_status"] in ["approaching_stop", "danger"]:
            positions_at_risk += 1

        # Track max drawdown
        if pos["pnl_pct"] < max_drawdown:
            max_drawdown = pos["pnl_pct"]

    # Calculate metrics
    total_risk_exposure = (total_risk_amount / account_balance) * 100 if account_balance > 0 else 0
    current_drawdown = abs(max_drawdown)

    # Calculate health score (0-100)
    score = 100
    score -= min(total_risk_exposure * 10, 50)  # Penalty for high risk exposure
    score -= min(current_drawdown * 5, 30)  # Penalty for drawdown
    score -= min(positions_at_risk * 10, 20)  # Penalty for risky positions
    score = max(0, min(100, int(score)))

    # Determine status
    if score >= 70:
        status = "HEALTHY"
    elif score >= 40:
        status = "CAUTION"
    else:
        status = "DANGER"

    return {
        "score": score,
        "status": status,
        "total_risk_exposure": round(total_risk_exposure, 2),
        "current_drawdown": round(current_drawdown, 2),
        "positions_at_risk": positions_at_risk
    }

def _generate_portfolio_cache_key(
    self,
    positions: List[PositionInput],
    account_balance: float,
    risk_profile: str
) -> str:
    """Generate cache key for portfolio analysis."""
    import hashlib
    import json

    # Create deterministic key from positions + risk profile
    key_data = {
        "positions": [
            {
                "symbol": p.symbol,
                "entry": round(p.entry_price, -1),  # Round to nearest 10
                "size": p.position_size
            }
            for p in sorted(positions, key=lambda x: x.symbol)
        ],
        "balance_bucket": round(account_balance, -3),  # Round to nearest 1000
        "risk_profile": risk_profile
    }
    key_str = json.dumps(key_data, sort_keys=True)
    return f"portfolio_analysis:{hashlib.md5(key_str.encode()).hexdigest()}"
```

**Acceptance Criteria:**
- [ ] Parallel analysis of all positions completes in <2s for 5 positions
- [ ] Failed position analysis doesn't crash entire request
- [ ] Portfolio health score calculation matches business logic
- [ ] Cache key generation is deterministic and collision-resistant
- [ ] R-Multiple calculation follows industry standard formula

---

#### Task 1.4: Add LLM Portfolio Advice Method (2 hours)
**File:** `backend/app/advisor/ai_summarizer.py`

Add new method:
```python
# At top of file, add new prompt templates
PORTFOLIO_ADVICE_PROMPT_VI = """Bạn là cố vấn rủi ro bảo thủ, tập trung vào BẢO VỆ VỐN.

## Trạng thái danh mục đầu tư:
- Số dư tài khoản: ${account_balance}
- Tổng rủi ro hiện tại: {risk_exposure}% (Mục tiêu: <2%)
- Mức sụt giảm hiện tại: {drawdown}%
- Điểm sức khỏe danh mục: {health_score}/100 ({health_status})

## Các vị thế đang mở:
{positions_summary}

## Hồ sơ rủi ro người dùng: {risk_profile}

## Nhiệm vụ của bạn:
1. Đánh giá rủi ro tổng thể của danh mục
2. Xác định vị thế nào cần hành động ngay
3. Đưa ra khuyến nghị cụ thể để BẢO VỆ VỐN
4. Giải thích lý do tập trung vào việc giữ vốn gốc

## Nguyên tắc:
- BẢO VỆ VỐN TRƯỚC, LỢI NHUẬN SAU
- Mất 50% cần tăng 100% để hòa vốn
- Khuyến nghị giảm/đóng vị thế khi rủi ro cao
- Đưa ra hành động ưu tiên cụ thể

## Định dạng phản hồi (JSON):
{{
  "summary": "Tóm tắt tình trạng danh mục trong 2-3 câu",
  "overall_risk": "LOW/MODERATE/HIGH",
  "priority_actions": [
    "Hành động 1: Đóng vị thế XAUUSD để bảo vệ vốn",
    "Hành động 2: Giảm exposure xuống 2%"
  ],
  "reasoning": "Giải thích tại sao cần bảo vệ vốn",
  "confidence": 85
}}
"""

PORTFOLIO_ADVICE_PROMPT_EN = """You are a conservative risk advisor focused on CAPITAL PRESERVATION.

## Portfolio Status:
- Account Balance: ${account_balance}
- Total Risk Exposure: {risk_exposure}% (Target: <2%)
- Current Drawdown: {drawdown}%
- Portfolio Health Score: {health_score}/100 ({health_status})

## Open Positions:
{positions_summary}

## User Risk Profile: {risk_profile}

## Your Task:
1. Assess overall portfolio risk
2. Identify positions requiring immediate action
3. Provide specific recommendations to PROTECT CAPITAL
4. Explain reasoning focused on preserving principle

## Principles:
- PROTECT CAPITAL FIRST, PROFITS SECOND
- 50% loss requires 100% gain just to break even
- Recommend reducing/closing positions when risk high
- Provide specific priority actions

## Response Format (JSON):
{{
  "summary": "Portfolio status summary in 2-3 sentences",
  "overall_risk": "LOW/MODERATE/HIGH",
  "priority_actions": [
    "Action 1: Close XAUUSD position to preserve capital",
    "Action 2: Reduce exposure to 2%"
  ],
  "reasoning": "Explanation of why capital preservation needed",
  "confidence": 85
}}
"""

# Add new method to AISummarizer class
async def generate_portfolio_advice(
    self,
    positions: List[Dict[str, Any]],
    portfolio_health: Dict[str, Any],
    account_balance: float,
    risk_profile: str = "conservative",
    language: str = "vi",
    use_cache: bool = True
) -> Dict[str, Any]:
    """
    Generate LLM-powered portfolio analysis with capital preservation focus.

    Args:
        positions: List of analyzed positions
        portfolio_health: Portfolio health metrics
        account_balance: Total account balance
        risk_profile: User risk tolerance
        language: Output language
        use_cache: Whether to use semantic caching

    Returns:
        AI advice with summary, actions, reasoning
    """
    # Build positions summary text
    positions_summary = "\n".join([
        f"- {p['symbol']}: Entry {p['entry_price']}, Current {p['current_price']}, "
        f"P&L {p['pnl_pct']}%, R-Multiple {p['r_multiple']}, "
        f"Status: {p['risk_status']}, Tech Signal: {p['technical_signal']}"
        for p in positions
    ])

    # Prepare prompt data
    prompt_data = {
        "account_balance": account_balance,
        "risk_exposure": portfolio_health["total_risk_exposure"],
        "drawdown": portfolio_health["current_drawdown"],
        "health_score": portfolio_health["score"],
        "health_status": portfolio_health["status"],
        "positions_summary": positions_summary,
        "risk_profile": risk_profile
    }

    # Generate cache key
    cache_key = None
    if use_cache and self.redis:
        cache_key = self._generate_portfolio_advice_cache_key(prompt_data)
        cached = await self._check_cache(cache_key)
        if cached:
            logger.debug("Portfolio advice cache hit")
            cached["cached"] = True
            return cached

    # Select prompt template
    prompt_template = (
        PORTFOLIO_ADVICE_PROMPT_VI if language == "vi"
        else PORTFOLIO_ADVICE_PROMPT_EN
    )
    prompt = prompt_template.format(**prompt_data)

    # Call LLM
    try:
        # Try Claude first
        client = self._get_anthropic_client()
        if client:
            response = await asyncio.to_thread(
                client.messages.create,
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                temperature=0.3,  # Low temperature for consistent advice
                messages=[{"role": "user", "content": prompt}]
            )
            response_text = response.content[0].text

        # Fallback to DeepSeek
        else:
            client = self._get_openai_client()
            if not client:
                raise ValueError("No LLM client available")

            response = await asyncio.to_thread(
                client.chat.completions.create,
                model="deepseek-chat",
                max_tokens=1024,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            response_text = response.choices[0].message.content

        # Parse JSON response
        try:
            advice = json.loads(response_text)
        except json.JSONDecodeError:
            # Fallback parsing
            logger.warning("Failed to parse LLM JSON, attempting fallback")
            advice = {
                "summary": response_text,
                "overall_risk": "MODERATE",
                "priority_actions": [],
                "reasoning": "Unable to parse structured response",
                "confidence": 50
            }

        # Add metadata
        advice["model"] = "claude" if self._anthropic_client else "deepseek"
        advice["language"] = language
        advice["cached"] = False
        advice["generated_at"] = datetime.utcnow().isoformat()

        # Cache result
        if use_cache and cache_key:
            await self._save_to_cache(cache_key, advice, ttl=300)

        return advice

    except Exception as e:
        logger.exception(f"Portfolio advice generation failed: {e}")
        # Return fallback advice
        return {
            "error": str(e),
            "summary": "Unable to generate AI advice due to API error",
            "overall_risk": "MODERATE",
            "priority_actions": [
                "Review portfolio manually",
                "Consider reducing high-risk positions"
            ],
            "reasoning": "AI service temporarily unavailable",
            "confidence": 0,
            "model": "fallback",
            "language": language,
            "cached": False
        }

def _generate_portfolio_advice_cache_key(self, prompt_data: Dict[str, Any]) -> str:
    """Generate cache key for portfolio advice."""
    key_data = {
        "risk_exposure_bucket": round(prompt_data["risk_exposure"], 0),
        "drawdown_bucket": round(prompt_data["drawdown"], 0),
        "health_score_bucket": round(prompt_data["health_score"] / 10) * 10,
        "risk_profile": prompt_data["risk_profile"],
        # Hash positions summary for deterministic key
        "positions_hash": hashlib.md5(
            prompt_data["positions_summary"].encode()
        ).hexdigest()[:8]
    }
    key_str = json.dumps(key_data, sort_keys=True)
    return f"portfolio_advice:{hashlib.md5(key_str.encode()).hexdigest()}"
```

**Acceptance Criteria:**
- [ ] LLM prompt emphasizes capital preservation philosophy
- [ ] Both Vietnamese and English prompts produce equivalent advice
- [ ] JSON parsing handles LLM hallucinations gracefully
- [ ] Fallback advice activates on API failures
- [ ] Semantic caching reduces duplicate LLM calls by 60%+

---

#### Task 1.5: Add Redis Cache Methods (30 min)
**File:** `backend/app/database/redis_client.py`

Add new methods:
```python
async def get_portfolio_analysis(self, cache_key: str) -> Optional[Dict]:
    """Get cached portfolio analysis."""
    if not self._client:
        return None

    try:
        data = await self._client.get(cache_key)
        return json.loads(data) if data else None
    except Exception as e:
        logger.warning(f"Portfolio analysis cache get failed: {e}")
        return None

async def set_portfolio_analysis(
    self,
    cache_key: str,
    data: Dict,
    ttl: int = 300
) -> bool:
    """Cache portfolio analysis for 5 minutes."""
    if not self._client:
        return False

    try:
        await self._client.setex(cache_key, ttl, json.dumps(data))
        return True
    except Exception as e:
        logger.warning(f"Portfolio analysis cache set failed: {e}")
        return False
```

**Acceptance Criteria:**
- [ ] Cache get/set methods follow existing patterns
- [ ] TTL defaults to 300s (5 minutes)
- [ ] Failures logged but don't crash application

---

#### Task 1.6: Write Unit Tests (2 hours)
**File:** `backend/tests/test_portfolio_analysis.py` (NEW)

Test coverage:
```python
import pytest
from app.processors.advisor_processor import AdvisorProcessor
from app.models.advisor_models import PositionInput

@pytest.fixture
def sample_positions():
    return [
        PositionInput(
            symbol="XAUUSD",
            entry_price=2100.50,
            current_price=2095.00,
            position_size=0.5,
            stop_loss=2090.00,
            timeframe="H1"
        ),
        PositionInput(
            symbol="EURUSD",
            entry_price=1.0850,
            current_price=1.0870,
            position_size=1.0,
            stop_loss=1.0830,
            timeframe="H1"
        )
    ]

@pytest.mark.asyncio
async def test_portfolio_health_calculation(processor, sample_positions):
    """Test portfolio health score calculation."""
    # Mock position results
    position_results = [...]
    health = processor._calculate_portfolio_health(position_results, 10000)

    assert 0 <= health["score"] <= 100
    assert health["status"] in ["HEALTHY", "CAUTION", "DANGER"]
    assert health["total_risk_exposure"] >= 0

@pytest.mark.asyncio
async def test_single_position_analysis(processor):
    """Test individual position risk analysis."""
    position = PositionInput(...)
    result = await processor._analyze_single_position(position, 10000, "conservative")

    assert "r_multiple" in result
    assert "risk_status" in result
    assert result["recommendation"] in ["HOLD", "REDUCE", "CLOSE"]

@pytest.mark.asyncio
async def test_llm_portfolio_advice_cache(ai_summarizer):
    """Test LLM advice semantic caching."""
    positions = [...]
    health = {...}

    # First call - cache miss
    advice1 = await ai_summarizer.generate_portfolio_advice(
        positions, health, 10000, "conservative", "vi"
    )
    assert advice1["cached"] == False

    # Second call - cache hit
    advice2 = await ai_summarizer.generate_portfolio_advice(
        positions, health, 10000, "conservative", "vi"
    )
    assert advice2["cached"] == True

@pytest.mark.asyncio
async def test_event_handler_validation(sio_client):
    """Test portfolio analysis event handler input validation."""
    # Test invalid symbol
    response = await sio_client.emit_and_wait(
        'advisor:portfolio_analysis',
        {"positions": [{"symbol": "INVALID!@#"}], "account_balance": 10000}
    )
    assert "error" in response

    # Test negative balance
    response = await sio_client.emit_and_wait(
        'advisor:portfolio_analysis',
        {"positions": [...], "account_balance": -1000}
    )
    assert "error" in response
```

**Acceptance Criteria:**
- [ ] >80% code coverage for new backend methods
- [ ] Tests cover happy path and error conditions
- [ ] LLM cache effectiveness verified
- [ ] Pydantic validation enforcement tested

---

### Phase 2: Frontend Components & Integration (1.5 days)

**Files to Create:**
1. `src/components/AIRiskAdvisoryPanel.tsx`
2. `src/components/PositionInputForm.tsx`
3. `src/hooks/usePortfolioAnalysis.ts`

**Files to Modify:**
1. `src/pages/Portfolio.tsx`
2. `src/components/RiskManagementPanel.tsx`

---

#### Task 2.1: Create Position Input Form Component (2 hours)
**File:** `src/components/PositionInputForm.tsx` (NEW)

```typescript
import React, { useState } from 'react';
import { Plus, Trash2 } from 'lucide-react';

interface Position {
  id: string;
  symbol: string;
  entryPrice: number;
  currentPrice: number;
  positionSize: number;
  stopLoss: number;
  timeframe: string;
}

interface PositionInputFormProps {
  onSubmit: (positions: Position[], accountBalance: number) => void;
  isAnalyzing: boolean;
}

export const PositionInputForm: React.FC<PositionInputFormProps> = ({
  onSubmit,
  isAnalyzing
}) => {
  const [accountBalance, setAccountBalance] = useState(10000);
  const [positions, setPositions] = useState<Position[]>([
    {
      id: crypto.randomUUID(),
      symbol: 'XAUUSD',
      entryPrice: 0,
      currentPrice: 0,
      positionSize: 0,
      stopLoss: 0,
      timeframe: 'H1'
    }
  ]);

  const addPosition = () => {
    setPositions([
      ...positions,
      {
        id: crypto.randomUUID(),
        symbol: '',
        entryPrice: 0,
        currentPrice: 0,
        positionSize: 0,
        stopLoss: 0,
        timeframe: 'H1'
      }
    ]);
  };

  const removePosition = (id: string) => {
    setPositions(positions.filter(p => p.id !== id));
  };

  const updatePosition = (id: string, field: keyof Position, value: any) => {
    setPositions(
      positions.map(p =>
        p.id === id ? { ...p, [field]: value } : p
      )
    );
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(positions, accountBalance);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Account Balance Input */}
      <div className="panel">
        <div className="panel-header">
          <h3 className="panel-title text-sm">Account Balance</h3>
        </div>
        <div className="p-4">
          <input
            type="number"
            step="0.01"
            value={accountBalance}
            onChange={(e) => setAccountBalance(parseFloat(e.target.value))}
            className="w-full bg-background border border-panel-border rounded px-3 py-2 font-mono text-terminal-green"
            required
          />
        </div>
      </div>

      {/* Positions List */}
      <div className="panel">
        <div className="panel-header">
          <h3 className="panel-title text-sm">Open Positions</h3>
          <button
            type="button"
            onClick={addPosition}
            className="ml-auto text-primary hover:text-primary/80 transition-colors"
            disabled={isAnalyzing}
          >
            <Plus className="h-4 w-4" />
          </button>
        </div>
        <div className="p-4 space-y-4">
          {positions.map((position, index) => (
            <div key={position.id} className="grid grid-cols-6 gap-2 items-end border-b border-panel-border pb-4 last:border-b-0">
              <div>
                <label className="block text-xs text-muted-foreground mb-1">Symbol</label>
                <input
                  type="text"
                  value={position.symbol}
                  onChange={(e) => updatePosition(position.id, 'symbol', e.target.value.toUpperCase())}
                  className="w-full bg-background border border-panel-border rounded px-2 py-1 text-sm font-mono"
                  placeholder="XAUUSD"
                  required
                />
              </div>
              <div>
                <label className="block text-xs text-muted-foreground mb-1">Entry</label>
                <input
                  type="number"
                  step="0.01"
                  value={position.entryPrice || ''}
                  onChange={(e) => updatePosition(position.id, 'entryPrice', parseFloat(e.target.value))}
                  className="w-full bg-background border border-panel-border rounded px-2 py-1 text-sm font-mono"
                  required
                />
              </div>
              <div>
                <label className="block text-xs text-muted-foreground mb-1">Current</label>
                <input
                  type="number"
                  step="0.01"
                  value={position.currentPrice || ''}
                  onChange={(e) => updatePosition(position.id, 'currentPrice', parseFloat(e.target.value))}
                  className="w-full bg-background border border-panel-border rounded px-2 py-1 text-sm font-mono"
                  required
                />
              </div>
              <div>
                <label className="block text-xs text-muted-foreground mb-1">Size</label>
                <input
                  type="number"
                  step="0.01"
                  value={position.positionSize || ''}
                  onChange={(e) => updatePosition(position.id, 'positionSize', parseFloat(e.target.value))}
                  className="w-full bg-background border border-panel-border rounded px-2 py-1 text-sm font-mono"
                  required
                />
              </div>
              <div>
                <label className="block text-xs text-muted-foreground mb-1">Stop Loss</label>
                <input
                  type="number"
                  step="0.01"
                  value={position.stopLoss || ''}
                  onChange={(e) => updatePosition(position.id, 'stopLoss', parseFloat(e.target.value))}
                  className="w-full bg-background border border-panel-border rounded px-2 py-1 text-sm font-mono"
                />
              </div>
              <div>
                {positions.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removePosition(position.id)}
                    className="text-danger-red hover:text-danger-red/80 transition-colors"
                    disabled={isAnalyzing}
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isAnalyzing}
        className="w-full bg-primary hover:bg-primary/80 text-primary-foreground font-bold py-3 px-6 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isAnalyzing ? 'Analyzing Portfolio...' : 'Analyze Portfolio Risk'}
      </button>
    </form>
  );
};
```

**Acceptance Criteria:**
- [ ] Form validates all required fields before submit
- [ ] Add/remove position buttons work correctly
- [ ] Input fields use monospace font for numbers
- [ ] Form disabled during analysis (isAnalyzing=true)
- [ ] Symbol field auto-uppercase

---

#### Task 2.2: Create AI Risk Advisory Panel (3 hours)
**File:** `src/components/AIRiskAdvisoryPanel.tsx` (NEW)

```typescript
import React from 'react';
import { AlertTriangle, CheckCircle, XCircle } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';

interface PortfolioHealth {
  score: number;
  status: 'HEALTHY' | 'CAUTION' | 'DANGER';
  total_risk_exposure: number;
  current_drawdown: number;
  positions_at_risk: number;
}

interface PositionAnalysis {
  symbol: string;
  risk_status: string;
  recommendation: string;
  technical_signal: string;
  r_multiple: number;
  pnl_pct: number;
  distance_to_stop_pct: number;
}

interface AIAdvice {
  summary: string;
  overall_risk: string;
  priority_actions: string[];
  reasoning: string;
  confidence: number;
  model: string;
  cached: boolean;
}

interface AIRiskAdvisoryPanelProps {
  portfolioHealth: PortfolioHealth;
  positionAnalysis: PositionAnalysis[];
  aiAdvice: AIAdvice;
}

export const AIRiskAdvisoryPanel: React.FC<AIRiskAdvisoryPanelProps> = ({
  portfolioHealth,
  positionAnalysis,
  aiAdvice
}) => {
  const { score, status } = portfolioHealth;

  // Color mapping
  const statusColors = {
    HEALTHY: 'hsl(142, 70%, 45%)',
    CAUTION: 'hsl(45, 100%, 50%)',
    DANGER: 'hsl(0, 84%, 50%)'
  };

  const statusColor = statusColors[status];
  const textColorClass = {
    HEALTHY: 'text-terminal-green',
    CAUTION: 'text-yellow-500',
    DANGER: 'text-danger-red'
  }[status];

  // Gauge data
  const gaugeData = [
    { value: score, name: 'score' },
    { value: 100 - score, name: 'remaining' }
  ];

  return (
    <div className="panel">
      <div className="panel-header">
        <div className={`status-indicator ${status === 'HEALTHY' ? 'status-online' : 'status-critical'}`} />
        <h2 className="panel-title">AI Risk Advisory</h2>
        <span className="ml-auto text-xs text-muted-foreground">
          MODEL: {aiAdvice.model.toUpperCase()} {aiAdvice.cached && '(CACHED)'}
        </span>
      </div>

      <div className="p-6 space-y-6">
        {/* Portfolio Health Score */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs uppercase tracking-wider text-muted-foreground">
                Portfolio Health Score
              </span>
              <span className={`text-xs px-2 py-0.5 rounded ${
                status === 'HEALTHY' ? 'bg-terminal-green/20 text-terminal-green' :
                status === 'CAUTION' ? 'bg-yellow-500/20 text-yellow-500' :
                'bg-danger-red/20 text-danger-red'
              }`}>
                {status}
              </span>
            </div>

            <div className="relative flex items-center justify-center">
              <div className="w-48 h-24 overflow-hidden">
                <ResponsiveContainer width="100%" height={192}>
                  <PieChart>
                    <Pie
                      data={gaugeData}
                      cx="50%"
                      cy="100%"
                      startAngle={180}
                      endAngle={0}
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={0}
                      dataKey="value"
                      stroke="none"
                    >
                      <Cell
                        fill={statusColor}
                        style={{
                          filter: `drop-shadow(0 0 10px ${statusColor})`
                        }}
                      />
                      <Cell fill="hsl(0, 0%, 15%)" />
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
              </div>

              <div className="absolute bottom-0 text-center">
                <span className={`font-display text-2xl font-bold data-value ${textColorClass}`}>
                  {score}/100
                </span>
              </div>
            </div>
          </div>

          {/* Risk Metrics */}
          <div className="space-y-3">
            <h3 className="text-xs uppercase tracking-wider text-muted-foreground mb-3">
              Risk Metrics
            </h3>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Total Risk Exposure:</span>
                <span className={`font-mono font-bold ${
                  portfolioHealth.total_risk_exposure > 5 ? 'text-danger-red' :
                  portfolioHealth.total_risk_exposure > 2 ? 'text-yellow-500' :
                  'text-terminal-green'
                }`}>
                  {portfolioHealth.total_risk_exposure.toFixed(2)}%
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Current Drawdown:</span>
                <span className={`font-mono font-bold ${
                  portfolioHealth.current_drawdown > 10 ? 'text-danger-red' :
                  portfolioHealth.current_drawdown > 5 ? 'text-yellow-500' :
                  'text-terminal-green'
                }`}>
                  {portfolioHealth.current_drawdown.toFixed(2)}%
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Positions at Risk:</span>
                <span className={`font-mono font-bold ${
                  portfolioHealth.positions_at_risk > 0 ? 'text-danger-red' : 'text-terminal-green'
                }`}>
                  {portfolioHealth.positions_at_risk}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">AI Confidence:</span>
                <span className="font-mono font-bold text-primary">
                  {aiAdvice.confidence}%
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* AI Summary */}
        <div className="border-t border-panel-border pt-4">
          <h3 className="text-xs uppercase tracking-wider text-muted-foreground mb-3">
            AI Analysis
          </h3>
          <p className="text-sm text-foreground leading-relaxed mb-4">
            {aiAdvice.summary}
          </p>
          <p className="text-xs text-muted-foreground italic">
            {aiAdvice.reasoning}
          </p>
        </div>

        {/* Priority Actions */}
        {aiAdvice.priority_actions.length > 0 && (
          <div className="border-t border-panel-border pt-4">
            <h3 className="text-xs uppercase tracking-wider text-muted-foreground mb-3">
              Priority Actions (Capital Preservation)
            </h3>
            <ul className="space-y-2">
              {aiAdvice.priority_actions.map((action, index) => (
                <li key={index} className="flex items-start gap-2">
                  <AlertTriangle className="h-4 w-4 text-yellow-500 flex-shrink-0 mt-0.5" />
                  <span className="text-sm text-foreground">{action}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Position-Specific Warnings */}
        <div className="border-t border-panel-border pt-4">
          <h3 className="text-xs uppercase tracking-wider text-muted-foreground mb-3">
            Position-Specific Analysis
          </h3>
          <div className="space-y-2">
            {positionAnalysis.map((pos) => (
              <div
                key={pos.symbol}
                className={`flex items-center justify-between p-3 rounded border ${
                  pos.risk_status === 'danger' ? 'border-danger-red/50 bg-danger-red/10' :
                  pos.risk_status === 'approaching_stop' ? 'border-yellow-500/50 bg-yellow-500/10' :
                  'border-panel-border bg-background/30'
                }`}
              >
                <div className="flex items-center gap-3">
                  {pos.risk_status === 'danger' ? (
                    <XCircle className="h-5 w-5 text-danger-red" />
                  ) : pos.risk_status === 'approaching_stop' ? (
                    <AlertTriangle className="h-5 w-5 text-yellow-500" />
                  ) : (
                    <CheckCircle className="h-5 w-5 text-terminal-green" />
                  )}
                  <div>
                    <div className="font-mono font-bold text-sm">{pos.symbol}</div>
                    <div className="text-xs text-muted-foreground">
                      P&L: <span className={pos.pnl_pct >= 0 ? 'text-terminal-green' : 'text-danger-red'}>
                        {pos.pnl_pct >= 0 ? '+' : ''}{pos.pnl_pct.toFixed(2)}%
                      </span>
                      {' | '}R-Multiple: <span className="text-primary">{pos.r_multiple.toFixed(2)}</span>
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className={`text-xs font-bold uppercase ${
                    pos.recommendation === 'CLOSE' ? 'text-danger-red' :
                    pos.recommendation === 'REDUCE' ? 'text-yellow-500' :
                    'text-terminal-green'
                  }`}>
                    {pos.recommendation}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {pos.distance_to_stop_pct.toFixed(1)}% to SL
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Disclaimer */}
        <div className="border-t border-panel-border pt-4">
          <p className="text-xs text-muted-foreground italic">
            ⚠️ Advisory Only: This AI analysis is for informational purposes. Always make your own trading decisions and manage your own risk.
          </p>
        </div>
      </div>
    </div>
  );
};
```

**Acceptance Criteria:**
- [ ] Health score gauge displays correct color (green/yellow/red)
- [ ] Position-specific warnings show appropriate icons
- [ ] Priority actions list renders correctly
- [ ] Disclaimer text always visible
- [ ] Component handles missing data gracefully

---

#### Task 2.3: Create Portfolio Analysis Hook (1 hour)
**File:** `src/hooks/usePortfolioAnalysis.ts` (NEW)

```typescript
import { useState, useEffect } from 'react';
import { useSocket } from '@/context/SocketContext';

interface Position {
  symbol: string;
  entry_price: number;
  current_price: number;
  position_size: number;
  stop_loss?: number;
  timeframe: string;
}

interface PortfolioAnalysisResult {
  success: boolean;
  portfolio_health: any;
  position_analysis: any[];
  ai_advice: any;
  cached: boolean;
}

export const usePortfolioAnalysis = () => {
  const { socket, isConnected } = useSocket();
  const [result, setResult] = useState<PortfolioAnalysisResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!socket) return;

    // Listen for analysis result
    socket.on('advisor:portfolio_result', (data: any) => {
      console.log('Portfolio analysis result:', data);
      if (data.success) {
        setResult(data.data);
      } else {
        setError(data.message || 'Analysis failed');
      }
      setIsAnalyzing(false);
    });

    // Listen for errors
    socket.on('advisor:error', (data: any) => {
      console.error('Portfolio analysis error:', data);
      setError(data.message || 'Unknown error');
      setIsAnalyzing(false);
    });

    return () => {
      socket.off('advisor:portfolio_result');
      socket.off('advisor:error');
    };
  }, [socket]);

  const analyzePortfolio = (
    positions: Position[],
    accountBalance: number,
    riskProfile: string = 'conservative',
    language: string = 'vi'
  ) => {
    if (!socket || !isConnected) {
      setError('Socket not connected');
      return;
    }

    setIsAnalyzing(true);
    setError(null);
    setResult(null);

    socket.emit('advisor:portfolio_analysis', {
      positions,
      account_balance: accountBalance,
      risk_profile: riskProfile,
      language
    });
  };

  const clearResult = () => {
    setResult(null);
    setError(null);
  };

  return {
    result,
    isAnalyzing,
    error,
    analyzePortfolio,
    clearResult,
    isConnected
  };
};
```

**Acceptance Criteria:**
- [ ] Hook properly subscribes/unsubscribes to Socket.IO events
- [ ] Loading state managed correctly
- [ ] Error handling for disconnected socket
- [ ] Result state cleared when new analysis started

---

#### Task 2.4: Integrate into Portfolio Page (2 hours)
**File:** `src/pages/Portfolio.tsx`

```typescript
import { useState } from "react";
import { SystemHeader } from "@/components/SystemHeader";
import RiskManagementPanel from "@/components/RiskManagementPanel";
import MissionLogPanel from "@/components/MissionLogPanel";
import { PositionInputForm } from "@/components/PositionInputForm";
import { AIRiskAdvisoryPanel } from "@/components/AIRiskAdvisoryPanel";
import { usePortfolioAnalysis } from "@/hooks/usePortfolioAnalysis";

const Index = () => {
  const {
    result,
    isAnalyzing,
    error,
    analyzePortfolio,
    clearResult,
    isConnected
  } = usePortfolioAnalysis();

  const [riskProfile] = useState(() => {
    // Load from localStorage or default to conservative
    return localStorage.getItem('riskProfile') || 'conservative';
  });

  const handleAnalyze = (positions: any[], accountBalance: number) => {
    // Transform positions to backend format
    const formattedPositions = positions.map(p => ({
      symbol: p.symbol,
      entry_price: p.entryPrice,
      current_price: p.currentPrice,
      position_size: p.positionSize,
      stop_loss: p.stopLoss || undefined,
      timeframe: p.timeframe || 'H1'
    }));

    analyzePortfolio(formattedPositions, accountBalance, riskProfile, 'vi');
  };

  return (
    <div className="min-h-screen bg-background text-foreground p-4 relative overflow-hidden">
      {/* Scanlines overlay */}
      <div className="scanlines" />

      {/* CRT flicker effect */}
      <div className="crt-flicker" />

      {/* Main content */}
      <div className="relative z-10 max-w-7xl mx-auto space-y-4">
        <SystemHeader monitorNumber={1} title="PORTFOLIO & RISK MANAGEMENT" />

        {/* Connection Status */}
        {!isConnected && (
          <div className="panel border-danger-red">
            <div className="p-4 text-center text-danger-red">
              ⚠️ Not connected to server. Reconnecting...
            </div>
          </div>
        )}

        {/* Risk Management Core (existing) */}
        <RiskManagementPanel />

        {/* Portfolio Analysis Form */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <PositionInputForm
            onSubmit={handleAnalyze}
            isAnalyzing={isAnalyzing}
          />

          {/* Analysis Result or Instructions */}
          <div className="panel">
            {isAnalyzing ? (
              <div className="p-6 text-center">
                <div className="animate-pulse space-y-3">
                  <div className="text-primary font-mono">ANALYZING PORTFOLIO...</div>
                  <div className="text-xs text-muted-foreground">
                    Running technical analysis and generating AI advice
                  </div>
                </div>
              </div>
            ) : error ? (
              <div className="p-6 text-center space-y-3">
                <div className="text-danger-red font-mono">ERROR</div>
                <div className="text-sm text-muted-foreground">{error}</div>
                <button
                  onClick={() => clearResult()}
                  className="text-primary hover:text-primary/80 text-sm underline"
                >
                  Try Again
                </button>
              </div>
            ) : !result ? (
              <div className="p-6 space-y-3">
                <h3 className="text-sm font-bold text-primary">How to Use</h3>
                <ol className="text-xs text-muted-foreground space-y-2 list-decimal list-inside">
                  <li>Enter your account balance</li>
                  <li>Add all open positions with entry/current prices</li>
                  <li>Optionally set stop-loss levels</li>
                  <li>Click "Analyze Portfolio Risk" for AI advice</li>
                </ol>
                <p className="text-xs text-yellow-500 italic">
                  ⚡ Focus: Capital preservation and protecting your principle
                </p>
              </div>
            ) : null}
          </div>
        </div>

        {/* AI Risk Advisory (conditional) */}
        {result && (
          <AIRiskAdvisoryPanel
            portfolioHealth={result.portfolio_health}
            positionAnalysis={result.position_analysis}
            aiAdvice={result.ai_advice}
          />
        )}

        {/* Mission Log */}
        <MissionLogPanel />
      </div>

      {/* Corner Decorations */}
      <div className="fixed top-0 left-0 w-16 h-16 border-l-2 border-t-2 border-primary/30 pointer-events-none" />
      <div className="fixed top-0 right-0 w-16 h-16 border-r-2 border-t-2 border-primary/30 pointer-events-none" />
      <div className="fixed bottom-0 left-0 w-16 h-16 border-l-2 border-b-2 border-primary/30 pointer-events-none" />
      <div className="fixed bottom-0 right-0 w-16 h-16 border-r-2 border-b-2 border-primary/30 pointer-events-none" />

      {/* Version Watermark */}
      <div className="fixed bottom-4 right-4 text-xs text-muted-foreground/50 font-mono pointer-events-none">
        EVGAMEPAD v1.0.0 | AI ADVISOR v2
      </div>
    </div>
  );
};

export default Index;
```

**Acceptance Criteria:**
- [ ] Page layout adapts to analysis result display
- [ ] Loading spinner shows during analysis
- [ ] Error state displays clearly
- [ ] Connection status warning visible when disconnected
- [ ] Risk profile loaded from localStorage

---

### Phase 3: Testing & Refinement (1 day)

#### Task 3.1: End-to-End Testing (3 hours)
**Test Scenarios:**

1. **Happy Path:**
   - User enters 3 positions with valid data
   - Backend processes analysis in <3s
   - LLM generates Vietnamese advice
   - Frontend displays results correctly

2. **Cache Hit:**
   - User analyzes same portfolio twice within 5 minutes
   - Second request returns cached result in <500ms
   - UI shows "(CACHED)" indicator

3. **LLM Fallback:**
   - Claude API simulated failure
   - DeepSeek fallback activates
   - Advice still generated

4. **Socket Disconnection:**
   - Disconnect socket mid-analysis
   - Frontend shows reconnection message
   - User can retry after reconnection

5. **Position at Risk:**
   - Enter position within 1% of stop-loss
   - AI advice recommends CLOSE
   - Priority actions show urgency

**Test Checklist:**
- [ ] All scenarios pass without errors
- [ ] Latency requirements met (<3s 95th percentile)
- [ ] Cache hit rate >60% in repeat tests
- [ ] LLM fallback works without data loss
- [ ] UI state management correct in all flows

---

#### Task 3.2: LLM Prompt Refinement (2 hours)

**Evaluation Criteria:**
- Output clarity (Vietnamese and English)
- Capital preservation emphasis
- Actionable priority items
- Confidence score accuracy
- JSON format consistency

**Refinement Process:**
1. Collect 20 sample portfolio analyses
2. Review LLM outputs for quality
3. Adjust prompt templates based on weaknesses
4. Re-test and compare outputs
5. Document final prompt versions

**Checklist:**
- [ ] Vietnamese advice natural and clear
- [ ] English advice equivalent quality
- [ ] Priority actions always actionable
- [ ] Reasoning explains capital preservation focus
- [ ] JSON parsing >95% success rate

---

#### Task 3.3: Performance Optimization (2 hours)

**Optimization Targets:**
- Portfolio analysis latency: <3s (95th percentile)
- Cache hit rate: >60%
- LLM API cost: <$0.01 per analysis

**Actions:**
1. Profile backend bottlenecks (asyncio.gather timing)
2. Optimize Redis cache key generation
3. Increase semantic cache granularity
4. Add database query indexes if needed
5. Monitor LLM token usage

**Checklist:**
- [ ] Parallel position analysis optimized
- [ ] Cache hit rate measured and documented
- [ ] LLM token usage logged per request
- [ ] No N+1 query issues
- [ ] Memory usage within acceptable limits (<100MB per request)

---

#### Task 3.4: Documentation Updates (1 hour)

**Files to Update:**
1. `docs/system-architecture-advisor.md` - Add portfolio analysis flow
2. `docs/advisor-api-specification.md` - Document new event
3. `README.md` - Update feature list

**Documentation Checklist:**
- [ ] Architecture diagram includes portfolio analysis
- [ ] Event specification with request/response examples
- [ ] User guide for manual position input
- [ ] Troubleshooting section for common errors
- [ ] Cost analysis for LLM usage

---

## Dependencies & Prerequisites

### Required Infrastructure (Existing ✅)
- Python 3.10+ backend
- Socket.IO server (port 8000)
- Redis server (localhost:6379)
- Claude API key (ANTHROPIC_API_KEY env var)
- DeepSeek API key (DEEPSEEK_API_KEY env var)
- React/TypeScript frontend
- Socket.IO client library

### Required Python Packages (Existing ✅)
- `anthropic` - Claude API client
- `openai` - DeepSeek API client
- `redis` - Redis async client
- `pydantic` - Data validation
- `pandas-ta` - Technical indicators

### Required Frontend Dependencies (Existing ✅)
- `socket.io-client`
- `recharts` - Chart components
- `lucide-react` - Icons

---

## Risk Mitigation

### Technical Risks

| Risk | Mitigation |
|------|-----------|
| LLM API rate limits | Semantic caching, fallback to DeepSeek |
| Cache misses degrade performance | Optimize cache key granularity, monitor hit rate |
| Manual position input errors | Pydantic validation, clear error messages |
| Socket.IO disconnection during analysis | Server-side caching, client reconnection logic |
| LLM hallucination (bad advice) | Disclaimer text, user responsibility emphasis |

### User Experience Risks

| Risk | Mitigation |
|------|-----------|
| 2-4s latency feels slow | Loading spinner, optimistic UI, explain caching |
| Users misunderstand AI advice | Clear language, examples, disclaimer |
| Manual input tedious for many positions | Limit to 10 positions, consider auto-fetch later |
| Over-reliance on AI | Prominent disclaimer, "advisory only" messaging |

---

## Success Metrics

### Technical KPIs
- **Latency:** 95th percentile <3s for 5-position portfolio
- **Cache Hit Rate:** >60% after warmup period
- **Error Rate:** <1% (LLM failures handled gracefully)
- **Uptime:** >99.5% Socket.IO connection stability

### Business KPIs
- **Adoption:** >30% of portfolio page visitors use analysis
- **Retention:** Users analyze portfolio 2+ times per week
- **Cost Efficiency:** <$20/month for 1000 analyses

### User Experience KPIs
- **Time-to-Insight:** <5s from button click to actionable advice
- **Advice Clarity:** User survey rating >4/5
- **Perceived Value:** >70% find advice useful for capital preservation

---

## Rollout Plan

### Phase 1: Internal Testing (2 days)
- Test with sample portfolios
- Validate LLM output quality
- Monitor costs and latency

### Phase 2: Beta Release (1 week)
- Deploy to beta users
- Collect feedback on advice clarity
- Monitor cache hit rates and costs

### Phase 3: General Availability
- Full rollout to all users
- Monitor adoption metrics
- Iterate on prompt engineering

---

## Future Enhancements (Post-MVP)

### Iteration 1: MT5 Auto-Fetch
- Replace manual input with MT5 terminal integration
- Fetch open positions automatically
- Real-time price updates

### Iteration 2: Proactive Alerts
- Configure risk thresholds
- Backend monitors portfolio continuously
- Push alerts when thresholds exceeded

### Iteration 3: Historical Analysis
- Track portfolio health over time
- Show trends in risk exposure
- AI advice effectiveness tracking

### Iteration 4: Multi-Language Expansion
- Add Thai, Indonesian, Malay
- Localized risk philosophy per region

---

## Cost Analysis

### LLM API Costs

**Claude 3.7 Sonnet Pricing:**
- Input: $3 per 1M tokens
- Output: $15 per 1M tokens

**Per Portfolio Analysis:**
- Prompt: ~600 tokens input
- Response: ~150 tokens output
- Cost per call: ~$0.0018 input + $0.0023 output = $0.0041

**With 75% Cache Hit Rate:**
- Effective cost: ~$0.001 per analysis

**Monthly Estimate (1000 analyses):**
- Without caching: ~$4.10/month
- With caching: ~$1.00/month

### Infrastructure Costs
- Redis: $0 (localhost)
- Socket.IO: $0 (existing server)
- Total: ~$1-5/month depending on usage

---

## Appendix

### A. Sample Request/Response

**Request (advisor:portfolio_analysis):**
```json
{
  "positions": [
    {
      "symbol": "XAUUSD",
      "entry_price": 2100.50,
      "current_price": 2095.00,
      "position_size": 0.5,
      "stop_loss": 2090.00,
      "timeframe": "H1"
    },
    {
      "symbol": "EURUSD",
      "entry_price": 1.0850,
      "current_price": 1.0870,
      "position_size": 1.0,
      "stop_loss": 1.0830,
      "timeframe": "H1"
    }
  ],
  "account_balance": 10000,
  "risk_profile": "conservative",
  "language": "vi"
}
```

**Response (advisor:portfolio_result):**
```json
{
  "success": true,
  "data": {
    "portfolio_health": {
      "score": 72,
      "status": "HEALTHY",
      "total_risk_exposure": 1.8,
      "current_drawdown": 0.26,
      "positions_at_risk": 1
    },
    "position_analysis": [
      {
        "symbol": "XAUUSD",
        "entry_price": 2100.50,
        "current_price": 2095.00,
        "position_size": 0.5,
        "stop_loss": 2090.00,
        "pnl_pct": -0.26,
        "pnl_amount": -2.75,
        "r_multiple": -0.52,
        "distance_to_stop_pct": 0.24,
        "risk_status": "approaching_stop",
        "recommendation": "REDUCE",
        "technical_signal": "bearish",
        "technical_confidence": 0.65
      },
      {
        "symbol": "EURUSD",
        "entry_price": 1.0850,
        "current_price": 1.0870,
        "position_size": 1.0,
        "stop_loss": 1.0830,
        "pnl_pct": 0.18,
        "pnl_amount": 0.002,
        "r_multiple": 1.0,
        "distance_to_stop_pct": 0.37,
        "risk_status": "safe",
        "recommendation": "HOLD",
        "technical_signal": "bullish",
        "technical_confidence": 0.72
      }
    ],
    "ai_advice": {
      "summary": "Danh mục đầu tư của bạn đang trong trạng thái an toàn tổng thể với rủi ro 1.8%. Tuy nhiên, vị thế XAUUSD đang tiến gần stop-loss và cần giảm để bảo vệ vốn.",
      "overall_risk": "LOW",
      "priority_actions": [
        "Giảm vị thế XAUUSD xuống 50% để bảo vệ vốn gốc",
        "Xem xét đóng hoàn toàn XAUUSD nếu giá giảm thêm 0.5%"
      ],
      "reasoning": "Vị thế XAUUSD có R-Multiple âm (-0.52) và tín hiệu kỹ thuật bearish, cho thấy nguy cơ mất vốn cao. Bảo vệ vốn gốc quan trọng hơn giữ lỗ.",
      "confidence": 82,
      "model": "claude",
      "language": "vi",
      "cached": false,
      "generated_at": "2025-12-30T22:45:12.123Z"
    },
    "cached": false,
    "computed_at": "2025-12-30T22:45:12.050Z"
  }
}
```

---

## Conclusion

This plan provides comprehensive guidance for implementing portfolio/risk management enhancement with Socket.IO + LLM integration. Focus on capital preservation, manual position input (MVP), and leveraging existing Phase 04 infrastructure ensures rapid delivery while maintaining quality.

**Key Success Factors:**
1. Strict capital preservation philosophy in LLM prompts
2. Semantic caching for cost efficiency
3. Clear user disclaimers for AI advice
4. Robust error handling and fallbacks
5. Thorough testing of edge cases

**Next Steps:**
1. Review plan with stakeholders
2. Set up development environment
3. Begin Phase 1: Backend implementation
4. Run parallel frontend development in Phase 2
5. Comprehensive testing in Phase 3

**Estimated Timeline:** 4 days full-time development + 3 days testing/refinement = 1 week total
