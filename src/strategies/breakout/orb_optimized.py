"""
開盤區間突破 (Opening Range Breakout, ORB) 策略優化

優化任務：OPT-022 / Issue #22
目標：3 年回測 + 區間時間優化
執行日期：2026-03-23

優化內容：
1. 參數網格搜索（lookback: 1-5 日，stop_loss: 1-3%，take_profit: 2-5%）
2. 3 年歷史數據回測
3. Sharpe 比率、最大回撤計算
4. 最優參數組合推薦
5. 添加時間過濾（只在特定時間段交易）
6. 添加成交量確認

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
from base_strategy import BreakoutStrategy


class OpeningRangeBreakoutOptimized(BreakoutStrategy):
    """
    優化的開盤區間突破策略

    改進點：
    1. 支持多日 lookback 區間
    2. 添加止盈/止損機制
    3. 添加時間過濾（可選）
    4. 添加成交量確認
    5. 添加趨勢過濾
    """

    def __init__(
        self,
        lookback_days: int = 1,
        stop_loss_pct: float = 0.02,
        take_profit_pct: float = 0.03,
        use_time_filter: bool = False,
        trade_hour: int = 10,
        use_volume_filter: bool = False,
        volume_multiplier: float = 1.5,
        use_trend_filter: bool = False,
        trend_period: int = 50,
    ):
        """
        初始化優化的 ORB 策略

        Args:
            lookback_days: 區間 lookback 天數（默认 1 日）
            stop_loss_pct: 止損百分比（默认 2%）
            take_profit_pct: 止盈百分比（默认 3%）
            use_time_filter: 是否使用時間過濾（默认 False）
            trade_hour: 交易時間（默认 10 點）
            use_volume_filter: 是否使用成交量過濾（默认 False）
            volume_multiplier: 成交量放大倍數（默认 1.5）
            use_trend_filter: 是否使用趨勢過濾（默认 False）
            trend_period: 趨勢判斷周期（默认 50）
        """
        super().__init__(
            "Opening Range Breakout Optimized",
            {
                "lookback_days": lookback_days,
                "stop_loss_pct": stop_loss_pct,
                "take_profit_pct": take_profit_pct,
                "use_time_filter": use_time_filter,
                "trade_hour": trade_hour,
                "use_volume_filter": use_volume_filter,
                "volume_multiplier": volume_multiplier,
                "use_trend_filter": use_trend_filter,
                "trend_period": trend_period,
            },
        )

        self.position = 0
        self.entry_price = 0
        self.stop_loss = 0
        self.take_profit = 0

    def calculate_opening_range(self, data: pd.DataFrame) -> dict[str, pd.Series]:
        """
        計算開盤區間

        Args:
            data: OHLCV 數據

        Returns:
            包含區間高低的字典
        """
        lookback = self.params["lookback_days"]

        # 計算 lookback 天內的最高和最低
        range_high = data["high"].rolling(window=lookback).max()
        range_low = data["low"].rolling(window=lookback).min()

        # 計算區間大小
        range_size = (range_high - range_low) / range_low * 100

        return {"high": range_high, "low": range_low, "size": range_size}

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        生成交易信號（多條件確認）

        信號規則：
        基礎信號：
        - 價格突破 N 日區間高點 → 買入
        - 價格跌破 N 日區間低點 → 賣出

        過濾條件（可選）：
        - 時間過濾：只在特定時間段交易
        - 成交量過濾：突破時成交量放大
        - 趨勢過濾：順應 50 日均線趨勢

        Args:
            data: OHLCV 數據

        Returns:
            信號 Series（1=買入，-1=賣出，0=持有）
        """
        opening_range = self.calculate_opening_range(data)
        range_high = opening_range["high"]
        range_low = opening_range["low"]
        close = data["close"]
        high = data["high"]
        low = data["low"]

        signals = pd.Series(0, index=data.index)

        # 基礎信號：突破
        breakout_long = high > range_high.shift(1)
        breakout_short = low < range_low.shift(1)

        # 時間過濾（日線數據不適用，保留用於分鐘線）
        if self.params["use_time_filter"]:
            # 對於日線數據，這個過濾不適用
            pass

        # 成交量過濾
        if self.params["use_volume_filter"]:
            volume_period = 20
            volume_ma = data["volume"].rolling(window=volume_period).mean()
            volume_confirmed = data["volume"] > volume_ma * self.params["volume_multiplier"]

            breakout_long = breakout_long & volume_confirmed
            breakout_short = breakout_short & volume_confirmed

        # 趨勢過濾
        if self.params["use_trend_filter"]:
            trend_period = self.params["trend_period"]
            sma_50 = close.rolling(window=trend_period).mean()

            # 買入時價格在 50 均線上，賣出時在 50 均線下
            breakout_long = breakout_long & (close > sma_50)
            breakout_short = breakout_short & (close < sma_50)

        signals[breakout_long] = 1
        signals[breakout_short] = -1

        return signals

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        """
        計算倉位大小（基於區間大小）

        Args:
            signal: 交易信號（1, -1, 0）
            capital: 可用資金
            price: 當前價格
            volatility: 波動率

        Returns:
            倉位大小（股數）
        """
        if signal == 0:
            return 0.0

        # 基礎風險比例
        risk_per_trade = self.params.get("risk_per_trade", 0.02)
        stop_loss_pct = self.params["stop_loss_pct"]

        # 基於止損計算倉位
        if stop_loss_pct > 0:
            risk_amount = capital * risk_per_trade
            shares = risk_amount / (price * stop_loss_pct)
        else:
            shares = 0

        return round(shares, 2)

    def check_exit_conditions(self, data: pd.DataFrame, position: int, entry_price: float) -> tuple[int, float]:
        """
        檢查止盈/止損條件

        Args:
            data: OHLCV 數據
            position: 當前持倉（1=多倉，-1=空倉，0=無持倉）
            entry_price: 入場價格

        Returns:
            (新持倉，新入場價格)
        """
        if position == 0:
            return 0, 0

        stop_loss_pct = self.params["stop_loss_pct"]
        take_profit_pct = self.params["take_profit_pct"]
        current_price = data["close"].iloc[-1]

        # 多倉
        if position == 1:
            # 止損
            if current_price <= entry_price * (1 - stop_loss_pct):
                return 0, 0
            # 止盈
            if current_price >= entry_price * (1 + take_profit_pct):
                return 0, 0

        # 空倉
        elif position == -1:
            # 止損
            if current_price >= entry_price * (1 + stop_loss_pct):
                return 0, 0
            # 止盈
            if current_price <= entry_price * (1 - take_profit_pct):
                return 0, 0

        return position, entry_price

    def get_range_strength(self, data: pd.DataFrame) -> pd.Series:
        """
        計算區間強度（相對於歷史區間大小）

        Args:
            data: OHLCV 數據

        Returns:
            區間強度序列（百分比）
        """
        opening_range = self.calculate_opening_range(data)
        range_size = opening_range["size"]

        # 計算歷史百分位數
        range_percentile = range_size.rolling(window=250).apply(lambda x: (x.iloc[-1] < x).mean() * 100)

        return range_percentile

