# Options Trading Model with Technical Analysis

An educational Python application that performs technical analysis on stocks and provides options trading recommendations using the Polygon.io API.

## ⚠️ Important Disclaimers

- **This is for educational purposes only**
- **Past performance does not guarantee future results**
- **Always paper trade first before using real money**
- **Risk only what you can afford to lose**
- **This is not financial advice**

## Features

- **Technical Analysis**: RSI, MACD, EMA, and Volume indicators
- **Signal Generation**: Automated buy/sell signals with confidence levels
- **Options Selection**: Smart contract filtering based on risk/reward
- **Multiple Strategies**: Calls, puts, and advanced strategies (spreads, straddles)
- **Educational Output**: Detailed explanations of why each recommendation is made

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get Polygon.io API Key

1. Sign up at [polygon.io](https://polygon.io)
2. Get your free API key from the dashboard
3. Create a `.env` file in the project root:

```bash
POLYGON_API_KEY=your_api_key_here
```

### 3. Run the Application

```bash
# Analyze a single ticker
python main.py analyze AAPL

# Analyze multiple tickers with custom lookback period
python main.py analyze AAPL TSLA NVDA --lookback 30

# Show detailed indicator values
python main.py analyze AAPL --verbose

# Output JSON for further processing
python main.py analyze AAPL --output json
```

## How It Works

### Technical Indicators

The model uses four complementary indicators:

1. **RSI (Relative Strength Index)**: Identifies overbought/oversold conditions
2. **MACD**: Detects trend changes and momentum shifts
3. **EMA (Exponential Moving Averages)**: Confirms trend direction
4. **Volume Analysis**: Validates the strength of price movements

### Signal Generation

**Bullish Signals (Call Options):**
- RSI crossing above 30 (oversold recovery)
- MACD bullish crossover
- Price above 21 EMA with 9 EMA crossing above 21 EMA
- Volume above 20-day average

**Bearish Signals (Put Options):**
- RSI crossing below 70 (overbought reversal)
- MACD bearish crossover
- Price below 21 EMA with 9 EMA crossing below 21 EMA
- Volume above 20-day average

### Options Selection

Contracts are scored based on:
- **Delta**: 0.4-0.7 for optimal risk/reward
- **Liquidity**: High open interest, tight spreads
- **Time to Expiration**: 2-6 weeks
- **Implied Volatility**: Compared to historical levels

## Project Structure

```
options_trading_algo/
├── requirements.txt
├── config.py                    # Configuration and API keys
├── src/
│   ├── data/
│   │   └── polygon_client.py    # Polygon.io API wrapper
│   ├── indicators/
│   │   └── technical.py         # Technical indicators
│   ├── strategies/
│   │   ├── signal_generator.py  # Signal generation
│   │   └── options_selector.py # Options contract selection
│   └── utils/
│       └── helpers.py           # Helper functions
└── main.py                      # CLI entry point
```

## Learning Resources

Each recommendation includes:
- **Signal Breakdown**: Which indicators triggered and why
- **Market Context**: Current trend and volatility state
- **Risk Metrics**: Maximum loss, breakeven point, probability of profit
- **Entry/Exit Plan**: Specific prices and targets
- **Learning Notes**: Educational explanations

## Next Steps

- Add backtesting capabilities
- Implement position sizing recommendations
- Create real-time monitoring mode
- Build performance tracking database

## Contributing

This is an educational project. Feel free to fork and experiment with different indicators, strategies, and risk management approaches.
