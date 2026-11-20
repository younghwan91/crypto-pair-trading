# QuantBox

[![LinkedIn](https://img.shields.io/badge/LinkedIn-younghwan--chae-0A66C2?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/younghwan-chae/)

**암호화폐 페어 트레이딩 프레임워크**

백테스팅과 실거래를 통합한 이벤트 기반 암호화폐 페어 트레이딩 시스템

---

## 목차

1. [설치](#설치)
2. [빠른 시작](#빠른-시작)
3. [아키텍처 개요](#아키텍처-개요)
4. [모듈별 상세 설명](#모듈별-상세-설명)
   - [Core 모듈](#1-core-모듈)
   - [Data 모듈](#2-data-모듈)
   - [Strategy 모듈](#3-strategy-모듈)
   - [Backtest 모듈](#4-backtest-모듈)
   - [Optimization 모듈](#5-optimization-모듈)
   - [Utils 모듈](#6-utils-모듈)
5. [API 레퍼런스](#api-레퍼런스)
6. [예제 코드](#예제-코드)
7. [테스트](#테스트)

---

## 설치

```bash
# 저장소 클론
git clone https://github.com/younghwan91/crypto-pair-trading.git
cd crypto-pair-trading

# uv 사용시
uv sync

# pip 사용시
pip install -e .
```

### 의존성

- Python 3.9+
- numpy, pandas, scipy, statsmodels
- numba (JIT 가속)
- pykalman (칼만 필터)
- ta (기술적 지표)
- python-binance (거래소 연동)

---

## 빠른 시작

### 1. 데이터 다운로드

```python
from quantbox.data import BinanceDataLoader

loader = BinanceDataLoader()
data = loader.download(
    symbol="BTCUSDT",
    interval="1h",
    start_date="2024-01-01",
    end_date="2024-12-31"
)
```

### 2. 페어 필터링

```python
from quantbox.strategy.filters import (
    FilterPipeline,
    CorrelationFilter,
    CointegrationFilter,
    HalfLifeFilter
)

pipeline = FilterPipeline([
    CorrelationFilter(min_corr=0.7, max_corr=0.99),
    CointegrationFilter(max_pvalue=0.05),
    HalfLifeFilter(min_hl=5, max_hl=100)
])

result = pipeline.apply(btc_prices, eth_prices)
print(f"페어 적합성: {result.passed}")
print(f"점수: {result.score:.2f}")
```

### 3. 백테스트 실행

```python
from quantbox.backtest import BacktestRunner
from quantbox.core import Config

config = Config(
    initial_capital=10000.0,
    entry_z_score=2.0,
    exit_z_score=0.5,
    trading_fee=0.0004
)

runner = BacktestRunner(config)
results = runner.run(data)
print(results.metrics.summary())
```

---

## API 키 설정

API 키는 코드나 설정 파일에 넣지 않고 환경변수로만 읽습니다. `.env.example` 을 `.env` 로 복사해
`BINANCE_API_KEY`, `BINANCE_API_SECRET`(선택: `BINANCE_TESTNET=true`)을 채운 뒤
`set -a; . ./.env; set +a` 로 불러옵니다. `.env` 는 `.gitignore` 대상입니다. 백테스트는 키 없이 동작하고,
실거래(`TradingMode.LIVE`, `LiveExecutionHandler`)는 키가 없으면 시작을 거부합니다.

## 아키텍처 개요

```
┌─────────────────────────────────────────────────────────────┐
│                        QUANTBOX                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │   Data   │───▶│ Strategy │───▶│ Backtest │              │
│  │  Module  │    │  Module  │    │  Module  │              │
│  └──────────┘    └──────────┘    └──────────┘              │
│       │              │               │                      │
│       ▼              ▼               ▼                      │
│  ┌──────────────────────────────────────────┐              │
│  │              Core Module                  │              │
│  │  (Events, Portfolio, Execution, Config)  │              │
│  └──────────────────────────────────────────┘              │
│       │              │               │                      │
│       ▼              ▼               ▼                      │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │  Utils   │    │Optimiza- │    │    UI    │              │
│  │  Module  │    │   tion   │    │  Module  │              │
│  └──────────┘    └──────────┘    └──────────┘              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 이벤트 흐름

```
MarketData ──▶ Signal ──▶ Order ──▶ Fill ──▶ Position Update
    │            │          │         │            │
    ▼            ▼          ▼         ▼            ▼
 가격 수신   신호 생성   주문 생성  체결 처리   포지션 갱신
```

---

## 모듈별 상세 설명

### 1. Core 모듈

핵심 트레이딩 엔진 컴포넌트

#### 1.1 Config (설정 관리)

```python
from quantbox.core import Config, StrategyConfig, TradingMode

# 기본 설정
config = Config(
    mode=TradingMode.BACKTEST,      # BACKTEST, PAPER, LIVE
    initial_capital=10000.0,        # 초기 자본금 (USDT)
    trading_fee=0.0004,             # 거래 수수료 (0.04%)
    slippage=0.001                  # 슬리피지 (0.1%)
)

# 전략 설정
strategy_config = StrategyConfig(
    entry_z_score=2.0,              # 진입 Z-Score 임계값
    exit_z_score=0.5,               # 청산 Z-Score 임계값
    stop_loss_z_score=3.5,          # 손절 Z-Score
    lookback_period=100,            # 룩백 기간 (봉 수)
    max_holding_period=168          # 최대 보유 기간 (시간)
)
```

**주요 파라미터:**

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `mode` | TradingMode | BACKTEST | 실행 모드 |
| `initial_capital` | float | 10000.0 | 초기 자본금 |
| `trading_fee` | float | 0.0004 | 거래 수수료 비율 |
| `slippage` | float | 0.001 | 슬리피지 비율 |
| `entry_z_score` | float | 2.0 | 진입 임계값 |
| `exit_z_score` | float | 0.5 | 청산 임계값 |

#### 1.2 Events (이벤트 시스템)

```python
from quantbox.core.events import (
    SignalEvent, OrderEvent, FillEvent,
    SignalType, OrderSide, OrderType
)

# 시그널 이벤트 생성
signal = SignalEvent(
    symbol1="BTCUSDT",
    symbol2="ETHUSDT",
    signal_type=SignalType.LONG,    # LONG, SHORT, EXIT
    z_score=2.5,
    hedge_ratio=0.5,
    strength=0.83                    # 신호 강도 (0~1)
)

# 주문 이벤트 생성
order = OrderEvent(
    symbol="BTCUSDT",
    side=OrderSide.BUY,
    order_type=OrderType.MARKET,
    quantity=0.1
)

# 체결 이벤트
fill = FillEvent(
    symbol="BTCUSDT",
    side=OrderSide.BUY,
    fill_quantity=0.1,
    fill_price=50000.0,
    commission=2.0
)
```

**이벤트 타입:**

| 이벤트 | 설명 | 주요 필드 |
|--------|------|----------|
| `SignalEvent` | 트레이딩 신호 | symbol1, symbol2, signal_type, z_score |
| `OrderEvent` | 주문 요청 | symbol, side, quantity, order_type |
| `FillEvent` | 체결 결과 | fill_price, fill_quantity, commission |
| `PositionEvent` | 포지션 변경 | symbol, quantity, entry_price |

#### 1.3 Portfolio (포트폴리오 관리)

```python
from quantbox.core.portfolio import Portfolio, Position
from quantbox.core.events import FillEvent, OrderSide

# 포트폴리오 생성
portfolio = Portfolio(initial_capital=100000.0)

# 체결 이벤트 처리
fill = FillEvent(
    symbol="BTCUSDT",
    side=OrderSide.BUY,
    fill_quantity=0.5,
    fill_price=50000.0,
    commission=10.0
)
portfolio.process_fill(fill)

# 포지션 확인
for symbol, pos in portfolio.positions.items():
    print(f"{symbol}: {pos.quantity} @ ${pos.avg_entry_price:,.0f}")
    print(f"  미실현 손익: ${pos.unrealized_pnl:+,.0f}")

# 포트폴리오 요약
print(f"총 자산: ${portfolio.total_equity:,.0f}")
print(f"현금: ${portfolio.cash:,.0f}")
print(f"드로다운: {portfolio.current_drawdown*100:.2f}%")
```

**Portfolio 주요 메서드:**

| 메서드 | 설명 |
|--------|------|
| `process_fill(fill)` | 체결 이벤트 처리 |
| `update_prices(prices)` | 시장 가격 업데이트 |
| `get_position(symbol)` | 포지션 조회 |
| `record_snapshot()` | 현재 상태 스냅샷 저장 |
| `get_performance_metrics()` | 성과 지표 계산 |

**Position 속성:**

| 속성 | 설명 |
|------|------|
| `quantity` | 보유 수량 (음수: 숏) |
| `avg_entry_price` | 평균 진입가 |
| `market_value` | 현재 시장가치 |
| `unrealized_pnl` | 미실현 손익 |
| `realized_pnl` | 실현 손익 |
| `is_long` / `is_short` | 포지션 방향 |

#### 1.4 Execution (주문 실행)

```python
from quantbox.core.execution import (
    BacktestExecutionHandler,
    LiveExecutionHandler
)

# 백테스트 실행 핸들러
backtest_exec = BacktestExecutionHandler(
    trading_fee=0.0004,
    slippage=0.001
)

# 주문 실행
fill = backtest_exec.execute_order(order, current_price=50000.0)

# 실거래 핸들러 (Binance)
# config.exchange.api_key / api_secret 은 환경변수 BINANCE_API_KEY / BINANCE_API_SECRET 에서 읽는다.
# 키가 없으면 LiveExecutionHandler 는 생성 단계에서 RuntimeError 로 거부한다.
live_exec = LiveExecutionHandler(config)
```

---

### 2. Data 모듈

데이터 수집 및 캐싱

#### 2.1 BinanceDataLoader

```python
from quantbox.data import BinanceDataLoader

loader = BinanceDataLoader()

# 단일 심볼 다운로드
btc = loader.download(
    symbol="BTCUSDT",
    interval="1h",           # 1m, 5m, 15m, 1h, 4h, 1d
    start_date="2024-01-01",
    end_date="2024-12-31"
)

# 복수 심볼 다운로드
symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"]
data = loader.download_multiple(
    symbols=symbols,
    interval="1h",
    days=90  # 최근 90일
)
```

**반환 데이터 컬럼:**

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `open` | float | 시가 |
| `high` | float | 고가 |
| `low` | float | 저가 |
| `close` | float | 종가 |
| `volume` | float | 거래량 |

#### 2.2 DataCache (캐싱 시스템)

```python
from quantbox.data.cache import DataCache, CacheConfig

# 캐시 설정
cache_config = CacheConfig(
    cache_dir="./data/cache",
    memory_cache_size=100,      # 메모리 LRU 크기
    compression=True,           # 디스크 압축
    ttl_hours=24               # 캐시 유효 시간
)

cache = DataCache(cache_config)

# 데이터 저장
cache.set("BTCUSDT_1h", btc_data)

# 데이터 조회 (메모리 -> 디스크 -> None)
data = cache.get("BTCUSDT_1h")

# 캐시 통계
stats = cache.get_stats()
print(f"히트율: {stats['hit_rate']:.1%}")
```

---

### 3. Strategy 모듈

페어 선택 및 트레이딩 전략

#### 3.1 Filters (필터)

```python
from quantbox.strategy.filters import (
    CorrelationFilter,
    CointegrationFilter,
    HalfLifeFilter,
    HurstFilter,
    StationarityFilter,
    VolumeFilter,
    FilterPipeline
)

# 개별 필터 사용
corr_filter = CorrelationFilter(min_corr=0.5, max_corr=0.99)
result = corr_filter.apply(series1, series2)
print(f"상관계수: {result.value:.4f}")
print(f"통과: {result.passed}")

# 공적분 필터
coint_filter = CointegrationFilter(max_pvalue=0.05)
result = coint_filter.apply(series1, series2)
print(f"p-value: {result.value:.4f}")

# Half-Life 필터 (평균회귀 속도)
hl_filter = HalfLifeFilter(min_hl=5, max_hl=100)
result = hl_filter.apply(series1, series2)
print(f"Half-Life: {result.value:.1f} 기간")

# Hurst 지수 필터 (0.5 미만: 평균회귀)
hurst_filter = HurstFilter(max_hurst=0.5)
result = hurst_filter.apply(series1, series2)
print(f"Hurst: {result.value:.3f}")
```

**필터 종류:**

| 필터 | 목적 | 통과 조건 |
|------|------|----------|
| `CorrelationFilter` | 상관관계 확인 | min_corr <= r <= max_corr |
| `CointegrationFilter` | 공적분 검정 | p-value < max_pvalue |
| `HalfLifeFilter` | 평균회귀 속도 | min_hl <= HL <= max_hl |
| `HurstFilter` | 시계열 특성 | H < max_hurst (평균회귀) |
| `StationarityFilter` | ADF 정상성 검정 | p-value < threshold |
| `VolumeFilter` | 최소 거래량 | volume >= min_volume |

#### 3.2 FilterPipeline

```python
# 파이프라인 구성
pipeline = FilterPipeline([
    CorrelationFilter(min_corr=0.5, max_corr=0.99),
    CointegrationFilter(max_pvalue=0.05),
    HalfLifeFilter(min_hl=5, max_hl=100),
    HurstFilter(max_hurst=0.5)
])

# 필터링 실행
result = pipeline.apply(btc_prices, eth_prices)

print(f"전체 통과: {result.passed}")
print(f"종합 점수: {result.score:.2f}")

# 개별 필터 결과
for name, detail in result.details.items():
    status = "통과" if detail['passed'] else "실패"
    print(f"  {name}: {status} (값: {detail['value']:.4f})")
```

#### 3.3 PairStrategy

```python
from quantbox.strategy import PairTradingStrategy
from quantbox.core import Config

config = Config(
    entry_z_score=2.0,
    exit_z_score=0.5,
    stop_loss_z_score=3.5,
    lookback_period=100
)

strategy = PairTradingStrategy(config)

# 신호 생성
signal = strategy.generate_signal(
    price1=btc_prices,
    price2=eth_prices,
    hedge_ratio=0.5
)

if signal:
    print(f"신호: {signal.signal_type}")
    print(f"Z-Score: {signal.z_score:.2f}")
    print(f"강도: {signal.strength:.2f}")
```

**신호 조건:**

| Z-Score | 신호 | 동작 |
|---------|------|------|
| Z > entry | SHORT | 스프레드 숏 (A 매도, B 매수) |
| Z < -entry | LONG | 스프레드 롱 (A 매수, B 매도) |
| abs(Z) < exit | EXIT | 포지션 청산 |
| abs(Z) > stop_loss | EXIT | 손절 청산 |

---

### 4. Backtest 모듈

백테스팅 및 성과 분석

#### 4.1 BacktestRunner

```python
from quantbox.backtest import BacktestRunner, BacktestConfig

config = BacktestConfig(
    initial_capital=10000.0,
    trading_fee=0.0004,
    slippage=0.001,
    entry_z_score=2.0,
    exit_z_score=0.5
)

runner = BacktestRunner(config)
results = runner.run(data)

# 결과 요약
print(results.metrics.summary())
```

#### 4.2 PerformanceMetrics

```python
from quantbox.backtest.metrics import calculate_metrics

metrics = calculate_metrics(
    equity_curve=equity_df,
    trades=trade_list,
    initial_capital=10000.0,
    risk_free_rate=0.05
)

print(f"총 수익률: {metrics.total_return_pct:.2f}%")
print(f"연환산 수익률: {metrics.annualized_return:.2f}%")
print(f"Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
print(f"Sortino Ratio: {metrics.sortino_ratio:.2f}")
print(f"Calmar Ratio: {metrics.calmar_ratio:.2f}")
print(f"최대 낙폭: {metrics.max_drawdown:.2f}%")
print(f"승률: {metrics.win_rate:.1f}%")
print(f"Profit Factor: {metrics.profit_factor:.2f}")
```

**성과 지표:**

| 지표 | 설명 | 목표 |
|------|------|------|
| `total_return_pct` | 총 수익률 (%) | 높을수록 좋음 |
| `annualized_return` | 연환산 수익률 (CAGR) | 높을수록 좋음 |
| `sharpe_ratio` | 변동성 대비 수익률 | > 1.5 양호 |
| `sortino_ratio` | 하방 변동성 대비 수익률 | > 2.0 양호 |
| `calmar_ratio` | MDD 대비 수익률 | > 1.0 양호 |
| `max_drawdown` | 최대 낙폭 (%) | < 15% 권장 |
| `win_rate` | 수익 거래 비율 (%) | > 50% 권장 |
| `profit_factor` | 총이익/총손실 | > 1.5 양호 |

#### 4.3 WalkForwardAnalysis

```python
from quantbox.backtest import WalkForwardAnalysis

wfa = WalkForwardAnalysis(
    train_periods=500,      # 훈련 기간 (봉 수)
    test_periods=100,       # 테스트 기간
    step_periods=50,        # 이동 간격
    n_folds=10             # 폴드 수
)

results = wfa.run(
    data=data,
    strategy=strategy,
    param_ranges={
        'entry_z_score': (1.5, 3.0),
        'exit_z_score': (0.2, 1.0)
    }
)

print(f"평균 IS 수익률: {results['avg_train_return']:.2f}%")
print(f"평균 OOS 수익률: {results['avg_test_return']:.2f}%")
print(f"효율성 비율: {results['efficiency_ratio']:.2f}")
```

**Walk-Forward 해석:**

| 지표 | 설명 | 판단 기준 |
|------|------|----------|
| IS Return | In-Sample 수익률 | 기준선 |
| OOS Return | Out-of-Sample 수익률 | IS의 50% 이상이면 양호 |
| Efficiency | OOS/IS 비율 | > 0.5 권장 |

---

### 5. Optimization 모듈

파라미터 최적화

#### 5.1 GridSearchOptimizer

```python
from quantbox.optimization import GridSearchOptimizer

optimizer = GridSearchOptimizer()

param_grid = {
    'entry_z_score': [1.5, 2.0, 2.5, 3.0],
    'exit_z_score': [0.25, 0.5, 0.75],
    'lookback_period': [50, 100, 150]
}

result = optimizer.optimize(
    data=data,
    strategy_class=PairTradingStrategy,
    param_grid=param_grid,
    objective='sharpe_ratio'
)

print(f"최적 파라미터: {result.best_params}")
print(f"최고 Sharpe: {result.best_score:.2f}")
```

#### 5.2 DifferentialEvolutionOptimizer

```python
from quantbox.optimization import DifferentialEvolutionOptimizer

optimizer = DifferentialEvolutionOptimizer(
    population_size=15,
    max_iterations=50,
    mutation=(0.5, 1.0),
    recombination=0.7
)

param_bounds = {
    'entry_z_score': (1.5, 3.5),
    'exit_z_score': (0.1, 1.0),
    'stop_loss_z_score': (2.5, 4.5)
}

result = optimizer.optimize(
    data=data,
    strategy_class=PairTradingStrategy,
    param_bounds=param_bounds,
    objective='sharpe_ratio'
)
```

#### 5.3 SensitivityAnalysis

```python
from quantbox.optimization import SensitivityAnalysis

analyzer = SensitivityAnalysis()

results = analyzer.analyze(
    data=data,
    strategy=strategy,
    base_params=best_params,
    param_ranges={
        'entry_z_score': (-0.5, 0.5, 0.1),  # (min_delta, max_delta, step)
        'exit_z_score': (-0.3, 0.3, 0.1)
    }
)

# 민감도 보고서
for param, sensitivity in results.items():
    print(f"{param}: 민감도 = {sensitivity['sensitivity']:.3f}")
```

---

### 6. Utils 모듈

유틸리티 함수

#### 6.1 numba_ops (Numba 가속 함수)

```python
from quantbox.utils.numba_ops import (
    calculate_rolling_zscore,
    calculate_half_life,
    calculate_hurst_exponent,
    calculate_correlation,
    ols_hedge_ratio,
    optimal_position_sizing,
    kelly_criterion
)

# Rolling Z-Score (JIT 가속)
spread = prices1 - hedge_ratio * prices2
z_scores = calculate_rolling_zscore(spread, window=100)

# Half-Life 계산
half_life = calculate_half_life(spread)
print(f"Half-Life: {half_life:.1f} 기간")

# Hurst 지수
hurst = calculate_hurst_exponent(spread)
print(f"Hurst: {hurst:.3f}")

# OLS 헤지 비율
hedge_ratio = ols_hedge_ratio(prices1, prices2)

# 최적 포지션 크기
position = optimal_position_sizing(
    capital=10000.0,
    risk_per_trade=0.02,      # 2% 리스크
    entry_price=50000.0,
    stop_loss_price=48000.0
)

# Kelly Criterion
kelly = kelly_criterion(win_rate=0.55, win_loss_ratio=1.5)
print(f"Kelly 비율: {kelly*100:.1f}%")
```

**Numba 함수 성능:**

| 함수 | 순수 Python | Numba | 속도 향상 |
|------|-------------|-------|----------|
| `rolling_zscore` | 15ms | 0.5ms | 30x |
| `half_life` | 8ms | 0.3ms | 27x |
| `hurst_exponent` | 25ms | 1.2ms | 21x |

#### 6.2 costs (거래 비용 모델)

```python
from quantbox.utils.costs import (
    TransactionCosts,
    SlippageModel,
    create_binance_futures_costs
)

# 바이낸스 선물 비용 모델
costs = create_binance_futures_costs()

# 비용 계산
cost = costs.calculate_total_cost(
    price=50000.0,
    quantity=0.1,
    is_buy=True,
    is_maker=False,      # 테이커 주문
    volume=100_000_000   # 일일 거래량
)

print(f"수수료: ${cost['commission']:.2f}")
print(f"슬리피지: ${cost['slippage']:.2f}")
print(f"총 비용: ${cost['total']:.2f}")
print(f"비용 (bps): {cost['total_bps']:.1f} bps")

# 왕복 비용 추정
roundtrip = costs.estimate_roundtrip_cost(
    entry_price=50000.0,
    quantity=0.1,
    is_maker=False,
    volume=100_000_000,
    expected_holding_8h=3  # 예상 보유 기간 (8시간 단위)
)
print(f"왕복 비용: ${roundtrip:.2f}")

# 최소 수익 목표
min_profit = costs.minimum_profit_target(
    entry_price=50000.0,
    quantity=0.1,
    risk_multiple=1.5
)
print(f"최소 수익 목표: {min_profit*100:.3f}%")
```

---

## API 레퍼런스

### 주요 클래스

| 클래스 | 모듈 | 설명 |
|--------|------|------|
| `Config` | `quantbox.core` | 전역 설정 |
| `Portfolio` | `quantbox.core` | 포트폴리오 관리 |
| `SignalEvent` | `quantbox.core.events` | 신호 이벤트 |
| `BinanceDataLoader` | `quantbox.data` | 데이터 로더 |
| `DataCache` | `quantbox.data.cache` | 캐시 시스템 |
| `FilterPipeline` | `quantbox.strategy.filters` | 필터 파이프라인 |
| `PairTradingStrategy` | `quantbox.strategy` | 페어 전략 |
| `BacktestRunner` | `quantbox.backtest` | 백테스트 실행 |
| `WalkForwardAnalysis` | `quantbox.backtest` | Walk-Forward 분석 |
| `GridSearchOptimizer` | `quantbox.optimization` | 그리드 탐색 |

### 주요 Enum

```python
from quantbox.core.events import SignalType, OrderSide, OrderType
from quantbox.core.config import TradingMode

# SignalType
SignalType.LONG      # 롱 포지션 진입
SignalType.SHORT     # 숏 포지션 진입
SignalType.EXIT      # 포지션 청산

# OrderSide
OrderSide.BUY        # 매수
OrderSide.SELL       # 매도

# OrderType
OrderType.MARKET     # 시장가
OrderType.LIMIT      # 지정가

# TradingMode
TradingMode.BACKTEST # 백테스트
TradingMode.PAPER    # 페이퍼 트레이딩
TradingMode.LIVE     # 실거래
```

---

## 예제 코드

### 완전한 백테스트 예제

```python
from quantbox.data import BinanceDataLoader
from quantbox.strategy.filters import (
    FilterPipeline, CorrelationFilter,
    CointegrationFilter, HalfLifeFilter
)
from quantbox.strategy import PairTradingStrategy
from quantbox.backtest import BacktestRunner
from quantbox.core import Config

# 1. 데이터 로드
loader = BinanceDataLoader()
btc = loader.download("BTCUSDT", "1h", days=180)
eth = loader.download("ETHUSDT", "1h", days=180)

# 2. 페어 검증
pipeline = FilterPipeline([
    CorrelationFilter(min_corr=0.7),
    CointegrationFilter(max_pvalue=0.05),
    HalfLifeFilter(min_hl=10, max_hl=80)
])

result = pipeline.apply(btc['close'], eth['close'])
if not result.passed:
    print("페어가 적합하지 않습니다")
    exit()

print(f"페어 검증 통과! 점수: {result.score:.2f}")

# 3. 백테스트 실행
config = Config(
    initial_capital=10000.0,
    entry_z_score=2.0,
    exit_z_score=0.5,
    trading_fee=0.0004
)

runner = BacktestRunner(config)
results = runner.run({'BTCUSDT': btc, 'ETHUSDT': eth})

# 4. 결과 출력
m = results.metrics
print(f"\n===== 백테스트 결과 =====")
print(f"총 수익률: {m.total_return_pct:+.2f}%")
print(f"Sharpe Ratio: {m.sharpe_ratio:.2f}")
print(f"Max Drawdown: {m.max_drawdown:.2f}%")
print(f"총 거래 수: {m.total_trades}")
print(f"승률: {m.win_rate:.1f}%")
```

---

## 테스트

```bash
# 전체 테스트 실행
pytest tests/ -v

# 특정 모듈 테스트
pytest tests/test_filters.py -v
pytest tests/test_portfolio.py -v

# 커버리지 리포트
pytest tests/ --cov=quantbox --cov-report=html
```

---

## 프로젝트 구조

```
crypto-pair-trading/
├── quantbox/
│   ├── __init__.py
│   ├── core/
│   │   ├── config.py          # 설정 관리
│   │   ├── events.py          # 이벤트 시스템
│   │   ├── portfolio.py       # 포트폴리오
│   │   ├── execution.py       # 주문 실행
│   │   └── engine.py          # 트레이딩 엔진
│   ├── data/
│   │   ├── downloader.py      # 데이터 다운로드
│   │   ├── cache.py           # 캐싱 시스템
│   │   └── preprocessor.py    # 전처리
│   ├── strategy/
│   │   ├── filters.py         # 페어 필터
│   │   ├── pair_strategy.py   # 페어 전략
│   │   └── pair_selector.py   # 페어 선택
│   ├── backtest/
│   │   ├── runner.py          # 백테스트 실행
│   │   ├── metrics.py         # 성과 지표
│   │   ├── analyzer.py        # 결과 분석
│   │   └── walk_forward.py    # Walk-Forward
│   ├── optimization/
│   │   ├── optimizer.py       # 최적화 알고리즘
│   │   ├── objective.py       # 목적 함수
│   │   └── sensitivity.py     # 민감도 분석
│   └── utils/
│       ├── numba_ops.py       # Numba 가속 함수
│       └── costs.py           # 거래 비용 모델
├── tests/                     # 유닛 테스트
├── data/                      # 데이터 캐시
└── pyproject.toml
```

---

## 면책 조항

이 소프트웨어는 교육 및 연구 목적으로만 사용해야 합니다.

- 암호화폐 거래는 원금 손실 위험이 있습니다
- 백테스트 결과가 미래 수익을 보장하지 않습니다
- 실거래 전 충분한 테스트와 검증이 필요합니다
- 투자 결정에 대한 책임은 사용자에게 있습니다
