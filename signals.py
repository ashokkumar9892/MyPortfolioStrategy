from dataclasses import dataclass
from typing import Dict

import pandas as pd

from strategy import STRATEGY_VARIANTS, MeanReversionRSIBB, ZScoreRSI, StochRSIReversal, rsi, bollinger_bands, zscore, stochastic_k


@dataclass
class Signal:
    action: str
    reason: str


def _signal_mean_reversion(df: pd.DataFrame) -> Signal:
    close = df["Close"]
    rsi_v = rsi(close).iloc[-1]
    bb_mid, bb_up, bb_low = bollinger_bands(close)
    trend = close.rolling(200).mean().iloc[-1]
    last = close.iloc[-1]

    if last >= trend and last < bb_low.iloc[-1] and rsi_v < 30:
        return Signal("BUY", "Price below lower BB with RSI oversold in uptrend")
    if last < trend and last > bb_up.iloc[-1] and rsi_v > 70:
        return Signal("SELL_SHORT", "Price above upper BB with RSI overbought in downtrend")
    if last > bb_mid.iloc[-1] and rsi_v > 50:
        return Signal("SELL", "Mean reversion achieved")
    if last < bb_mid.iloc[-1] and rsi_v < 50:
        return Signal("COVER", "Mean reversion achieved")
    return Signal("HOLD", "No edge")


def _signal_zscore(df: pd.DataFrame) -> Signal:
    close = df["Close"]
    z = zscore(close).iloc[-1]
    rsi_v = rsi(close).iloc[-1]

    if z < -1.5 and rsi_v < 35:
        return Signal("BUY", "Z-score and RSI oversold")
    if z > 1.5 and rsi_v > 65:
        return Signal("SELL_SHORT", "Z-score and RSI overbought")
    if z > -0.2:
        return Signal("SELL", "Z-score reverted")
    if z < 0.2:
        return Signal("COVER", "Z-score reverted")
    return Signal("HOLD", "No edge")


def _signal_stoch(df: pd.DataFrame) -> Signal:
    close = df["Close"]
    k = stochastic_k(df["High"], df["Low"], close).iloc[-1]
    rsi_v = rsi(close).iloc[-1]

    if k < 20 and rsi_v < 40:
        return Signal("BUY", "Stoch/RSI oversold")
    if k > 80 and rsi_v > 60:
        return Signal("SELL_SHORT", "Stoch/RSI overbought")
    if k > 50 or rsi_v > 55:
        return Signal("SELL", "Momentum mean reversion")
    if k < 50 or rsi_v < 45:
        return Signal("COVER", "Momentum mean reversion")
    return Signal("HOLD", "No edge")


def get_signal(strategy_name: str, df: pd.DataFrame) -> Signal:
    if strategy_name == "MeanReversionRSIBB":
        return _signal_mean_reversion(df)
    if strategy_name == "ZScoreRSI":
        return _signal_zscore(df)
    if strategy_name == "StochRSIReversal":
        return _signal_stoch(df)
    return Signal("HOLD", "Unknown strategy")