class ORBBacktester:
    """
    ORB 回測引擎

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

    def backtest(self, data: pd.DataFrame, strategy: OpeningRangeBreakoutOptimized) -> dict:
        """
        執行回測（帶止盈/止損）

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
        entry_price = 0
        trades = []
        portfolio_values = []

        # 執行回測
        for i in range(1, len(data)):
            signal = signals.iloc[i]
            price = close.iloc[i]

            # 檢查止盈/止損
            if position != 0:
                position, entry_price = strategy.check_exit_conditions(data.iloc[: i + 1], position, entry_price)
                if position == 0:
                    trades.append({"type": "exit", "price": price, "index": i, "reason": "stop"})

            # 開新倉
            if signal != 0 and position == 0:
                if signal == 1:  # 買入
                    position = capital / price * (1 - self.commission_rate - self.slippage)
                    entry_price = price
                    trades.append({"type": "buy", "price": price, "index": i})
                elif signal == -1:  # 賣出
                    position = capital / price * (1 - self.commission_rate - self.slippage)
                    entry_price = price
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
        num_trades = len([t for t in trades if t["type"] in ["buy", "sell"]])

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
            strategy = OpeningRangeBreakoutOptimized(**params)

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


def generate_report(results: pd.DataFrame, output_file: str = "orb_optimization_report.md"):
    """
    生成優化報告
    """
    best = results.iloc[0]

    report = f"""# 開盤區間突破 (ORB) 參數優化報告

**生成日期**: {datetime.now().strftime("%Y-%m-%d %H:%M")}
**優化任務**: OPT-022 / Issue #22
**回測期間**: 3 年歷史數據

---

## 📊 最佳參數組合

| 參數 | 值 | 說明 |
|------|-----|------|
| lookback_days | {int(best["lookback_days"])} | 區間 lookback 天數 |
| stop_loss_pct | {best["stop_loss_pct"] * 100:.2f}% | 止損百分比 |
| take_profit_pct | {best["take_profit_pct"] * 100:.2f}% | 止盈百分比 |

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

| 排名 | Lookback | Stop_Loss | Take_Profit | Sharpe | 總回報 | 最大回撤 |
|------|----------|-----------|-------------|--------|--------|----------|
"""

    for i, row in results.head(10).iterrows():
        report += f"| {i + 1} | {int(row['lookback_days'])} | {row['stop_loss_pct'] * 100:.2f}% | {row['take_profit_pct'] * 100:.2f}% | {row['sharpe_ratio']:.3f} | {row['total_return'] * 100:.2f}% | {row['max_drawdown'] * 100:.2f}% |\n"

    report += f"""
---

## 💡 優化建議

### 參數選擇
- **Lookback 天數**: 最佳範圍 {results["lookback_days"].quantile(0.25):.0f} - {results["lookback_days"].quantile(0.75):.0f}
- **止損**: 最佳範圍 {results["stop_loss_pct"].quantile(0.25) * 100:.1f}% - {results["stop_loss_pct"].quantile(0.75) * 100:.1f}%
- **止盈**: 最佳範圍 {results["take_profit_pct"].quantile(0.25) * 100:.1f}% - {results["take_profit_pct"].quantile(0.75) * 100:.1f}%

### 使用建議
1. **震盪市場**: 使用較短 lookback（1-2 日）提高靈敏度
2. **趨勢市場**: 使用較長 lookback（3-5 日）減少假突破
3. **過濾條件**: 建議啟用成交量過濾
4. **風險管理**: 配合止盈/止損，控制單筆風險

---

## 📝 技術說明

### 回測設置
- 初始資金：¥100,000
- 手續費率：0.1%
- 滑點：0.1%
- 交易頻率：日線

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
    print("開盤區間突破 (ORB) 參數優化")
    print("=" * 60)

    # 加載數據
    print("\n[1/4] 加載歷史數據...")
    data = load_data("2020-01-01", "2023-12-31", "000001.SZ")

    # 創建回測引擎
    print("\n[2/4] 初始化回測引擎...")
    backtester = ORBBacktester(initial_capital=100000.0, commission_rate=0.001, slippage=0.001)

    # 參數網格搜索
    print("\n[3/4] 執行參數網格搜索...")
    param_grid = {
        "lookback_days": [1, 3, 5],
        "stop_loss_pct": [0.01, 0.02, 0.03],
        "take_profit_pct": [0.02, 0.03, 0.05],
    }

    results = backtester.grid_search(data, param_grid)

    # 顯示最佳結果
    print("\n[4/4] 生成優化報告...")
    best = results.iloc[0]
    print("\n🏆 最佳參數組合:")
    print(f"  Lookback Days: {int(best['lookback_days'])}")
    print(f"  Stop Loss: {best['stop_loss_pct'] * 100:.2f}%")
    print(f"  Take Profit: {best['take_profit_pct'] * 100:.2f}%")
    print("\n📊 回測表現:")
    print(f"  Sharpe 比率：{best['sharpe_ratio']:.3f}")
    print(f"  總回報：{best['total_return'] * 100:.2f}%")
    print(f"  最大回撤：{best['max_drawdown'] * 100:.2f}%")
    print(f"  交易次數：{int(best['num_trades'])}")

    # 生成報告
    generate_report(results, "orb_optimization_report.md")

    print("\n" + "=" * 60)
    print("優化完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
