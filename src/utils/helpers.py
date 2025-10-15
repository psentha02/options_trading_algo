"""
Helper Functions for Options Trading Model

This module contains utility functions used throughout the application.
These functions handle data formatting, calculations, and common operations.

Educational Focus:
- Understanding data preprocessing and formatting
- Learning about options calculations and Greeks
- Implementing risk management utilities
- Creating user-friendly output formatting
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
import json


def format_currency(amount: float, currency: str = "USD") -> str:
    """
    Format currency values for display.
    
    Educational Note:
    Proper formatting makes financial data more readable and professional.
    This function handles different currency formats and decimal places.
    
    Args:
        amount: The amount to format
        currency: Currency code (default: USD)
    
    Returns:
        Formatted currency string
    """
    if currency == "USD":
        return f"${amount:,.2f}"
    else:
        return f"{amount:,.2f} {currency}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Format percentage values for display.
    
    Educational Note:
    Percentages are crucial in options trading for:
    - Risk/reward ratios
    - Probability of profit
    - Volatility measurements
    - Return calculations
    
    Args:
        value: The percentage value (as decimal)
        decimals: Number of decimal places
    
    Returns:
        Formatted percentage string
    """
    return f"{value * 100:.{decimals}f}%"


def calculate_days_to_expiry(expiration_date: str) -> int:
    """
    Calculate days to expiration for an options contract.
    
    Educational Note:
    Time to expiration is crucial for options trading because:
    - Time decay accelerates as expiration approaches
    - Short-term options have higher gamma (price sensitivity)
    - Long-term options have higher theta (time decay)
    
    Args:
        expiration_date: Expiration date in YYYY-MM-DD format
    
    Returns:
        Number of days to expiration
    """
    try:
        exp_date = datetime.strptime(expiration_date, '%Y-%m-%d')
        current_date = datetime.now()
        days = (exp_date - current_date).days
        return max(0, days)  # Don't return negative days
    except ValueError:
        return 0


def calculate_breakeven_price(option_type: str, strike: float, premium: float) -> float:
    """
    Calculate break-even price for an options position.
    
    Educational Note:
    Break-even price is where the option position becomes profitable:
    - Long calls: Strike + Premium
    - Long puts: Strike - Premium
    - Short calls: Strike + Premium (breakeven for buyer)
    - Short puts: Strike - Premium (breakeven for buyer)
    
    Args:
        option_type: 'call' or 'put'
        strike: Strike price
        premium: Premium paid/received
    
    Returns:
        Break-even price
    """
    if option_type.lower() == 'call':
        return strike + premium
    else:  # put
        return strike - premium


def calculate_max_profit_loss(option_type: str, strike: float, premium: float, 
                            current_price: float, position: str = 'long') -> Dict[str, float]:
    """
    Calculate maximum profit and loss for an options position.
    
    Educational Note:
    Understanding max profit/loss is essential for risk management:
    - Long options: Limited loss (premium), unlimited/limited gain
    - Short options: Unlimited/limited loss, limited gain (premium)
    - Position size should be based on max loss tolerance
    
    Args:
        option_type: 'call' or 'put'
        strike: Strike price
        premium: Premium paid/received
        current_price: Current stock price
        position: 'long' or 'short'
    
    Returns:
        Dictionary with max_profit and max_loss
    """
    if position.lower() == 'long':
        # Long options
        max_loss = premium  # Maximum loss is the premium paid
        if option_type.lower() == 'call':
            # Long calls have unlimited upside potential
            # In practice, we estimate based on reasonable price targets
            max_gain = max(0, current_price * 2 - strike - premium)  # Assume 100% move
        else:  # put
            # Long puts are limited by strike price (stock can't go below $0)
            max_gain = max(0, strike - premium)
    else:
        # Short options
        max_profit = premium  # Maximum profit is the premium received
        if option_type.lower() == 'call':
            # Short calls have unlimited loss potential
            max_loss = float('inf')  # In practice, this would be managed with stops
        else:  # put
            # Short puts are limited by strike price
            max_loss = strike - premium
    
    return {
        'max_profit': max_gain if position.lower() == 'long' else max_profit,
        'max_loss': max_loss
    }


