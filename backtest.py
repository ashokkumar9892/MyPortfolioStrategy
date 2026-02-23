from dataclasses import dataclass
from typing import Dict, Tuple

import pandas as pd
from backtesting import Backtest

from strategy import STRATEGY_VARIANTS


@dataclass
class BacktestResult:
    name: str
    stats: pd.Series


def run_backtests(data: pd.DataFrame, cash: float = 10000, commission: float = 0.001) -> Dict[str, BacktestResult]:
    results = {}
    for name, strat in STRATEGY_VARIANTS.items():
        bt = Backtest(data, strat, cash=cash, commission=commission, trade_on_close=True)
        stats = bt.run()
        results[name] = BacktestResult(name=name, stats=stats)
    return results


def score_result(stats: pd.Series) -> float:
    ret = float(stats.get("Return [%]", 0.0))
    sharpe = float(stats.get("Sharpe Ratio", 0.0))
    win_rate = float(stats.get("Win Rate [%]", 0.0))
    return ret * (1 + sharpe) * (1 + win_rate / 200)


def pick_best(results: Dict[str, BacktestResult]) -> Tuple[str, BacktestResult]:
    best_name = None
    best_score = float("-inf")
    best_res = None
    for name, res in results.items():
        score = score_result(res.stats)
        if score > best_score:
            best_score = score
            best_name = name
            best_res = res
    if best_name is None:
        raise RuntimeError("No backtest results")
    return best_name, best_res
