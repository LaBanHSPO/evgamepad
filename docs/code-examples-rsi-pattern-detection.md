# RSI Pattern Detection - Code Examples

Complete implementation examples for detecting RSI patterns in Capital Companion.

---

## 1. Basic RSI Calculation (Python)

```python
# backend/indicators/rsi.py
import pandas as pd
import numpy as np

def calculate_rsi(prices: list[float], period: int = 14) -> float:
    """
    Calculate Relative Strength Index (RSI)

    Args:
        prices: List of closing prices (most recent last)
        period: RSI period (default 14)

    Returns:
        RSI value (0-100)

    Example:
        prices = [2100, 2105, 2098, 2110, 2108, ...]
        rsi = calculate_rsi(prices, period=14)
        # Returns: 65.2
    """
    if len(prices) < period + 1:
        raise ValueError(f"Need at least {period + 1} prices, got {len(prices)}")

    # Convert to pandas Series for easier calculation
    df = pd.DataFrame({'close': prices})

    # Calculate price changes
    delta = df['close'].diff()

    # Separate gains and losses
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    # Calculate average gain and loss using SMA
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    # Calculate RS (Relative Strength)
    rs = avg_gain / avg_loss

    # Calculate RSI
    rsi = 100 - (100 / (1 + rs))

    # Return most recent RSI value
    return round(rsi.iloc[-1], 2)


def calculate_rsi_series(prices: list[float], period: int = 14) -> list[float]:
    """
    Calculate RSI for entire price series

    Returns:
        List of RSI values (same length as prices, first 'period' values are NaN)
    """
    df = pd.DataFrame({'close': prices})
    delta = df['close'].diff()

    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi.tolist()
```

---

## 2. RSI Pattern Detection

