"""
Polygon.io API Client

Handles all interactions with the Polygon.io API including:
- Rate limiting for starter tier (5 calls/minute)
- Caching to minimize API calls
- Error handling and retries
- Data formatting and validation

Educational Notes:
- The starter tier has a 5 calls/minute limit, so we implement rate limiting
- We cache responses to avoid redundant API calls
- Error handling ensures the application doesn't crash on API issues
"""

import requests
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import (
    POLYGON_API_KEY, POLYGON_BASE_URL, RATE_LIMIT_CALLS, RATE_LIMIT_WINDOW,
    CACHE_TTL, MAX_CACHE_SIZE
)


class RateLimiter:
    """
    Rate limiter to ensure we don't exceed Polygon.io starter tier limits.
    
    Educational Note:
    - Tracks API calls in a sliding window
    - Blocks execution if we're approaching the limit
    - Essential for free tier usage
    """
    
    def __init__(self, max_calls: int, window_seconds: int):
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self.calls = []
    
    def can_make_call(self) -> bool:
        """Check if we can make another API call without exceeding rate limit."""
        now = time.time()
        # Remove calls outside the window
        self.calls = [call_time for call_time in self.calls 
                     if now - call_time < self.window_seconds]
        return len(self.calls) < self.max_calls
    
    def record_call(self):
        """Record that we made an API call."""
        self.calls.append(time.time())
    
    def wait_if_needed(self):
        """Wait if we need to respect rate limits."""
        if not self.can_make_call():
            sleep_time = self.window_seconds - (time.time() - self.calls[0]) + 1
            if sleep_time > 0:
                print(f"Rate limit reached. Waiting {sleep_time:.1f} seconds...")
                time.sleep(sleep_time)


class Cache:
    """
    Simple in-memory cache for API responses.
    
    Educational Note:
    - Reduces API calls by storing responses temporarily
    - Uses TTL (Time To Live) to ensure data freshness
    - Helps stay within rate limits
    """
    
    def __init__(self, ttl_seconds: int, max_size: int):
        self.ttl = ttl_seconds
        self.max_size = max_size
        self.cache = {}
        self.timestamps = {}
    
    def get(self, key: str) -> Optional[Dict]:
        """Get cached data if it exists and hasn't expired."""
        if key not in self.cache:
            return None
        
        # Check if data has expired
        if time.time() - self.timestamps[key] > self.ttl:
            del self.cache[key]
            del self.timestamps[key]
            return None
        
        return self.cache[key]
    
    def set(self, key: str, value: Dict):
        """Store data in cache with timestamp."""
        # Remove oldest entries if cache is full
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.timestamps.keys(), key=lambda k: self.timestamps[k])
            del self.cache[oldest_key]
            del self.timestamps[oldest_key]
        
        self.cache[key] = value
        self.timestamps[key] = time.time()


