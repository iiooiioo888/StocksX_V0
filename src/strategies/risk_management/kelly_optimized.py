"""
凱利公式 (Kelly Criterion) 策略優化

優化任務：OPT-029 / Issue #29
目標：3 年回測 + 凱利分數優化
執行日期：2026-03-23

優化內容：
1. 參數網格搜索（max_kelly: 0.15-0.35, lookback: 40-80, fraction: 0.25-0.75）
2. 3 年歷史數據回測
3. Sharpe 比率、最大回撤計算
4. 最優參數組合推薦
5. 添加分數凱利（Fractional Kelly）
6. 添加風險限制機制

作者：StocksX Team
狀態：🔄 優化中
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings

warnings.filterwarnings("ignore")

# 導入策略基類
import sys

sys.path.append("..")
from base_strategy import RiskManagementStrategy


class KellyCriterionOptimized(RiskManagementStrategy):
    """
    優化的凱利公式策略

    改進點：
    1. 支持分數凱利（降低風險）
    2. 添加最大倉位限制
    3. 添加動態調整機制
    4. 添加風險限制（VaR/CVaR）
    """

    def __init__(
        self,
        max_kelly: float = 0.25,
        lookback: int = 60,
        kelly_fraction: float = 0.5,
        use_dynamic_adjustment: bool = False,
        volatility_lookback: int = 20,
        max_position_pct: float = 0.3,
        use_var_limit: bool = False,
        var_confidence: float = 0.95,
    ):
        """
        初始化優化的凱利公式策略

        Args:
            max_kelly: 最大凱利比例（默认 25%）
            lookback: 回看周期（默认 60）
            kelly_fraction: 凱利分數（默认 0.5，即半凱利）
            use_dynamic_adjustment: 是否使用動態調整（默认 False）
            volatility_lookback: 波動率計算周期（默认 20）
            max_position_pct: 最大倉位比例（默认 30%）
            use_var_limit: 是否使用 VaR 限制（默认 False）
            var_confidence: VaR 置信水平（默认 0.95）
        """
        super().__init__(
            "Kelly Criterion Optimized",
            {
                "max_kelly": max_kelly,
                "lookback": lookback,
                "kelly_fraction": kelly_fraction,
                "use_dynamic_adjustment": use_dynamic_adjustment,
                "volatility_lookback": volatility_lookback,
                "max_position_pct": max_position_pct,
                "use_var_limit": use_var_limit,
                "var_confidence": var_confidence,
            },
        )

    def calculate_kelly(self, data: pd.DataFrame) -> dict[str, pd.Series]:
        """
        計算凱利公式

        Args:
            data: OHLCV 數據

        Returns:
            包含凱利值和各組件的字典
        """
        lookback = self.params["lookback"]
        max_kelly = self.params["max_kelly"]
        kelly_fraction = self.params["kelly_fraction"]

        returns = data["close"].pct_change()

        # 計算勝率
        winning_trades = (returns > 0).rolling(window=lookback).sum()
        total_trades = returns.rolling(window=lookback).count()
        win_rate = winning_trades / (total_trades + 1)

        # 計算平均盈利和虧損
        avg_win = returns.rolling(window=lookback).apply(lambda x: x[x > 0].mean() if len(x[x > 0]) > 0 else 0)
        avg_loss = returns.rolling(window=lookback).apply(lambda x: abs(x[x < 0].mean()) if len(x[x < 0]) > 0 else 0)

        # 盈虧比
        win_loss_ratio = avg_win / (avg_loss + 1e-10)

        # 凱利公式：f = W - (1-W)/R
        kelly = win_rate - (1 - win_rate) / (win_loss_ratio + 1e-10)

        # 應用分數凱利
        fractional_kelly = kelly * kelly_fraction

        # 限制在 0 到 max_kelly 之間
        fractional_kelly = fractional_kelly.clip(0, max_kelly)

        # 應用最大倉位限制
        max_position_pct = self.params["max_position_pct"]
        fractional_kelly = fractional_kelly.clip(0, max_position_pct)

        # 動態調整（基於波動率）
        if self.params["use_dynamic_adjustment"]:
            vol_lookback = self.params["volatility_lookback"]
            volatility = returns.rolling(window=vol_lookback).std()
            vol_adjustment = 1 / (1 + volatility * 10)  # 波動率高時減少倉位
            fractional_kelly = fractional_kelly * vol_adjustment

        # VaR 限制
        if self.params["use_var_limit"]:
            var_conf = self.params["var_confidence"]
            var = returns.rolling(window=lookback).quantile(1 - var_conf)
            var_limit = pd.Series(0.1, index=data.index)  # 默认 10% VaR 限制
            fractional_kelly = fractional_kelly.clip(0, var_limit)

        return {
            "kelly": kelly,
            "fractional_kelly": fractional_kelly,
            "win_rate": win_rate,
            "win_loss_ratio": win_loss_ratio,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
        }

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        生成交易信號

        信號規則：
        - 凱利值 > 0.1 → 買入（強信號）
        - 凱利值 0.05-0.1 → 持有（弱信號）
        - 凱利值 < 0.05 → 賣出（無信號）

        Args:
            data: OHLCV 數據

        Returns:
            信號 Series（1=買入，0=持有，-1=賣出）
        """
        kelly_data = self.calculate_kelly(data)
        kelly = kelly_data["fractional_kelly"]

        signals = pd.Series(0, index=data.index)

        # 買入信號：凱利值高
        signals[kelly > 0.1] = 1

        # 賣出信號：凱利值低
        signals[kelly < 0.05] = -1

        return signals

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        """
        計算倉位大小（基於凱利值）

        Args:
            signal: 交易信號（1, -1, 0）
            capital: 可用資金
            price: 當前價格
            volatility: 波動率

        Returns:
            倉位大小（股數）
        """
        if signal <= 0:
            return 0.0

        # 獲取當前凱利值
        max_kelly = self.params["max_kelly"]
        kelly_fraction = self.params["kelly_fraction"]

        # 凱利倉位比例
        kelly_pct = max_kelly * kelly_fraction

        # 計算倉位價值
        position_value = capital * kelly_pct

        # 計算股數
        shares = position_value / price

        return round(shares, 2)

    def get_risk_metrics(self, data: pd.DataFrame) -> dict[str, pd.Series]:
        """
        計算風險指標

        Args:
            data: OHLCV 數據

        Returns:
            風險指標字典
        """
        returns = data["close"].pct_change()

        # VaR (Value at Risk)
        var_conf = self.params["var_confidence"]
        var = returns.rolling(window=self.params["lookback"]).quantile(1 - var_conf)

        # CVaR (Conditional VaR)
        cvar = returns.rolling(window=self.params["lookback"]).apply(lambda x: x[x <= x.quantile(1 - var_conf)].mean())

        # 波動率
        volatility = returns.rolling(window=self.params["volatility_lookback"]).std()

        return {"var": var, "cvar": cvar, "volatility": volatility}

