"""
統計套利策略批量優化

優化任務：OPT-037, OPT-038, OPT-040
目標：批量回測驗證 協整配對、Kalman 濾波、做市策略
執行日期：2026-03-23
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings

warnings.filterwarnings("ignore")

import sys

sys.path.append("..")
from base_strategy import BaseStrategy


# ============================================================================
# 1. 協整配對優化
# ============================================================================


class CointegrationPairOptimized(BaseStrategy):
    """優化的協整配對策略"""

    def __init__(
        self,
        lookback: int = 60,
        threshold: float = 2.0,
        use_dynamic_threshold: bool = True,
        vol_adjustment: bool = True,
    ):
        super().__init__(
            "Cointegration Pair Optimized",
            {
                "lookback": lookback,
                "threshold": threshold,
                "use_dynamic_threshold": use_dynamic_threshold,
                "vol_adjustment": vol_adjustment,
            },
            category="statistical",
        )

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        lookback = self.params["lookback"]
        threshold = self.params["threshold"]

        spread = data["close"] - data["close"].rolling(window=lookback).mean()
        spread_std = spread.rolling(window=lookback).std()

        zscore = spread / (spread_std + 1e-10)

        # 動態閾值調整
        if self.params["use_dynamic_threshold"]:
            volatility = data["close"].pct_change().rolling(window=lookback).std()
            vol_multiplier = volatility / volatility.rolling(window=lookback).mean()
            threshold = threshold * vol_multiplier

        signals = pd.Series(0, index=data.index)

        signals[zscore < -threshold] = 1
        signals[zscore > threshold] = -1

        return signals

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0:
            return 0.0

        risk_per_trade = 0.015
        risk_amount = capital * risk_per_trade

        if volatility > 0:
            shares = risk_amount / (2 * volatility)
        else:
            shares = 0

        return round(shares, 2)


# ============================================================================
# 2. Kalman 濾波優化
# ============================================================================


class KalmanFilterOptimized(BaseStrategy):
    """優化的 Kalman 濾波策略"""

    def __init__(
        self,
        process_variance: float = 1e-5,
        measurement_variance: float = 0.1,
        signal_threshold: float = 0.02,
        use_adaptive_alpha: bool = True,
    ):
        super().__init__(
            "Kalman Filter Optimized",
            {
                "process_variance": process_variance,
                "measurement_variance": measurement_variance,
                "signal_threshold": signal_threshold,
                "use_adaptive_alpha": use_adaptive_alpha,
            },
            category="statistical",
        )

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        Q = self.params["process_variance"]
        R = self.params["measurement_variance"]
        threshold = self.params["signal_threshold"]

        # 計算 Kalman alpha
        alpha = Q / (Q + R)

        # 自適應 alpha
        if self.params["use_adaptive_alpha"]:
            volatility = data["close"].pct_change().rolling(window=20).std()
            vol_avg = volatility.rolling(window=50).mean()
            vol_ratio = (volatility / vol_avg).fillna(1.0)
            # 使用標量 alpha，根據波動率調整信號閾值
            kalman = data["close"].ewm(alpha=alpha, adjust=False).mean()
            # 調整閾值
            threshold = threshold * vol_ratio
        else:
            kalman = data["close"].ewm(alpha=alpha, adjust=False).mean()

        signals = pd.Series(0, index=data.index)

        # 價格偏離閾值
        signals[data["close"] > kalman * (1 + threshold)] = -1
        signals[data["close"] < kalman * (1 - threshold)] = 1

        return signals

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0:
            return 0.0

        risk_per_trade = 0.02
        risk_amount = capital * risk_per_trade

        if volatility > 0:
            shares = risk_amount / (2 * volatility)
        else:
            shares = 0

        return round(shares, 2)


# ============================================================================
# 3. 做市策略優化
# ============================================================================


class MarketMakingOptimized(BaseStrategy):
    """優化的做市策略"""

    def __init__(
        self,
        spread_pct: float = 0.01,
        order_size_pct: float = 0.05,
        inventory_limit: float = 0.2,
        skew_factor: float = 0.5,
    ):
        super().__init__(
            "Market Making Optimized",
            {
                "spread_pct": spread_pct,
                "order_size_pct": order_size_pct,
                "inventory_limit": inventory_limit,
                "skew_factor": skew_factor,
            },
            category="execution",
        )

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        spread = self.params["spread_pct"]
        order_size = self.params["order_size_pct"]
        inventory_limit = self.params["inventory_limit"]
        skew = self.params["skew_factor"]

        # 計算中間價（使用 VWAP 近似）
        vwap = (data["close"] * data["volume"]).rolling(window=10).sum() / data["volume"].rolling(window=10).sum()

        # 買賣價
        bid = vwap * (1 - spread / 2)
        ask = vwap * (1 + spread / 2)

        signals = pd.Series(0, index=data.index)

        # 價格接近買入價 → 買入
        near_bid = (data["low"] <= bid * 1.001) & (data["close"] > data["open"])
        signals[near_bid] = 1

        # 價格接近賣出價 → 賣出
        near_ask = (data["high"] >= ask * 0.999) & (data["close"] < data["open"])
        signals[near_ask] = -1

        return signals

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0:
            return 0.0

        order_size = self.params["order_size_pct"]
        position_value = capital * order_size
        shares = position_value / price

        return round(shares, 2)


# ============================================================================
# 回測引擎
# ============================================================================


class StrategyBacktester:
    """策略回測引擎"""

    def __init__(self, initial_capital: float = 100000.0, commission_rate: float = 0.001, slippage: float = 0.001):
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage = slippage

    def backtest(self, data: pd.DataFrame, strategy: BaseStrategy) -> dict:
        signals = strategy.generate_signals(data)
        close = data["close"]

        capital = self.initial_capital
        position = 0
        trades = []
        portfolio_values = []

        for i in range(1, len(data)):
            signal = signals.iloc[i]
            price = close.iloc[i]

            if signal == 1 and position == 0:
                position = capital / price * (1 - self.commission_rate - self.slippage)
                capital = 0
                trades.append({"type": "buy", "price": price, "index": i})

            elif signal == -1 and position > 0:
                capital = position * price * (1 - self.commission_rate - self.slippage)
                position = 0
                trades.append({"type": "sell", "price": price, "index": i})

            portfolio_value = capital + position * price
            portfolio_values.append(portfolio_value)

        if position > 0:
            capital = position * close.iloc[-1] * (1 - self.commission_rate - self.slippage)
            portfolio_values.append(capital)

        portfolio_values = pd.Series(portfolio_values)
        returns = portfolio_values.pct_change().dropna()

        sharpe = np.sqrt(252) * returns.mean() / returns.std() if returns.std() > 0 else 0
        cumulative = (portfolio_values / self.initial_capital).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()

        total_return = (portfolio_values.iloc[-1] - self.initial_capital) / self.initial_capital
        num_trades = len([t for t in trades if t["type"] == "sell"])

        return {
            "total_return": total_return,
            "sharpe_ratio": sharpe,
            "max_drawdown": max_drawdown,
            "num_trades": num_trades,
            "final_value": portfolio_values.iloc[-1],
        }


def load_data(start_date: str = "2020-01-01", end_date: str = "2023-12-31") -> pd.DataFrame:
    """加載歷史數據"""
    try:
        import akshare as ak

        df = ak.stock_zh_a_hist(
            symbol="000001.SZ",
            period="daily",
            start_date=start_date.replace("-", ""),
            end_date=end_date.replace("-", ""),
            adjust="qfq",
        )

        df = df.rename(
            columns={"日期": "date", "開盤": "open", "收盤": "close", "最高": "high", "最低": "low", "成交量": "volume"}
        )
        df.set_index("date", inplace=True)

        print(f"成功加載數據：{len(df)} 天")
        return df

    except Exception as e:
        print(f"加載數據失敗：{e}")
        print("使用模擬數據...")

        dates = pd.date_range(start_date, end_date, freq="B")
        np.random.seed(42)
        prices = 10 + np.cumsum(np.random.randn(len(dates)) * 0.2)

        df = pd.DataFrame(
            {
                "open": prices + np.random.randn(len(dates)) * 0.1,
                "high": prices + np.abs(np.random.randn(len(dates))) * 0.3,
                "low": prices - np.abs(np.random.randn(len(dates))) * 0.3,
                "close": prices,
                "volume": np.random.randint(1000000, 10000000, len(dates)),
            },
            index=dates,
        )
        df.index.name = "date"

        return df


def optimize_strategy(data: pd.DataFrame, strategy_class, param_grid: dict, strategy_name: str):
    """優化單一策略"""
    from itertools import product

    backtester = StrategyBacktester()
    results = []

    param_names = list(param_grid.keys())
    param_values = list(param_grid.values())

    total = np.prod([len(v) for v in param_values])
    print(f"\n開始 {strategy_name} 參數網格搜索，總共 {total} 種組合...")

    for i, values in enumerate(product(*param_values)):
        params = dict(zip(param_names, values))
        strategy = strategy_class(**params)
        result = backtester.backtest(data, strategy)
        result.update(params)
        results.append(result)

        if (i + 1) % 5 == 0:
            print(f"進度：{i + 1}/{total}, 當前 Sharpe: {result['sharpe_ratio']:.3f}")

    df_results = pd.DataFrame(results).sort_values("sharpe_ratio", ascending=False)

    best = df_results.iloc[0]
    print(f"\n🏆 {strategy_name} 最佳結果:")
    print(f"  Sharpe: {best['sharpe_ratio']:.3f}")
    print(f"  總回報：{best['total_return'] * 100:.2f}%")
    print(f"  最大回撤：{best['max_drawdown'] * 100:.2f}%")

    return best, df_results


def main():
    """主函數"""
    print("=" * 60)
    print("統計套利 & 做市策略批量優化")
    print("=" * 60)

    # 加載數據
    print("\n[1/5] 加載歷史數據...")
    data = load_data()

    # 優化 協整配對
    print("\n[2/5] 優化 協整配對...")
    coint_best, coint_results = optimize_strategy(
        data, CointegrationPairOptimized, {"lookback": [40, 60, 80], "threshold": [1.5, 2.0, 2.5]}, "Cointegration Pair"
    )

    # 優化 Kalman 濾波
    print("\n[3/5] 優化 Kalman 濾波...")
    kalman_best, kalman_results = optimize_strategy(
        data,
        KalmanFilterOptimized,
        {"process_variance": [1e-5, 1e-4], "measurement_variance": [0.05, 0.1, 0.2], "signal_threshold": [0.01, 0.02]},
        "Kalman Filter",
    )

    # 優化 做市策略
    print("\n[4/5] 優化 做市策略...")
    mm_best, mm_results = optimize_strategy(
        data,
        MarketMakingOptimized,
        {"spread_pct": [0.005, 0.01, 0.02], "order_size_pct": [0.03, 0.05], "skew_factor": [0.3, 0.5]},
        "Market Making",
    )

    # 生成報告
    print("\n[5/5] 生成批量優化報告...")

    report = f"""# 統計套利 & 做市策略批量優化報告

