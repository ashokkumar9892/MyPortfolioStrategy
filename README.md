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

## Notes

- Default data source is yfinance. Set the Data Source selector to polygon in the UI.
- The app refreshes every hour to update signals.
