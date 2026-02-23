import os
from typing import Dict

import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from backtest import pick_best, run_backtests
from config import DEFAULT_INTERVAL, DEFAULT_PERIOD, TICKERS
from data import get_price_data
from signals import get_signal


st.set_page_config(page_title="Cycle Strategy Signals", layout="wide")
st.title("Cycle Strategy - 1D Mean Reversion")

st_autorefresh(interval=60 * 60 * 1000, key="hourly-refresh")

with st.sidebar:
    st.header("Settings")
    tickers = st.multiselect("Tickers", TICKERS, default=TICKERS)
    data_source = st.selectbox("Data Source", ["yfinance", "polygon"], index=0)
    os.environ["DATA_SOURCE"] = data_source
    st.caption("Backtests run automatically every hour. Set POLYGON_API_KEY env var if using Polygon.")


@st.cache_data(ttl=60 * 60)
def load_data(ticker: str) -> pd.DataFrame:
    return get_price_data(ticker, interval=DEFAULT_INTERVAL, period=DEFAULT_PERIOD)


@st.cache_data(ttl=60 * 60)
def run_backtests_cached(ticker: str, df: pd.DataFrame):
    results = run_backtests(df)
    best_name, best_res = pick_best(results)
    stats = best_res.stats
    return best_name, {
        "Return %": round(float(stats.get("Return [%]", 0.0)), 2),
        "Sharpe": round(float(stats.get("Sharpe Ratio", 0.0)), 2),
        "Win Rate %": round(float(stats.get("Win Rate [%]", 0.0)), 2),
    }


st.subheader("Backtest Comparison (auto-refresh hourly)")

results_table = []

for ticker in tickers:
    df = load_data(ticker)
    if df.empty:
        st.warning(f"No data for {ticker}")
        continue

    best_name, stats = run_backtests_cached(ticker, df)
    results_table.append(
        {
            "Ticker": ticker,
            "Best Strategy": best_name,
            "Return %": stats["Return %"],
            "Sharpe": stats["Sharpe"],
            "Win Rate %": stats["Win Rate %"],
        }
    )

    signal = get_signal(best_name, df)
    st.write(
        {
            "Ticker": ticker,
            "Strategy": best_name,
            "Signal": signal.action,
            "Reason": signal.reason,
            "Last Close": round(float(df["Close"].iloc[-1]), 4),
        }
    )

if results_table:
    st.dataframe(pd.DataFrame(results_table), use_container_width=True)
