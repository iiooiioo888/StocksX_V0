#!/usr/bin/env python3
"""
StocksX 自動化回測 Pipeline

功能：
- 自動加載所有策略
- 批量執行回測
- 生成綜合報告
- 支持並行計算
- 自動保存結果

使用方式：
    python automated_backtest_pipeline.py --strategies all --output results/

作者：StocksX Team
日期：2026-03-23
"""

import os
import sys
import json
import argparse
import pandas as pd
import numpy as np
from datetime import datetime
from multiprocessing import Pool, cpu_count
import warnings

warnings.filterwarnings("ignore")

# 添加策略路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "strategies"))

from base_strategy import BaseStrategy


class AutomatedBacktestPipeline:
    """自動化回測 Pipeline"""

    def __init__(
        self,
        initial_capital: float = 100000.0,
        commission_rate: float = 0.001,
        slippage: float = 0.001,
        n_workers: int = None,
    ):
        """
        初始化 Pipeline

        Args:
            initial_capital: 初始資金
            commission_rate: 手續費率
            slippage: 滑點
            n_workers: 並行工作進程數
        """
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage = slippage
        self.n_workers = n_workers or cpu_count()
        self.results = {}
        self.strategies = {}

    def load_strategies(self, strategy_dir: str = None) -> dict[str, BaseStrategy]:
        """
        自動加載所有策略

        Args:
            strategy_dir: 策略目錄路徑

        Returns:
            策略字典
        """
        if strategy_dir is None:
            strategy_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "strategies")

        strategies = {}

        # 掃描所有策略文件
        for root, dirs, files in os.walk(strategy_dir):
            for file in files:
                if file.endswith("_optimized.py") and not file.startswith("__"):
                    try:
                        module_name = file[:-3]
                        module = __import__(f"{os.path.basename(root)}.{module_name}", fromlist=[""])

                        # 查找策略類
                        for name in dir(module):
                            obj = getattr(module, name)
                            if isinstance(obj, type) and issubclass(obj, BaseStrategy) and obj != BaseStrategy:
                                strategy_key = f"{os.path.basename(root)}.{name}"
                                strategies[strategy_key] = obj
                                print(f"✓ 加載策略：{strategy_key}")
                    except Exception as e:
                        print(f"✗ 加載失敗 {file}: {e}")

        self.strategies = strategies
        print(f"\n總共加載 {len(strategies)} 個策略")
        return strategies

    def load_data(
        self, symbol: str = "000001.SZ", start_date: str = "2020-01-01", end_date: str = "2023-12-31"
    ) -> pd.DataFrame:
        """
        加載歷史數據

        Args:
            symbol: 股票代碼
            start_date: 開始日期
            end_date: 結束日期

        Returns:
            OHLCV 數據
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
                }
            )
            df.set_index("date", inplace=True)

            print(f"✓ 成功加載數據：{len(df)} 天，{start_date} 至 {end_date}")
            return df

        except Exception as e:
            print(f"✗ 加載數據失敗：{e}")
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

    def backtest_single(self, args) -> dict:
        """
        單一策略回測

        Args:
            args: (strategy_class, data, params)

        Returns:
            回測結果
        """
        strategy_class, data, params = args

        try:
            strategy = strategy_class(**params)
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
            sortino = (
                np.sqrt(252) * returns.mean() / returns[returns < 0].std() if returns[returns < 0].std() > 0 else 0
            )
            cumulative = (portfolio_values / self.initial_capital).cumprod()
            max_drawdown = ((cumulative - cumulative.cummax()) / cumulative.cummax()).min()
            total_return = (portfolio_values.iloc[-1] - self.initial_capital) / self.initial_capital
            num_trades = len([t for t in trades if t["type"] == "sell"])

            # 計算月度回報
            monthly_returns = portfolio_values.pct_change().resample("M").apply(lambda x: (1 + x).prod() - 1)

            return {
                "total_return": total_return,
                "sharpe_ratio": sharpe,
                "sortino_ratio": sortino,
                "max_drawdown": max_drawdown,
                "num_trades": num_trades,
                "final_value": portfolio_values.iloc[-1],
                "monthly_returns": monthly_returns.tolist() if len(monthly_returns) > 0 else [],
                "status": "success",
            }

        except Exception as e:
            return {
                "total_return": 0,
                "sharpe_ratio": 0,
                "sortino_ratio": 0,
                "max_drawdown": 0,
                "num_trades": 0,
                "final_value": 0,
                "monthly_returns": [],
                "status": "failed",
                "error": str(e),
            }

    def run_backtest(
        self, data: pd.DataFrame, strategies: dict[str, BaseStrategy] = None, default_params: dict = None
    ) -> dict[str, dict]:
        """
        執行批量回測

        Args:
            data: OHLCV 數據
            strategies: 策略字典
            default_params: 默認參數

        Returns:
            回測結果字典
        """
        if strategies is None:
            strategies = self.strategies

        if default_params is None:
            default_params = {}

        print(f"\n開始回測 {len(strategies)} 個策略...")
        print(f"使用 {self.n_workers} 個並行進程")

        # 準備回測任務
        tasks = []
        for name, strategy_class in strategies.items():
            params = default_params.get(name, {})
            tasks.append((strategy_class, data, params))

        # 並行執行回測
        results = {}
        with Pool(processes=self.n_workers) as pool:
            for i, (name, result) in enumerate(zip(strategies.keys(), pool.imap(self.backtest_single, tasks))):
                results[name] = result
                if (i + 1) % 10 == 0:
                    print(f"進度：{i + 1}/{len(strategies)}, 當前策略：{name}")

        self.results = results
        print(f"\n回測完成！成功：{sum(1 for r in results.values() if r['status'] == 'success')}/{len(results)}")

        return results

    def generate_report(self, output_dir: str = "results") -> str:
        """
        生成回測報告

        Args:
            output_dir: 輸出目錄

        Returns:
            報告文件路徑
        """
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 生成 JSON 結果
        json_file = os.path.join(output_dir, f"backtest_results_{timestamp}.json")
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, default=str)

        # 生成 Markdown 報告
        md_file = os.path.join(output_dir, f"backtest_report_{timestamp}.md")

        # 排序結果
        sorted_results = sorted(
            [(name, r) for name, r in self.results.items() if r["status"] == "success"],
            key=lambda x: x[1]["sharpe_ratio"],
            reverse=True,
        )

        report = f"""# StocksX 自動化回測報告

