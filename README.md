# Cycle Strategy Signals

This Streamlit app runs 1D mean-reversion cycle strategies, picks the best version per ticker, and refreshes hourly.

## Setup

1. Create a Python environment.
2. Install deps:

```
pip install -r requirements.txt
```

## Optional: Polygon

Set your API key:

```
setx POLYGON_API_KEY "YOUR_KEY"
```

## Run

```
streamlit run app.py
```

## Hourly Scheduler (no VS Code needed)

This runs an hourly job that writes signals to signals.csv.

1. Run the task setup script (PowerShell):

```
scripts\create_task.ps1
```

2. The task will run every hour using Windows Task Scheduler.

## Telegram Alerts

Set these environment variables (PowerShell):

```
setx TELEGRAM_BOT_TOKEN "YOUR_BOT_TOKEN"
setx TELEGRAM_CHAT_ID "YOUR_CHAT_ID"
```

Optional alert controls:

```
setx ALERT_SIGNALS "ALL"
setx ALERT_ON_CHANGE "true"
```

ALERT_SIGNALS can be ALL or a comma-separated list like "BUY,SELL_SHORT".

## Manual hourly run (optional)

```
python run_signals.py
```

## Notes

- Default data source is yfinance. Set the Data Source selector to polygon in the UI.
- The app refreshes every hour to update signals.
