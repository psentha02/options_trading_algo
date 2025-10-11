# options_activity_concurrent.py
# Fast multi-ticker unusual options volume scanner using Polygon.io

import datetime as dt
import numpy as np
import pandas as pd
from polygon import RESTClient
from concurrent.futures import ThreadPoolExecutor, as_completed

# ===== CONFIGURATION =====
API_KEY = "yZNud5OhJOB2zX7646CAKj7IEw3xzuqa"
TICKERS = [
    "AAPL","MSFT","TSLA","NVDA","AMZN","META","GOOGL","SPY","QQQ","AMD",
    "NFLX","BA","JPM","BAC","XOM","CVX","WMT","NKE","DIS","INTC",
    "COIN","PLTR","SNAP","MU","SHOP"
]
MIN_OI = 10
MIN_NOTIONAL = 1000
MAX_WORKERS = 8     # number of concurrent threads
# =========================

client = RESTClient(API_KEY)

def option_notional(contracts, last_price):
    return contracts * (last_price or 0.0) * 100.0

def analyze_ticker(ticker):
    rows = []
    try:
        for c in client.list_snapshot_options_chain(ticker):
            try:
                oi = c.open_interest or 0
                vol = c.day.volume or 0
                last_price = c.last_trade.price if c.last_trade else None
                if oi < MIN_OI or vol == 0 or not last_price:
                    continue

                iv = c.greeks.implied_volatility if c.greeks else np.nan
                delta = c.greeks.delta if c.greeks else np.nan
                notional = option_notional(vol, last_price)
                if notional < MIN_NOTIONAL:
                    continue

                # simple fast "unusual" score: heavy relative volume + delta magnitude
                score = 0.7 * (vol / max(1, oi)) + 0.3 * (abs(delta) if not np.isnan(delta) else 0)

                rows.append({
                    "ticker": ticker,
                    "symbol": c.details.ticker,
                    "type": c.details.contract_type,
                    "expiry": c.details.expiration_date,
                    "strike": c.details.strike_price,
                    "last_price": last_price,
                    "volume": vol,
                    "open_interest": oi,
                    "IV": iv,
                    "delta": delta,
                    "notional": round(notional, 0),
                    "score": round(score, 3)
                })
            except Exception:
                continue
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
    return pd.DataFrame(rows)


if __name__ == "__main__":
    print(f"Scanning {len(TICKERS)} tickers concurrently...\n")

    all_df = pd.DataFrame()
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(analyze_ticker, t): t for t in TICKERS}
        for f in as_completed(futures):
            t = futures[f]
            df = f.result()
            if not df.empty:
                all_df = pd.concat([all_df, df], ignore_index=True)
            print(f"Done: {t}, {len(df)} option contracts analyzed")

    if not all_df.empty:
        top = all_df.sort_values("score", ascending=False).head(25)
        print("\nTop Unusual Options Activity:")
        print(top.to_string(index=False))
    else:
        print("\nNo data returned (market likely closed or all filters excluded).")