**生成日期**: {datetime.now().strftime("%Y-%m-%d %H:%M")}
**優化任務**: OPT-037, OPT-038, OPT-040
**回測期間**: 3 年歷史數據

---

## 📊 優化結果總覽

| 策略 | Sharpe | 總回報 | 最大回撤 | 交易次數 |
|------|--------|--------|----------|----------|
| Cointegration | {coint_best["sharpe_ratio"]:.3f} | {coint_best["total_return"] * 100:.2f}% | {coint_best["max_drawdown"] * 100:.2f}% | - |
| Kalman Filter | {kalman_best["sharpe_ratio"]:.3f} | {kalman_best["total_return"] * 100:.2f}% | {kalman_best["max_drawdown"] * 100:.2f}% | - |
| Market Making | {mm_best["sharpe_ratio"]:.3f} | {mm_best["total_return"] * 100:.2f}% | {mm_best["max_drawdown"] * 100:.2f}% | - |

---

## 🔧 最佳參數

### 協整配對
| 參數 | 值 |
|------|-----|
| lookback | {int(coint_best["lookback"])} |
| threshold | {coint_best["threshold"]:.2f} |

### Kalman 濾波
| 參數 | 值 |
|------|-----|
| process_variance | {kalman_best["process_variance"]:.2e} |
| measurement_variance | {kalman_best["measurement_variance"]:.2f} |
| signal_threshold | {kalman_best["signal_threshold"]:.4f} |

### 做市策略
| 參數 | 值 |
|------|-----|
| spread_pct | {mm_best["spread_pct"]:.4f} |
| order_size_pct | {mm_best["order_size_pct"]:.2f} |
| skew_factor | {mm_best["skew_factor"]:.2f} |

---

**報告完成時間**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

    with open("statistical_strategies_optimization_report.md", "w", encoding="utf-8") as f:
        f.write(report)

    print("\n✅ 報告已生成：statistical_strategies_optimization_report.md")

    print("\n" + "=" * 60)
    print("批量優化完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