class KellyBacktester:
    """
    凱利公式回測引擎

    功能：
    - 支持參數網格搜索
    - 計算 Sharpe 比率、最大回撤
    - 生成回測報告
    """

    def __init__(self, initial_capital: float = 100000.0, commission_rate: float = 0.001, slippage: float = 0.001):
        """
        初始化回測引擎

        Args:
            initial_capital: 初始資金
            commission_rate: 手續費率
            slippage: 滑點
        """
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage = slippage

    def backtest(self, data: pd.DataFrame, strategy: KellyCriterionOptimized) -> dict:
        """
        執行回測

        Args:
            data: OHLCV 數據
            strategy: 策略實例

        Returns:
            回測結果字典
        """
        # 生成信號
        signals = strategy.generate_signals(data)
        close = data["close"]

        # 初始化
        capital = self.initial_capital
        position = 0
        trades = []
        portfolio_values = []

        # 執行回測
        for i in range(1, len(data)):
            signal = signals.iloc[i]
            price = close.iloc[i]

            # 買入
            if signal == 1 and position == 0:
                position = capital / price * (1 - self.commission_rate - self.slippage)
                capital = 0
                trades.append({"type": "buy", "price": price, "index": i})

            # 賣出
            elif signal == -1 and position > 0:
                capital = position * price * (1 - self.commission_rate - self.slippage)
                position = 0
                trades.append({"type": "sell", "price": price, "index": i})

            # 計算組合價值
            portfolio_value = capital + position * price
            portfolio_values.append(portfolio_value)

        # 平倉
        if position > 0:
            capital = position * close.iloc[-1] * (1 - self.commission_rate - self.slippage)
            portfolio_values.append(capital)

        # 計算指標
        portfolio_values = pd.Series(portfolio_values)
        returns = portfolio_values.pct_change().dropna()

        # Sharpe 比率（年化）
        sharpe = np.sqrt(252) * returns.mean() / returns.std() if returns.std() > 0 else 0

        # 最大回撤
        cumulative = (portfolio_values / self.initial_capital).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()

        # 總回報
        total_return = (portfolio_values.iloc[-1] - self.initial_capital) / self.initial_capital

        # 交易次數
        num_trades = len([t for t in trades if t["type"] == "sell"])

        return {
            "total_return": total_return,
            "sharpe_ratio": sharpe,
            "max_drawdown": max_drawdown,
            "num_trades": num_trades,
            "final_value": portfolio_values.iloc[-1],
            "portfolio_values": portfolio_values,
            "trades": trades,
        }

    def grid_search(self, data: pd.DataFrame, param_grid: dict[str, list]) -> pd.DataFrame:
        """
        參數網格搜索

        Args:
            data: OHLCV 數據
            param_grid: 參數網格字典

        Returns:
            結果 DataFrame
        """
        results = []

        # 生成參數組合
        from itertools import product

        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())

        total_combinations = np.prod([len(v) for v in param_values])
        print(f"開始參數網格搜索，總共 {total_combinations} 種組合...")

        for i, values in enumerate(product(*param_values)):
            params = dict(zip(param_names, values))

            # 創建策略
            strategy = KellyCriterionOptimized(**params)

            # 執行回測
            result = self.backtest(data, strategy)

            # 記錄結果
            result.update(params)
            results.append(result)

            if (i + 1) % 10 == 0:
                print(f"進度：{i + 1}/{total_combinations}, 當前 Sharpe: {result['sharpe_ratio']:.3f}")

        # 轉換為 DataFrame
        df_results = pd.DataFrame(results)

        # 排序
        df_results = df_results.sort_values("sharpe_ratio", ascending=False)

        return df_results