def calculate_probability_of_profit(delta: float) -> float:
    """
    Calculate probability of profit based on delta.
    
    Educational Note:
    Delta approximates the probability of finishing in-the-money:
    - Delta of 0.5 = ~50% chance of profit
    - Delta of 0.3 = ~30% chance of profit
    - Delta of 0.7 = ~70% chance of profit
    
    Args:
        delta: Delta value of the option
    
    Returns:
        Probability of profit as decimal
    """
    return abs(delta)


def format_options_chain(contracts: List[Dict]) -> pd.DataFrame:
    """
    Format options chain data for display.
    
    Educational Note:
    Options chains can be complex with many contracts.
    This function formats the data in a readable table format
    with key metrics highlighted.
    
    Args:
        contracts: List of options contracts
    
    Returns:
        Formatted DataFrame
    """
    if not contracts:
        return pd.DataFrame()
    
    # Create DataFrame from contracts
    df = pd.DataFrame(contracts)
    
    # Select and rename key columns
    key_columns = [
        'contract_type', 'strike_price', 'expiration_date', 'bid', 'ask', 'last',
        'volume', 'open_interest', 'delta', 'gamma', 'theta', 'vega', 'implied_volatility'
    ]
    
    # Filter to available columns
    available_columns = [col for col in key_columns if col in df.columns]
    formatted_df = df[available_columns].copy()
    
    # Format numeric columns
    numeric_columns = ['strike_price', 'bid', 'ask', 'last', 'delta', 'gamma', 'theta', 'vega', 'implied_volatility']
    for col in numeric_columns:
        if col in formatted_df.columns:
            formatted_df[col] = pd.to_numeric(formatted_df[col], errors='coerce')
    
    # Add calculated columns
    if 'bid' in formatted_df.columns and 'ask' in formatted_df.columns:
        formatted_df['mid_price'] = (formatted_df['bid'] + formatted_df['ask']) / 2
        formatted_df['spread'] = formatted_df['ask'] - formatted_df['bid']
        formatted_df['spread_pct'] = (formatted_df['spread'] / formatted_df['mid_price']) * 100
    
    # Add days to expiry
    if 'expiration_date' in formatted_df.columns:
        formatted_df['days_to_expiry'] = formatted_df['expiration_date'].apply(calculate_days_to_expiry)
    
    return formatted_df


