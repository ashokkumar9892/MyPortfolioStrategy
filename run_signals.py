import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from backtest import pick_best, run_backtests
from config import DEFAULT_INTERVAL, DEFAULT_PERIOD, TICKERS
from data import get_price_data
from signals import get_signal
from telegram_alerts import send_telegram_message


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = BASE_DIR / "signals.csv"
STATE_FILE = BASE_DIR / "signals_state.json"
ALERT_SIGNALS = os.getenv("ALERT_SIGNALS", "ALL").strip().upper()
ALERT_ON_CHANGE = os.getenv("ALERT_ON_CHANGE", "true").strip().lower() in {"1", "true", "yes"}


def _load_state() -> dict:
    if not STATE_FILE.exists():
        return {}
    with STATE_FILE.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _save_state(state: dict) -> None:
    with STATE_FILE.open("w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2)


def _signal_allowed(action: str) -> bool:
    if ALERT_SIGNALS == "ALL":
        return True
    allowed = {s.strip().upper() for s in ALERT_SIGNALS.split(",") if s.strip()}
    return action.upper() in allowed


def run_once() -> pd.DataFrame:
    rows = []
    ts = datetime.now(timezone.utc).isoformat()
    state = _load_state()

    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    telegram_ready = bool(token and chat_id)

    for ticker in TICKERS:
        df = get_price_data(ticker, interval=DEFAULT_INTERVAL, period=DEFAULT_PERIOD)
        if df.empty:
            continue

        results = run_backtests(df)
        best_name, best_res = pick_best(results)
        stats = best_res.stats
        signal = get_signal(best_name, df)

        rows.append(
            {
                "timestamp": ts,
                "ticker": ticker,
                "strategy": best_name,
                "signal": signal.action,
                "reason": signal.reason,
                "last_close": round(float(df["Close"].iloc[-1]), 4),
                "return_pct": round(float(stats.get("Return [%]", 0.0)), 2),
                "sharpe": round(float(stats.get("Sharpe Ratio", 0.0)), 2),
                "win_rate_pct": round(float(stats.get("Win Rate [%]", 0.0)), 2),
            }
        )

        prev_action = state.get(ticker)
        should_alert = _signal_allowed(signal.action)
        changed = prev_action is None or prev_action != signal.action
        if telegram_ready and should_alert and (not ALERT_ON_CHANGE or changed):
            msg = (
                f"{ticker} | {signal.action}\n"
                f"Strategy: {best_name}\n"
                f"Reason: {signal.reason}\n"
                f"Last Close: {round(float(df['Close'].iloc[-1]), 4)}"
            )
            send_telegram_message(token, chat_id, msg)

        state[ticker] = signal.action

    _save_state(state)

    return pd.DataFrame(rows)


def save_results(df: pd.DataFrame) -> None:
    if df.empty:
        print("No data to save")
        return

    if OUTPUT_FILE.exists():
        existing = pd.read_csv(OUTPUT_FILE)
        combined = pd.concat([existing, df], ignore_index=True)
        combined.to_csv(OUTPUT_FILE, index=False)
    else:
        df.to_csv(OUTPUT_FILE, index=False)


if __name__ == "__main__":
    data_source = os.getenv("DATA_SOURCE", "yfinance")
    print(f"Running hourly signals with data source: {data_source}")
    result_df = run_once()
    save_results(result_df)
    print(f"Saved {len(result_df)} rows to {OUTPUT_FILE}")
