# Phase 3: Risk Analyzer & Position Sizing

## Context Links
- Main Plan: `plan.md`
- Phase 1: `phase-01-technical-analysis-engine.md`
- Phase 2: `phase-02-pattern-recognition-sr.md`
- Research: `research/researcher-01-technical-analysis.md`

---

## Overview

Implement professional risk management calculations: position sizing (fixed fractional, Kelly, ATR-based), stop loss optimization (ATR, S/R-based), risk/reward ratio analysis, and drawdown monitoring. Expose via `advisor:risk_analysis` Socket.IO event.

**Effort:** 6 hours
**Priority:** P1 (critical for responsible trading advice)

---

## Key Insights from Research

1. **Fixed Fractional:** Risk 1-2% per trade (simplest, robust, recommended for most users)
2. **Kelly Criterion:** Optimal bet sizing for long-term growth (requires win rate + avg win/loss)
3. **Volatility-Based:** Adjust position size inversely to ATR (consistent dollar risk across symbols)
4. **Risk Profiles:** Conservative (1%), Moderate (2%), Aggressive (3%) per trade
5. **Drawdown Caps:** 5% daily, 7% weekly hard stops recommended

---

## Requirements

### Functional
- FR1: Calculate position size from entry, stop loss, account size, risk %
- FR2: Implement fixed fractional position sizing
- FR3: Implement Kelly criterion (with user win rate input)
- FR4: Implement ATR-based position sizing
- FR5: Calculate stop loss from ATR or nearest S/R
- FR6: Calculate risk/reward ratio from entry, SL, TP
- FR7: Support 3 risk profiles (conservative, moderate, aggressive)
- FR8: Emit via `advisor:risk_analysis` event

### Non-Functional
- NFR1: Calculation latency < 100ms
- NFR2: All calculations server-side (no trust on client input)
- NFR3: Validate all inputs (prevent negative values, division by zero)

---

## Architecture

### Component Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                    advisor_events.py                           │
│               @sio.event('advisor:risk_analysis')              │
└──────────────────────────┬─────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────────┐
│                   advisor_processor.py                         │
│              AdvisorProcessor.process_risk_analysis()          │
└──────────────────────────┬─────────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
┌─────────────────┐ ┌─────────────────┐ ┌───────────────────┐
│ risk_analyzer   │ │ support_        │ │ technical_        │
│ .py             │ │ resistance.py   │ │ analyzer.py       │
│                 │ │ (Phase 2)       │ │ (Phase 1)         │
│ - fixed_frac()  │ │                 │ │                   │
│ - kelly()       │ │ - get_nearest_  │ │ - get_atr()       │
│ - atr_based()   │ │   support()     │ │                   │
│ - rr_ratio()    │ │                 │ │                   │
└─────────────────┘ └─────────────────┘ └───────────────────┘
```

### Risk Profile Settings

| Profile | Risk per Trade | Max Daily DD | Max Weekly DD | Stop Distance |
|---------|---------------|--------------|---------------|---------------|
| Conservative | 1% | 3% | 5% | 2x ATR |
| Moderate | 2% | 5% | 7% | 1.5x ATR |
| Aggressive | 3% | 7% | 10% | 1x ATR |

---

## Related Code Files

### From Phase 1 & 2 (USE)
- `backend/app/advisor/technical_analyzer.py` - ATR calculation
- `backend/app/advisor/support_resistance.py` - S/R levels for stop placement
- `backend/app/advisor/data_fetcher.py` - OHLCV data

### New (CREATE)
- `backend/app/advisor/risk_analyzer.py`
- `backend/app/models/advisor_models.py` (extend)

---

## Implementation Steps

### Step 1: Risk Analyzer Module (3h)

**File:** `backend/app/advisor/risk_analyzer.py`

```python
"""
Risk management and position sizing calculator.
Implements fixed fractional, Kelly criterion, and ATR-based sizing.
"""
import logging
from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class RiskProfile(Enum):
    """User risk profile levels."""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"

@dataclass
class RiskProfileSettings:
    """Settings for each risk profile."""
    risk_per_trade: float  # Percentage (0.01 = 1%)
    max_daily_drawdown: float
    max_weekly_drawdown: float
    atr_stop_multiplier: float
    min_rr_ratio: float

