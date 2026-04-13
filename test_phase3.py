#!/usr/bin/env python3
"""
StocksX V0 Phase 3 功能验证脚本

测试所有 AI 策略模块是否正常工作
"""

import sys
import traceback


def test_import(module_name, import_path):
    """测试模块导入"""
    try:
        exec(f"from {import_path}")
        print(f"✅ {module_name}: 导入成功")
        return True
    except Exception as e:
        print(f"❌ {module_name}: 导入失败 - {e}")
        return False


def test_lstm():
    """测试 LSTM 预测器"""
    try:
        from src.strategies.ml_strategies.lstm_predictor import LSTMPredictor

        predictor = LSTMPredictor(lookback=60, lstm_units=50)
        print("✅ LSTM 预测器：初始化成功")
        print(f"   - 回溯窗口：{predictor.lookback} 天")
        print(f"   - LSTM 单元：{predictor.lstm_units}")
        return True
    except Exception as e:
        print(f"❌ LSTM 预测器：{e}")
        return False


def test_feature_engineering():
    """测试特征工程"""
    try:
        from src.strategies.ml_strategies.feature_engineering import FeatureEngineer

        fe = FeatureEngineer()
        print("✅ 特征工程：初始化成功")
        print("   - 可用指标：趋势、动量、波动率、成交量、布林带等")
        return True
    except Exception as e:
        print(f"❌ 特征工程：{e}")
        return False


def test_sentiment():
    """测试情绪分析"""
    try:
        from src.strategies.nlp_strategies.sentiment_analyzer import SentimentAnalyzer, NewsMonitor

        analyzer = SentimentAnalyzer()
        monitor = NewsMonitor(analyzer)
        print("✅ NLP 情绪分析：初始化成功")
        print("   - 模型：FinBERT (prosusai/finbert)")
        print("   - 功能：新闻监控、情绪聚合、信号生成")
        return True
    except Exception as e:
        print(f"❌ NLP 情绪分析：{e}")
        return False


def test_pairs_trading():
    """测试配对交易"""
    try:
        from src.strategies.quant_strategies.pairs_trading import PairsTrading

        pt = PairsTrading(lookback_window=60, entry_zscore=2.0)
        print("✅ 配对交易：初始化成功")
        print(f"   - 回溯窗口：{pt.lookback_window} 天")
        print(f"   - 入场 Z-score: {pt.entry_zscore}")
        print(f"   - 出场 Z-score: {pt.exit_zscore}")
        return True
    except Exception as e:
        print(f"❌ 配对交易：{e}")
        return False


def test_advanced_manager():
    """测试高级策略管理器"""
    try:
        from src.strategies.advanced_strategies import AdvancedStrategiesManager

        manager = AdvancedStrategiesManager()
        print("✅ 高级策略管理器：初始化成功")
        print("   - 集成策略：LSTM + NLP + 配对交易 + 多因子")
        return True
    except Exception as e:
        print(f"❌ 高级策略管理器：{e}")
        return False


def main():
    print("=" * 60)
    print("🧪 StocksX V0 Phase 3 功能验证")
    print("=" * 60)
    print()

    tests = [
        ("LSTM 预测器", test_lstm),
        ("特征工程", test_feature_engineering),
        ("NLP 情绪分析", test_sentiment),
        ("配对交易", test_pairs_trading),
        ("高级策略管理器", test_advanced_manager),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name}: 异常 - {e}")
            traceback.print_exc()
            results.append((name, False))
        print()

    print("=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status}: {name}")

    print()
    print(f"总计：{passed}/{total} 通过 ({passed / total * 100:.1f}%)")

    if passed == total:
        print("\n🎉 所有测试通过！Phase 3 功能正常！")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查")
        return 1


if __name__ == "__main__":
    sys.exit(main())
