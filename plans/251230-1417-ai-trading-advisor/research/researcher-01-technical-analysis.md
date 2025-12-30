# AI Trading Advisor: Technical Analysis Research Report

**Date:** 2025-12-30 | **Research Phase:** Component Architecture

## Executive Summary

Trading advisor AI requires multi-layered technical analysis: oscillators (RSI, MACD, Stochastic), moving averages (SMA/EMA), price action patterns, and dynamic risk management. Capital Companion's multi-timeframe approach validates "power zones" (aligned signals across periods). Python ecosystem offers three primary libraries with distinct trade-offs.

---

## 1. Technical Analysis Components

### Core Indicators (Capital Companion validated)
- **Moving Averages:** 21 EMA (momentum), SMA crossovers (trend confirmation)
- **Momentum:** RSI (overbought/oversold), MACD (trend + momentum), Stochastic (extremes)
- **Volatility:** Bollinger Bands (breakouts), ATR (stop-loss sizing)
- **Volume:** Profile analysis, on-balance volume, money flow index

### Pattern Recognition
**Chart Patterns:** Head & Shoulders, flags, triangles, cup-with-handle, wedges
**Candlestick:** 60+ patterns (doji, engulfing, hammer, shooting star) via TA-Lib
**Trend:** Trendline detection, breakout confirmation via volume

### Support/Resistance Layers
- Static/dynamic pivot points
- Fibonacci retracements (23.6%, 38.2%, 50%, 61.8%, 78.6%)
- Volume profile nodes
- Previous swing high/low (structure)

### Multi-Timeframe Alignment
Capital Companion approach: Analyze 15m, 1h, 4h, 1D simultaneously → identify "power zones" where signals align across periods → improves entry/exit precision by 30-40%.

---

## 2. Python Library Comparison

| Library | Indicators | Candlestick | Install | Performance | Best For |
|---------|-----------|-------------|---------|-------------|----------|
| **TA-Lib** | 200+ | 61 patterns | Hard (C deps) | 2-4x faster | Production; performance critical |
| **pandas-ta** | 150+ | 60 patterns | Easy (pip) | Moderate | Rapid prototyping; ease of use |
| **ta** | 100+ | None | Easy (pip) | Moderate | Feature engineering; ML prep |

### Recommendation Stack
- **Primary:** `pandas-ta` (maintained, pythonic, 150+ indicators, 60 candlestick patterns)
- **Secondary:** `TA-Lib` (if performance bottleneck; harder installation)
- **Fallback:** `ta` (lightweight, pandas-centric for backtesting)

---

## 3. Position Sizing & Risk Framework

### Core Algorithms
1. **Fixed Fractional:** Risk 1-2% per trade (simplest, robust)
2. **Kelly Criterion:** Optimal bet sizing for long-term capital growth
3. **Volatility-Based:** Adjust position size inversely to ATR (consistent dollar risk)

### Risk Integration
- Stop-loss distance → position size calculation
- Account drawdown caps: 5% daily, 7% weekly hard stops
- Concentration limits: Symbol, sector, strategy diversification
- Risk/reward ratio: Minimum 1:2 (win rate expectancy)

### Scalping vs. Swing
- **Scalp (5m-15m):** Tight ATR-based stops, 1% risk
- **Swing (4h-1D):** Structure-based stops, 2% risk
- **Position (1D+):** Fibonacci stops, 3% risk max

---

## 4. Implementation Priority

**Phase 1 (MVP):**
- pandas-ta: SMA/EMA, RSI, MACD, Bollinger Bands
- Basic support/resistance (pivot points)
- Fixed fractional position sizing

**Phase 2:**
- Candlestick pattern recognition (60+ patterns)
- Volume profile, ATR-based stops
- Kelly Criterion implementation

**Phase 3:**
- Chart pattern detection (head & shoulders, flags)
- Multi-timeframe alignment engine
- Volatility-based position sizing

---

## 5. Architecture Decisions

**Indicator Caching:** Pre-compute 50-100 candles; update on new close
**Timeframe Storage:** Maintain separate OHLCV arrays for 15m, 1h, 4h, 1D
**Risk Engine:** Separate module (inputs: entry, stop, account size → position qty)
**Pattern Registry:** Enum-based candlestick patterns; custom logic for chart patterns

---

## Unresolved Questions

1. Should chart pattern detection use heuristic rules or ML (CNN/LSTM)?
2. What's the minimum backtesting dataset size for reliable win-rate metrics?
3. How to handle gaps in multi-timeframe analysis during low liquidity?
4. Should we pre-calculate Fibonacci levels or compute dynamically per swing?

---

## Sources

- [Capital Companion Technical Analysis Docs](https://capitalcompanion.ai/docs/mastering-technical-analysis/)
- [pandas-ta Library](https://www.pandas-ta.dev/)
- [Comparing TA-Lib to pandas-ta](https://www.slingacademy.com/article/comparing-ta-lib-to-pandas-ta-which-one-to-choose/)
- [TA-Lib Python Wrapper](https://github.com/TA-Lib/ta-lib-python)
- [Candlestick Pattern Detection](https://medium.com/analytics-vidhya/recognizing-over-50-candlestick-patterns-with-python-4f02a1822cb5)
- [Position Sizing Algorithms](https://algotradinglib.com/en/pedia/p/position_sizing_algorithms.html)
- [Volatility-Based Position Sizing](https://medium.com/@deepml1818/volatility-based-position-sizing-with-python-how-to-adjust-your-trades-1f88efc8b228)