```python
# backend/patterns/rsi_patterns.py
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class RSISignal:
    """RSI pattern signal"""
    pattern: str  # 'overbought', 'oversold', 'divergence', 'reversal'
    symbol: str
    timeframe: str
    rsi_value: float
    confidence: float  # 0.0 - 1.0
    action: str  # 'buy', 'sell', 'hold', 'warning'
    message: str
    reasoning: List[str]
    timestamp: datetime


class RSIPatternDetector:
    """Detects trading patterns using RSI"""

    def __init__(self, overbought: float = 70, oversold: float = 30):
        self.overbought = overbought
        self.oversold = oversold

    def analyze(
        self,
        symbol: str,
        timeframe: str,
        prices: List[float],
        rsi_period: int = 14
    ) -> Optional[RSISignal]:
        """
        Analyze price data for RSI patterns

        Args:
            symbol: Trading pair (e.g., 'XAUUSD', 'BTCUSD')
            timeframe: Timeframe (e.g., 'H1', 'H4', 'D1')
            prices: Historical closing prices
            rsi_period: RSI calculation period

        Returns:
            RSISignal if pattern detected, None otherwise
        """
        if len(prices) < rsi_period + 10:
            return None

        # Calculate RSI series
        from backend.indicators.rsi import calculate_rsi_series
        rsi_values = calculate_rsi_series(prices, period=rsi_period)

        # Get recent values (remove NaN)
        rsi_values = [v for v in rsi_values if not pd.isna(v)]
        if len(rsi_values) < 5:
            return None

        current_rsi = rsi_values[-1]
        current_price = prices[-1]

        # Pattern 1: Overbought
        if current_rsi > self.overbought:
            return self._detect_overbought(
                symbol, timeframe, current_price, current_rsi, rsi_values
            )

        # Pattern 2: Oversold
        if current_rsi < self.oversold:
            return self._detect_oversold(
                symbol, timeframe, current_price, current_rsi, rsi_values
            )

        # Pattern 3: Bullish Divergence
        divergence = self._detect_bullish_divergence(prices, rsi_values)
        if divergence:
            return divergence

        # Pattern 4: Bearish Divergence
        divergence = self._detect_bearish_divergence(prices, rsi_values)
        if divergence:
            return divergence

        return None

    def _detect_overbought(
        self,
        symbol: str,
        timeframe: str,
        price: float,
        rsi: float,
        rsi_history: List[float]
    ) -> RSISignal:
        """Detect overbought condition"""

        # Calculate confidence based on how extreme the RSI is
        confidence = min((rsi - self.overbought) / (100 - self.overbought), 1.0)
        confidence = round(0.6 + (confidence * 0.3), 2)  # 60-90% range

        # Check if RSI is turning down (reversal signal)
        is_turning = len(rsi_history) >= 3 and rsi_history[-1] < rsi_history[-2]

        reasoning = [
            f"RSI at {rsi:.1f} exceeds overbought threshold ({self.overbought})",
            f"Market may be overextended",
        ]

        if is_turning:
            reasoning.append("RSI starting to decline - reversal signal")
            confidence = min(confidence + 0.1, 1.0)
            action = "sell"
            message = f"{symbol} overbought on {timeframe} - Consider taking profit"
        else:
            action = "warning"
            message = f"{symbol} overbought on {timeframe} - Watch for reversal"

        return RSISignal(
            pattern='overbought',
            symbol=symbol,
            timeframe=timeframe,
            rsi_value=rsi,
            confidence=confidence,
            action=action,
            message=message,
            reasoning=reasoning,
            timestamp=datetime.utcnow()
        )

    def _detect_oversold(
        self,
        symbol: str,
        timeframe: str,
        price: float,
        rsi: float,
        rsi_history: List[float]
    ) -> RSISignal:
        """Detect oversold condition"""

        # Calculate confidence based on how extreme the RSI is
        confidence = min((self.oversold - rsi) / self.oversold, 1.0)
        confidence = round(0.6 + (confidence * 0.3), 2)  # 60-90% range

        # Check if RSI is turning up (reversal signal)
        is_turning = len(rsi_history) >= 3 and rsi_history[-1] > rsi_history[-2]

        reasoning = [
            f"RSI at {rsi:.1f} below oversold threshold ({self.oversold})",
            f"Market may be oversold - potential bounce",
        ]

        if is_turning:
            reasoning.append("RSI starting to rise - reversal signal")
            confidence = min(confidence + 0.1, 1.0)
            action = "buy"
            message = f"{symbol} oversold on {timeframe} - Potential buy opportunity"
        else:
            action = "warning"
            message = f"{symbol} oversold on {timeframe} - Watch for bounce"

        return RSISignal(
            pattern='oversold',
            symbol=symbol,
            timeframe=timeframe,
            rsi_value=rsi,
            confidence=confidence,
            action=action,
            message=message,
            reasoning=reasoning,
            timestamp=datetime.utcnow()
        )

    def _detect_bullish_divergence(
        self,
        prices: List[float],
        rsi_values: List[float]
    ) -> Optional[RSISignal]:
        """
        Detect bullish divergence:
        - Price making lower lows
        - RSI making higher lows
        → Reversal signal (buy)
        """
        if len(prices) < 20 or len(rsi_values) < 20:
            return None

        # Find last two price lows
        price_lows = self._find_lows(prices[-20:])
        rsi_lows = self._find_lows(rsi_values[-20:])

        if len(price_lows) < 2 or len(rsi_lows) < 2:
            return None

        # Check for divergence
        last_price_low = price_lows[-1]
        prev_price_low = price_lows[-2]
        last_rsi_low = rsi_lows[-1]
        prev_rsi_low = rsi_lows[-2]

        # Bullish divergence: price lower, RSI higher
        if (prices[last_price_low] < prices[prev_price_low] and
            rsi_values[last_rsi_low] > rsi_values[prev_rsi_low]):

            return RSISignal(
                pattern='bullish_divergence',
                symbol='',  # Set by caller
                timeframe='',
                rsi_value=rsi_values[-1],
                confidence=0.75,
                action='buy',
                message='Bullish divergence detected - Reversal likely',
                reasoning=[
                    f"Price making lower lows ({prices[prev_price_low]:.2f} → {prices[last_price_low]:.2f})",
                    f"RSI making higher lows ({rsi_values[prev_rsi_low]:.1f} → {rsi_values[last_rsi_low]:.1f})",
                    "Strong reversal signal"
                ],
                timestamp=datetime.utcnow()
            )

        return None

    def _detect_bearish_divergence(
        self,
        prices: List[float],
        rsi_values: List[float]
    ) -> Optional[RSISignal]:
        """
        Detect bearish divergence:
        - Price making higher highs
        - RSI making lower highs
        → Reversal signal (sell)
        """
        if len(prices) < 20 or len(rsi_values) < 20:
            return None

        # Find last two price highs
        price_highs = self._find_highs(prices[-20:])
        rsi_highs = self._find_highs(rsi_values[-20:])

        if len(price_highs) < 2 or len(rsi_highs) < 2:
            return None

        # Check for divergence
        last_price_high = price_highs[-1]
        prev_price_high = price_highs[-2]
        last_rsi_high = rsi_highs[-1]
        prev_rsi_high = rsi_highs[-2]

        # Bearish divergence: price higher, RSI lower
        if (prices[last_price_high] > prices[prev_price_high] and
            rsi_values[last_rsi_high] < rsi_values[prev_rsi_high]):

            return RSISignal(
                pattern='bearish_divergence',
                symbol='',
                timeframe='',
                rsi_value=rsi_values[-1],
                confidence=0.75,
                action='sell',
                message='Bearish divergence detected - Reversal likely',
                reasoning=[
                    f"Price making higher highs ({prices[prev_price_high]:.2f} → {prices[last_price_high]:.2f})",
                    f"RSI making lower highs ({rsi_values[prev_rsi_high]:.1f} → {rsi_values[last_rsi_high]:.1f})",
                    "Strong reversal signal"
                ],
                timestamp=datetime.utcnow()
            )

        return None

    @staticmethod
    def _find_lows(values: List[float]) -> List[int]:
        """Find local lows (valleys) in data"""
        lows = []
        for i in range(2, len(values) - 2):
            if (values[i] < values[i-1] and values[i] < values[i-2] and
                values[i] < values[i+1] and values[i] < values[i+2]):
                lows.append(i)
        return lows

    @staticmethod
    def _find_highs(values: List[float]) -> List[int]:
        """Find local highs (peaks) in data"""
        highs = []
        for i in range(2, len(values) - 2):
            if (values[i] > values[i-1] and values[i] > values[i-2] and
                values[i] > values[i+1] and values[i] > values[i+2]):
                highs.append(i)
        return highs
```

