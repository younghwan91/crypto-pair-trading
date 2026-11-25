"""Offline demo: runs the real filter pipeline and backtest engine on SYNTHETIC data.

No API keys, no network. The prices are generated (a cointegrated pair plus two
unrelated random walks), so the numbers below are a smoke test of the engine,
not evidence of any edge.

    uv run python -m quantbox.examples.offline_demo
"""

import numpy as np
import pandas as pd

from quantbox.backtest.runner import BacktestConfig, BacktestRunner
from quantbox.strategy.filters import (
    CointegrationFilter, CorrelationFilter, FilterPipeline, HalfLifeFilter,
)
from quantbox.strategy.pair_selector import PairSelector


def synthetic_market(n: int = 1500, seed: int = 7) -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2024-01-01", periods=n, freq="h")  # naive, like most CSV/exchange dumps
    base = np.cumsum(rng.normal(0, 0.02, n))
    spread = np.zeros(n)
    for i in range(1, n):  # mean-reverting (Ornstein-Uhlenbeck) spread
        spread[i] = 0.9 * spread[i - 1] + rng.normal(0, 0.006)
    paths = {
        "AAAUSDT": 100 * np.exp(base),
        "BBBUSDT": 50 * np.exp(base + spread),  # cointegrated with AAA
        "CCCUSDT": 30 * np.exp(np.cumsum(rng.normal(0, 0.01, n))),  # independent
        "DDDUSDT": 10 * np.exp(np.cumsum(rng.normal(0, 0.01, n))),  # independent
    }
    return {
        s: pd.DataFrame({"Open": p, "High": p * 1.001, "Low": p * 0.999,
                         "Close": p, "Volume": 1000.0}, index=idx)
        for s, p in paths.items()
    }


def main() -> None:
    data = synthetic_market()
    pipeline = FilterPipeline([
        CorrelationFilter(min_correlation=0.7, max_correlation=0.99),
        CointegrationFilter(max_pvalue=0.05),
        HalfLifeFilter(min_half_life=2, max_half_life=100),
    ])
    print("Pair filter (synthetic data):")
    for a, b in [("AAAUSDT", "BBBUSDT"), ("AAAUSDT", "CCCUSDT"), ("CCCUSDT", "DDDUSDT")]:
        passed, score, _ = pipeline.apply(data[a]["Close"], data[b]["Close"])
        print(f"  {a}/{b}: passed={passed} score={score:.2f}")

    config = BacktestConfig(formation_periods=240, trading_periods=48, window_shift=48)
    runner = BacktestRunner(config)
    results = runner.run_backtest(data, pair_selector=PairSelector(), progress=False)
    print("\nBacktest (synthetic data, fees + slippage included):")
    print(results["metrics"].summary())
    print(f"Trades: {len(results['trades'])}")


if __name__ == "__main__":
    main()
