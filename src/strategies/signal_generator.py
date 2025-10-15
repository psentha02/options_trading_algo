"""
Signal Generation for Options Trading

This module generates trading signals based on technical indicators and market conditions.
It combines multiple indicators to create high-probability trading opportunities.

Educational Focus:
- How to combine indicators for better signal quality
- Understanding different options strategies and when to use them
- Risk management and position sizing considerations
- Market context and volatility analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.indicators.technical import TechnicalIndicators
from config import STRONG_SIGNAL, MODERATE_SIGNAL, WEAK_SIGNAL


class SignalGenerator:
    """
    Generates trading signals based on technical analysis.
    
    Educational Philosophy:
    - Combines multiple indicators to reduce false signals
    - Provides clear explanations for each signal
    - Considers market context and volatility
    - Recommends appropriate options strategies
    """
    
    def __init__(self, price_data: pd.DataFrame):
        """
        Initialize with price data.
        
        Args:
            price_data: DataFrame with OHLCV data
        """
        self.price_data = price_data
        self.indicators = TechnicalIndicators(price_data)
        self.latest_values = self.indicators.get_latest_values()
        self.signal_strength = self.indicators.calculate_signal_strength()
    
    def generate_signals(self) -> Dict:
        """
        Generate comprehensive trading signals.
        
        Educational Note:
        This method analyzes multiple factors to determine the best trading opportunities:
        1. Technical indicator confluence
        2. Market volatility conditions
        3. Trend strength and direction
        4. Volume confirmation
        5. Risk/reward assessment
        
        Returns:
            Dictionary with signal analysis and recommendations
        """
        # Get current market state
        market_state = self._analyze_market_state()
        
        # Generate directional signals
        directional_signals = self._generate_directional_signals()
        
        # Determine optimal strategy
        strategy_recommendation = self._recommend_strategy(market_state, directional_signals)
        
        # Calculate risk metrics
        risk_metrics = self._calculate_risk_metrics()
        
        return {
            'market_state': market_state,
            'directional_signals': directional_signals,
            'strategy_recommendation': strategy_recommendation,
            'risk_metrics': risk_metrics,
            'confidence_level': self._calculate_confidence_level(),
            'timestamp': datetime.now().isoformat()
        }
    
    def _analyze_market_state(self) -> Dict:
        """
        Analyze current market conditions.
        
        Educational Explanation:
        Market state analysis helps determine which options strategies are most appropriate:
        - Trending markets favor directional plays (calls/puts)
        - Range-bound markets favor neutral strategies (iron condors, butterflies)
        - High volatility favors strategies that benefit from volatility expansion
        - Low volatility favors strategies that benefit from volatility contraction
        
        Returns:
            Dictionary with market state analysis
        """
        values = self.latest_values
        
        # Determine trend strength
        trend_strength = self._calculate_trend_strength()
        
        # Analyze volatility
        volatility_state = self._analyze_volatility()
        
        # Determine market regime
        if trend_strength > 70 and volatility_state['level'] == 'high':
            regime = 'trending_volatile'
        elif trend_strength > 70 and volatility_state['level'] == 'low':
            regime = 'trending_calm'
        elif trend_strength < 30 and volatility_state['level'] == 'high':
            regime = 'ranging_volatile'
        elif trend_strength < 30 and volatility_state['level'] == 'low':
            regime = 'ranging_calm'
        else:
            regime = 'mixed'
        
        return {
            'trend_strength': trend_strength,
            'volatility': volatility_state,
            'regime': regime,
            'price_position': self._get_price_position(),
            'volume_profile': self._analyze_volume_profile()
        }
    
    def _calculate_trend_strength(self) -> float:
        """
        Calculate overall trend strength.
        
        Educational Note:
        Trend strength is calculated by analyzing:
        - EMA alignment (9 > 21 > 50 for uptrend, reverse for downtrend)
        - MACD momentum
        - Price position relative to EMAs
        - Volume confirmation
        
        Returns:
            Trend strength score (0-100)
        """
        values = self.latest_values
        score = 0
        
        # EMA alignment scoring
        if values['ema_9'] > values['ema_21'] > values['ema_50']:
            score += 40  # Strong uptrend alignment
        elif values['ema_9'] < values['ema_21'] < values['ema_50']:
            score += 40  # Strong downtrend alignment
        elif values['ema_9'] > values['ema_21']:
            score += 20  # Partial uptrend
        elif values['ema_9'] < values['ema_21']:
            score += 20  # Partial downtrend
        
        # MACD momentum
        if values['macd'] > values['macd_signal']:
            score += 20  # Bullish MACD
        elif values['macd'] < values['macd_signal']:
            score += 20  # Bearish MACD
        
        # Price position
        if values['price'] > values['ema_50']:
            score += 20  # Above long-term trend
        elif values['price'] < values['ema_50']:
            score += 20  # Below long-term trend
        
        # Volume confirmation
        if values['volume_ratio'] > 1.2:
            score += 20  # High volume confirms trend
        
        return min(score, 100)
    
    def _analyze_volatility(self) -> Dict:
        """
        Analyze current volatility conditions.
        
        Educational Note:
        Volatility analysis is crucial for options trading because:
        - High volatility = higher options prices = sell premium strategies
        - Low volatility = lower options prices = buy premium strategies
        - Volatility expansion = good for long options
        - Volatility contraction = good for short options
        
        Returns:
            Dictionary with volatility analysis
        """
        values = self.latest_values
        
        # Calculate Bollinger Band position
        bb_position = (values['price'] - values['bb_lower']) / (values['bb_upper'] - values['bb_lower'])
        
        # Determine volatility level
        if bb_position > 0.8 or bb_position < 0.2:
            volatility_level = 'high'
        elif bb_position > 0.6 or bb_position < 0.4:
            volatility_level = 'medium'
        else:
            volatility_level = 'low'
        
        # RSI volatility indicator
        rsi_volatility = 'high' if values['rsi'] > 70 or values['rsi'] < 30 else 'normal'
        
        return {
            'level': volatility_level,
            'bb_position': bb_position,
            'rsi_volatility': rsi_volatility,
            'recommendation': self._get_volatility_recommendation(volatility_level)
        }
    
    def _get_volatility_recommendation(self, level: str) -> str:
        """
        Get volatility-based strategy recommendations.
        
        Educational Note:
        Different volatility levels favor different strategies:
        - High volatility: Long straddles, short iron condors
        - Low volatility: Short straddles, long iron condors
        - Medium volatility: Directional plays with defined risk
        """
        if level == 'high':
            return "Consider volatility expansion strategies (long straddles, short iron condors)"
        elif level == 'low':
            return "Consider volatility contraction strategies (short straddles, long iron condors)"
        else:
            return "Moderate volatility - directional strategies may be appropriate"
    
    def _get_price_position(self) -> str:
        """
        Determine price position relative to key levels.
        
        Educational Note:
        Price position helps identify:
        - Support/resistance levels
        - Breakout potential
        - Reversal zones
        """
        values = self.latest_values
        
        if values['price'] >= values['bb_upper']:
            return "at_upper_band"
        elif values['price'] <= values['bb_lower']:
            return "at_lower_band"
        elif values['price'] > values['bb_middle']:
            return "above_middle"
        else:
            return "below_middle"
    
    def _analyze_volume_profile(self) -> Dict:
        """
        Analyze volume characteristics.
        
        Educational Note:
        Volume analysis helps confirm signal strength:
        - High volume = strong conviction
        - Low volume = weak conviction
        - Volume trends = institutional interest
        """
        values = self.latest_values
        
        volume_ratio = values['volume_ratio']
        
        if volume_ratio > 1.5:
            volume_state = 'very_high'
        elif volume_ratio > 1.2:
            volume_state = 'high'
        elif volume_ratio > 0.8:
            volume_state = 'normal'
        else:
            volume_state = 'low'
        
        return {
            'state': volume_state,
            'ratio': volume_ratio,
            'confirmation': 'strong' if volume_ratio > 1.2 else 'weak'
        }
    
    def _generate_directional_signals(self) -> Dict:
        """
        Generate directional trading signals.
        
        Educational Note:
        Directional signals are the foundation of options trading:
        - Bullish signals favor call options or bullish spreads
        - Bearish signals favor put options or bearish spreads
        - Signal strength determines position size and strategy complexity
        """
        values = self.latest_values
        signals = self.signal_strength
        
        # Analyze individual indicators
        rsi_signal = self._analyze_rsi_signal(values['rsi'])
        macd_signal = self._analyze_macd_signal(values['macd'], values['macd_signal'])
        ema_signal = self._analyze_ema_signal(values['price'], values['ema_9'], values['ema_21'], values['ema_50'])
        volume_signal = self._analyze_volume_signal(values['volume_ratio'])
        
        # Combine signals
        bullish_confluence = sum([
            rsi_signal['bullish'],
            macd_signal['bullish'],
            ema_signal['bullish'],
            volume_signal['bullish']
        ])
        
        bearish_confluence = sum([
            rsi_signal['bearish'],
            macd_signal['bearish'],
            ema_signal['bearish'],
            volume_signal['bearish']
        ])
        
        return {
            'overall': {
                'bullish_strength': signals['bullish'],
                'bearish_strength': signals['bearish'],
                'neutral_strength': signals['neutral']
            },
            'individual': {
                'rsi': rsi_signal,
                'macd': macd_signal,
                'ema': ema_signal,
                'volume': volume_signal
            },
            'confluence': {
                'bullish_count': bullish_confluence,
                'bearish_count': bearish_confluence,
                'total_indicators': 4
            }
        }
    
    def _analyze_rsi_signal(self, rsi: float) -> Dict:
        """
        Analyze RSI for trading signals.
        
        Educational Note:
        RSI provides momentum signals:
        - RSI < 30: Oversold, potential bullish reversal
        - RSI > 70: Overbought, potential bearish reversal
        - RSI 40-60: Neutral, no strong signal
        """
        if rsi < 30:
            return {'bullish': 1, 'bearish': 0, 'signal': 'oversold_bullish', 'strength': 'strong'}
        elif rsi > 70:
            return {'bullish': 0, 'bearish': 1, 'signal': 'overbought_bearish', 'strength': 'strong'}
        elif rsi < 40:
            return {'bullish': 0.5, 'bearish': 0, 'signal': 'weak_bullish', 'strength': 'weak'}
        elif rsi > 60:
            return {'bullish': 0, 'bearish': 0.5, 'signal': 'weak_bearish', 'strength': 'weak'}
        else:
            return {'bullish': 0, 'bearish': 0, 'signal': 'neutral', 'strength': 'none'}
    
    def _analyze_macd_signal(self, macd: float, signal: float) -> Dict:
        """
        Analyze MACD for trading signals.
        
        Educational Note:
        MACD provides trend and momentum signals:
        - MACD > Signal: Bullish momentum
        - MACD < Signal: Bearish momentum
        - Crossover points are key signals
        """
        if macd > signal:
            return {'bullish': 1, 'bearish': 0, 'signal': 'bullish_crossover', 'strength': 'strong'}
        elif macd < signal:
            return {'bullish': 0, 'bearish': 1, 'signal': 'bearish_crossover', 'strength': 'strong'}
        else:
            return {'bullish': 0, 'bearish': 0, 'signal': 'neutral', 'strength': 'none'}
    
    def _analyze_ema_signal(self, price: float, ema_9: float, ema_21: float, ema_50: float) -> Dict:
        """
        Analyze EMA alignment for trading signals.
        
        Educational Note:
        EMA alignment indicates trend strength:
        - Price > EMAs with EMAs aligned: Strong uptrend
        - Price < EMAs with EMAs aligned: Strong downtrend
        - Mixed alignment: Weak or changing trend
        """
        if price > ema_21 and ema_9 > ema_21 and ema_21 > ema_50:
            return {'bullish': 1, 'bearish': 0, 'signal': 'strong_uptrend', 'strength': 'strong'}
        elif price < ema_21 and ema_9 < ema_21 and ema_21 < ema_50:
            return {'bullish': 0, 'bearish': 1, 'signal': 'strong_downtrend', 'strength': 'strong'}
        elif price > ema_21 and ema_9 > ema_21:
            return {'bullish': 0.5, 'bearish': 0, 'signal': 'weak_uptrend', 'strength': 'moderate'}
        elif price < ema_21 and ema_9 < ema_21:
            return {'bullish': 0, 'bearish': 0.5, 'signal': 'weak_downtrend', 'strength': 'moderate'}
        else:
            return {'bullish': 0, 'bearish': 0, 'signal': 'mixed_trend', 'strength': 'weak'}
    
    def _analyze_volume_signal(self, volume_ratio: float) -> Dict:
        """
        Analyze volume for signal confirmation.
        
        Educational Note:
        Volume confirms signal strength:
        - High volume: Strong conviction
        - Low volume: Weak conviction
        - Volume trends: Institutional interest
        """
        if volume_ratio > 1.5:
            return {'bullish': 0.5, 'bearish': 0.5, 'signal': 'high_volume', 'strength': 'strong'}
        elif volume_ratio > 1.2:
            return {'bullish': 0.3, 'bearish': 0.3, 'signal': 'above_average_volume', 'strength': 'moderate'}
        else:
            return {'bullish': 0, 'bearish': 0, 'signal': 'low_volume', 'strength': 'weak'}
    
    def _recommend_strategy(self, market_state: Dict, directional_signals: Dict) -> Dict:
        """
        Recommend optimal options strategy based on market conditions.
        
        Educational Note:
        Strategy selection depends on:
        1. Market regime (trending vs ranging)
        2. Volatility level (high vs low)
        3. Signal strength and confluence
        4. Risk tolerance and time horizon
        
        Strategy Types:
        - Directional: Calls, puts, spreads
        - Neutral: Iron condors, butterflies
        - Volatility: Straddles, strangles
        - Income: Covered calls, cash-secured puts
        """
        regime = market_state['regime']
        volatility = market_state['volatility']['level']
        bullish_strength = directional_signals['overall']['bullish_strength']
        bearish_strength = directional_signals['overall']['bearish_strength']
        
        # Determine primary direction
        if bullish_strength > bearish_strength and bullish_strength > 60:
            direction = 'bullish'
            strength = bullish_strength
        elif bearish_strength > bullish_strength and bearish_strength > 60:
            direction = 'bearish'
            strength = bearish_strength
        else:
            direction = 'neutral'
            strength = max(bullish_strength, bearish_strength)
        
        # Recommend strategy based on conditions
        if regime == 'trending_volatile' and direction != 'neutral':
            if direction == 'bullish':
                strategy = 'bull_call_spread'
                rationale = "Strong bullish trend with high volatility - bull call spread captures upside with defined risk"
            else:
                strategy = 'bear_put_spread'
                rationale = "Strong bearish trend with high volatility - bear put spread captures downside with defined risk"
        
        elif regime == 'trending_calm' and direction != 'neutral':
            if direction == 'bullish':
                strategy = 'long_call'
                rationale = "Strong bullish trend with low volatility - long call benefits from trend continuation"
            else:
                strategy = 'long_put'
                rationale = "Strong bearish trend with low volatility - long put benefits from trend continuation"
        
        elif regime == 'ranging_volatile':
            strategy = 'iron_condor'
            rationale = "Range-bound market with high volatility - iron condor profits from volatility contraction"
        
        elif regime == 'ranging_calm':
            strategy = 'short_straddle'
            rationale = "Range-bound market with low volatility - short straddle profits from time decay"
        
        elif direction == 'neutral' and volatility == 'high':
            strategy = 'long_straddle'
            rationale = "Neutral direction with high volatility - long straddle profits from volatility expansion"
        
        else:
            strategy = 'wait'
            rationale = "Mixed signals - wait for clearer setup"
        
        return {
            'strategy': strategy,
            'direction': direction,
            'strength': strength,
            'rationale': rationale,
            'market_regime': regime,
            'volatility_level': volatility
        }
    
    def _calculate_risk_metrics(self) -> Dict:
        """
        Calculate risk metrics for position sizing.
        
        Educational Note:
        Risk management is crucial for options trading:
        - Position size should be based on account size and risk tolerance
        - Stop losses should be based on technical levels
        - Profit targets should consider risk/reward ratios
        - Time decay affects all strategies differently
        """
        values = self.latest_values
        
        # Calculate potential move based on Bollinger Bands
        bb_range = values['bb_upper'] - values['bb_lower']
        current_price = values['price']
        
        # Estimate potential upside and downside
        upside_target = values['bb_upper']
        downside_target = values['bb_lower']
        
        upside_potential = (upside_target - current_price) / current_price
        downside_potential = (current_price - downside_target) / current_price
        
        return {
            'current_price': current_price,
            'upside_target': upside_target,
            'downside_target': downside_target,
            'upside_potential_pct': upside_potential * 100,
            'downside_potential_pct': downside_potential * 100,
            'bb_range_pct': (bb_range / current_price) * 100,
            'recommended_position_size': self._calculate_position_size(),
            'stop_loss_levels': self._calculate_stop_loss_levels()
        }
    
    def _calculate_position_size(self) -> Dict:
        """
        Calculate recommended position size.
        
        Educational Note:
        Position sizing should be based on:
        - Account size and risk tolerance
        - Signal strength and confidence
        - Volatility and potential move size
        - Time to expiration
        """
        signal_strength = max(self.signal_strength['bullish'], self.signal_strength['bearish'])
        
        if signal_strength >= STRONG_SIGNAL:
            size_pct = 0.02  # 2% of account
        elif signal_strength >= MODERATE_SIGNAL:
            size_pct = 0.01  # 1% of account
        else:
            size_pct = 0.005  # 0.5% of account
        
        return {
            'percentage': size_pct,
            'rationale': f"Based on signal strength of {signal_strength:.1f}",
            'max_loss': f"Maximum {size_pct * 100:.1f}% of account at risk"
        }
    
    def _calculate_stop_loss_levels(self) -> Dict:
        """
        Calculate stop loss levels based on technical analysis.
        
        Educational Note:
        Stop losses should be based on:
        - Key technical levels (support/resistance)
        - Volatility and ATR (Average True Range)
        - Risk/reward ratio requirements
        - Time decay considerations
        """
        values = self.latest_values
        
        # Calculate stop loss levels
        bullish_stop = values['bb_lower'] * 0.98  # 2% below lower band
        bearish_stop = values['bb_upper'] * 1.02  # 2% above upper band
        
        return {
            'bullish_stop': bullish_stop,
            'bearish_stop': bearish_stop,
            'rationale': 'Based on Bollinger Band levels with 2% buffer'
        }
    
    def _calculate_confidence_level(self) -> str:
        """
        Calculate overall confidence level.
        
        Educational Note:
        Confidence levels help determine:
        - Position size
        - Strategy complexity
        - Risk management approach
        """
        max_signal = max(self.signal_strength['bullish'], self.signal_strength['bearish'])
        
        if max_signal >= STRONG_SIGNAL:
            return 'high'
        elif max_signal >= MODERATE_SIGNAL:
            return 'medium'
        else:
            return 'low'


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
    
    # Test the signal generator
    signal_gen = SignalGenerator(sample_data)
    signals = signal_gen.generate_signals()
    
    print("Testing Signal Generator...")
    print(f"Market Regime: {signals['market_state']['regime']}")
    print(f"Recommended Strategy: {signals['strategy_recommendation']['strategy']}")
    print(f"Confidence Level: {signals['confidence_level']}")
    print("Signal generation test completed successfully!")
