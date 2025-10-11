# polygon_news_sentiment.py
import requests
import pandas as pd
from datetime import datetime
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

API_KEY = "yZNud5OhJOB2zX7646CAKj7IEw3xzuqa"
TICKERS = ["AAPL", "TSLA", "NVDA", "SPY", "QQQ"]
MODEL_NAME = "yiyanghkust/finbert-tone"  # finance-specific model

# ---- FinBERT setup ----
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
labels = ["negative", "neutral", "positive"]

def classify_sentiment(texts):
    """Return sentiment label & confidence for a list of short texts."""
    inputs = tokenizer(texts, return_tensors="pt", padding=True, truncation=True, max_length=256)
    with torch.no_grad():
        outputs = model(**inputs).logits
        probs = torch.nn.functional.softmax(outputs, dim=-1)
    conf, idx = probs.max(1)
    return [labels[i] for i in idx], conf.tolist()

def get_news_for_ticker(ticker, limit=5):
    """Fetch latest Polygon news headlines & summaries."""
    url = f"https://api.polygon.io/v2/reference/news?ticker={ticker}&limit={limit}&apiKey={API_KEY}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        if "results" not in data:
            return []
        return [{
            "ticker": ticker,
            "published_utc": n.get("published_utc", ""),
            "title": n.get("title", ""),
            "summary": n.get("description", ""),
            "source": n.get("publisher", {}).get("name", ""),
            "article_url": n.get("article_url", "")
        } for n in data["results"]]
    except Exception as e:
        print(f"Error fetching news for {ticker}: {e}")
        return []

if __name__ == "__main__":
    all_news = []
    for t in TICKERS:
        items = get_news_for_ticker(t)
        all_news.extend(items)
        print(f"Fetched {len(items)} stories for {t}")

    if all_news:
        df = pd.DataFrame(all_news)
        df["published_utc"] = pd.to_datetime(df["published_utc"], errors="coerce")
        df = df.sort_values("published_utc", ascending=False)

        # ---- Sentiment analysis ----
        texts = df["title"].fillna("").tolist()
        sentiments, confs = classify_sentiment(texts)
        df["sentiment"] = sentiments
        df["confidence"] = confs

        # ---- Aggregate per ticker ----
        sentiment_map = {"positive": 1, "neutral": 0, "negative": -1}
        df["sentiment_score"] = df["sentiment"].map(sentiment_map)
        summary = df.groupby("ticker")["sentiment_score"].mean().round(2)

        print("\nHeadline Sentiment:")
        for t, s in summary.items():
            label = "Bullish" if s > 0.2 else "Bearish" if s < -0.2 else "Neutral"
            print(f"{t}: {label} ({s:+.2f})")

        print("\nRecent Headlines with Sentiment:")
        for _, r in df.head(10).iterrows():
            ts = r["published_utc"].strftime("%Y-%m-%d %H:%M") if pd.notnull(r["published_utc"]) else ""
            print(f"[{ts}] {r['ticker']} ({r['sentiment']}): {r['title']} ({r['source']})")

        # optional save
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        df.to_csv(f"polygon_news_sentiment_{date_str}.csv", index=False)
        print(f"\nSaved {len(df)} headlines with sentiment to polygon_news_sentiment_{date_str}.csv")
    else:
        print("\nNo news returned (API delay or no recent headlines).")
