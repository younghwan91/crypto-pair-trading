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

Run the full pair filter and backtest pipeline offline, with no API keys and no network (the data is **synthetic**: one cointegrated pair plus two unrelated random walks):

```bash
uv run python -m quantbox.examples.offline_demo
```

Real output (synthetic data, so the numbers only prove the engine runs, not that a strategy works):

```text
Pair filter (synthetic data):
  AAAUSDT/BBBUSDT: passed=True score=0.84
  AAAUSDT/CCCUSDT: passed=False score=0.00
  CCCUSDT/DDDUSDT: passed=False score=0.26

Backtest (synthetic data, fees + slippage included):
Return: 0.20% | Sharpe: 3.67 | Max DD: 0.01% | Win Rate: 100.0% | Trades: 1
```

The script is [quantbox/examples/offline_demo.py](quantbox/examples/offline_demo.py); swap `synthetic_market()` for Binance data via `DataDownloader` (see [basic_usage.py](quantbox/examples/basic_usage.py)). For live trading (`TradingMode.LIVE`), copy `.env.example` to `.env` and export `BINANCE_API_KEY` and `BINANCE_API_SECRET`. This repo is not published on PyPI; install from source as above.

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

## More from the same author

- [quantbox](https://github.com/younghwan91/quantbox): a sibling quant framework.
- [crypto-quant-insights](https://github.com/younghwan91/crypto-quant-insights): crypto quant research notes.
- [kiwoom-client](https://github.com/younghwan91/kiwoom-client): Python client for the Kiwoom (Korean stock) API.
- [fin-checkup](https://github.com/younghwan91/fin-checkup): financial health check-up for Korean listed companies from DART filings.

## License

[MIT](LICENSE) © 2026 Younghwan Chae
