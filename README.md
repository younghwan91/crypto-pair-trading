<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/images/brand/wordmark-dark.svg">
  <img alt="crypto-pair-trading" src="docs/images/brand/wordmark-light.svg" height="52">
</picture>

# crypto-pair-trading

**Event-driven crypto pair trading (statistical arbitrage) framework unifying backtesting and live execution.**

Built for Binance futures research and live trading; package name `quantbox` is separate from [younghwan91/quantbox](https://github.com/younghwan91/quantbox).

[![Python](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-younghwan--chae-0A66C2?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/younghwan-chae/)

[Quick start](#quick-start) · [Guide](docs/guide.md) · [Testing](docs/guide.md#testing--project-structure) · [한국어](README.ko.md)

</div>

## Quick start

```bash
git clone https://github.com/younghwan91/crypto-pair-trading.git
cd crypto-pair-trading
uv sync
```

Run a pair filter and backtest on Binance historical data without API keys:

```python
from quantbox.data import BinanceDataLoader
from quantbox.strategy.filters import (
    FilterPipeline, CorrelationFilter, CointegrationFilter, HalfLifeFilter
)
from quantbox.backtest import BacktestRunner
from quantbox.core import Config

loader = BinanceDataLoader()
btc = loader.download("BTCUSDT", interval="1h", start_date="2024-01-01", end_date="2024-12-31")
eth = loader.download("ETHUSDT", interval="1h", start_date="2024-01-01", end_date="2024-12-31")

pipeline = FilterPipeline([
    CorrelationFilter(min_corr=0.7, max_corr=0.99),
    CointegrationFilter(max_pvalue=0.05),
    HalfLifeFilter(min_hl=5, max_hl=100),
])
result = pipeline.apply(btc["close"], eth["close"])
print(f"Pair passed: {result.passed} (score: {result.score:.2f})")

config = Config(initial_capital=10000.0, entry_z_score=2.0, exit_z_score=0.5, trading_fee=0.0004)
results = BacktestRunner(config).run({"BTCUSDT": btc, "ETHUSDT": eth})
print(results.metrics.summary())
```

You will see the pair filter pass/fail result and a summary of backtest return, Sharpe ratio, drawdown, and trade statistics. For live trading (`TradingMode.LIVE`), copy `.env.example` to `.env` and export `BINANCE_API_KEY` and `BINANCE_API_SECRET`.

## What it does

- **Unified Event-Driven Engine**: Runs the same `MarketData → Signal → Order → Fill → Position` pipeline across backtest, paper, and live (`TradingMode`) execution.
- **Multi-Stage Pair Filtering**: Combines correlation, cointegration, half-life, Hurst exponent, ADF stationarity, and volume filters via `FilterPipeline`.
- **Numba JIT Acceleration & Cost Modeling**: Accelerates rolling Z-Score, half-life, Hurst, and OLS hedge ratio 20–30x with Numba, factoring in Binance futures fees and slippage.
- **Walk-Forward & Optimization**: Includes Grid Search, Differential Evolution, sensitivity analysis, and out-of-sample validation.

## Modules

| Module | Role | Key Classes / Functions |
|---|---|---|
| `quantbox.core` | Config, events, portfolio, order execution | `Config`, `Portfolio`, `SignalEvent`, `BacktestExecutionHandler`, `LiveExecutionHandler` |
| `quantbox.data` | Binance data ingestion & 2-tier cache | `BinanceDataLoader`, `DataCache`, `CacheConfig` |
| `quantbox.strategy` | Pair filtering & Z-Score strategy | `FilterPipeline`, `PairTradingStrategy` |
| `quantbox.backtest` | Backtest runner, performance metrics, WFA | `BacktestRunner`, `calculate_metrics`, `WalkForwardAnalysis` |
| `quantbox.optimization` | Parameter optimization & sensitivity analysis | `GridSearchOptimizer`, `DifferentialEvolutionOptimizer`, `SensitivityAnalysis` |
| `quantbox.utils` | Numba JIT ops & transaction cost model | `calculate_rolling_zscore`, `ols_hedge_ratio`, `TransactionCosts` |

See the [Module Guide](docs/guide.md#module-guide) for configuration options and usage examples for each module.

## Caveats

- **Educational and research use only**: This framework is not financial advice.
- **Risk of loss**: Cryptocurrency trading carries risk of principal loss, and backtest results do not guarantee future returns.
- **Live trading guard**: `LiveExecutionHandler` refuses to start unless `BINANCE_API_KEY` and `BINANCE_API_SECRET` are set in environment variables; test thoroughly before live execution.

## Docs

| Doc | What's inside |
|---|---|
| [Architecture Overview](docs/guide.md#architecture-overview) | Component diagram and event flow |
| [Module Guide](docs/guide.md#module-guide) | Detailed API examples for all 6 `quantbox` modules |
| [Testing & Project Structure](docs/guide.md#testing--project-structure) | `pytest` commands, coverage, and directory layout |
| [한국어 README](README.ko.md) | Korean overview and quick start |

## Contributing

Issues and pull requests are welcome. Run the test suite with `pytest tests/ -v` before opening a PR.

## License

[MIT](LICENSE) © 2026 Younghwan Chae
