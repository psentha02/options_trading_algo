"""
Options Contract Selection and Scoring System

This module selects optimal options contracts based on technical signals,
risk/reward ratios, and market conditions. It implements a comprehensive
scoring system to rank available contracts.

Educational Focus:
- Understanding options Greeks and their impact on strategy selection
- Risk/reward analysis for different contract types
- Liquidity considerations and bid-ask spreads
- Time decay and volatility effects on options pricing
- Position sizing and risk management
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import (
    MIN_OPEN_INTEREST, MAX_BID_ASK_SPREAD_PCT, OPTIMAL_DELTA_RANGE,
    MIN_DAYS_TO_EXPIRY, MAX_DAYS_TO_EXPIRY
)


class OptionsSelector:
    """
    Selects and scores options contracts based on multiple criteria.
    
    Educational Philosophy:
    - Combines technical signals with options-specific metrics
    - Considers risk/reward ratios and probability of profit
    - Evaluates liquidity and trading costs
    - Provides educational explanations for each recommendation
    """
    
    def __init__(self, polygon_client, signal_data: Dict):
        """
        Initialize with Polygon client and signal data.
        
        Args:
            polygon_client: Polygon.io API client
            signal_data: Signal analysis from SignalGenerator
        """
        self.client = polygon_client
        self.signal_data = signal_data
        self.current_price = signal_data['risk_metrics']['current_price']
        self.strategy = signal_data['strategy_recommendation']['strategy']
        self.direction = signal_data['strategy_recommendation']['direction']
        self.strength = signal_data['strategy_recommendation']['strength']
    
    def select_contracts(self, ticker: str, max_contracts: int = 10) -> List[Dict]:
        """
        Select optimal options contracts based on signals and criteria.
        
        Educational Note:
        This method implements a comprehensive scoring system that considers:
        1. Signal alignment (does the contract match our directional bias?)
        2. Risk/reward ratio (potential profit vs potential loss)
        3. Liquidity (can we easily enter/exit the position?)
        4. Time decay (how much time value is there?)
        5. Volatility (are we overpaying for volatility?)
        
        Args:
            ticker: Stock symbol
            max_contracts: Maximum number of contracts to return
        
        Returns:
            List of scored and ranked contracts
        """
        # Get available options contracts
        options_data = self._get_options_data(ticker)
        
        if not options_data:
            return []
        
        # Filter contracts based on strategy
        filtered_contracts = self._filter_contracts(options_data)
        
        # Score each contract
        scored_contracts = []
        for contract in filtered_contracts:
            score_data = self._score_contract(contract)
            if score_data['total_score'] > 0:  # Only include contracts with positive scores
                scored_contracts.append(score_data)
        
        # If no contracts scored well, be more lenient
        if not scored_contracts and filtered_contracts:
            print("⚠️  No contracts scored well, using fallback scoring...")
            for contract in filtered_contracts:
                # Create a basic score for any contract
                basic_score = {
                    **contract,
                    'signal_score': 50,  # Neutral score
                    'liquidity_score': 50,
                    'risk_reward_score': 50,
                    'time_decay_score': 50,
                    'volatility_score': 50,
                    'total_score': 50,
                    'recommendation': 'Hold',
                    'rationale': 'Fallback recommendation - basic contract analysis'
                }
                scored_contracts.append(basic_score)
        
        # Sort by total score (highest first)
        scored_contracts.sort(key=lambda x: x['total_score'], reverse=True)
        
        # Return top contracts
        return scored_contracts[:max_contracts]
    
    def _get_options_data(self, ticker: str) -> List[Dict]:
        """
        Get options data from Polygon.io API.
        
        Educational Note:
        Options data includes:
        - Contract details (strike, expiration, type)
        - Pricing data (bid, ask, last)
        - Greeks (delta, gamma, theta, vega)
        - Volume and open interest
        - Implied volatility
        """
        try:
            print(f"🔍 Fetching options data for {ticker}...")
            
            # Get options chain
            options_chain = self.client.get_options_chain(ticker)
            
            if not options_chain:
                print(f"❌ No options data found for {ticker}")
                return []
            
            print(f"📊 Retrieved {len(options_chain)} total contracts")
            
            # Filter for reasonable expiration dates
            current_date = datetime.now()
            filtered_options = []
            
            for contract in options_chain:
                try:
                    exp_date = datetime.strptime(contract['expiration_date'], '%Y-%m-%d')
                    days_to_expiry = (exp_date - current_date).days
                    
                    # More lenient expiration date filtering
                    if 7 <= days_to_expiry <= 60:  # 1 week to 2 months
                        # Add days to expiry for easier analysis
                        contract['days_to_expiry'] = days_to_expiry
                        filtered_options.append(contract)
                        print(f"  ✅ Added contract: {contract.get('contract_type', 'Unknown')} "
                              f"${contract.get('strike_price', 0)} exp {contract['expiration_date']} "
                              f"({days_to_expiry} days)")
                    else:
                        print(f"  ❌ Skipped contract: {contract.get('contract_type', 'Unknown')} "
                              f"${contract.get('strike_price', 0)} exp {contract['expiration_date']} "
                              f"({days_to_expiry} days) - outside date range")
                
                except (ValueError, KeyError) as e:
                    # Skip contracts with invalid dates
                    print(f"  ❌ Invalid contract data: {e}")
                    continue
            
            print(f"📊 Filtered to {len(filtered_options)} contracts within date range")
            return filtered_options
            
        except Exception as e:
            print(f"❌ Error fetching options data: {e}")
            return []
    
    def _filter_contracts(self, options_data: List[Dict]) -> List[Dict]:
        """
        Filter contracts based on strategy requirements.
        
        Educational Note:
        Different strategies require different contract types:
        - Directional strategies: Calls for bullish, puts for bearish
        - Neutral strategies: Both calls and puts at different strikes
        - Volatility strategies: Both calls and puts at same strike
        - Income strategies: Out-of-the-money options
        """
        filtered = []
        
        print(f"🔍 Filtering {len(options_data)} contracts...")
        
        for contract in options_data:
            # Debug: Print contract details
            print(f"  Contract: {contract.get('contract_type', 'Unknown')} ${contract.get('strike_price', 0)} "
                  f"OI: {contract.get('open_interest', 0)} Bid: {contract.get('bid', 0)} Ask: {contract.get('ask', 0)}")
            
            # Relaxed liquidity filter - lower threshold
            open_interest = contract.get('open_interest', 0)
            if open_interest < 10:  # Much lower threshold
                print(f"    ❌ Low open interest: {open_interest}")
                continue
            
            # Relaxed bid-ask spread filter
            bid = contract.get('bid', 0)
            ask = contract.get('ask', 0)
            if bid > 0 and ask > 0:
                spread_pct = ((ask - bid) / ((ask + bid) / 2)) * 100
                if spread_pct > 50:  # Much more lenient spread filter
                    print(f"    ❌ Wide spread: {spread_pct:.1f}%")
                    continue
            elif bid <= 0 and ask <= 0:
                print(f"    ❌ No bid/ask data")
                continue
            
            # Strategy-specific filtering
            if self._matches_strategy(contract):
                print(f"    ✅ Matches strategy")
                filtered.append(contract)
            else:
                print(f"    ❌ Doesn't match strategy")
        
        print(f"📊 Filtered to {len(filtered)} contracts")
        return filtered
    
    def _matches_strategy(self, contract: Dict) -> bool:
        """
        Check if contract matches the recommended strategy.
        
        Educational Note:
        Strategy matching ensures we select contracts that align with our analysis:
        - Directional strategies need contracts in the right direction
        - Neutral strategies need contracts that profit from range-bound movement
        - Volatility strategies need contracts that benefit from volatility changes
        """
        option_type = contract.get('contract_type', '').lower()
        strike = contract.get('strike_price', 0)
        
        print(f"    Strategy: {self.strategy}, Direction: {self.direction}, Option Type: {option_type}")
        
        # If strategy is 'wait', don't match anything
        if self.strategy == 'wait':
            print(f"    ❌ Strategy is 'wait' - no contracts needed")
            return False
        
        # For directional strategies, match based on direction
        if self.strategy in ['long_call', 'bull_call_spread']:
            match = option_type == 'call'
            print(f"    {'✅' if match else '❌'} Call strategy - {'call' if match else 'not call'}")
            return match
        
        elif self.strategy in ['long_put', 'bear_put_spread']:
            match = option_type == 'put'
            print(f"    {'✅' if match else '❌'} Put strategy - {'put' if match else 'not put'}")
            return match
        
        # For neutral/volatility strategies, accept both calls and puts
        elif self.strategy in ['iron_condor', 'long_straddle', 'short_straddle']:
            print(f"    ✅ Neutral/volatility strategy - accepting both calls and puts")
            return True
        
        # Default to directional based on signal
        else:
            if self.direction == 'bullish':
                match = option_type == 'call'
                print(f"    {'✅' if match else '❌'} Bullish direction - {'call' if match else 'not call'}")
                return match
            elif self.direction == 'bearish':
                match = option_type == 'put'
                print(f"    {'✅' if match else '❌'} Bearish direction - {'put' if match else 'not put'}")
                return match
            else:
                print(f"    ✅ Neutral direction - accepting both calls and puts")
                return True
    
    def _score_contract(self, contract: Dict) -> Dict:
        """
        Score a contract based on multiple criteria.
        
        Educational Note:
        The scoring system evaluates contracts on:
        1. Signal Alignment (40%): How well the contract matches our signals
        2. Liquidity Score (20%): How easy it is to trade
        3. Risk/Reward Score (20%): Potential profit vs potential loss
        4. Time Decay Score (10%): How time decay affects the position
        5. Volatility Score (10%): Whether we're overpaying for volatility
        
        Total Score = (Signal × 0.4) + (Liquidity × 0.2) + (Risk/Reward × 0.2) + 
                     (Time Decay × 0.1) + (Volatility × 0.1)
        """
        # Calculate individual scores
        signal_score = self._calculate_signal_score(contract)
        liquidity_score = self._calculate_liquidity_score(contract)
        risk_reward_score = self._calculate_risk_reward_score(contract)
        time_decay_score = self._calculate_time_decay_score(contract)
        volatility_score = self._calculate_volatility_score(contract)
        
        # Calculate weighted total score
        total_score = (
            signal_score * 0.4 +
            liquidity_score * 0.2 +
            risk_reward_score * 0.2 +
            time_decay_score * 0.1 +
            volatility_score * 0.1
        )
        
        # Add contract details and scores
        result = contract.copy()
        result.update({
            'signal_score': signal_score,
            'liquidity_score': liquidity_score,
            'risk_reward_score': risk_reward_score,
            'time_decay_score': time_decay_score,
            'volatility_score': volatility_score,
            'total_score': total_score,
            'recommendation': self._get_recommendation(total_score),
            'rationale': self._get_rationale(contract, {
                'signal': signal_score,
                'liquidity': liquidity_score,
                'risk_reward': risk_reward_score,
                'time_decay': time_decay_score,
                'volatility': volatility_score
            })
        })
        
        return result
    
    def _calculate_signal_score(self, contract: Dict) -> float:
        """
        Calculate how well the contract aligns with our signals.
        
        Educational Note:
        Signal alignment considers:
        - Directional bias (bullish/bearish)
        - Strike price relative to current price
        - Delta value (probability of finishing in-the-money)
        - Time to expiration vs signal strength
        """
        option_type = contract.get('contract_type', '').lower()
        strike = contract.get('strike_price', 0)
        delta = contract.get('delta', 0)
        days_to_expiry = contract.get('days_to_expiry', 0)
        
        score = 0
        
        # Directional alignment
        if self.direction == 'bullish' and option_type == 'call':
            score += 30
        elif self.direction == 'bearish' and option_type == 'put':
            score += 30
        elif self.direction == 'neutral':
            score += 20  # Neutral strategies can use both
        
        # Strike price alignment
        if option_type == 'call':
            # For calls, strikes near current price are better for directional plays
            strike_ratio = strike / self.current_price
            if 0.95 <= strike_ratio <= 1.05:  # At-the-money
                score += 25
            elif 0.90 <= strike_ratio < 0.95:  # Slightly out-of-the-money
                score += 20
            elif 0.85 <= strike_ratio < 0.90:  # Out-of-the-money
                score += 15
        else:  # put
            # For puts, strikes near current price are better for directional plays
            strike_ratio = strike / self.current_price
            if 0.95 <= strike_ratio <= 1.05:  # At-the-money
                score += 25
            elif 1.05 < strike_ratio <= 1.10:  # Slightly out-of-the-money
                score += 20
            elif 1.10 < strike_ratio <= 1.15:  # Out-of-the-money
                score += 15
        
        # Delta alignment
        if 0.4 <= abs(delta) <= 0.7:  # Optimal delta range
            score += 25
        elif 0.3 <= abs(delta) <= 0.8:  # Acceptable delta range
            score += 15
        
        # Time to expiration alignment
        if self.strength >= 80:  # Strong signal
            if 14 <= days_to_expiry <= 30:  # Short-term for strong signals
                score += 20
        else:  # Moderate/weak signal
            if 30 <= days_to_expiry <= 45:  # Medium-term for moderate signals
                score += 20
        
        return min(score, 100)
    
    def _calculate_liquidity_score(self, contract: Dict) -> float:
        """
        Calculate liquidity score based on volume and open interest.
        
        Educational Note:
        Liquidity is crucial for options trading because:
        - High liquidity = tight bid-ask spreads = lower trading costs
        - High liquidity = easier to enter/exit positions
        - Low liquidity = wide spreads = higher costs and slippage
        """
        open_interest = contract.get('open_interest', 0)
        volume = contract.get('volume', 0)
        bid = contract.get('bid', 0)
        ask = contract.get('ask', 0)
        
        score = 0
        
        # Open interest scoring
        if open_interest >= 1000:
            score += 40
        elif open_interest >= 500:
            score += 30
        elif open_interest >= 200:
            score += 20
        elif open_interest >= 100:
            score += 10
        
        # Volume scoring
        if volume >= 100:
            score += 30
        elif volume >= 50:
            score += 20
        elif volume >= 20:
            score += 10
        
        # Bid-ask spread scoring
        if bid > 0 and ask > 0:
            spread_pct = ((ask - bid) / ((ask + bid) / 2)) * 100
            if spread_pct <= 5:
                score += 30
            elif spread_pct <= 10:
                score += 20
            elif spread_pct <= 20:
                score += 10
        
        return min(score, 100)
    
    def _calculate_risk_reward_score(self, contract: Dict) -> float:
        """
        Calculate risk/reward score based on potential outcomes.
        
        Educational Note:
        Risk/reward analysis considers:
        - Maximum potential loss (premium paid)
        - Maximum potential gain (unlimited for long options)
        - Probability of profit (delta)
        - Break-even point
        """
        bid = contract.get('bid', 0)
        ask = contract.get('ask', 0)
        strike = contract.get('strike_price', 0)
        delta = contract.get('delta', 0)
        option_type = contract.get('contract_type', '').lower()
        
        if bid <= 0 or ask <= 0:
            return 0
        
        # Estimate entry price (mid-point of bid-ask)
        entry_price = (bid + ask) / 2
        
        # Calculate risk/reward ratio
        max_loss = entry_price  # Maximum loss is the premium paid
        max_gain = self._calculate_max_gain(contract, entry_price)
        
        if max_loss > 0:
            risk_reward_ratio = max_gain / max_loss
        else:
            return 0
        
        # Score based on risk/reward ratio
        score = 0
        
        if risk_reward_ratio >= 3:
            score += 40  # Excellent risk/reward
        elif risk_reward_ratio >= 2:
            score += 30  # Good risk/reward
        elif risk_reward_ratio >= 1.5:
            score += 20  # Acceptable risk/reward
        elif risk_reward_ratio >= 1:
            score += 10  # Poor risk/reward
        
        # Probability of profit scoring
        prob_profit = abs(delta) * 100
        if prob_profit >= 60:
            score += 30
        elif prob_profit >= 50:
            score += 20
        elif prob_profit >= 40:
            score += 10
        
        # Break-even analysis
        breakeven = self._calculate_breakeven(contract, entry_price)
        if breakeven:
            if option_type == 'call':
                breakeven_ratio = breakeven / self.current_price
                if 0.95 <= breakeven_ratio <= 1.05:  # Near current price
                    score += 30
            else:  # put
                breakeven_ratio = breakeven / self.current_price
                if 0.95 <= breakeven_ratio <= 1.05:  # Near current price
                    score += 30
        
        return min(score, 100)
    
    def _calculate_max_gain(self, contract: Dict, entry_price: float) -> float:
        """
        Calculate maximum potential gain.
        
        Educational Note:
        Maximum gain depends on strategy:
        - Long calls: Unlimited upside potential
        - Long puts: Limited to strike price (stock can't go below $0)
        - Spreads: Limited to the difference between strikes minus premium paid
        """
        option_type = contract.get('contract_type', '').lower()
        strike = contract.get('strike_price', 0)
        
        if option_type == 'call':
            # For calls, maximum gain is unlimited in theory
            # In practice, we estimate based on potential move
            potential_move = self.current_price * 0.2  # Assume 20% move
            max_gain = max(0, potential_move - strike - entry_price)
        else:  # put
            # For puts, maximum gain is limited to strike price
            max_gain = max(0, strike - entry_price)
        
        return max_gain
    
    def _calculate_breakeven(self, contract: Dict, entry_price: float) -> float:
        """
        Calculate break-even point.
        
        Educational Note:
        Break-even point is where the option position becomes profitable:
        - Long calls: Strike + Premium
        - Long puts: Strike - Premium
        """
        option_type = contract.get('contract_type', '').lower()
        strike = contract.get('strike_price', 0)
        
        if option_type == 'call':
            return strike + entry_price
        else:  # put
            return strike - entry_price
    
    def _calculate_time_decay_score(self, contract: Dict) -> float:
        """
        Calculate time decay score.
        
        Educational Note:
        Time decay (theta) affects options differently:
        - Long options: Time decay hurts (lose value over time)
        - Short options: Time decay helps (gain value over time)
        - Time decay accelerates as expiration approaches
        """
        days_to_expiry = contract.get('days_to_expiry', 0)
        theta = contract.get('theta', 0)
        
        score = 0
        
        # Time to expiration scoring
        if 14 <= days_to_expiry <= 30:
            score += 40  # Optimal time range
        elif 7 <= days_to_expiry < 14:
            score += 30  # Short-term
        elif 30 < days_to_expiry <= 45:
            score += 30  # Medium-term
        elif days_to_expiry > 45:
            score += 20  # Long-term
        else:
            score += 10  # Very short-term
        
        # Theta scoring (time decay)
        if theta < 0:  # Long option (time decay hurts)
            if days_to_expiry >= 21:  # Enough time for move to develop
                score += 30
            else:
                score += 10  # Not enough time
        else:  # Short option (time decay helps)
            if days_to_expiry <= 30:  # Time decay accelerates
                score += 40
            else:
                score += 20
        
        return min(score, 100)
    
    def _calculate_volatility_score(self, contract: Dict) -> float:
        """
        Calculate volatility score.
        
        Educational Note:
        Volatility affects options pricing:
        - High implied volatility = expensive options
        - Low implied volatility = cheap options
        - Volatility expansion = good for long options
        - Volatility contraction = good for short options
        """
        implied_vol = contract.get('implied_volatility', 0)
        vega = contract.get('vega', 0)
        
        if implied_vol <= 0:
            return 50  # Neutral score if no volatility data
        
        score = 0
        
        # Volatility level scoring
        if implied_vol <= 0.2:  # Low volatility
            score += 40  # Options are cheap
        elif implied_vol <= 0.4:  # Medium volatility
            score += 30  # Fair value
        elif implied_vol <= 0.6:  # High volatility
            score += 20  # Options are expensive
        else:  # Very high volatility
            score += 10  # Options are very expensive
        
        # Vega scoring (sensitivity to volatility changes)
        if abs(vega) >= 0.1:  # High vega sensitivity
            score += 30
        elif abs(vega) >= 0.05:  # Medium vega sensitivity
            score += 20
        else:  # Low vega sensitivity
            score += 10
        
        return min(score, 100)
    
    def _get_recommendation(self, total_score: float) -> str:
        """
        Get recommendation based on total score.
        
        Educational Note:
        Recommendations help prioritize contracts:
        - Strong Buy: Excellent opportunity
        - Buy: Good opportunity
        - Hold: Acceptable opportunity
        - Avoid: Poor opportunity
        """
        if total_score >= 80:
            return "Strong Buy"
        elif total_score >= 60:
            return "Buy"
        elif total_score >= 40:
            return "Hold"
        else:
            return "Avoid"
    
    def _get_rationale(self, contract: Dict, scores: Dict) -> str:
        """
        Generate educational rationale for the recommendation.
        
        Educational Note:
        The rationale explains why this contract was selected and what
        factors contributed to its score. This helps users understand
        the decision-making process and learn from the analysis.
        """
        option_type = contract.get('contract_type', '').upper()
        strike = contract.get('strike_price', 0)
        days_to_expiry = contract.get('days_to_expiry', 0)
        
        rationale_parts = []
        
        # Signal alignment explanation
        if scores['signal'] >= 70:
            rationale_parts.append(f"Excellent signal alignment ({scores['signal']:.0f}/100)")
        elif scores['signal'] >= 50:
            rationale_parts.append(f"Good signal alignment ({scores['signal']:.0f}/100)")
        else:
            rationale_parts.append(f"Weak signal alignment ({scores['signal']:.0f}/100)")
        
        # Liquidity explanation
        if scores['liquidity'] >= 70:
            rationale_parts.append(f"High liquidity ({scores['liquidity']:.0f}/100)")
        elif scores['liquidity'] >= 50:
            rationale_parts.append(f"Moderate liquidity ({scores['liquidity']:.0f}/100)")
        else:
            rationale_parts.append(f"Low liquidity ({scores['liquidity']:.0f}/100)")
        
        # Risk/reward explanation
        if scores['risk_reward'] >= 70:
            rationale_parts.append(f"Excellent risk/reward ({scores['risk_reward']:.0f}/100)")
        elif scores['risk_reward'] >= 50:
            rationale_parts.append(f"Good risk/reward ({scores['risk_reward']:.0f}/100)")
        else:
            rationale_parts.append(f"Poor risk/reward ({scores['risk_reward']:.0f}/100)")
        
        # Time decay explanation
        if scores['time_decay'] >= 70:
            rationale_parts.append(f"Favorable time decay ({scores['time_decay']:.0f}/100)")
        elif scores['time_decay'] >= 50:
            rationale_parts.append(f"Neutral time decay ({scores['time_decay']:.0f}/100)")
        else:
            rationale_parts.append(f"Unfavorable time decay ({scores['time_decay']:.0f}/100)")
        
        # Volatility explanation
        if scores['volatility'] >= 70:
            rationale_parts.append(f"Favorable volatility ({scores['volatility']:.0f}/100)")
        elif scores['volatility'] >= 50:
            rationale_parts.append(f"Neutral volatility ({scores['volatility']:.0f}/100)")
        else:
            rationale_parts.append(f"Unfavorable volatility ({scores['volatility']:.0f}/100)")
        
        # Combine rationale
        rationale = f"{option_type} ${strike} expiring in {days_to_expiry} days. "
        rationale += "Key factors: " + ", ".join(rationale_parts)
        
        return rationale


# Example usage and testing
if __name__ == "__main__":
    # This would be used with actual Polygon client and signal data
    print("Options Selector module loaded successfully!")
    print("This module requires Polygon client and signal data to function.")
