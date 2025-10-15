"""
Technical Indicators for Options Trading Analysis

This module implements the core technical indicators used for generating
trading signals. Each indicator includes detailed educational explanations
of the mathematical formulas and trading applications.

Educational Focus:
- Understanding what each indicator measures
- How indicators work together to confirm signals
- Why certain combinations are effective for options trading
- Mathematical foundations with clear explanations
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import RSI_PERIOD, MACD_FAST, MACD_SLOW, MACD_SIGNAL, EMA_PERIODS, VOLUME_MA_PERIOD


class TechnicalIndicators:
    """
    Comprehensive technical analysis toolkit for options trading.
    
    Educational Philosophy:
    - Each indicator is explained with its mathematical foundation
    - Real-world trading applications are highlighted
    - Indicator combinations that work well together are identified
    - Signal strength scoring helps quantify trading opportunities
    """
    
    def __init__(self, data: pd.DataFrame):
        """
        Initialize with price data.
        
        Args:
            data: DataFrame with columns ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        """
        self.data = data.copy()
        self.data['timestamp'] = pd.to_datetime(self.data['timestamp'], unit='ms')
        self.data.set_index('timestamp', inplace=True)
        
        # Ensure we have the required columns
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in self.data.columns:
                raise ValueError(f"Missing required column: {col}")
    
    def calculate_rsi(self, period: int = RSI_PERIOD) -> pd.Series:
        """
        Calculate Relative Strength Index (RSI).
        
        Educational Explanation:
        RSI measures the speed and magnitude of price changes. It oscillates
        between 0 and 100, helping identify overbought (>70) and oversold (<30) conditions.
        
        Mathematical Formula:
        1. Calculate price changes: Change = Close[t] - Close[t-1]
        2. Separate gains and losses: Gain = max(Change, 0), Loss = max(-Change, 0)
        3. Calculate average gain and loss over the period
        4. RSI = 100 - (100 / (1 + RS)) where RS = Average Gain / Average Loss
        
        Trading Applications:
        - RSI < 30: Oversold condition, potential bullish reversal
        - RSI > 70: Overbought condition, potential bearish reversal
        - Divergence: Price makes new high/low but RSI doesn't (reversal signal)
        - Centerline crossovers: RSI crossing 50 can indicate trend changes
        
        Args:
            period: Number of periods for calculation (default 14)
        
        Returns:
            RSI values as pandas Series
        """
        close_prices = self.data['close']
        
        # Calculate price changes
        delta = close_prices.diff()
        
        # Separate gains and losses
        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)
        
        # Calculate average gains and losses using exponential smoothing
        avg_gains = gains.ewm(alpha=1/period, adjust=False).mean()
        avg_losses = losses.ewm(alpha=1/period, adjust=False).mean()
        
        # Calculate relative strength
        rs = avg_gains / avg_losses
        
        # Calculate RSI
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_macd(self, fast: int = MACD_FAST, slow: int = MACD_SLOW, signal: int = MACD_SIGNAL) -> Dict[str, pd.Series]:
        """
        Calculate MACD (Moving Average Convergence Divergence).
        
        Educational Explanation:
        MACD is a trend-following momentum indicator that shows the relationship
        between two moving averages. It consists of three components:
        1. MACD Line: Fast EMA - Slow EMA
        2. Signal Line: EMA of MACD Line
        3. Histogram: MACD Line - Signal Line
        
        Mathematical Formula:
        1. MACD Line = EMA(close, fast) - EMA(close, slow)
        2. Signal Line = EMA(MACD Line, signal)
        3. Histogram = MACD Line - Signal Line
        
        Trading Applications:
        - Bullish Crossover: MACD crosses above Signal Line (buy signal)
        - Bearish Crossover: MACD crosses below Signal Line (sell signal)
        - Zero Line Cross: MACD crosses above/below zero (trend change)
        - Divergence: Price and MACD move in opposite directions
        - Histogram: Shows momentum strength and potential reversals
        
        Args:
            fast: Fast EMA period (default 12)
            slow: Slow EMA period (default 26)
            signal: Signal line EMA period (default 9)
        
        Returns:
            Dictionary with 'macd', 'signal', and 'histogram' Series
        """
        close_prices = self.data['close']
        
        # Calculate EMAs
        ema_fast = close_prices.ewm(span=fast, adjust=False).mean()
        ema_slow = close_prices.ewm(span=slow, adjust=False).mean()
        
        # Calculate MACD line
        macd_line = ema_fast - ema_slow
        
        # Calculate signal line
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        
        # Calculate histogram
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    def calculate_ema(self, period: int) -> pd.Series:
        """
        Calculate Exponential Moving Average (EMA).
        
        Educational Explanation:
        EMA gives more weight to recent prices compared to Simple Moving Average (SMA).
        This makes it more responsive to recent price changes, which is crucial for
        options trading where timing is everything.
        
        Mathematical Formula:
        EMA[t] = α × Price[t] + (1-α) × EMA[t-1]
        where α = 2 / (period + 1)
        
        Trading Applications:
        - Trend Direction: Price above EMA = uptrend, below = downtrend
        - Support/Resistance: EMAs often act as dynamic support/resistance levels
        - Crossovers: Shorter EMA crossing longer EMA indicates trend changes
        - Multiple EMAs: 9, 21, 50 EMAs provide different trend perspectives
        
        Args:
            period: EMA period
        
        Returns:
            EMA values as pandas Series
        """
        return self.data['close'].ewm(span=period, adjust=False).mean()
    
    def calculate_volume_indicators(self) -> Dict[str, pd.Series]:
        """
        Calculate volume-based indicators.
        
        Educational Explanation:
        Volume is often called the "fuel" of price movements. High volume confirms
        the strength of price moves, while low volume suggests weak conviction.
        
        Volume Indicators:
        1. Volume Moving Average: Smoothed volume to identify trends
        2. Volume Ratio: Current volume vs average volume
        3. On-Balance Volume (OBV): Cumulative volume based on price direction
        
        Trading Applications:
        - Volume Confirmation: Price moves with high volume are more reliable
        - Volume Divergence: Price up but volume down = weak move
        - Breakout Confirmation: Volume should increase on breakouts
        - Distribution/Accumulation: OBV shows institutional activity
        
        Returns:
            Dictionary with volume indicators
        """
        volume = self.data['volume']
        close = self.data['close']
        
        # Volume moving average
        volume_ma = volume.rolling(window=VOLUME_MA_PERIOD).mean()
        
        # Volume ratio (current vs average)
        volume_ratio = volume / volume_ma
        
        # On-Balance Volume (OBV)
        obv = pd.Series(index=close.index, dtype=float)
        obv.iloc[0] = volume.iloc[0]
        
        for i in range(1, len(close)):
            if close.iloc[i] > close.iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + volume.iloc[i]
            elif close.iloc[i] < close.iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - volume.iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        
        return {
            'volume_ma': volume_ma,
            'volume_ratio': volume_ratio,
            'obv': obv
        }
    
    def calculate_bollinger_bands(self, period: int = 20, std_dev: float = 2.0) -> Dict[str, pd.Series]:
        """
        Calculate Bollinger Bands.
        
        Educational Explanation:
        Bollinger Bands consist of a middle band (SMA) and two outer bands that are
        standard deviations away from the middle band. They help identify:
        1. Overbought/oversold conditions
        2. Volatility expansion/contraction
        3. Potential reversal points
        
        Mathematical Formula:
        1. Middle Band = SMA(close, period)
        2. Upper Band = Middle Band + (std_dev × Standard Deviation)
        3. Lower Band = Middle Band - (std_dev × Standard Deviation)
        
        Trading Applications:
        - Squeeze: Bands close together = low volatility, potential breakout
        - Expansion: Bands widen = high volatility, potential reversal
        - Bounce: Price touching lower band = potential bounce
        - Breakout: Price breaking upper/lower band = trend continuation
        
        Args:
            period: Period for SMA calculation
            std_dev: Standard deviation multiplier
        
        Returns:
            Dictionary with 'upper', 'middle', 'lower' bands
        """
        close = self.data['close']
        
        # Calculate middle band (SMA)
        middle_band = close.rolling(window=period).mean()
        
        # Calculate standard deviation
        std = close.rolling(window=period).std()
        
        # Calculate upper and lower bands
        upper_band = middle_band + (std * std_dev)
        lower_band = middle_band - (std * std_dev)
        
        return {
            'upper': upper_band,
            'middle': middle_band,
            'lower': lower_band
        }
    
    def calculate_all_indicators(self) -> pd.DataFrame:
        """
        Calculate all technical indicators and return as DataFrame.
        
        Educational Note:
        This method combines all indicators into a single DataFrame for easy analysis.
        The indicators are designed to work together:
        - RSI identifies overbought/oversold conditions
        - MACD confirms trend changes
        - EMAs provide trend direction
        - Volume confirms signal strength
        
        Returns:
            DataFrame with all indicators
        """
        result = self.data.copy()
        
        # Calculate RSI
        result['rsi'] = self.calculate_rsi()
        
        # Calculate MACD
        macd_data = self.calculate_macd()
        result['macd'] = macd_data['macd']
        result['macd_signal'] = macd_data['signal']
        result['macd_histogram'] = macd_data['histogram']
        
        # Calculate EMAs
        for period in EMA_PERIODS:
            result[f'ema_{period}'] = self.calculate_ema(period)
        
        # Calculate volume indicators
        volume_data = self.calculate_volume_indicators()
        result['volume_ma'] = volume_data['volume_ma']
        result['volume_ratio'] = volume_data['volume_ratio']
        result['obv'] = volume_data['obv']
        
        # Calculate Bollinger Bands
        bb_data = self.calculate_bollinger_bands()
        result['bb_upper'] = bb_data['upper']
        result['bb_middle'] = bb_data['middle']
        result['bb_lower'] = bb_data['lower']
        
        return result
    
    def get_latest_values(self) -> Dict:
        """
        Get the most recent indicator values.
        
        Educational Note:
        This method provides the current state of all indicators, which is
        essential for generating real-time trading signals.
        
        Returns:
            Dictionary with latest indicator values
        """
        df = self.calculate_all_indicators()
        latest = df.iloc[-1]
        
        return {
            'price': latest['close'],
            'rsi': latest['rsi'],
            'macd': latest['macd'],
            'macd_signal': latest['macd_signal'],
            'macd_histogram': latest['macd_histogram'],
            'ema_9': latest['ema_9'],
            'ema_21': latest['ema_21'],
            'ema_50': latest['ema_50'],
            'volume_ratio': latest['volume_ratio'],
            'bb_upper': latest['bb_upper'],
            'bb_middle': latest['bb_middle'],
            'bb_lower': latest['bb_lower']
        }
    
    def calculate_signal_strength(self) -> Dict[str, float]:
        """
        Calculate signal strength for different trading directions.
        
        Educational Explanation:
        Signal strength quantifies how confident we can be in a trading signal.
        It combines multiple indicators to create a score from 0-100.
        
        Scoring Methodology:
        - Each indicator contributes to the overall score
        - Confluence (multiple indicators agreeing) increases strength
        - Divergence (indicators disagreeing) decreases strength
        - Volume confirmation is weighted heavily
        
        Returns:
            Dictionary with bullish, bearish, and neutral signal strengths
        """
        df = self.calculate_all_indicators()
        latest = df.iloc[-1]
        
        # Initialize scores
        bullish_score = 0
        bearish_score = 0
        
        # RSI scoring
        rsi = latest['rsi']
        if rsi < 30:
            bullish_score += 25  # Oversold, potential bounce
        elif rsi > 70:
            bearish_score += 25  # Overbought, potential drop
        elif 40 <= rsi <= 60:
            # Neutral RSI, no strong signal
            pass
        
        # MACD scoring
        macd = latest['macd']
        macd_signal = latest['macd_signal']
        if macd > macd_signal:
            bullish_score += 20  # MACD above signal line
        elif macd < macd_signal:
            bearish_score += 20  # MACD below signal line
        
        # EMA scoring
        price = latest['close']
        ema_9 = latest['ema_9']
        ema_21 = latest['ema_21']
        ema_50 = latest['ema_50']
        
        if price > ema_21 and ema_9 > ema_21:
            bullish_score += 20  # Price and short EMA above medium EMA
        elif price < ema_21 and ema_9 < ema_21:
            bearish_score += 20  # Price and short EMA below medium EMA
        
        if price > ema_50:
            bullish_score += 10  # Price above long-term trend
        elif price < ema_50:
            bearish_score += 10  # Price below long-term trend
        
        # Volume scoring
        volume_ratio = latest['volume_ratio']
        if volume_ratio > 1.2:  # Above average volume
            if bullish_score > bearish_score:
                bullish_score += 15  # Volume confirms bullish move
            elif bearish_score > bullish_score:
                bearish_score += 15  # Volume confirms bearish move
        
        # Bollinger Bands scoring
        bb_upper = latest['bb_upper']
        bb_lower = latest['bb_lower']
        if price <= bb_lower:
            bullish_score += 10  # Price at lower band, potential bounce
        elif price >= bb_upper:
            bearish_score += 10  # Price at upper band, potential drop
        
        # Calculate final scores
        total_bullish = min(bullish_score, 100)
        total_bearish = min(bearish_score, 100)
        
        # Determine neutral score
        neutral_score = max(0, 100 - max(total_bullish, total_bearish))
        
        return {
            'bullish': total_bullish,
            'bearish': total_bearish,
            'neutral': neutral_score
        }


# Example usage and testing
if __name__ == "__main__":
    # Create sample data for testing
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    np.random.seed(42)
    
    # Generate sample OHLCV data
    sample_data = pd.DataFrame({
        'timestamp': [int(d.timestamp() * 1000) for d in dates],
        'open': 100 + np.cumsum(np.random.randn(100) * 0.5),
        'high': 100 + np.cumsum(np.random.randn(100) * 0.5) + np.random.rand(100) * 2,
        'low': 100 + np.cumsum(np.random.randn(100) * 0.5) - np.random.rand(100) * 2,
        'close': 100 + np.cumsum(np.random.randn(100) * 0.5),
        'volume': np.random.randint(1000000, 5000000, 100)
    })
    
    # Test the indicators
    indicators = TechnicalIndicators(sample_data)
    
    print("Testing Technical Indicators...")
    print(f"Latest RSI: {indicators.calculate_rsi().iloc[-1]:.2f}")
    
    macd_data = indicators.calculate_macd()
    print(f"Latest MACD: {macd_data['macd'].iloc[-1]:.2f}")
    
    signal_strength = indicators.calculate_signal_strength()
    print(f"Signal Strength: {signal_strength}")
    
    print("Technical indicators test completed successfully!")