**生成時間**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**回測期間**: 2020-01-01 至 2023-12-31
**初始資金**: ¥{self.initial_capital:,.2f}
**手續費率**: {self.commission_rate * 100:.2f}%
**滑點**: {self.slippage * 100:.2f}%

---

## 📊 回測總覽

| 指標 | 數值 |
|------|------|
| 回測策略數 | {len(self.results)} |
| 成功策略數 | {len(sorted_results)} |
| 失敗策略數 | {len(self.results) - len(sorted_results)} |
| 成功率 | {len(sorted_results) / len(self.results) * 100:.1f}% |

---

## 🏆 Top 20 策略排行榜

| # | 策略 | Sharpe | Sortino | 總回報 | 最大回撤 | 交易次數 |
|---|------|--------|---------|--------|----------|----------|
"""

        for i, (name, result) in enumerate(sorted_results[:20]):
            report += f"| {i + 1} | {name} | {result['sharpe_ratio']:.3f} | {result['sortino_ratio']:.3f} | {result['total_return'] * 100:.2f}% | {result['max_drawdown'] * 100:.2f}% | {result['num_trades']} |\n"

        report += f"""
---

## 📈 詳細統計

### 最佳策略
- **Sharpe 最高**: {sorted_results[0][0]} ({sorted_results[0][1]["sharpe_ratio"]:.3f})
- **回報最高**: {max(sorted_results, key=lambda x: x[1]["total_return"])[0]} ({max(sorted_results, key=lambda x: x[1][
                "total_return"
            ])[1]["total_return"] * 100:.2f}%)
- **回撤最小**: {min(sorted_results, key=lambda x: x[1]["max_drawdown"])[0]} ({min(sorted_results, key=lambda x: x[1][
                "max_drawdown"
            ])[1]["max_drawdown"] * 100:.2f}%)

### 平均表現
- **平均 Sharpe**: {np.mean([r["sharpe_ratio"] for _, r in sorted_results]):.3f}
- **平均回報**: {np.mean([r["total_return"] for _, r in sorted_results]) * 100:.2f}%
- **平均回撤**: {np.mean([r["max_drawdown"] for _, r in sorted_results]) * 100:.2f}%

---

## 📁 輸出文件

- JSON 結果：`{json_file}`
- Markdown 報告：`{md_file}`

---

**報告完成時間**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

        with open(md_file, "w", encoding="utf-8") as f:
            f.write(report)

        print("\n✓ 報告已生成:")
        print(f"  JSON: {json_file}")
        print(f"  Markdown: {md_file}")

        return md_file


def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="StocksX 自動化回測 Pipeline")
    parser.add_argument("--strategies", type=str, default="all", help="策略選擇 (all 或逗號分隔)")
    parser.add_argument("--output", type=str, default="results", help="輸出目錄")
    parser.add_argument("--capital", type=float, default=100000.0, help="初始資金")
    parser.add_argument("--workers", type=int, default=None, help="並行進程數")
    parser.add_argument("--symbol", type=str, default="000001.SZ", help="股票代碼")
    parser.add_argument("--start-date", type=str, default="2020-01-01", help="開始日期")
    parser.add_argument("--end-date", type=str, default="2023-12-31", help="結束日期")

    args = parser.parse_args()

    print("=" * 60)
    print("StocksX 自動化回測 Pipeline")
    print("=" * 60)

    # 初始化 Pipeline
    pipeline = AutomatedBacktestPipeline(initial_capital=args.capital, n_workers=args.workers)

    # 加載數據
    print("\n[1/4] 加載歷史數據...")
    data = pipeline.load_data(symbol=args.symbol, start_date=args.start_date, end_date=args.end_date)

    # 加載策略
    print("\n[2/4] 加載策略...")
    strategies = pipeline.load_strategies()

    # 執行回測
    print("\n[3/4] 執行回測...")
    results = pipeline.run_backtest(data, strategies)

    # 生成報告
    print("\n[4/4] 生成報告...")
    report_file = pipeline.generate_report(args.output)

    print("\n" + "=" * 60)
    print("回測完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