class PolygonClient:
    """
    Main client for interacting with Polygon.io API.
    
    Educational Features:
    - Handles authentication and rate limiting
    - Provides clean methods for different data types
    - Includes comprehensive error handling
    - Caches responses to minimize API usage
    """
    
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Polygon API key is required. Set POLYGON_API_KEY in .env file")
        
        self.api_key = api_key
        self.base_url = POLYGON_BASE_URL
        self.rate_limiter = RateLimiter(RATE_LIMIT_CALLS, RATE_LIMIT_WINDOW)
        self.cache = Cache(CACHE_TTL, MAX_CACHE_SIZE)
        self.session = requests.Session()
        self.session.headers.update({'Authorization': f'Bearer {api_key}'})
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """
        Make a rate-limited API request with caching and error handling.
        
        Educational Note:
        - Checks cache first to avoid unnecessary API calls
        - Implements rate limiting to respect API limits
        - Handles common API errors gracefully
        - Returns formatted data for easy use
        """
        # Create cache key
        cache_key = f"{endpoint}_{hash(str(params)) if params else 'no_params'}"
        
        # Check cache first
        cached_data = self.cache.get(cache_key)
        if cached_data:
            print(f"Using cached data for {endpoint}")
            return cached_data
        
        # Wait for rate limit if needed
        self.rate_limiter.wait_if_needed()
        
        # Make the request
        url = f"{self.base_url}{endpoint}"
        try:
            print(f"Making API request to {endpoint}")
            response = self.session.get(url, params=params, timeout=30)
            self.rate_limiter.record_call()
            
            # Handle different response codes
            if response.status_code == 200:
                data = response.json()
                # Cache successful responses
                self.cache.set(cache_key, data)
                return data
            elif response.status_code == 429:
                print("Rate limit exceeded. Waiting before retry...")
                time.sleep(60)  # Wait a minute for rate limit reset
                return self._make_request(endpoint, params)  # Retry
            elif response.status_code == 401:
                raise ValueError("Invalid API key. Check your POLYGON_API_KEY")
            elif response.status_code == 403:
                raise ValueError("API access forbidden. Check your subscription level")
            else:
                raise Exception(f"API request failed with status {response.status_code}: {response.text}")
                
        except requests.exceptions.Timeout:
            print("Request timeout. Retrying...")
            time.sleep(5)
            return self._make_request(endpoint, params)
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {str(e)}")
    
    def get_aggregates(self, ticker: str, multiplier: int = 1, timespan: str = 'day', 
                      from_date: str = None, to_date: str = None, limit: int = 120) -> List[Dict]:
        """
        Get aggregate bars (OHLCV data) for a ticker.
        
        Educational Note:
        - This is the main data source for technical analysis
        - Returns OHLCV (Open, High, Low, Close, Volume) data
        - Can specify different timeframes (day, hour, minute)
        - Limited to 120 bars by default to stay within rate limits
        
        Args:
            ticker: Stock symbol (e.g., 'AAPL')
            multiplier: Number of timespans to aggregate (1 = single day/hour/minute)
            timespan: 'minute', 'hour', 'day', 'week', 'month', 'quarter', 'year'
            from_date: Start date in YYYY-MM-DD format
            to_date: End date in YYYY-MM-DD format
            limit: Maximum number of bars to return (max 50000)
        
        Returns:
            List of dictionaries with OHLCV data
        """
        if not from_date:
            # Default to 6 months ago if no date specified
            from_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
        
        if not to_date:
            to_date = datetime.now().strftime('%Y-%m-%d')
        
        endpoint = f"/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from_date}/{to_date}"
        params = {
            'adjusted': 'true',
            'sort': 'asc',
            'limit': min(limit, 50000)
        }
        
        data = self._make_request(endpoint, params)
        
        if 'results' not in data:
            raise Exception(f"No data returned for {ticker}. Check if ticker is valid.")
        
        return data['results']
    
    def get_options_chain(self, ticker: str, expiration_date: str = None) -> List[Dict]:
        """
        Get options contracts for a ticker.
        
        Educational Note:
        - Returns all available options contracts
        - Can filter by expiration date
        - Includes Greeks, volume, open interest, and pricing data
        - Essential for options strategy selection
        
        Args:
            ticker: Stock symbol
            expiration_date: Filter by expiration date (YYYY-MM-DD format)
        
        Returns:
            List of options contracts with pricing and Greeks
        """
        endpoint = f"/v3/reference/options/contracts"
        params = {
            'underlying_ticker': ticker,
            'limit': 1000  # Maximum allowed
        }
        
        if expiration_date:
            params['expiration_date'] = expiration_date
        
        data = self._make_request(endpoint, params)
        
        if 'results' not in data:
            print(f"No options data found for {ticker}")
            return []
        
        return data['results']
    
    def get_last_quote(self, ticker: str) -> Dict:
        """
        Get the last quote (bid/ask) for a ticker.
        
        Educational Note:
        - Provides real-time pricing data
        - Useful for calculating bid-ask spreads
        - Helps determine liquidity of options contracts
        
        Args:
            ticker: Stock symbol
        
        Returns:
            Dictionary with last quote data
        """
        endpoint = f"/v1/last_quote/stocks/{ticker}"
        
        data = self._make_request(endpoint)
        
        if 'results' not in data:
            raise Exception(f"No quote data found for {ticker}")
        
        return data['results']
    
    def get_ticker_details(self, ticker: str) -> Dict:
        """
        Get detailed information about a ticker.
        
        Educational Note:
        - Provides company information and market data
        - Useful for understanding the underlying asset
        - Helps with fundamental analysis context
        
        Args:
            ticker: Stock symbol
        
        Returns:
            Dictionary with ticker details
        """
        endpoint = f"/v3/reference/tickers/{ticker}"
        
        data = self._make_request(endpoint)
        
        if 'results' not in data:
            raise Exception(f"No details found for {ticker}")
        
        return data['results']
    
    def get_historical_volatility(self, ticker: str, days: int = 30) -> float:
        """
        Calculate historical volatility for a ticker.
        
        Educational Note:
        - Volatility is crucial for options pricing
        - Higher volatility = higher options prices
        - Helps identify if options are overpriced or underpriced
        
        Args:
            ticker: Stock symbol
            days: Number of days to calculate volatility over
        
        Returns:
            Annualized volatility as a decimal (e.g., 0.25 = 25%)
        """
        # Get recent price data
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days + 10)).strftime('%Y-%m-%d')
        
        data = self.get_aggregates(ticker, from_date=start_date, to_date=end_date, limit=days + 10)
        
        if len(data) < 2:
            raise Exception(f"Insufficient data for volatility calculation")
        
        # Calculate daily returns
        closes = [bar['c'] for bar in data]
        returns = []
        
        for i in range(1, len(closes)):
            daily_return = (closes[i] - closes[i-1]) / closes[i-1]
            returns.append(daily_return)
        
        # Calculate standard deviation of returns
        import statistics
        volatility = statistics.stdev(returns)
        
        # Annualize (assuming 252 trading days per year)
        annualized_volatility = volatility * (252 ** 0.5)
        
        return annualized_volatility


# Example usage and testing
if __name__ == "__main__":
    # Test the client (requires valid API key)
    try:
        client = PolygonClient(POLYGON_API_KEY)
        print("Polygon client initialized successfully!")
        
        # Test with a simple request
        # data = client.get_aggregates("AAPL", limit=5)
        # print(f"Retrieved {len(data)} bars for AAPL")
        
    except Exception as e:
        print(f"Error initializing client: {e}")
        print("Make sure to set POLYGON_API_KEY in your .env file")
