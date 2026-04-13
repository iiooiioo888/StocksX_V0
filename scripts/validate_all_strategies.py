#!/usr/bin/env python3
"""
130 策略全驗證腳本
驗證所有策略的：
1. 語法正確性
2. 信號生成能力
3. 倉位計算能力
4. 性能指標

作者：StocksX Team
創建日期：2026-03-22
"""

import sys
import time
import pandas as pd
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def generate_test_data(n=300):
    """生成測試數據"""
    np.random.seed(42)

    # 模擬價格走勢（幾何布朗運動）
    dt = 1
    mu = 0.0005
    sigma = 0.02

    returns = np.random.normal(mu, sigma, n)
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

    return data


def validate_strategy_instance(name, strategy, data):
    """驗證單一策略實例"""
    try:
        # 生成信號
        start_time = time.time()
        signals = strategy.generate_signals(data)
        gen_time = time.time() - start_time

        # 計算倉位
        start_time = time.time()
        position = strategy.calculate_position_size(
            signal=1, capital=100000, price=float(data["close"].iloc[-1]), volatility=0.02
        )
        pos_time = time.time() - start_time

        # 驗證信號
        signal_count = (signals != 0).sum()
        buy_count = (signals == 1).sum()
        sell_count = (signals == -1).sum()

        return {
            "name": name,
            "status": "✅",
            "signals": int(signal_count),
            "buy": int(buy_count),
            "sell": int(sell_count),
            "gen_time_ms": gen_time * 1000,
            "pos_time_ms": pos_time * 1000,
            "position": float(position) if position else 0.0,
        }

    except Exception as e:
        return {"name": name, "status": "❌", "error": str(e)}


