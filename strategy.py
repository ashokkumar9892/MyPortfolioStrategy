import numpy as np
import pandas as pd
from backtesting import Strategy
from backtesting.lib import crossover


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def bollinger_bands(series: pd.Series, period: int = 20, std: float = 2.0):
    sma = series.rolling(period).mean()
    dev = series.rolling(period).std()
    upper = sma + std * dev
    lower = sma - std * dev
    return sma, upper, lower


def zscore(series: pd.Series, period: int = 50) -> pd.Series:
    mean = series.rolling(period).mean()
    std = series.rolling(period).std()
    return (series - mean) / std


def stochastic_k(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    lowest = low.rolling(period).min()
    highest = high.rolling(period).max()
    return 100 * (close - lowest) / (highest - lowest)


class MeanReversionRSIBB(Strategy):
    rsi_period = 14
    bb_period = 20
    bb_std = 2.0
    trend_period = 200

    def init(self):
        close = self.data.Close
        self.rsi = self.I(rsi, close, self.rsi_period)
        self.bb_mid, self.bb_up, self.bb_low = self.I(bollinger_bands, close, self.bb_period, self.bb_std)
        self.trend = self.I(lambda s: s.rolling(self.trend_period).mean(), close)

    def next(self):
        close = self.data.Close[-1]
        rsi_v = self.rsi[-1]
        bb_mid = self.bb_mid[-1]
        bb_up = self.bb_up[-1]
        bb_low = self.bb_low[-1]
        trend = self.trend[-1]

        uptrend = close >= trend
        downtrend = close < trend

        if not self.position:
            if uptrend and close < bb_low and rsi_v < 30:
                self.buy()
            elif downtrend and close > bb_up and rsi_v > 70:
                self.sell()
        else:
            if self.position.is_long and (close > bb_mid or rsi_v > 50):
                self.position.close()
            elif self.position.is_short and (close < bb_mid or rsi_v < 50):
                self.position.close()


class ZScoreRSI(Strategy):
    z_period = 50
    rsi_period = 14

    def init(self):
        close = self.data.Close
        self.z = self.I(zscore, close, self.z_period)
        self.rsi = self.I(rsi, close, self.rsi_period)

    def next(self):
        z_v = self.z[-1]
        rsi_v = self.rsi[-1]

        if not self.position:
            if z_v < -1.5 and rsi_v < 35:
                self.buy()
            elif z_v > 1.5 and rsi_v > 65:
                self.sell()
        else:
            if self.position.is_long and z_v > -0.2:
                self.position.close()
            elif self.position.is_short and z_v < 0.2:
                self.position.close()


class StochRSIReversal(Strategy):
    rsi_period = 14
    stoch_period = 14
    stoch_signal = 3

    def init(self):
        close = self.data.Close
        self.rsi = self.I(rsi, close, self.rsi_period)
        self.k = self.I(stochastic_k, self.data.High, self.data.Low, close, self.stoch_period)
        self.d = self.I(lambda s: pd.Series(s).rolling(self.stoch_signal).mean(), self.k)

    def next(self):
        k_v = self.k[-1]
        d_v = self.d[-1]
        rsi_v = self.rsi[-1]

        if not self.position:
            if k_v < 20 and d_v < 20 and rsi_v < 40:
                self.buy()
            elif k_v > 80 and d_v > 80 and rsi_v > 60:
                self.sell()
        else:
            if self.position.is_long and (k_v > 50 or rsi_v > 55):
                self.position.close()
            elif self.position.is_short and (k_v < 50 or rsi_v < 45):
                self.position.close()


STRATEGY_VARIANTS = {
    "MeanReversionRSIBB": MeanReversionRSIBB,
    "ZScoreRSI": ZScoreRSI,
    "StochRSIReversal": StochRSIReversal,
}
