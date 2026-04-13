#!/usr/bin/env python3
"""
策略評分系統
基於多維度指標對策略進行評分和排名

作者：StocksX Team
創建日期：2026-03-22
"""

import pandas as pd
import numpy as np
from pathlib import Path

class StrategyScorer:
    """策略評分器"""

    def __init__(self):
        """初始化評分器"""
        self.scores = []

    def score_strategy(self, name: str, strategy, data: pd.DataFrame) -> dict:
        """
        對單一策略進行評分

        Args:
            name: 策略名
            strategy: 策略實例
            data: OHLCV 數據

        Returns:
            評分明細
        """
        try:
            # 生成信號
            signals = strategy.generate_signals(data)
            returns = data["close"].pct_change()
            positions = signals.shift(1)
            strategy_returns = positions * returns

            # 計算各項指標
            metrics = self._calculate_metrics(strategy_returns, signals)

            # 計算評分
            score = self._calculate_score(metrics)

            return {"name": name, "score": score, "grade": self._score_to_grade(score), "metrics": metrics}

        except Exception as e:
            return {"name": name, "score": 0, "grade": "F", "metrics": {}, "error": str(e)}

    def _calculate_metrics(self, returns: pd.Series, signals: pd.Series) -> dict:
        """計算各項績效指標"""
        non_zero = returns[signals.shift(1) != 0]

        # 1. 收益率指標
        total_return = (1 + returns).cumprod().iloc[-1] - 1 if len(returns) > 0 else 0

        # 2. 風險調整收益
        if returns.std() > 0:
            sharpe = np.sqrt(252) * returns.mean() / returns.std()
        else:
            sharpe = 0

        # 3. 最大回撤
        cum_returns = (1 + returns).cumprod()
        rolling_max = cum_returns.expanding().max()
        drawdown = (cum_returns - rolling_max) / rolling_max
        max_dd = abs(drawdown.min()) if len(drawdown) > 0 else 0

        # 4. 勝率
        if len(non_zero) > 0:
            win_rate = (non_zero > 0).sum() / len(non_zero)
        else:
            win_rate = 0

        # 5. 盈虧比
        winning_trades = non_zero[non_zero > 0]
        losing_trades = -non_zero[non_zero < 0]
        if len(losing_trades) > 0 and len(winning_trades) > 0:
            profit_factor = winning_trades.mean() / losing_trades.mean()
        else:
            profit_factor = 0

        # 6. 交易頻率
        trade_count = (signals.diff() != 0).sum()
        avg_trades_per_month = trade_count / (len(signals) / 21) if len(signals) > 0 else 0

        # 7. 信號穩定性
        signal_std = signals.std()

        return {
            "total_return": total_return,
            "sharpe_ratio": sharpe,
            "max_drawdown": max_dd,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "trade_count": trade_count,
            "trades_per_month": avg_trades_per_month,
            "signal_stability": signal_std,
        }

    def _calculate_score(self, metrics: dict) -> float:
        """
        計算綜合評分（0-100）

        權重分配：
        - 夏普比率：30%
        - 總回報：25%
        - 最大回撤：20%
        - 勝率：15%
        - 盈虧比：10%
        """
        score = 0

        # 夏普比率評分（0-30）
        sharpe_score = min(30, max(0, metrics["sharpe_ratio"] * 15))
        score += sharpe_score

        # 總回報評分（0-25）
        return_score = min(25, max(0, (metrics["total_return"] + 1) * 25))
        score += return_score

        # 最大回撤評分（0-20）
        dd_score = max(0, 20 - metrics["max_drawdown"] * 100)
        score += dd_score

        # 勝率評分（0-15）
        win_score = metrics["win_rate"] * 15
        score += win_score

        # 盈虧比評分（0-10）
        pf_score = min(10, max(0, metrics["profit_factor"] * 5))
        score += pf_score

        return min(100, max(0, score))

    def _score_to_grade(self, score: float) -> str:
        """評分轉等級"""
        if score >= 90:
            return "A+"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B+"
        elif score >= 60:
            return "B"
        elif score >= 50:
            return "C+"
        elif score >= 40:
            return "C"
        elif score >= 30:
            return "D"
        else:
            return "F"

    def score_all_strategies(self, strategies: dict, data: pd.DataFrame) -> pd.DataFrame:
        """
        對所有策略進行評分

        Args:
            strategies: 策略字典
            data: OHLCV 數據

        Returns:
            評分 DataFrame
        """
        results = []

        for name, strategy_class in strategies.items():
            print(f"  評分：{name}...", end="\r")
            try:
                strategy = strategy_class()
                result = self.score_strategy(name, strategy, data)
                results.append(result)
            except Exception as e:
                results.append({"name": name, "score": 0, "grade": "F", "metrics": {}, "error": str(e)})

        # 轉換為 DataFrame
        df = pd.DataFrame(results)

        # 展開 metrics
        if "metrics" in df.columns:
            metrics_df = pd.DataFrame(df["metrics"].tolist())
            df = pd.concat([df.drop("metrics", axis=1), metrics_df], axis=1)

        # 排序
        df = df.sort_values("score", ascending=False).reset_index(drop=True)
        df["rank"] = df.index + 1

        return df

    def generate_report_html(self, scores_df: pd.DataFrame, output_path: str):
        """生成 HTML 評分報告"""
        html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>StocksX 策略評分報告</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1400px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 13px; }
        th, td { padding: 10px; text-align: center; border-bottom: 1px solid #ddd; }
        th { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; position: sticky; top: 0; }
        tr:hover { background-color: #f5f5f5; }
        .rank { font-weight: bold; }
        .rank-1 { color: #f1c40f; }
        .rank-2 { color: #95a5a6; }
        .rank-3 { color: #cd7f32; }
        .grade { font-size: 18px; font-weight: bold; padding: 5px 15px; border-radius: 20px; display: inline-block; }
        .grade-Aplus { background: #d4edda; color: #155724; }
        .grade-A { background: #d4edda; color: #155724; }
        .grade-Bplus { background: #d1ecf1; color: #0c5460; }
        .grade-B { background: #d1ecf1; color: #0c5460; }
        .grade-Cplus { background: #fff3cd; color: #856404; }
        .grade-C { background: #fff3cd; color: #856404; }
        .grade-D { background: #f8d7da; color: #721c24; }
        .grade-F { background: #f8d7da; color: #721c24; }
        .positive { color: #27ae60; font-weight: bold; }
        .negative { color: #e74c3c; font-weight: bold; }
        .score-bar { width: 100px; height: 20px; background: #e0e0e0; border-radius: 10px; overflow: hidden; display: inline-block; }
        .score-fill { height: 100%; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); transition: width 0.3s; }
        .filter-section { margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 5px; }
        .filter-section select, .filter-section input { margin: 5px; padding: 8px; border-radius: 5px; border: 1px solid #ddd; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏆 StocksX 策略評分報告</h1>
        <p>基於多維度指標對所有策略進行綜合評分</p>

        <div class="filter-section">
            <strong>篩選:</strong>
            <select id="gradeFilter" onchange="filterTable()">
                <option value="">所有等級</option>
                <option value="A+">A+</option>
                <option value="A">A</option>
                <option value="B+">B+</option>
                <option value="B">B</option>
                <option value="C+">C+</option>
                <option value="C">C</option>
                <option value="D">D</option>
                <option value="F">F</option>
            </select>
            <input type="number" id="minScore" placeholder="最低分數" onchange="filterTable()">
        </div>

        <table id="scoreTable">
            <thead>
                <tr>
                    <th>排名</th>
                    <th>策略名</th>
                    <th>評分</th>
                    <th>等級</th>
                    <th>總回報</th>
                    <th>夏普比率</th>
                    <th>最大回撤</th>
                    <th>勝率</th>
                    <th>盈虧比</th>
                    <th>月交易</th>
                </tr>
            </thead>
            <tbody>
"""

        # 添加數據行
        for _, row in scores_df.iterrows():
            rank_class = ""
            if row["rank"] == 1:
                rank_class = "rank-1"
            elif row["rank"] == 2:
                rank_class = "rank-2"
            elif row["rank"] == 3:
                rank_class = "rank-3"

            grade_class = f"grade-{row['grade'].replace('+', 'plus')}"

            score_pct = row["score"]

            html += f"""
                <tr>
                    <td class="rank {rank_class}">#{row["rank"]}</td>
                    <td style="text-align: left;"><strong>{row["name"]}</strong></td>
                    <td>
                        <div class="score-bar">
                            <div class="score-fill" style="width: {score_pct}%;"></div>
                        </div>
                        {score_pct:.1f}
                    </td>
                    <td><span class="grade {grade_class}">{row["grade"]}</span></td>
                    <td class="{"positive" if row["total_return"] > 0 else "negative"}">{row["total_return"] * 100:+.2f}%</td>
                    <td>{row["sharpe_ratio"]:.2f}</td>
                    <td class="negative">-{row["max_drawdown"] * 100:.2f}%</td>
                    <td>{row["win_rate"] * 100:.1f}%</td>
                    <td>{row["profit_factor"]:.2f}</td>
                    <td>{row["trades_per_month"]:.1f}</td>
                </tr>
"""

        html += """
            </tbody>
        </table>

        <h2>📊 評分說明</h2>
        <table>
            <tr>
                <th>指標</th>
                <th>權重</th>
                <th>說明</th>
            </tr>
            <tr>
                <td>夏普比率</td>
                <td>30%</td>
                <td>風險調整後收益，越高越好</td>
            </tr>
            <tr>
                <td>總回報</td>
                <td>25%</td>
                <td>累計收益率</td>
            </tr>
            <tr>
                <td>最大回撤</td>
                <td>20%</td>
                <td>最大虧損幅度，越低越好</td>
            </tr>
            <tr>
                <td>勝率</td>
                <td>15%</td>
                <td>盈利交易比例</td>
            </tr>
            <tr>
                <td>盈虧比</td>
                <td>10%</td>
                <td>平均盈利/平均虧損</td>
            </tr>
        </table>

        <script>
            function filterTable() {
                const gradeFilter = document.getElementById('gradeFilter').value;
                const minScore = document.getElementById('minScore').value;
                const rows = document.querySelectorAll('#scoreTable tbody tr');

                rows.forEach(row => {
                    const grade = row.querySelector('.grade').textContent;
                    const score = parseFloat(row.querySelector('.score-fill').style.width);

                    let show = true;
                    if (gradeFilter && grade !== gradeFilter) show = false;
                    if (minScore && score < parseFloat(minScore)) show = false;

                    row.style.display = show ? '' : 'none';
                });
            }
        </script>
    </div>
</body>
</html>
"""

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        print(f"✅ 評分報告已保存：{output_path}")

def main():
    """主函數"""
    print("=" * 80)
    print("🏆 StocksX 策略評分系統")
    print("=" * 80)

    # 導入策略
    from strategies.trend import ALL_TREND_STRATEGIES
    from strategies.oscillator import ALL_OSCILLATOR_STRATEGIES
    from strategies.breakout import ALL_BREAKOUT_STRATEGIES
    from strategies.ai_ml import ALL_AI_ML_STRATEGIES

    # 合併所有策略
    all_strategies = {}
    all_strategies.update(ALL_TREND_STRATEGIES)
    all_strategies.update(ALL_OSCILLATOR_STRATEGIES)
    all_strategies.update(ALL_BREAKOUT_STRATEGIES)
    all_strategies.update(ALL_AI_ML_STRATEGIES)

    print(f"\n📊 評分策略數量：{len(all_strategies)}")

    # 生成測試數據
    print("\n⏳ 生成測試數據...")
    np.random.seed(42)
    n = 500
    returns = np.random.normal(0.0005, 0.02, n)
    price = 100 * np.cumprod(1 + returns)

    data = pd.DataFrame(
        {
            "open": price * (1 + np.random.uniform(-0.01, 0.01, n)),
            "high": price * (1 + np.random.uniform(0, 0.02, n)),
            "low": price * (1 - np.random.uniform(0, 0.02, n)),
            "close": price,
            "volume": np.random.uniform(1e6, 1e7, n),
        },
        index=pd.date_range("2025-01-01", periods=n, freq="D"),
    )

    print(f"✅ 數據生成完成：{len(data)} 天")

    # 創建評分器
    scorer = StrategyScorer()

    # 評分所有策略
    print("\n⏳ 開始評分所有策略...\n")
    scores_df = scorer.score_all_strategies(all_strategies, data)

    # 顯示 Top 10
    print("\n" + "=" * 80)
    print("🏆 Top 10 最佳策略")
    print("=" * 80)
    top_10 = scores_df.head(10)
    for _, row in top_10.iterrows():
        print(f"#{row['rank']:2d}. {row['name']:<30s} {row['score']:5.1f}分 [{row['grade']}]")

    # 顯示等級分佈
    print("\n📊 等級分佈:")
    grade_counts = scores_df["grade"].value_counts().sort_index()
    for grade, count in grade_counts.items():
        bar = "█" * count
        print(f"  {grade}: {bar} ({count})")

    # 生成報告
    print("\n⏳ 生成評分報告...")
    output_dir = Path(__file__).parent.parent.parent / "docs" / "analytics"
    output_dir.mkdir(parents=True, exist_ok=True)

    report_path = output_dir / "strategy_scores.html"
    scorer.generate_report_html(scores_df, str(report_path))

    # 保存 CSV
    csv_path = output_dir / "strategy_scores.csv"
    scores_df.to_csv(csv_path, index=False)
    print(f"✅ CSV 數據：{csv_path}")

    print("\n" + "=" * 80)
    print("✅ 策略評分完成！")
    print("=" * 80)


if __name__ == "__main__":
    main()
