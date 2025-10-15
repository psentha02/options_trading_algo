"""
Configuration file for the Options Trading Model.
Handles API keys, rate limits, and other settings.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Polygon.io API Configuration
POLYGON_API_KEY = os.getenv('POLYGON_API_KEY')
POLYGON_BASE_URL = 'https://api.polygon.io'

# Rate limiting for Polygon.io starter tier (5 calls/minute)
RATE_LIMIT_CALLS = 5
RATE_LIMIT_WINDOW = 60  # seconds

# Technical Analysis Settings
RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
EMA_PERIODS = [9, 21, 50]
VOLUME_MA_PERIOD = 20

# Options Selection Criteria
MIN_OPEN_INTEREST = 10  # Much lower threshold for testing
MAX_BID_ASK_SPREAD_PCT = 50  # Much more lenient spread filter
OPTIMAL_DELTA_RANGE = (0.4, 0.7)
MIN_DAYS_TO_EXPIRY = 7  # More lenient date range
MAX_DAYS_TO_EXPIRY = 60  # Extended date range

# Signal Strength Thresholds
STRONG_SIGNAL = 80
MODERATE_SIGNAL = 60
WEAK_SIGNAL = 40

# Risk Management
DEFAULT_RISK_REWARD_RATIO = 2.0
MAX_POSITION_SIZE_PCT = 0.02  # 2% of portfolio per trade

# Cache Settings
CACHE_TTL = 300  # 5 minutes
MAX_CACHE_SIZE = 1000
