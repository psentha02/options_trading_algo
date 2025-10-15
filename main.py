#!/usr/bin/env python3
"""
Options Trading Model - Command Line Interface

This is the main entry point for the options trading analysis application.
It provides a user-friendly CLI for analyzing stocks and generating options recommendations.

Educational Features:
- Clear explanations of all analysis steps
- Detailed output with rationale for each recommendation
- Risk metrics and position sizing guidance
- Learning-focused output that teaches options trading concepts

Usage:
    python main.py analyze AAPL
    python main.py analyze AAPL TSLA NVDA --lookback 30
    python main.py analyze AAPL --verbose
    python main.py analyze AAPL --output json
"""

import click
import sys
import os
from datetime import datetime, timedelta
from tabulate import tabulate
import json

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.data.polygon_client import PolygonClient
from src.indicators.technical import TechnicalIndicators
from src.strategies.signal_generator import SignalGenerator
from src.strategies.options_selector import OptionsSelector
from src.utils.helpers import (
    format_currency, format_percentage, create_signal_summary,
    format_contract_recommendation, save_analysis_to_file
)
from config import POLYGON_API_KEY


@click.group()
def cli():
    """
    Options Trading Model - Educational Options Analysis Tool
    
    This tool performs technical analysis on stocks and provides
    educational recommendations for options trading strategies.
    
    ⚠️  IMPORTANT: This is for educational purposes only.
    Always paper trade first and never risk more than you can afford to lose.
    """
    pass


@cli.command()
@click.argument('tickers', nargs=-1, required=True)
@click.option('--lookback', default=120, help='Number of days to look back for analysis (default: 120)')
@click.option('--verbose', is_flag=True, help='Show detailed indicator values')
@click.option('--output', type=click.Choice(['table', 'json']), default='table', help='Output format')
@click.option('--max-contracts', default=5, help='Maximum number of contract recommendations')
def analyze(tickers, lookback, verbose, output, max_contracts):
    """
    Analyze ticker(s) and generate options trading recommendations.
    
    TICKERS: One or more stock symbols to analyze (e.g., AAPL, TSLA, NVDA)
    
    Examples:
        python main.py analyze AAPL
        python main.py analyze AAPL TSLA --lookback 60 --verbose
        python main.py analyze NVDA --output json
    """
    try:
        # Initialize Polygon client
        if not POLYGON_API_KEY:
            click.echo("❌ Error: POLYGON_API_KEY not found. Please set it in your .env file.", err=True)
            sys.exit(1)
        
        client = PolygonClient(POLYGON_API_KEY)
        click.echo("✅ Connected to Polygon.io API")
        
        # Process each ticker
        all_results = {}
        
        for ticker in tickers:
            click.echo(f"\n🔍 Analyzing {ticker}...")
            
            try:
                # Get price data
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=lookback + 10)).strftime('%Y-%m-%d')
                
                price_data = client.get_aggregates(
                    ticker=ticker,
                    from_date=start_date,
                    to_date=end_date,
                    limit=lookback
                )
                
                if not price_data:
                    click.echo(f"❌ No price data found for {ticker}")
                    continue
                
                # Convert to DataFrame
                import pandas as pd
                df = pd.DataFrame(price_data)
                df.columns = ['volume', 'volume_weighted', 'open', 'close', 'high', 'low', 'timestamp', 'transactions']
                df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
                
                click.echo(f"📊 Retrieved {len(df)} days of price data")
                
                # Perform technical analysis
                click.echo("📈 Calculating technical indicators...")
                indicators = TechnicalIndicators(df)
                latest_values = indicators.get_latest_values()
                signal_strength = indicators.calculate_signal_strength()
                
                # Generate signals
                click.echo("🎯 Generating trading signals...")
                signal_generator = SignalGenerator(df)
                signals = signal_generator.generate_signals()
                
                # Get options recommendations
                click.echo("🎲 Analyzing options contracts...")
                options_selector = OptionsSelector(client, signals)
                contracts = options_selector.select_contracts(ticker, max_contracts)
                
                # Store results
                all_results[ticker] = {
                    'price_data': df,
                    'latest_values': latest_values,
                    'signal_strength': signal_strength,
                    'signals': signals,
                    'contracts': contracts
                }
                
                click.echo(f"✅ Analysis complete for {ticker}")
                
            except Exception as e:
                click.echo(f"❌ Error analyzing {ticker}: {str(e)}", err=True)
                continue
        
        # Display results
        if output == 'json':
            _output_json(all_results)
        else:
            _output_table(all_results, verbose)
    
    except Exception as e:
        click.echo(f"❌ Fatal error: {str(e)}", err=True)
        sys.exit(1)


