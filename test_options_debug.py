#!/usr/bin/env python3
"""
Test script to debug options contract selection without API calls.
This helps identify why no contracts are being found.
"""

import sys
import os
from datetime import datetime, timedelta

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.strategies.options_selector import OptionsSelector
from src.strategies.signal_generator import SignalGenerator
import pandas as pd
import numpy as np

# Mock Polygon client for testing
class MockPolygonClient:
    def get_options_chain(self, ticker):
        """Return mock options data for testing"""
        # Use future dates
        future_date_1 = (datetime.now() + timedelta(days=21)).strftime('%Y-%m-%d')
        future_date_2 = (datetime.now() + timedelta(days=35)).strftime('%Y-%m-%d')
        
        return [
            {
                'contract_type': 'call',
                'strike_price': 150.0,
                'expiration_date': future_date_1,
                'bid': 2.50,
                'ask': 2.75,
                'last': 2.60,
                'volume': 150,
                'open_interest': 500,
                'delta': 0.65,
                'gamma': 0.02,
                'theta': -0.15,
                'vega': 0.30,
                'implied_volatility': 0.25
            },
            {
                'contract_type': 'put',
                'strike_price': 150.0,
                'expiration_date': future_date_1,
                'bid': 2.25,
                'ask': 2.50,
                'last': 2.35,
                'volume': 200,
                'open_interest': 750,
                'delta': -0.35,
                'gamma': 0.02,
                'theta': -0.12,
                'vega': 0.28,
                'implied_volatility': 0.24
            },
            {
                'contract_type': 'call',
                'strike_price': 155.0,
                'expiration_date': future_date_2,
                'bid': 1.80,
                'ask': 2.05,
                'last': 1.90,
                'volume': 100,
                'open_interest': 300,
                'delta': 0.45,
                'gamma': 0.03,
                'theta': -0.18,
                'vega': 0.35,
                'implied_volatility': 0.26
            }
        ]

def test_options_selection():
    """Test the options selection process"""
    print("🧪 Testing Options Contract Selection")
    print("=" * 50)
    
    # Create mock price data with strong bullish trend
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    np.random.seed(42)
    
    # Create a strong uptrend
    trend = np.linspace(100, 150, 100)  # Strong uptrend
    noise = np.random.randn(100) * 2   # Small amount of noise
    
    sample_data = pd.DataFrame({
        'timestamp': [int(d.timestamp() * 1000) for d in dates],
        'open': trend + noise,
        'high': trend + noise + np.random.rand(100) * 3,
        'low': trend + noise - np.random.rand(100) * 3,
        'close': trend + noise,
        'volume': np.random.randint(2000000, 6000000, 100)  # Higher volume
    })
    
    # Generate signals
    signal_generator = SignalGenerator(sample_data)
    signals = signal_generator.generate_signals()
    
    print(f"📊 Generated signals:")
    print(f"  Strategy: {signals['strategy_recommendation']['strategy']}")
    print(f"  Direction: {signals['strategy_recommendation']['direction']}")
    print(f"  Strength: {signals['strategy_recommendation']['strength']}")
    print()
    
    # Test options selection
    mock_client = MockPolygonClient()
    options_selector = OptionsSelector(mock_client, signals)
    
    print("🔍 Testing options contract selection...")
    contracts = options_selector.select_contracts("AAPL", max_contracts=3)
    
    print(f"\n📊 Results:")
    print(f"  Found {len(contracts)} contracts")
    
    for i, contract in enumerate(contracts, 1):
        print(f"\n#{i} Contract:")
        print(f"  Type: {contract.get('contract_type', 'Unknown')}")
        print(f"  Strike: ${contract.get('strike_price', 0)}")
        print(f"  Expiration: {contract.get('expiration_date', 'Unknown')}")
        print(f"  Days to Expiry: {contract.get('days_to_expiry', 0)}")
        print(f"  Bid/Ask: ${contract.get('bid', 0)}/${contract.get('ask', 0)}")
        print(f"  Total Score: {contract.get('total_score', 0):.1f}/100")
        print(f"  Recommendation: {contract.get('recommendation', 'Unknown')}")
        print(f"  Rationale: {contract.get('rationale', 'No rationale')}")

if __name__ == "__main__":
    test_options_selection()
