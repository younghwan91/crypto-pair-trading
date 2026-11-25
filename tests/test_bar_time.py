"""The strategy must run on bar time, not wall-clock time.

A backtest fed timezone-naive bars used to crash (aware wall-clock minus naive
bar timestamp), and with aware bars the hedge-ratio refresh compared bar time
against the wall clock, so it never fired in a historical backtest.
"""

import pandas as pd

from quantbox.backtest.runner import BacktestConfig, BacktestRunner
from quantbox.examples.offline_demo import synthetic_market
from quantbox.strategy.pair_selector import PairSelector
from quantbox.strategy.pair_strategy import PairTradingStrategy


def _naive(data):
    return {s: df.tz_localize(None) if df.index.tz else df for s, df in data.items()}


def _aware(data):
    return {s: df.tz_localize("UTC") if df.index.tz is None else df for s, df in data.items()}


def _run(data):
    config = BacktestConfig(formation_periods=240, trading_periods=48, window_shift=48)
    return BacktestRunner(config).run_backtest(data, pair_selector=PairSelector(), progress=False)


def test_backtest_accepts_naive_timestamps():
    aware = _run(_aware(synthetic_market()))
    naive = _run(_naive(synthetic_market()))
    assert len(naive["trades"]) == len(aware["trades"])
    assert len(aware["trades"]) > 0


def _feed(strategy, data, start, stop):
    for ts in data["AAAUSDT"].index[start:stop]:
        bar = {s: {"close": df.loc[ts, "Close"]} for s, df in data.items()}
        strategy.on_bar(ts, bar)


def test_hedge_refresh_uses_bar_time():
    data = _aware(synthetic_market())
    formation = {s: df.iloc[:240] for s, df in data.items()}
    strategy = PairTradingStrategy(config={"lookback_periods": 24})
    strategy.initialize_pair("AAAUSDT", "BBBUSDT", formation["AAAUSDT"], formation["BBBUSDT"])
    params = strategy.get_pair_params("AAAUSDT", "BBBUSDT")
    assert params["last_updated"] == data["AAAUSDT"].index[239]

    _feed(strategy, data, 240, 240 + 30)  # 30 hourly bars > 24h refresh interval
    last_bar = data["AAAUSDT"].index[240 + 29]
    assert data["AAAUSDT"].index[239] < params["last_updated"] <= last_bar


def test_naive_bar_timestamps_are_treated_as_utc():
    data = _naive(synthetic_market())
    strategy = PairTradingStrategy()
    strategy.initialize_pair("AAAUSDT", "BBBUSDT", data["AAAUSDT"].iloc[:240], data["BBBUSDT"].iloc[:240])
    assert strategy.get_pair_params("AAAUSDT", "BBBUSDT")["last_updated"] == pd.Timestamp("2024-01-10 23:00", tz="UTC")