def _output_table(results, verbose):
    """Output results in table format."""
    
    for ticker, data in results.items():
        click.echo(f"\n{'='*80}")
        click.echo(f"📊 ANALYSIS RESULTS FOR {ticker}")
        click.echo(f"{'='*80}")
        
        # Current price and basic info
        latest_values = data['latest_values']
        click.echo(f"\n💰 Current Price: {format_currency(latest_values['price'])}")
        click.echo(f"📅 Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Signal summary
        signals = data['signals']
        signal_summary = create_signal_summary(signals)
        click.echo(f"\n{signal_summary}")
        
        # Technical indicators (if verbose)
        if verbose:
            click.echo(f"\n📈 TECHNICAL INDICATORS:")
            click.echo(f"  • RSI: {latest_values['rsi']:.2f}")
            click.echo(f"  • MACD: {latest_values['macd']:.4f}")
            click.echo(f"  • MACD Signal: {latest_values['macd_signal']:.4f}")
            click.echo(f"  • EMA 9: {format_currency(latest_values['ema_9'])}")
            click.echo(f"  • EMA 21: {format_currency(latest_values['ema_21'])}")
            click.echo(f"  • EMA 50: {format_currency(latest_values['ema_50'])}")
            click.echo(f"  • Volume Ratio: {latest_values['volume_ratio']:.2f}")
            click.echo(f"  • BB Upper: {format_currency(latest_values['bb_upper'])}")
            click.echo(f"  • BB Lower: {format_currency(latest_values['bb_lower'])}")
        
        # Options recommendations
        contracts = data['contracts']
        if contracts:
            click.echo(f"\n🎯 TOP OPTIONS RECOMMENDATIONS:")
            click.echo(f"{'='*80}")
            
            for i, contract in enumerate(contracts, 1):
                click.echo(f"\n#{i} - {contract.get('recommendation', 'Unknown')}")
                click.echo("-" * 40)
                
                # Contract details
                option_type = contract.get('contract_type', '').upper()
                strike = contract.get('strike_price', 0)
                expiration = contract.get('expiration_date', 'Unknown')
                days_to_expiry = contract.get('days_to_expiry', 0)
                
                click.echo(f"Contract: {option_type} ${strike} expiring {expiration} ({days_to_expiry} days)")
                
                # Pricing
                bid = contract.get('bid', 0)
                ask = contract.get('ask', 0)
                if bid > 0 and ask > 0:
                    mid_price = (bid + ask) / 2
                    spread = ask - bid
                    spread_pct = (spread / mid_price) * 100
                    click.echo(f"Pricing: Bid ${bid:.2f} | Ask ${ask:.2f} | Mid ${mid_price:.2f}")
                    click.echo(f"Spread: ${spread:.2f} ({spread_pct:.1f}%)")
                
                # Greeks
                delta = contract.get('delta', 0)
                gamma = contract.get('gamma', 0)
                theta = contract.get('theta', 0)
                vega = contract.get('vega', 0)
                iv = contract.get('implied_volatility', 0)
                
                click.echo(f"Greeks: Δ {delta:.3f} | Γ {gamma:.3f} | Θ {theta:.3f} | ν {vega:.3f}")
                click.echo(f"Implied Volatility: {format_percentage(iv)}")
                
                # Scores
                total_score = contract.get('total_score', 0)
                signal_score = contract.get('signal_score', 0)
                liquidity_score = contract.get('liquidity_score', 0)
                risk_reward_score = contract.get('risk_reward_score', 0)
                
                click.echo(f"Scores: Total {total_score:.1f}/100 | Signal {signal_score:.1f} | Liquidity {liquidity_score:.1f} | Risk/Reward {risk_reward_score:.1f}")
                
                # Rationale
                rationale = contract.get('rationale', 'No rationale provided')
                click.echo(f"Rationale: {rationale}")
                
                # Risk management
                click.echo(f"\n⚠️  RISK MANAGEMENT:")
                click.echo(f"  • Maximum Loss: {format_currency(contract.get('bid', 0))} (premium paid)")
                click.echo(f"  • Probability of Profit: {format_percentage(abs(delta))}")
                click.echo(f"  • Time Decay: ${abs(theta):.2f} per day")
                click.echo(f"  • Volatility Sensitivity: ${abs(vega):.2f} per 1% IV change")
        
        else:
            click.echo(f"\n❌ No suitable options contracts found for {ticker}")
            click.echo("This could be due to:")
            click.echo("  • No options available for this ticker")
            click.echo("  • All contracts failed liquidity/quality filters")
            click.echo("  • No clear trading signals generated")
        
        # Educational notes
        click.echo(f"\n📚 EDUCATIONAL NOTES:")
        click.echo(f"  • This analysis is for educational purposes only")
        click.echo(f"  • Always paper trade before using real money")
        click.echo(f"  • Consider your risk tolerance and position sizing")
        click.echo(f"  • Options trading involves significant risk of loss")
        click.echo(f"  • Past performance does not guarantee future results")


def _output_json(results):
    """Output results in JSON format."""
    
    # Convert results to JSON-serializable format
    json_results = {}
    
    for ticker, data in results.items():
        # Convert DataFrame to dict
        price_data = data['price_data'].to_dict('records')
        
        json_results[ticker] = {
            'analysis_date': datetime.now().isoformat(),
            'price_data': price_data,
            'latest_values': data['latest_values'],
            'signal_strength': data['signal_strength'],
            'signals': data['signals'],
            'contracts': data['contracts']
        }
    
    # Output JSON
    click.echo(json.dumps(json_results, indent=2, default=str))


@cli.command()
@click.argument('ticker')
@click.option('--days', default=30, help='Number of days to look back')
def indicators(ticker, days):
    """
    Show detailed technical indicators for a ticker.
    
    TICKER: Stock symbol to analyze
    
    This command provides a detailed breakdown of all technical indicators
    calculated for the specified ticker, useful for learning how indicators
    work and understanding their values.
    """
    try:
        # Initialize Polygon client
        if not POLYGON_API_KEY:
            click.echo("❌ Error: POLYGON_API_KEY not found. Please set it in your .env file.", err=True)
            sys.exit(1)
        
        client = PolygonClient(POLYGON_API_KEY)
        
        # Get price data
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days + 10)).strftime('%Y-%m-%d')
        
        price_data = client.get_aggregates(
            ticker=ticker,
            from_date=start_date,
            to_date=end_date,
            limit=days
        )
        
        if not price_data:
            click.echo(f"❌ No price data found for {ticker}")
            return
        
        # Convert to DataFrame
        import pandas as pd
        df = pd.DataFrame(price_data)
        df.columns = ['volume', 'volume_weighted', 'open', 'close', 'high', 'low', 'timestamp', 'transactions']
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        
        # Calculate indicators
        indicators = TechnicalIndicators(df)
        all_indicators = indicators.calculate_all_indicators()
        latest_values = indicators.get_latest_values()
        signal_strength = indicators.calculate_signal_strength()
        
        # Display results
        click.echo(f"\n📊 TECHNICAL INDICATORS FOR {ticker}")
        click.echo(f"{'='*60}")
        
        # Current price
        click.echo(f"\n💰 Current Price: {format_currency(latest_values['price'])}")
        
        # RSI
        rsi = latest_values['rsi']
        rsi_status = "Oversold" if rsi < 30 else "Overbought" if rsi > 70 else "Neutral"
        click.echo(f"\n📈 RSI (Relative Strength Index): {rsi:.2f} - {rsi_status}")
        click.echo(f"   • RSI < 30: Oversold (potential bullish reversal)")
        click.echo(f"   • RSI > 70: Overbought (potential bearish reversal)")
        click.echo(f"   • RSI 40-60: Neutral (no strong signal)")
        
        # MACD
        macd = latest_values['macd']
        macd_signal = latest_values['macd_signal']
        macd_histogram = latest_values['macd_histogram']
        macd_status = "Bullish" if macd > macd_signal else "Bearish"
        click.echo(f"\n📊 MACD: {macd:.4f} | Signal: {macd_signal:.4f} | Histogram: {macd_histogram:.4f} - {macd_status}")
        click.echo(f"   • MACD > Signal: Bullish momentum")
        click.echo(f"   • MACD < Signal: Bearish momentum")
        click.echo(f"   • Histogram: Shows momentum strength")
        
        # EMAs
        ema_9 = latest_values['ema_9']
        ema_21 = latest_values['ema_21']
        ema_50 = latest_values['ema_50']
        price = latest_values['price']
        
        click.echo(f"\n📈 EXPONENTIAL MOVING AVERAGES:")
        click.echo(f"   • EMA 9: {format_currency(ema_9)}")
        click.echo(f"   • EMA 21: {format_currency(ema_21)}")
        click.echo(f"   • EMA 50: {format_currency(ema_50)}")
        
        # EMA analysis
        if price > ema_21 > ema_50 and ema_9 > ema_21:
            ema_status = "Strong Uptrend"
        elif price < ema_21 < ema_50 and ema_9 < ema_21:
            ema_status = "Strong Downtrend"
        elif price > ema_21 and ema_9 > ema_21:
            ema_status = "Weak Uptrend"
        elif price < ema_21 and ema_9 < ema_21:
            ema_status = "Weak Downtrend"
        else:
            ema_status = "Mixed Signals"
        
        click.echo(f"   • Trend Analysis: {ema_status}")
        
        # Volume
        volume_ratio = latest_values['volume_ratio']
        volume_status = "High" if volume_ratio > 1.2 else "Normal" if volume_ratio > 0.8 else "Low"
        click.echo(f"\n📊 VOLUME ANALYSIS:")
        click.echo(f"   • Volume Ratio: {volume_ratio:.2f} - {volume_status}")
        click.echo(f"   • Ratio > 1.2: Above average volume (strong conviction)")
        click.echo(f"   • Ratio < 0.8: Below average volume (weak conviction)")
        
        # Bollinger Bands
        bb_upper = latest_values['bb_upper']
        bb_middle = latest_values['bb_middle']
        bb_lower = latest_values['bb_lower']
        
        click.echo(f"\n📊 BOLLINGER BANDS:")
        click.echo(f"   • Upper Band: {format_currency(bb_upper)}")
        click.echo(f"   • Middle Band: {format_currency(bb_middle)}")
        click.echo(f"   • Lower Band: {format_currency(bb_lower)}")
        
        # Bollinger Band position
        if price >= bb_upper:
            bb_status = "At Upper Band (Overbought)"
        elif price <= bb_lower:
            bb_status = "At Lower Band (Oversold)"
        elif price > bb_middle:
            bb_status = "Above Middle Band"
        else:
            bb_status = "Below Middle Band"
        
        click.echo(f"   • Position: {bb_status}")
        
        # Signal strength
        click.echo(f"\n🎯 SIGNAL STRENGTH:")
        click.echo(f"   • Bullish: {signal_strength['bullish']:.1f}/100")
        click.echo(f"   • Bearish: {signal_strength['bearish']:.1f}/100")
        click.echo(f"   • Neutral: {signal_strength['neutral']:.1f}/100")
        
        # Educational summary
        click.echo(f"\n📚 EDUCATIONAL SUMMARY:")
        click.echo(f"   • RSI identifies momentum extremes")
        click.echo(f"   • MACD confirms trend changes")
        click.echo(f"   • EMAs provide trend direction")
        click.echo(f"   • Volume confirms signal strength")
        click.echo(f"   • Bollinger Bands identify volatility levels")
        click.echo(f"   • Combined analysis provides trading signals")
    
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
def version():
    """Show version information."""
    click.echo("Options Trading Model v1.0.0")
    click.echo("Educational Options Analysis Tool")
    click.echo("Built with Python and Polygon.io API")


if __name__ == '__main__':
    cli()
