<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/images/brand/wordmark-dark.svg">
  <img alt="crypto-pair-trading" src="docs/images/brand/wordmark-light.svg" height="52">
</picture>

# crypto-pair-trading

**백테스팅과 실거래를 통합한 이벤트 기반 암호화폐 페어 트레이딩(통계적 차익거래) 프레임워크.**

바이낸스 선물 리서치와 실거래를 위해 설계했으며, 패키지 이름 `quantbox`는 같은 이름의 [younghwan91/quantbox](https://github.com/younghwan91/quantbox) 레포와는 별개입니다.

[![Python](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-younghwan--chae-0A66C2?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/younghwan-chae/)

[빠른 시작](#빠른-시작) · [가이드](docs/guide.ko.md) · [테스트](docs/guide.ko.md#테스트-및-프로젝트-구조) · [English](README.md)

</div>

## 빠른 시작

```bash
git clone https://github.com/younghwan91/crypto-pair-trading.git
cd crypto-pair-trading
uv sync
```

API 키도 네트워크도 없이 필터링과 백테스트 전체 흐름을 오프라인으로 실행할 수 있습니다. 데이터는 **합성 데이터**(공적분 페어 1쌍과 무관한 랜덤워크 2개)입니다.

```bash
uv run python -m quantbox.examples.offline_demo
```

실제 출력입니다. 합성 데이터이므로 엔진이 동작한다는 확인일 뿐, 전략의 성과를 뜻하지 않습니다.

```text
Pair filter (synthetic data):
  AAAUSDT/BBBUSDT: passed=True score=0.84
  AAAUSDT/CCCUSDT: passed=False score=0.00
  CCCUSDT/DDDUSDT: passed=False score=0.26

Backtest (synthetic data, fees + slippage included):
Return: 0.20% | Sharpe: 3.67 | Max DD: 0.01% | Win Rate: 100.0% | Trades: 1
```

스크립트는 [quantbox/examples/offline_demo.py](quantbox/examples/offline_demo.py)입니다. `synthetic_market()`을 `DataDownloader`로 받은 바이낸스 데이터로 바꾸는 방법은 [basic_usage.py](quantbox/examples/basic_usage.py)를 참고하세요. 실거래(`TradingMode.LIVE`)는 `.env.example`을 `.env`로 복사하고 `BINANCE_API_KEY`, `BINANCE_API_SECRET`을 설정합니다. 이 레포는 PyPI에 배포하지 않으므로 위처럼 소스로 설치합니다.

## 주요 기능

- **이벤트 기반 일체형 엔진**: `MarketData → Signal → Order → Fill → Position` 파이프라인이 백테스트·페이퍼·실거래(`TradingMode`)에서 동일하게 동작합니다.
- **다단계 페어 필터링**: 상관계수, 공적분(Cointegration), Half-Life, Hurst 지수, ADF 정상성, 거래량 필터를 `FilterPipeline`으로 조합합니다.
- **Numba JIT 가속 & 비용 모델**: Rolling Z-Score, Half-Life, Hurst, OLS 헤지 비율을 Numba로 20~30배 가속하고 바이낸스 선물 수수료·슬리피지를 반영합니다.
- **Walk-Forward & 최적화**: Grid Search, Differential Evolution, 민감도 분석 및 Out-of-Sample 검증을 내장합니다.

## 모듈 구성

| 모듈 | 역할 | 핵심 클래스 / 함수 |
|---|---|---|
| `quantbox.core` | 설정, 이벤트, 포트폴리오, 주문 실행 | `Config`, `Portfolio`, `SignalEvent`, `BacktestExecutionHandler`, `LiveExecutionHandler` |
| `quantbox.data` | 바이낸스 데이터 수집 및 2단계 캐시 | `BinanceDataLoader`, `DataCache`, `CacheConfig` |
| `quantbox.strategy` | 페어 필터링 및 Z-Score 전략 | `FilterPipeline`, `PairTradingStrategy` |
| `quantbox.backtest` | 백테스트 실행, 성과 지표, WFA | `BacktestRunner`, `calculate_metrics`, `WalkForwardAnalysis` |
| `quantbox.optimization` | 파라미터 최적화 및 민감도 분석 | `GridSearchOptimizer`, `DifferentialEvolutionOptimizer`, `SensitivityAnalysis` |
| `quantbox.utils` | Numba JIT 연산 및 거래 비용 모델 | `calculate_rolling_zscore`, `ols_hedge_ratio`, `TransactionCosts` |

모듈별 설정 옵션과 상세 예제는 [모듈별 상세 가이드](docs/guide.ko.md#모듈별-상세-가이드)에서 확인할 수 있습니다.

## 유의 사항

- **교육 및 연구 목적 전용**: 투자 자문이나 매매 권유 목적이 아닙니다.
- **원금 손실 위험**: 암호화폐 거래는 원금 손실 위험이 있으며, 백테스트 결과가 미래 수익을 보장하지 않습니다.
- **실거래 키 검증**: `LiveExecutionHandler`는 환경변수에 `BINANCE_API_KEY`와 `BINANCE_API_SECRET`이 없으면 시작을 거부합니다. 실거래 전 충분히 검증하시기 바랍니다.

## 문서

| 문서 | 내용 |
|---|---|
| [아키텍처 개요](docs/guide.ko.md#아키텍처-개요) | 컴포넌트 다이어그램 및 이벤트 흐름 |
| [모듈별 상세 가이드](docs/guide.ko.md#모듈별-상세-가이드) | `quantbox` 6개 모듈의 상세 API 예제 |
| [테스트 및 프로젝트 구조](docs/guide.ko.md#테스트-및-프로젝트-구조) | `pytest` 실행 명령, 커버리지, 디렉토리 구조 |
| [English README](README.md) | 영문 개요 및 빠른 시작 |

## 기여

이슈와 PR을 환영합니다. PR을 올리기 전에 `pytest tests/ -v`로 테스트를 실행해 주세요.

## 같은 저자의 도구

- [quantbox](https://github.com/younghwan91/quantbox): 형제 퀀트 프레임워크입니다.
- [crypto-quant-insights](https://github.com/younghwan91/crypto-quant-insights): 암호화폐 퀀트 리서치 노트입니다.
- [kiwoom-client](https://github.com/younghwan91/kiwoom-client): 키움 API 파이썬 클라이언트입니다.
- [fin-checkup](https://github.com/younghwan91/fin-checkup): DART 공시로 보는 한국 상장사 재무 진단입니다.

## 라이선스

[MIT](LICENSE) © 2026 Younghwan Chae