---

## 3. Integration with Capital Companion Backend

```python
# backend/services/pattern_analyzer.py
from typing import List, Dict
from backend.patterns.rsi_patterns import RSIPatternDetector, RSISignal
from backend.data.market_data import get_historical_prices

class PatternAnalyzer:
    """Main service for pattern analysis"""

    def __init__(self):
        self.rsi_detector = RSIPatternDetector(
            overbought=70,
            oversold=30
        )

    async def analyze_symbol(
        self,
        symbol: str,
        timeframes: List[str] = ['H1', 'H4', 'D1']
    ) -> List[RSISignal]:
        """
        Analyze symbol across multiple timeframes

        Args:
            symbol: Trading pair (e.g., 'XAUUSD', 'BTCUSD')
            timeframes: List of timeframes to analyze

        Returns:
            List of detected signals
        """
        signals = []

        for timeframe in timeframes:
            # Fetch historical prices
            prices = await get_historical_prices(symbol, timeframe, limit=100)

            if not prices:
                continue

            # Detect RSI patterns
            signal = self.rsi_detector.analyze(
                symbol=symbol,
                timeframe=timeframe,
                prices=prices
            )

            if signal:
                signal.symbol = symbol
                signal.timeframe = timeframe
                signals.append(signal)

        return signals

    def format_for_voice(self, signal: RSISignal) -> str:
        """
        Format signal for Atlas voice response

        Example output:
        "Gold is overbought on the 4-hour chart with RSI at 78.
         I recommend taking profit. Confidence: 85%"
        """
        symbol_name = {
            'XAUUSD': 'Gold',
            'BTCUSD': 'Bitcoin',
            'ETHUSD': 'Ethereum'
        }.get(signal.symbol, signal.symbol)

        timeframe_name = {
            'H1': '1-hour',
            'H4': '4-hour',
            'D1': 'daily'
        }.get(signal.timeframe, signal.timeframe)

        pattern_desc = {
            'overbought': 'overbought',
            'oversold': 'oversold',
            'bullish_divergence': 'showing bullish divergence',
            'bearish_divergence': 'showing bearish divergence'
        }.get(signal.pattern, signal.pattern)

        confidence_pct = int(signal.confidence * 100)

        return (
            f"{symbol_name} is {pattern_desc} on the {timeframe_name} chart "
            f"with RSI at {signal.rsi_value:.0f}. {signal.message}. "
            f"Confidence: {confidence_pct}%"
        )
```

---

## 4. WebSocket Integration

```python
# backend/websocket/market_alerts.py
from typing import Set
from socketio import AsyncServer
from backend.services.pattern_analyzer import PatternAnalyzer

class MarketAlertService:
    """Send real-time pattern alerts to connected clients"""

    def __init__(self, sio: AsyncServer):
        self.sio = sio
        self.analyzer = PatternAnalyzer()
        self.user_watchlists: Dict[str, Set[str]] = {}

    async def start_monitoring(self):
        """Background task: Check for patterns every 30 seconds"""
        import asyncio

        while True:
            await self.check_all_watchlists()
            await asyncio.sleep(30)

    async def check_all_watchlists(self):
        """Check patterns for all user watchlists"""
        for user_id, symbols in self.user_watchlists.items():
            for symbol in symbols:
                signals = await self.analyzer.analyze_symbol(symbol)

                for signal in signals:
                    await self.send_alert(user_id, signal)

    async def send_alert(self, user_id: str, signal: RSISignal):
        """Send alert to specific user"""

        # Format for voice
        voice_message = self.analyzer.format_for_voice(signal)

        # Send via WebSocket
        await self.sio.emit('alert:new', {
            'id': str(signal.timestamp.timestamp()),
            'type': 'pattern',
            'pattern': signal.pattern,
            'symbol': signal.symbol,
            'timeframe': signal.timeframe,
            'message': signal.message,
            'voiceMessage': voice_message,
            'confidence': signal.confidence,
            'action': signal.action,
            'reasoning': {
                'factors': [
                    {
                        'indicator': 'RSI',
                        'value': signal.rsi_value,
                        'threshold': 70 if signal.pattern == 'overbought' else 30,
                        'sentiment': 'bearish' if signal.action == 'sell' else 'bullish'
                    }
                ],
                'details': signal.reasoning
            },
            'timestamp': signal.timestamp.isoformat()
        }, room=user_id)

    async def subscribe(self, user_id: str, symbols: List[str]):
        """User subscribes to symbol alerts"""
        self.user_watchlists[user_id] = set(symbols)
```

