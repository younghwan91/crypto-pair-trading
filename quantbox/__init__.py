"""
QuantBox - Professional Cryptocurrency Pair Trading Framework

A comprehensive quantitative trading framework for cryptocurrency pair trading
with unified backtesting and live trading capabilities.

Features:
- Event-driven architecture for unified backtest/live trading
- Systematic multi-timeframe data caching
- Flexible filter pipeline for pair selection
- Multiple optimization algorithms (DE, Bayesian, Grid Search)
- Walk-forward analysis and robustness testing
- Interactive analysis dashboard

Usage (offline, synthetic data; see quantbox/examples/offline_demo.py):
    from quantbox import BacktestConfig, BacktestRunner, PairSelector
    from quantbox.examples.offline_demo import synthetic_market

    data = synthetic_market()  # Dict[symbol, OHLCV DataFrame]
    runner = BacktestRunner(BacktestConfig(formation_periods=240, trading_periods=48))
    results = runner.run_backtest(data, pair_selector=PairSelector(), progress=False)
    print(results["metrics"].summary())

    Real Binance data: DataDownloader().download_multiple(...) returns the same
    Dict[symbol, DataFrame] shape (network required). Naive bar timestamps are
    treated as UTC.

Author: QuantBox Team
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "QuantBox Team"

# Core components
from quantbox.core.config import Config, TradingMode
from quantbox.core.engine import TradingEngine
from quantbox.core.events import (
    Event, EventType, MarketEvent, SignalEvent, 
    OrderEvent, FillEvent, EventQueue, SignalType
)
from quantbox.core.portfolio import Portfolio, Position, PairPosition

# Data components
from quantbox.data.cache import DataCache, TimeframedCache
from quantbox.data.downloader import DataDownloader
from quantbox.data.preprocessor import DataPreprocessor, PairData

# Strategy components
from quantbox.strategy.base import Strategy, StatefulStrategy
from quantbox.strategy.filters import (
    FilterPipeline, CorrelationFilter, CointegrationFilter,
    HalfLifeFilter, HurstFilter
)
from quantbox.strategy.pair_selector import PairSelector, PairCandidate
from quantbox.strategy.pair_strategy import PairTradingStrategy

# Backtest components
from quantbox.backtest.runner import BacktestRunner, BacktestConfig
from quantbox.backtest.metrics import PerformanceMetrics, calculate_metrics
from quantbox.backtest.analyzer import BacktestAnalyzer
from quantbox.backtest.walk_forward import WalkForwardAnalysis

# Optimization components
from quantbox.optimization.optimizer import (
    GridSearchOptimizer, RandomSearchOptimizer,
    DifferentialEvolutionOptimizer, BayesianOptimizer,
    optimize_strategy
)
from quantbox.optimization.objective import (
    SharpeObjective, CalmarObjective, MultiObjective,
    create_objective
)
from quantbox.optimization.sensitivity import SensitivityAnalyzer

__all__ = [
    # Version
    "__version__",
    
    # Core
    "Config",
    "TradingMode",
    "TradingEngine",
    "Event",
    "EventType",
    "MarketEvent",
    "SignalEvent",
    "OrderEvent",
    "FillEvent",
    "EventQueue",
    "SignalType",
    "Portfolio",
    "Position",
    "PairPosition",
    
    # Data
    "DataCache",
    "TimeframedCache",
    "DataDownloader",
    "DataPreprocessor",
    "PairData",
    
    # Strategy
    "Strategy",
    "StatefulStrategy",
    "FilterPipeline",
    "CorrelationFilter",
    "CointegrationFilter",
    "HalfLifeFilter",
    "HurstFilter",
    "PairSelector",
    "PairCandidate",
    "PairTradingStrategy",
    
    # Backtest
    "BacktestRunner",
    "BacktestConfig",
    "PerformanceMetrics",
    "calculate_metrics",
    "BacktestAnalyzer",
    "WalkForwardAnalysis",
    
    # Optimization
    "GridSearchOptimizer",
    "RandomSearchOptimizer",
    "DifferentialEvolutionOptimizer",
    "BayesianOptimizer",
    "optimize_strategy",
    "SharpeObjective",
    "CalmarObjective",
    "MultiObjective",
    "create_objective",
    "SensitivityAnalyzer",
]