def create_signal_summary(signal_data: Dict) -> str:
    """
    Create a human-readable summary of trading signals.
    
    Educational Note:
    Signal summaries help users quickly understand:
    - What the analysis found
    - Why the recommendation was made
    - What risks to consider
    - How to implement the strategy
    
    Args:
        signal_data: Signal analysis data
    
    Returns:
        Formatted summary string
    """
    summary_parts = []
    
    # Market state
    market_state = signal_data.get('market_state', {})
    regime = market_state.get('regime', 'unknown')
    trend_strength = market_state.get('trend_strength', 0)
    volatility = market_state.get('volatility', {}).get('level', 'unknown')
    
    summary_parts.append(f"Market Analysis:")
    summary_parts.append(f"  • Regime: {regime.replace('_', ' ').title()}")
    summary_parts.append(f"  • Trend Strength: {trend_strength:.1f}/100")
    summary_parts.append(f"  • Volatility: {volatility.title()}")
    
    # Signal analysis
    directional_signals = signal_data.get('directional_signals', {})
    overall = directional_signals.get('overall', {})
    bullish_strength = overall.get('bullish_strength', 0)
    bearish_strength = overall.get('bearish_strength', 0)
    
    summary_parts.append(f"\nSignal Analysis:")
    summary_parts.append(f"  • Bullish Strength: {bullish_strength:.1f}/100")
    summary_parts.append(f"  • Bearish Strength: {bearish_strength:.1f}/100")
    
    # Strategy recommendation
    strategy_rec = signal_data.get('strategy_recommendation', {})
    strategy = strategy_rec.get('strategy', 'unknown')
    direction = strategy_rec.get('direction', 'unknown')
    rationale = strategy_rec.get('rationale', 'No rationale provided')
    
    summary_parts.append(f"\nRecommendation:")
    summary_parts.append(f"  • Strategy: {strategy.replace('_', ' ').title()}")
    summary_parts.append(f"  • Direction: {direction.title()}")
    summary_parts.append(f"  • Rationale: {rationale}")
    
    # Risk metrics
    risk_metrics = signal_data.get('risk_metrics', {})
    current_price = risk_metrics.get('current_price', 0)
    upside_potential = risk_metrics.get('upside_potential_pct', 0)
    downside_potential = risk_metrics.get('downside_potential_pct', 0)
    
    summary_parts.append(f"\nRisk Analysis:")
    summary_parts.append(f"  • Current Price: {format_currency(current_price)}")
    summary_parts.append(f"  • Upside Potential: {format_percentage(upside_potential/100)}")
    summary_parts.append(f"  • Downside Potential: {format_percentage(downside_potential/100)}")
    
    # Confidence level
    confidence = signal_data.get('confidence_level', 'unknown')
    summary_parts.append(f"\nConfidence Level: {confidence.title()}")
    
    return "\n".join(summary_parts)


def format_contract_recommendation(contract: Dict) -> str:
    """
    Format a single contract recommendation for display.
    
    Educational Note:
    Contract recommendations should include:
    - Contract details (type, strike, expiration)
    - Pricing information (bid, ask, last)
    - Greeks and risk metrics
    - Rationale for selection
    - Risk management guidelines
    
    Args:
        contract: Contract data with scores and analysis
    
    Returns:
        Formatted recommendation string
    """
    recommendation_parts = []
    
    # Contract details
    option_type = contract.get('contract_type', '').upper()
    strike = contract.get('strike_price', 0)
    expiration = contract.get('expiration_date', 'Unknown')
    days_to_expiry = contract.get('days_to_expiry', 0)
    
    recommendation_parts.append(f"Contract: {option_type} ${strike} expiring {expiration} ({days_to_expiry} days)")
    
    # Pricing
    bid = contract.get('bid', 0)
    ask = contract.get('ask', 0)
    last = contract.get('last', 0)
    
    if bid > 0 and ask > 0:
        mid_price = (bid + ask) / 2
        spread = ask - bid
        spread_pct = (spread / mid_price) * 100
        
        recommendation_parts.append(f"Pricing: Bid ${bid:.2f} | Ask ${ask:.2f} | Mid ${mid_price:.2f}")
        recommendation_parts.append(f"Spread: ${spread:.2f} ({spread_pct:.1f}%)")
    
    # Greeks
    delta = contract.get('delta', 0)
    gamma = contract.get('gamma', 0)
    theta = contract.get('theta', 0)
    vega = contract.get('vega', 0)
    iv = contract.get('implied_volatility', 0)
    
    recommendation_parts.append(f"Greeks: Δ {delta:.3f} | Γ {gamma:.3f} | Θ {theta:.3f} | ν {vega:.3f}")
    recommendation_parts.append(f"Implied Volatility: {format_percentage(iv)}")
    
    # Scores
    total_score = contract.get('total_score', 0)
    signal_score = contract.get('signal_score', 0)
    liquidity_score = contract.get('liquidity_score', 0)
    risk_reward_score = contract.get('risk_reward_score', 0)
    
    recommendation_parts.append(f"Scores: Total {total_score:.1f}/100 | Signal {signal_score:.1f} | Liquidity {liquidity_score:.1f} | Risk/Reward {risk_reward_score:.1f}")
    
    # Recommendation
    recommendation = contract.get('recommendation', 'Unknown')
    rationale = contract.get('rationale', 'No rationale provided')
    
    recommendation_parts.append(f"Recommendation: {recommendation}")
    recommendation_parts.append(f"Rationale: {rationale}")
    
    return "\n".join(recommendation_parts)