---

## 5. Usage Example

```python
# Example: Analyze Bitcoin for RSI patterns
import asyncio
from backend.services.pattern_analyzer import PatternAnalyzer

async def main():
    analyzer = PatternAnalyzer()

    # Analyze Bitcoin across multiple timeframes
    signals = await analyzer.analyze_symbol(
        symbol='BTCUSD',
        timeframes=['H1', 'H4', 'D1']
    )

    # Print results
    for signal in signals:
        print(f"\n{'='*60}")
        print(f"Pattern: {signal.pattern}")
        print(f"Symbol: {signal.symbol} ({signal.timeframe})")
        print(f"RSI: {signal.rsi_value:.1f}")
        print(f"Action: {signal.action}")
        print(f"Message: {signal.message}")
        print(f"Confidence: {signal.confidence * 100:.0f}%")
        print(f"\nReasoning:")
        for reason in signal.reasoning:
            print(f"  • {reason}")

        # Voice-friendly format
        print(f"\nVoice: {analyzer.format_for_voice(signal)}")

if __name__ == '__main__':
    asyncio.run(main())
```

**Example Output:**
```
============================================================
Pattern: overbought
Symbol: BTCUSD (H4)
RSI: 76.3
Action: sell
Message: BTCUSD overbought on H4 - Consider taking profit
Confidence: 72%

Reasoning:
  • RSI at 76.3 exceeds overbought threshold (70)
  • Market may be overextended
  • RSI starting to decline - reversal signal

Voice: Bitcoin is overbought on the 4-hour chart with RSI at 76.
BTCUSD overbought on H4 - Consider taking profit. Confidence: 72%
```

---

## 6. Testing

```python
# tests/test_rsi_patterns.py
import pytest
from backend.patterns.rsi_patterns import RSIPatternDetector

def test_overbought_detection():
    """Test overbought pattern detection"""
    detector = RSIPatternDetector(overbought=70, oversold=30)

    # Simulate uptrend with high RSI
    prices = [100 + i*0.5 for i in range(50)]  # Steady uptrend

    signal = detector.analyze(
        symbol='BTCUSD',
        timeframe='H4',
        prices=prices
    )

    assert signal is not None
    assert signal.pattern == 'overbought'
    assert signal.rsi_value > 70
    assert signal.confidence >= 0.6

def test_oversold_detection():
    """Test oversold pattern detection"""
    detector = RSIPatternDetector()

    # Simulate downtrend with low RSI
    prices = [100 - i*0.5 for i in range(50)]  # Steady downtrend

    signal = detector.analyze(
        symbol='XAUUSD',
        timeframe='H1',
        prices=prices
    )

    assert signal is not None
    assert signal.pattern == 'oversold'
    assert signal.rsi_value < 30

def test_no_signal_neutral_market():
    """Test that neutral market produces no signal"""
    detector = RSIPatternDetector()

    # Sideways market (RSI around 50)
    prices = [100 + (i % 5) * 0.1 for i in range(50)]

    signal = detector.analyze(
        symbol='BTCUSD',
        timeframe='D1',
        prices=prices
    )

    assert signal is None  # No extreme conditions
```

---

## Next Steps

1. **Install dependencies:**
   ```bash
   pip install pandas numpy
   ```

2. **Integration points:**
   - Connect to TwelveData API for real prices
   - Add to WebSocket server for real-time alerts
   - Integrate with voice system for Atlas responses

3. **Enhancements:**
   - Add MACD, Bollinger Bands patterns
   - Combine multiple indicators
   - Track pattern accuracy over time

---

## Unresolved Questions

1. Should we adjust RSI thresholds per symbol? (Gold vs Crypto volatility differs)
2. How many historical candles needed for reliable divergence detection?
3. Should Atlas auto-execute trades or only alert?
