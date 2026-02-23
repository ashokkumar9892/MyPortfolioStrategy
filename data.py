import os
from datetime import datetime, timezone
from typing import Optional

import numpy as np
import pandas as pd
import requests
import yfinance as yf

from config import DEFAULT_INTERVAL, DEFAULT_PERIOD, DATA_SOURCE_ENV, POLYGON_API_KEY_ENV


def _normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]
    df = df.rename(
        columns={
            "Open": "Open",
            "High": "High",
            "Low": "Low",
            "Close": "Close",
            "Volume": "Volume",
        }
    )
    df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
    return df


def fetch_yfinance(ticker: str, interval: str = DEFAULT_INTERVAL, period: str = DEFAULT_PERIOD) -> pd.DataFrame:
    df = yf.download(ticker, interval=interval, period=period, auto_adjust=False, progress=False)
    if df.empty:
        return df
    return _normalize_df(df)


def fetch_polygon(ticker: str, interval: str = DEFAULT_INTERVAL, period: str = DEFAULT_PERIOD) -> pd.DataFrame:
    api_key = os.getenv(POLYGON_API_KEY_ENV, "").strip()
    if not api_key:
        raise RuntimeError("POLYGON_API_KEY not set")

    if interval != "1d":
        raise ValueError("Only 1d interval supported for polygon fetch in this app")

    end = datetime.now(timezone.utc)
    start = end.replace(year=end.year - 5)
    url = (
        "https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{start}/{end}"
        "?adjusted=true&sort=asc&limit=50000&apiKey={api_key}"
    ).format(
        ticker=ticker,
        start=start.strftime("%Y-%m-%d"),
        end=end.strftime("%Y-%m-%d"),
        api_key=api_key,
    )
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    payload = resp.json()
    results = payload.get("results", [])
    if not results:
        return pd.DataFrame()

    df = pd.DataFrame(results)
    df["t"] = pd.to_datetime(df["t"], unit="ms", utc=True).dt.tz_convert(None)
    df = df.set_index("t")
    df = df.rename(columns={"o": "Open", "h": "High", "l": "Low", "c": "Close", "v": "Volume"})
    df = df[["Open", "High", "Low", "Close", "Volume"]]
    return df.dropna()


def get_price_data(ticker: str, interval: str = DEFAULT_INTERVAL, period: str = DEFAULT_PERIOD) -> pd.DataFrame:
    source = os.getenv(DATA_SOURCE_ENV, "yfinance").strip().lower()
    if source == "polygon":
        return fetch_polygon(ticker, interval=interval, period=period)
    return fetch_yfinance(ticker, interval=interval, period=period)
