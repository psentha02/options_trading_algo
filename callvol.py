# options_activity.py
# Detects unusual call/put volume using Polygon.io options data

import datetime as dt
from dateutil.relativedelta import relativedelta
import numpy as np
import pandas as pd
from polygon import RESTClient

# ======== CONFIGURATION ========
API_KEY = "yZNud5OhJOB2zX7646CAKj7IEw3xzuqa"
TICKERS = [
  "AAPL","MSFT","TSLA","NVDA","AMZN","META","GOOGL","SPY","QQQ","AMD",
  "NFLX","BA","JPM","BAC","XOM","CVX","WMT","NKE","DIS","INTC",
  "COIN","PLTR","SNAP","MU","SHOP"
]
MIN_OI = 50                     # minimum open interest
MIN_NOTIONAL = 5_000            # ignore tiny trades
LOOKBACK_DAYS = 30               # baseline for average volume
DEBUG = True                    # show progress

# ================================

client = RESTClient(API_KEY)

def option_notional(contracts, last_price):
    return contracts * (last_price or 0.0) * 100.0

def avg_daily_volume_for_contract(symbol, start, end):
    try:
        bars = client.get_aggs(
            ticker=symbol,
            multiplier=1,
            timespan="day",
            from_=start.isoformat(),
            to=end.isoformat(),
            adjusted=False
        )
        vols = [b.volume for b in bars or []]
        return float(np.mean(vols)) if vols else np.nan
    except Exception:
        return np.nan

def analyze_ticker(ticker):
    today = dt.date.today()
    start = today - relativedelta(days=LOOKBACK_DAYS + 2)
    rows = []

    print(f"\nAnalyzing {ticker} ...")
    try:
        snap = client.list_snapshot_options_chain(ticker)
    except Exception as e:
        print(f"  Error fetching {ticker}: {e}")
        return pd.DataFrame()

    for c in snap:
        try:
            symbol = c.details.ticker
            opt_type = c.details.contract_type
            strike = c.details.strike_price
            expiry = c.details.expiration_date
            oi = c.open_interest or 0
            vol = c.day.volume or 0
            last_price = c.last_trade.price if c.last_trade else None
            iv = c.greeks.implied_volatility if c.greeks else np.nan
            delta = c.greeks.delta if c.greeks else np.nan

            if oi < MIN_OI or vol == 0 or last_price in (None, 0):
                continue

            avg_vol = avg_daily_volume_for_contract(symbol, start, today)
            vol_vs_avg = vol / avg_vol if (avg_vol and avg_vol > 0) else np.nan
            vol_to_oi = vol / max(1, oi)
            notional = option_notional(vol, last_price)

            score = (
                0.5 * (vol_vs_avg if not np.isnan(vol_vs_avg) else 0) +
                0.4 * vol_to_oi +
                0.1 * (abs(delta) if not np.isnan(delta) else 0)
            )
            if DEBUG:
                print(f"{symbol} | {vol} vol | OI {oi} | notional {round(notional)} | vol_vs_avg {round(vol_vs_avg,2) if vol_vs_avg==vol_vs_avg else 'NA'}")


            if notional >= MIN_NOTIONAL:
                rows.append({
                    "ticker": ticker,
                    "symbol": symbol,
                    "type": opt_type,
                    "expiry": expiry,
                    "strike": strike,
                    "last_price": last_price,
                    "volume": vol,
                    "open_interest": oi,
                    "vol_vs_avg": round(vol_vs_avg, 2) if vol_vs_avg == vol_vs_avg else np.nan,
                    "vol_to_oi": round(vol_to_oi, 2),
                    "IV": iv,
                    "delta": delta,
                    "notional": round(notional, 0),
                    "score": round(score, 3)
                })
        except Exception:
            continue

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df = df.sort_values(["score", "notional"], ascending=[False, False])
    return df


if __name__ == "__main__":
    all_df = pd.DataFrame()
    for t in TICKERS:
        df = analyze_ticker(t)
        all_df = pd.concat([all_df, df], ignore_index=True)

    if not all_df.empty:
        top = all_df.sort_values("score", ascending=False).head(20)
        print("\nTop Unusual Options Activity:")
        print(top.to_string(index=False))
    else:
        print("\nNo data returned.")