def main():
    print("=" * 80)
    print("🔍 StocksX 130 策略全驗證")
    print("=" * 80)

    # 手動導入所有策略模塊
    print("\n⏳ 加載策略模塊...")

    from strategies.trend import ALL_TREND_STRATEGIES
    from strategies.oscillator import ALL_OSCILLATOR_STRATEGIES
    from strategies.breakout import ALL_BREAKOUT_STRATEGIES
    from strategies.ai_ml import ALL_AI_ML_STRATEGIES
    from strategies.risk_management import ALL_RISK_STRATEGIES
    from strategies.microstructure import ALL_MICRO_STRATEGIES
    from strategies.macro import ALL_MACRO_STRATEGIES
    from strategies.statistical import ALL_STAT_STRATEGIES
    from strategies.pattern import ALL_PATTERN_STRATEGIES
    from strategies.execution import ALL_EXECUTION_STRATEGIES

    # 合併所有策略
    all_strategies = {}
    all_strategies.update(ALL_TREND_STRATEGIES)
    all_strategies.update(ALL_OSCILLATOR_STRATEGIES)
    all_strategies.update(ALL_BREAKOUT_STRATEGIES)
    all_strategies.update(ALL_AI_ML_STRATEGIES)
    all_strategies.update(ALL_RISK_STRATEGIES)
    all_strategies.update(ALL_MICRO_STRATEGIES)
    all_strategies.update(ALL_MACRO_STRATEGIES)
    all_strategies.update(ALL_STAT_STRATEGIES)
    all_strategies.update(ALL_PATTERN_STRATEGIES)
    all_strategies.update(ALL_EXECUTION_STRATEGIES)

    total = len(all_strategies)
    print(f"✅ 加載完成：{total} 策略")

    # 按類別統計
    categories_map = {
        **{k: "trend" for k in ALL_TREND_STRATEGIES.keys()},
        **{k: "oscillator" for k in ALL_OSCILLATOR_STRATEGIES.keys()},
        **{k: "breakout" for k in ALL_BREAKOUT_STRATEGIES.keys()},
        **{k: "ai_ml" for k in ALL_AI_ML_STRATEGIES.keys()},
        **{k: "risk" for k in ALL_RISK_STRATEGIES.keys()},
        **{k: "microstructure" for k in ALL_MICRO_STRATEGIES.keys()},
        **{k: "macro" for k in ALL_MACRO_STRATEGIES.keys()},
        **{k: "statistical" for k in ALL_STAT_STRATEGIES.keys()},
        **{k: "pattern" for k in ALL_PATTERN_STRATEGIES.keys()},
        **{k: "execution" for k in ALL_EXECUTION_STRATEGIES.keys()},
    }

    print(f"\n📊 總策略數量：{total}")
    print("📈 測試數據：300 天 OHLCV")
    print("=" * 80)

    # 生成測試數據
    print("\n⏳ 生成測試數據...")
    data = generate_test_data(300)
    print(f"✅ 數據生成完成：{len(data)} 行")

    # 驗證所有策略
    print("\n⏳ 開始驗證所有策略...\n")

    results = []
    failed = []
    category_stats = {}
    start_time = time.time()

    for i, (name, strategy_class) in enumerate(all_strategies.items(), 1):
        cat = categories_map.get(name, "unknown")

        # 初始化類別統計
        if cat not in category_stats:
            category_stats[cat] = {"success": 0, "total": 0, "time": 0}
        category_stats[cat]["total"] += 1

        try:
            # 創建策略實例
            strategy = strategy_class()
            result = validate_strategy_instance(name, strategy, data)
        except Exception as e:
            result = {"name": name, "status": "❌", "error": str(e)}

        result["category"] = cat

        if result["status"] == "✅":
            results.append(result)
            category_stats[cat]["success"] += 1
            category_stats[cat]["time"] += result["gen_time_ms"]

            # 每 20 個顯示一次進度
            if i % 20 == 0:
                print(f"進度：{i}/{total} ({i / total * 100:.1f}%)")
        else:
            failed.append(result)
            print(f"❌ {name}: {result.get('error', 'Unknown error')}")

    total_time = time.time() - start_time

    # 統計結果
    print("\n" + "=" * 80)
    print("📊 驗證結果統計")
    print("=" * 80)

    success = len(results)
    fail = len(failed)
    success_rate = success / total * 100 if total > 0 else 0

    print(f"\n✅ 成功：{success}/{total} ({success_rate:.1f}%)")
    print(f"❌ 失敗：{fail}/{total}")
    print(f"⏱️  總用時：{total_time:.2f}秒")
    print(f"⚡ 平均每個策略：{total_time / total * 1000:.2f}ms")

    # 按類別統計
    print("\n📋 按類別統計:")
    for cat, stats in sorted(category_stats.items()):
        avg_time = stats["time"] / stats["success"] if stats["success"] > 0 else 0
        rate = stats["success"] / stats["total"] * 100 if stats["total"] > 0 else 0
        print(f"  {cat:20s}: {stats['success']:3d}/{stats['total']:3d} ({rate:.0f}%) - {avg_time:.2f}ms/策略")

    # 性能指標
    print("\n⚡ 性能指標:")
    if results:
        avg_gen_time = sum(r["gen_time_ms"] for r in results) / len(results)
        max_gen_time = max(r["gen_time_ms"] for r in results)
        min_gen_time = min(r["gen_time_ms"] for r in results)

        print(f"  平均信號生成時間：{avg_gen_time:.2f}ms")
        print(f"  最慢策略：{max_gen_time:.2f}ms")
        print(f"  最快策略：{min_gen_time:.2f}ms")

        concurrent_time = max_gen_time
        sequential_time = sum(r["gen_time_ms"] for r in results)

        print(f"\n  130 策略並發預估：{concurrent_time:.2f}ms")
        print(f"  130 策略串行預估：{sequential_time:.2f}ms ({sequential_time / 1000:.2f}秒)")

    # 信號統計
    print("\n📈 信號統計:")
    total_signals = sum(r["signals"] for r in results)
    total_buy = sum(r["buy"] for r in results)
    total_sell = sum(r["sell"] for r in results)

    print(f"  總信號數：{total_signals}")
    print(f"  買入信號：{total_buy}")
    print(f"  賣出信號：{total_sell}")
    if results:
        print(f"  平均每策略：{total_signals / len(results):.1f} 個信號")

    # 失敗詳情
    if failed:
        print("\n❌ 失敗策略詳情:")
        for f in failed:
            print(f"  - {f['name']}: {f.get('error', 'Unknown')}")

    # 保存結果
    print("\n💾 保存驗證結果...")

    # CSV 報告
    import csv

    csv_path = Path(__file__).parent.parent / "docs" / "validation_report.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["name", "category", "status", "signals", "buy", "sell", "gen_time_ms", "pos_time_ms"]
        )
        writer.writeheader()
        for r in results:
            writer.writerow({k: r.get(k, "") for k in writer.fieldnames})

    print(f"✅ CSV 報告：{csv_path}")

    # Markdown 報告
    md_path = Path(__file__).parent.parent / "docs" / "VALIDATION_REPORT_2026-03-22.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# 🔍 StocksX 130 策略驗證報告\n\n")
        f.write(f"**驗證時間**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("**測試數據**: 300 天 OHLCV 數據\n\n")

        f.write("## 📊 總體結果\n\n")
        f.write(f"- ✅ 成功：{success}/{total} ({success_rate:.1f}%)\n")
        f.write(f"- ❌ 失敗：{fail}/{total}\n")
        f.write(f"- ⏱️  總用時：{total_time:.2f}秒\n\n")

        f.write("## 📋 按類別統計\n\n")
        f.write("| 類別 | 成功 | 總數 | 成功率 | 平均時間 |\n")
        f.write("|------|------|------|--------|----------|\n")
        for cat, stats in sorted(category_stats.items()):
            rate = stats["success"] / stats["total"] * 100 if stats["total"] > 0 else 0
            avg = stats["time"] / stats["success"] if stats["success"] > 0 else 0
            f.write(f"| {cat} | {stats['success']} | {stats['total']} | {rate:.1f}% | {avg:.2f}ms |\n")

        f.write("\n## ⚡ 性能指標\n\n")
        if results:
            f.write(f"- 平均信號生成時間：{avg_gen_time:.2f}ms\n")
            f.write(f"- 最慢策略：{max_gen_time:.2f}ms\n")
            f.write(f"- 最快策略：{min_gen_time:.2f}ms\n")
            f.write(f"- 130 策略並發預估：{concurrent_time:.2f}ms\n")
            f.write(f"- 130 策略串行預估：{sequential_time / 1000:.2f}秒\n\n")

        f.write("## 📈 信號統計\n\n")
        f.write(f"- 總信號數：{total_signals}\n")
        f.write(f"- 買入信號：{total_buy}\n")
        f.write(f"- 賣出信號：{total_sell}\n")
        if results:
            f.write(f"- 平均每策略：{total_signals / len(results):.1f}個信號\n\n")

        if failed:
            f.write("## ❌ 失敗策略\n\n")
            for fail_item in failed:
                f.write(f"- **{fail_item['name']}**: {fail_item.get('error', 'Unknown')}\n")
        else:
            f.write("\n## 🎉 所有策略驗證通過！\n")

    print(f"✅ Markdown 報告：{md_path}")

    print("\n" + "=" * 80)
    if fail == 0:
        print("🎉 所有策略驗證通過！")
    else:
        print(f"⚠️  {fail} 個策略驗證失敗，請檢查詳情")
    print("=" * 80)

    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