def save_analysis_to_file(analysis_data: Dict, filename: str = None) -> str:
    """
    Save analysis data to a JSON file.
    
    Educational Note:
    Saving analysis data allows for:
    - Backtesting and performance tracking
    - Sharing analysis with others
    - Comparing different time periods
    - Building a database of trading decisions
    
    Args:
        analysis_data: Complete analysis data
        filename: Optional filename (defaults to timestamp)
    
    Returns:
        Filename where data was saved
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"analysis_{timestamp}.json"
    
    # Convert numpy types to Python types for JSON serialization
    def convert_numpy(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        return obj
    
    # Recursively convert numpy types
    def clean_data(data):
        if isinstance(data, dict):
            return {key: clean_data(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [clean_data(item) for item in data]
        else:
            return convert_numpy(data)
    
    cleaned_data = clean_data(analysis_data)
    
    with open(filename, 'w') as f:
        json.dump(cleaned_data, f, indent=2, default=str)
    
    return filename


def load_analysis_from_file(filename: str) -> Dict:
    """
    Load analysis data from a JSON file.
    
    Educational Note:
    Loading saved analysis allows for:
    - Reviewing past decisions
    - Comparing different strategies
    - Building performance metrics
    - Learning from historical data
    
    Args:
        filename: JSON filename to load
    
    Returns:
        Analysis data dictionary
    """
    with open(filename, 'r') as f:
        data = json.load(f)
    
    return data


def calculate_portfolio_metrics(positions: List[Dict]) -> Dict:
    """
    Calculate portfolio-level metrics.
    
    Educational Note:
    Portfolio metrics help with:
    - Risk management across multiple positions
    - Diversification analysis
    - Overall exposure calculation
    - Performance tracking
    
    Args:
        positions: List of position data
    
    Returns:
        Portfolio metrics dictionary
    """
    if not positions:
        return {}
    
    total_value = sum(pos.get('value', 0) for pos in positions)
    total_delta = sum(pos.get('delta', 0) for pos in positions)
    total_gamma = sum(pos.get('gamma', 0) for pos in positions)
    total_theta = sum(pos.get('theta', 0) for pos in positions)
    total_vega = sum(pos.get('vega', 0) for pos in positions)
    
    return {
        'total_positions': len(positions),
        'total_value': total_value,
        'total_delta': total_delta,
        'total_gamma': total_gamma,
        'total_theta': total_theta,
        'total_vega': total_vega,
        'net_exposure': total_delta,  # Net directional exposure
        'volatility_sensitivity': total_vega,  # Sensitivity to volatility changes
        'time_decay': total_theta  # Daily time decay
    }


# Example usage and testing
if __name__ == "__main__":
    # Test helper functions
    print("Testing Helper Functions...")
    
    # Test currency formatting
    print(f"Currency: {format_currency(1234.56)}")
    
    # Test percentage formatting
    print(f"Percentage: {format_percentage(0.1234)}")
    
    # Test days to expiry
    print(f"Days to expiry: {calculate_days_to_expiry('2024-12-20')}")
    
    # Test break-even calculation
    print(f"Call break-even: {calculate_breakeven_price('call', 100, 5)}")
    print(f"Put break-even: {calculate_breakeven_price('put', 100, 5)}")
    
    # Test max profit/loss
    profit_loss = calculate_max_profit_loss('call', 100, 5, 105, 'long')
    print(f"Max profit: {profit_loss['max_profit']}, Max loss: {profit_loss['max_loss']}")
    
    print("Helper functions test completed successfully!")