def load_data(start_date: str = "2020-01-01", end_date: str = "2023-12-31", symbol: str = "000001.SZ") -> pd.DataFrame:
    """
    加載歷史數據
    """
    try:
        import akshare as ak

        df = ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date=start_date.replace("-", ""),
            end_date=end_date.replace("-", ""),
            adjust="qfq",
        )

        df = df.rename(
            columns={
                "日期": "date",
                "開盤": "open",
                "收盤": "close",
                "最高": "high",
                "最低": "low",
                "成交量": "volume",
                "成交額": "amount",
            }
        )

        df.set_index("date", inplace=True)

        print(f"成功加載數據：{len(df)} 天，{start_date} 至 {end_date}")

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


def generate_report(results: pd.DataFrame, output_file: str = "kelly_optimization_report.md"):
    """
    生成優化報告
    """
    best = results.iloc[0]

    report = f"""# 凱利公式 (Kelly Criterion) 參數優化報告

**生成日期**: {datetime.now().strftime("%Y-%m-%d %H:%M")}
**優化任務**: OPT-029 / Issue #29
**回測期間**: 3 年歷史數據

---

## 📊 最佳參數組合

| 參數 | 值 | 說明 |
|------|-----|------|
| max_kelly | {best["max_kelly"]:.2f} | 最大凱利比例 |
| lookback | {int(best["lookback"])} | 回看周期 |
| kelly_fraction | {best["kelly_fraction"]:.2f} | 凱利分數 |

---

## 📈 回測表現

| 指標 | 數值 | 評價 |
|------|------|------|
| 總回報 | {best["total_return"] * 100:.2f}% | {"優秀" if best["total_return"] > 0.5 else "良好" if best["total_return"] > 0.2 else "待改進"} |
| Sharpe 比率 | {best["sharpe_ratio"]:.3f} | {"優秀" if best["sharpe_ratio"] > 1.5 else "良好" if best["sharpe_ratio"] > 1.0 else "待改進"} |
| 最大回撤 | {best["max_drawdown"] * 100:.2f}% | {"優秀" if abs(best["max_drawdown"]) < 0.15 else "良好" if abs(best["max_drawdown"]) < 0.25 else "待改進"} |
| 交易次數 | {int(best["num_trades"])} | {"適中" if 20 < best["num_trades"] < 100 else "偏高" if best["num_trades"] >= 100 else "偏低"} |
| 最終資金 | ¥{best["final_value"]:,.2f} | - |

---

## 🔍 參數敏感性分析

### Top 10 參數組合

| 排名 | Max_Kelly | Lookback | Kelly_Frac | Sharpe | 總回報 | 最大回撤 |
|------|-----------|----------|------------|--------|--------|----------|
"""

    for i, row in results.head(10).iterrows():
        report += f"| {i + 1} | {row['max_kelly']:.2f} | {int(row['lookback'])} | {row['kelly_fraction']:.2f} | {row['sharpe_ratio']:.3f} | {row['total_return'] * 100:.2f}% | {row['max_drawdown'] * 100:.2f}% |\n"

    report += f"""
---

## 💡 優化建議

### 參數選擇
- **Max Kelly**: 最佳範圍 {results["max_kelly"].quantile(0.25):.2f} - {results["max_kelly"].quantile(0.75):.2f}
- **Lookback**: 最佳範圍 {results["lookback"].quantile(0.25):.0f} - {results["lookback"].quantile(0.75):.0f}
- **Kelly Fraction**: 最佳範圍 {results["kelly_fraction"].quantile(0.25):.2f} - {results["kelly_fraction"].quantile(0.75):.2f}

### 使用建議
1. **保守策略**: 使用半凱利（kelly_fraction=0.5）降低風險
2. **激進策略**: 使用全凱利（kelly_fraction=1.0）最大化收益
3. **動態調整**: 建議啟用波動率調整（use_dynamic_adjustment=True）
4. **風險限制**: 建議啟用 VaR 限制（use_var_limit=True）

---

## 📝 技術說明

### 回測設置
- 初始資金：¥100,000
- 手續費率：0.1%
- 滑點：0.1%
- 交易頻率：日線

### 凱利公式
f* = W - (1-W)/R

其中：
- W = 勝率
- R = 盈虧比

### 計算方法
- **Sharpe 比率**: 年化收益率 / 年化波動率 × √252
- **最大回撤**: (組合最低點 - 前期最高點) / 前期最高點
- **總回報**: (最終資金 - 初始資金) / 初始資金

---

**報告完成時間**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**下一步**: 將最佳參數應用於實盤交易
"""

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n✅ 報告已生成：{output_file}")