# Default profile settings
PROFILE_SETTINGS = {
    RiskProfile.CONSERVATIVE: RiskProfileSettings(
        risk_per_trade=0.01,
        max_daily_drawdown=0.03,
        max_weekly_drawdown=0.05,
        atr_stop_multiplier=2.0,
        min_rr_ratio=3.0,
    ),
    RiskProfile.MODERATE: RiskProfileSettings(
        risk_per_trade=0.02,
        max_daily_drawdown=0.05,
        max_weekly_drawdown=0.07,
        atr_stop_multiplier=1.5,
        min_rr_ratio=2.0,
    ),
    RiskProfile.AGGRESSIVE: RiskProfileSettings(
        risk_per_trade=0.03,
        max_daily_drawdown=0.07,
        max_weekly_drawdown=0.10,
        atr_stop_multiplier=1.0,
        min_rr_ratio=1.5,
    ),
}

class RiskAnalyzer:
    """Calculates position sizing and risk metrics."""

    def __init__(self):
        pass

    def get_profile_settings(
        self,
        profile: str
    ) -> RiskProfileSettings:
        """Get settings for a risk profile."""
        try:
            profile_enum = RiskProfile(profile.lower())
            return PROFILE_SETTINGS[profile_enum]
        except (ValueError, KeyError):
            # Default to moderate
            return PROFILE_SETTINGS[RiskProfile.MODERATE]

    def calculate_position_size_fixed_fractional(
        self,
        account_balance: float,
        risk_per_trade: float,
        entry_price: float,
        stop_loss: float,
        pip_value: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculate position size using fixed fractional method.

        Formula: Position Size = (Account * Risk%) / (Entry - SL)

        Args:
            account_balance: Total account balance
            risk_per_trade: Risk percentage (0.02 = 2%)
            entry_price: Planned entry price
            stop_loss: Stop loss price
            pip_value: Value per pip (optional, for forex)

        Returns:
            Dict with position size, risk amount, and details
        """
        if account_balance <= 0:
            return {"error": "Account balance must be positive"}
        if risk_per_trade <= 0 or risk_per_trade > 0.1:
            return {"error": "Risk per trade must be between 0 and 10%"}
        if entry_price <= 0 or stop_loss <= 0:
            return {"error": "Prices must be positive"}

        # Calculate risk amount in dollars
        risk_amount = account_balance * risk_per_trade

        # Calculate stop distance
        stop_distance = abs(entry_price - stop_loss)
        if stop_distance == 0:
            return {"error": "Entry and stop loss cannot be the same"}

        # Position size in units
        # For non-forex: position_size = risk_amount / stop_distance
        # For forex with pip_value: adjust accordingly
        if pip_value and pip_value > 0:
            # Forex calculation (pips to dollars)
            stop_pips = stop_distance / pip_value
            position_size = risk_amount / (stop_pips * pip_value)
        else:
            # Standard calculation
            position_size = risk_amount / stop_distance

        # Determine trade direction
        direction = "long" if entry_price > stop_loss else "short"

        return {
            "method": "fixed_fractional",
            "position_size": round(position_size, 4),
            "risk_amount": round(risk_amount, 2),
            "risk_percentage": risk_per_trade * 100,
            "stop_distance": round(stop_distance, 5),
            "stop_distance_pct": round(stop_distance / entry_price * 100, 3),
            "direction": direction,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
        }

    def calculate_position_size_kelly(
        self,
        account_balance: float,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        entry_price: float,
        stop_loss: float,
        kelly_fraction: float = 0.5
    ) -> Dict[str, Any]:
        """
        Calculate position size using Kelly Criterion.

        Formula: f* = (W * R - L) / R
        Where: W = win rate, L = loss rate, R = avg_win/avg_loss

        Args:
            account_balance: Total account balance
            win_rate: Historical win rate (0-1)
            avg_win: Average winning trade (absolute)
            avg_loss: Average losing trade (absolute)
            entry_price: Planned entry price
            stop_loss: Stop loss price
            kelly_fraction: Fraction of Kelly to use (0.5 = half Kelly)

        Returns:
            Dict with Kelly-optimized position size
        """
        if win_rate <= 0 or win_rate >= 1:
            return {"error": "Win rate must be between 0 and 1"}
        if avg_win <= 0 or avg_loss <= 0:
            return {"error": "Average win/loss must be positive"}
        if kelly_fraction <= 0 or kelly_fraction > 1:
            return {"error": "Kelly fraction must be between 0 and 1"}

        # Calculate Kelly percentage
        loss_rate = 1 - win_rate
        win_loss_ratio = avg_win / avg_loss

        kelly_pct = (win_rate * win_loss_ratio - loss_rate) / win_loss_ratio

        # Apply fraction (half Kelly is common for safety)
        adjusted_kelly = kelly_pct * kelly_fraction

        # Cap at reasonable maximum (10%)
        adjusted_kelly = max(0, min(adjusted_kelly, 0.10))

        # If Kelly is negative, don't trade
        if kelly_pct <= 0:
            return {
                "method": "kelly",
                "position_size": 0,
                "risk_percentage": 0,
                "kelly_raw": round(kelly_pct * 100, 2),
                "recommendation": "Negative expectancy - DO NOT TRADE",
                "reason": "Win rate and win/loss ratio combination has negative expected value",
            }

        # Calculate position size using the Kelly percentage
        risk_amount = account_balance * adjusted_kelly
        stop_distance = abs(entry_price - stop_loss)

        if stop_distance == 0:
            return {"error": "Entry and stop loss cannot be the same"}

        position_size = risk_amount / stop_distance

        return {
            "method": "kelly",
            "position_size": round(position_size, 4),
            "risk_amount": round(risk_amount, 2),
            "risk_percentage": round(adjusted_kelly * 100, 2),
            "kelly_raw": round(kelly_pct * 100, 2),
            "kelly_adjusted": round(adjusted_kelly * 100, 2),
            "kelly_fraction_used": kelly_fraction,
            "win_rate": win_rate,
            "win_loss_ratio": round(win_loss_ratio, 2),
            "expected_value": round((win_rate * avg_win) - (loss_rate * avg_loss), 2),
        }

    def calculate_position_size_atr_based(
        self,
        account_balance: float,
        risk_per_trade: float,
        entry_price: float,
        atr: float,
        atr_multiplier: float = 1.5
    ) -> Dict[str, Any]:
        """
        Calculate position size based on ATR volatility.

        Stop loss is set at ATR * multiplier from entry.
        Position size adjusts to maintain consistent dollar risk.

        Args:
            account_balance: Total account balance
            risk_per_trade: Risk percentage (0.02 = 2%)
            entry_price: Planned entry price
            atr: Average True Range value
            atr_multiplier: Multiple of ATR for stop distance

        Returns:
            Dict with ATR-based position size
        """
        if atr <= 0:
            return {"error": "ATR must be positive"}
        if atr_multiplier <= 0:
            return {"error": "ATR multiplier must be positive"}

        # Calculate stop distance from ATR
        stop_distance = atr * atr_multiplier

        # Calculate risk amount
        risk_amount = account_balance * risk_per_trade

        # Position size
        position_size = risk_amount / stop_distance

        # Calculate stop loss prices (both directions)
        stop_loss_long = entry_price - stop_distance
        stop_loss_short = entry_price + stop_distance

        return {
            "method": "atr_based",
            "position_size": round(position_size, 4),
            "risk_amount": round(risk_amount, 2),
            "risk_percentage": risk_per_trade * 100,
            "atr": round(atr, 5),
            "atr_multiplier": atr_multiplier,
            "stop_distance": round(stop_distance, 5),
            "stop_distance_pct": round(stop_distance / entry_price * 100, 3),
            "stop_loss_long": round(stop_loss_long, 5),
            "stop_loss_short": round(stop_loss_short, 5),
        }

    def calculate_stop_loss(
        self,
        entry_price: float,
        direction: str,
        atr: Optional[float] = None,
        atr_multiplier: float = 1.5,
        nearest_sr: Optional[float] = None,
        sr_buffer_pct: float = 0.002
    ) -> Dict[str, Any]:
        """
        Calculate optimal stop loss placement.

        Priority:
        1. If S/R level provided, use it with buffer
        2. Otherwise use ATR-based stop

        Args:
            entry_price: Entry price
            direction: "long" or "short"
            atr: ATR value (optional)
            atr_multiplier: ATR stop multiplier
            nearest_sr: Nearest S/R level (optional)
            sr_buffer_pct: Buffer beyond S/R level

        Returns:
            Dict with recommended stop loss
        """
        direction = direction.lower()
        if direction not in ["long", "short"]:
            return {"error": "Direction must be 'long' or 'short'"}

        result = {
            "entry_price": entry_price,
            "direction": direction,
            "methods": {},
        }

        # ATR-based stop
        if atr and atr > 0:
            stop_distance = atr * atr_multiplier
            if direction == "long":
                atr_stop = entry_price - stop_distance
            else:
                atr_stop = entry_price + stop_distance

            result["methods"]["atr"] = {
                "stop_loss": round(atr_stop, 5),
                "distance": round(stop_distance, 5),
                "distance_pct": round(stop_distance / entry_price * 100, 3),
            }

        # S/R-based stop
        if nearest_sr and nearest_sr > 0:
            buffer = nearest_sr * sr_buffer_pct
            if direction == "long":
                # Stop below support
                sr_stop = nearest_sr - buffer
            else:
                # Stop above resistance
                sr_stop = nearest_sr + buffer

            sr_distance = abs(entry_price - sr_stop)
            result["methods"]["support_resistance"] = {
                "stop_loss": round(sr_stop, 5),
                "sr_level": round(nearest_sr, 5),
                "buffer": round(buffer, 5),
                "distance": round(sr_distance, 5),
                "distance_pct": round(sr_distance / entry_price * 100, 3),
            }

        # Recommend the tighter stop (but not too tight)
        recommended = None
        min_distance_pct = 0.3  # Minimum 0.3% stop distance

        for method, data in result["methods"].items():
            if data["distance_pct"] < min_distance_pct:
                continue  # Skip too-tight stops
            if recommended is None or data["distance"] < result["methods"].get(recommended, {}).get("distance", float('inf')):
                recommended = method

        if recommended:
            result["recommended"] = {
                "method": recommended,
                "stop_loss": result["methods"][recommended]["stop_loss"],
                "distance_pct": result["methods"][recommended]["distance_pct"],
            }
        else:
            result["recommended"] = None
            result["warning"] = "No valid stop loss found - check inputs"

        return result

    def calculate_risk_reward(
        self,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        direction: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate risk/reward ratio.

        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            direction: "long" or "short" (auto-detected if not provided)

        Returns:
            Dict with R/R ratio and recommendation
        """
        if entry_price <= 0 or stop_loss <= 0 or take_profit <= 0:
            return {"error": "All prices must be positive"}

        # Auto-detect direction
        if direction is None:
            if stop_loss < entry_price and take_profit > entry_price:
                direction = "long"
            elif stop_loss > entry_price and take_profit < entry_price:
                direction = "short"
            else:
                return {"error": "Cannot determine trade direction from prices"}

        # Calculate risk and reward
        if direction == "long":
            risk = entry_price - stop_loss
            reward = take_profit - entry_price
        else:
            risk = stop_loss - entry_price
            reward = entry_price - take_profit

        if risk <= 0:
            return {"error": "Invalid stop loss placement for direction"}
        if reward <= 0:
            return {"error": "Invalid take profit placement for direction"}

        rr_ratio = reward / risk

        # Recommendation based on R/R
        if rr_ratio >= 3:
            recommendation = "excellent"
            advice = "Excellent R/R - high probability setup if signal is strong"
        elif rr_ratio >= 2:
            recommendation = "good"
            advice = "Good R/R - acceptable for most strategies"
        elif rr_ratio >= 1.5:
            recommendation = "acceptable"
            advice = "Acceptable R/R - requires higher win rate to be profitable"
        elif rr_ratio >= 1:
            recommendation = "marginal"
            advice = "Marginal R/R - need 50%+ win rate to break even"
        else:
            recommendation = "poor"
            advice = "Poor R/R - not recommended, consider adjusting targets"

        return {
            "direction": direction,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "risk": round(risk, 5),
            "risk_pct": round(risk / entry_price * 100, 3),
            "reward": round(reward, 5),
            "reward_pct": round(reward / entry_price * 100, 3),
            "rr_ratio": round(rr_ratio, 2),
            "recommendation": recommendation,
            "advice": advice,
            "breakeven_win_rate": round(1 / (1 + rr_ratio) * 100, 1),
        }

    def analyze_full_risk(
        self,
        account_balance: float,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        risk_profile: str = "moderate",
        atr: Optional[float] = None,
        win_rate: Optional[float] = None,
        avg_win: Optional[float] = None,
        avg_loss: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Complete risk analysis combining all methods.

        Args:
            account_balance: Account size
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            risk_profile: conservative, moderate, aggressive
            atr: ATR value (optional)
            win_rate, avg_win, avg_loss: For Kelly calculation (optional)

        Returns:
            Comprehensive risk analysis
        """
        profile = self.get_profile_settings(risk_profile)

        result = {
            "risk_profile": risk_profile,
            "profile_settings": {
                "risk_per_trade": profile.risk_per_trade * 100,
                "max_daily_drawdown": profile.max_daily_drawdown * 100,
                "max_weekly_drawdown": profile.max_weekly_drawdown * 100,
                "min_rr_ratio": profile.min_rr_ratio,
            },
        }

        # Risk/Reward analysis
        rr = self.calculate_risk_reward(entry_price, stop_loss, take_profit)
        result["risk_reward"] = rr

        # Position sizing methods
        result["position_sizing"] = {}

        # Fixed fractional
        ff = self.calculate_position_size_fixed_fractional(
            account_balance, profile.risk_per_trade, entry_price, stop_loss
        )
        result["position_sizing"]["fixed_fractional"] = ff

        # ATR-based (if ATR provided)
        if atr and atr > 0:
            atr_sizing = self.calculate_position_size_atr_based(
                account_balance, profile.risk_per_trade, entry_price, atr, profile.atr_stop_multiplier
            )
            result["position_sizing"]["atr_based"] = atr_sizing

        # Kelly (if stats provided)
        if win_rate and avg_win and avg_loss:
            kelly = self.calculate_position_size_kelly(
                account_balance, win_rate, avg_win, avg_loss, entry_price, stop_loss
            )
            result["position_sizing"]["kelly"] = kelly

        # Recommendation
        recommended_size = ff.get("position_size", 0)
        risk_amount = ff.get("risk_amount", 0)

        # Check R/R minimum
        rr_ratio = rr.get("rr_ratio", 0)
        if rr_ratio < profile.min_rr_ratio:
            result["recommendation"] = {
                "action": "adjust_targets",
                "reason": f"R/R ratio {rr_ratio} below minimum {profile.min_rr_ratio}",
                "suggestion": f"Move TP to achieve at least {profile.min_rr_ratio}:1 R/R",
            }
        else:
            result["recommendation"] = {
                "action": "trade",
                "position_size": round(recommended_size, 4),
                "risk_amount": round(risk_amount, 2),
                "rr_ratio": rr_ratio,
            }

        return result
```

### Step 2: Extend Advisor Events (1h)

**Modify:** `backend/app/events/advisor_events.py`

Add new event:

```python
@sio.event
async def advisor_risk_analysis(sid: str, data: Dict[str, Any]):
    """
    Handle risk analysis request.

    Request: {
        "symbol": "XAUUSD",
        "account_balance": 10000,
        "entry_price": 2100.50,
        "stop_loss": 2095.00,
        "take_profit": 2115.00,
        "risk_profile": "moderate"
    }

    Response: {
        "success": true,
        "risk_reward": {...},
        "position_sizing": {...},
        "recommendation": {...}
    }
    """
    logger.info(f"Risk analysis request from {sid}: {data}")

    try:
        # Validate required fields
        required = ["account_balance", "entry_price", "stop_loss", "take_profit"]
        for field in required:
            if field not in data:
                await sio.emit('advisor:error', error_response(
                    ErrorCode.VALIDATION_ERROR,
                    f"Missing required field: {field}"
                ), to=sid)
                return

        if advisor_processor:
            result = await advisor_processor.process_risk_analysis(
                sid,
                data.get("symbol", ""),
                data["account_balance"],
                data["entry_price"],
                data["stop_loss"],
                data["take_profit"],
                data.get("risk_profile", "moderate"),
                data.get("timeframe", "H1"),
            )
            await sio.emit('advisor:risk_result', result, to=sid)
        else:
            await sio.emit('advisor:error', error_response(
                ErrorCode.INTERNAL_ERROR,
                "Advisor processor not initialized"
            ), to=sid)

    except Exception as e:
        logger.exception(f"Risk analysis failed for {sid}: {e}")
        await sio.emit('advisor:error', error_response(
            ErrorCode.INTERNAL_ERROR,
            str(e)
        ), to=sid)
```

### Step 3: Extend Advisor Processor (1.5h)

**Modify:** `backend/app/processors/advisor_processor.py`

Add to imports:
```python
from app.advisor.risk_analyzer import RiskAnalyzer
```

Add to __init__:
```python
self.risk_analyzer = RiskAnalyzer()
```

Add new method:
```python
async def process_risk_analysis(
    self,
    sid: str,
    symbol: str,
    account_balance: float,
    entry_price: float,
    stop_loss: float,
    take_profit: float,
    risk_profile: str = "moderate",
    timeframe: str = "H1"
) -> Dict[str, Any]:
    """
    Process complete risk analysis request.
    Fetches ATR if symbol provided.
    """
    logger.info(f"[{sid}] Processing risk analysis for {symbol}")

    # Get ATR if symbol provided
    atr = None
    if symbol:
        # Try to get from cache first
        cached = await self.redis_client.get_indicators(symbol, timeframe) if self.redis_client else None
        if cached and "atr" in cached.get("indicators", {}):
            atr = cached["indicators"]["atr"]
        else:
            # Calculate fresh
            df = await self.data_fetcher.fetch_ohlcv(symbol, timeframe, count=50)
            if df is not None:
                indicators = self.analyzer.calculate_indicators(df, ["atr"])
                atr = indicators.get("indicators", {}).get("atr")

    # Run full risk analysis
    result = self.risk_analyzer.analyze_full_risk(
        account_balance=account_balance,
        entry_price=entry_price,
        stop_loss=stop_loss,
        take_profit=take_profit,
        risk_profile=risk_profile,
        atr=atr,
    )

    result["symbol"] = symbol
    result["computed_at"] = datetime.utcnow().isoformat()

    return success_response(result)
```

### Step 4: Update Models (0.5h)

**Modify:** `backend/app/models/advisor_models.py`

Add:

```python
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
```

---

## Todo List

- [ ] Create `backend/app/advisor/risk_analyzer.py`
- [ ] Extend `backend/app/events/advisor_events.py` - add risk_analysis
- [ ] Extend `backend/app/processors/advisor_processor.py` - add risk methods
- [ ] Extend `backend/app/models/advisor_models.py` - add risk models
- [ ] Write unit tests for position sizing calculations
- [ ] Write unit tests for R/R calculations
- [ ] Test Socket.IO event manually
- [ ] Verify calculations against known examples

---

## Success Criteria

- [ ] Fixed fractional calculation matches manual calculation
- [ ] Kelly criterion produces sensible results (negative for losing strategies)
- [ ] ATR-based sizing adjusts properly for volatility
- [ ] R/R ratio calculation correct for both directions
- [ ] Risk profile settings applied correctly
- [ ] Event returns comprehensive analysis

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Division by zero | High | Validate all inputs, check stop != entry |
| Negative position sizes | High | Return error if inputs invalid |
| Over-leveraging | High | Cap Kelly at 10%, require min R/R |
| User misunderstands advice | Medium | Include clear explanations |

---

## Security Considerations

- Validate all numeric inputs (positive, reasonable range)
- Validate risk_profile enum value
- Log all risk calculations for audit
- Rate limit risk analysis requests

---

## Next Steps

After Phase 3 completion:
1. Validate calculations against known examples
2. Test with real trading scenarios
3. Begin Phase 4: AI Summarizer & Recommendations