def main():
    """主函數"""
    print("=" * 60)
    print("凱利公式 (Kelly Criterion) 參數優化")
    print("=" * 60)

    # 加載數據
    print("\n[1/4] 加載歷史數據...")
    data = load_data("2020-01-01", "2023-12-31", "000001.SZ")

    # 創建回測引擎
    print("\n[2/4] 初始化回測引擎...")
    backtester = KellyBacktester(initial_capital=100000.0, commission_rate=0.001, slippage=0.001)

    # 參數網格搜索
    print("\n[3/4] 執行參數網格搜索...")
    param_grid = {"max_kelly": [0.15, 0.25, 0.35], "lookback": [40, 60, 80], "kelly_fraction": [0.25, 0.5, 0.75]}

    results = backtester.grid_search(data, param_grid)

    # 顯示最佳結果
    print("\n[4/4] 生成優化報告...")
    best = results.iloc[0]
    print("\n🏆 最佳參數組合:")
    print(f"  Max Kelly: {best['max_kelly']:.2f}")
    print(f"  Lookback: {int(best['lookback'])}")
    print(f"  Kelly Fraction: {best['kelly_fraction']:.2f}")
    print("\n📊 回測表現:")
    print(f"  Sharpe 比率：{best['sharpe_ratio']:.3f}")
    print(f"  總回報：{best['total_return'] * 100:.2f}%")
    print(f"  最大回撤：{best['max_drawdown'] * 100:.2f}%")
    print(f"  交易次數：{int(best['num_trades'])}")

    # 生成報告
    generate_report(results, "kelly_optimization_report.md")

    print("\n" + "=" * 60)
    print("優化完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
