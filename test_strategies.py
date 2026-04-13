#!/usr/bin/env python3
"""
策略测试脚本

测试所有新技术策略的功能
- LSTM 价格预测
- 特征工程
- NLP 情绪分析
- 配对交易
- 多因子模型
- 强化学习环境
- DQN Agent
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# 颜色输出
class Colors:
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    RED = "\033[0;31m"
    BLUE = "\033[0;34m"
    NC = "\033[0m"  # No Color


def print_header(text):
    print(f"\n{Colors.BLUE}{'=' * 60}{Colors.NC}")
    print(f"{Colors.BLUE}{text:^60}{Colors.NC}")
    print(f"{Colors.BLUE}{'=' * 60}{Colors.NC}\n")


def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.NC}")


def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.NC}")


def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.NC}")

# ════════════════════════════════════════════════════════════
# 创建测试数据
# ════════════════════════════════════════════════════════════


def create_test_data(n=500):
    """创建示例测试数据"""
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=n, freq="D")

    # 生成价格数据
    df = pd.DataFrame(
        {
            "open": np.random.randn(n).cumsum() + 100,
            "high": np.random.randn(n).cumsum() + 101,
            "low": np.random.randn(n).cumsum() + 99,
            "close": np.random.randn(n).cumsum() + 100,
            "volume": np.random.randint(1000, 10000, n),
        },
        index=dates,
    )

    return df

# ════════════════════════════════════════════════════════════
# 测试 1: 特征工程
# ════════════════════════════════════════════════════════════


def test_feature_engineering():
    """测试特征工程模块"""
    print_header("测试 1: 特征工程模块")

    try:
        from src.strategies.ml_strategies.feature_engineering import FeatureEngineer

        # 创建测试数据
        df = create_test_data(500)

        # 创建特征
        fe = FeatureEngineer()
        df_features = fe.create_technical_features(df)

        print_success("创建特征完成")
        print(f"  原始特征数：{len(df.columns)}")
        print(f"  新增特征数：{len(df_features.columns) - len(df.columns)}")
        print(f"  总特征数：{len(df_features.columns)}")

        # 显示部分特征
        print("\n新增特征示例:")
        new_cols = [c for c in df_features.columns if c not in df.columns][:10]
        for col in new_cols:
            print(f"  - {col}")

        # 特征选择
        df_clean = df_features.dropna()
        target = pd.Series(np.random.randint(0, 2, len(df_clean)))
        selected = fe.select_features(df_clean, target, k=20)

        print_success(f"特征选择完成：选中 {len(selected)} 个特征")

        return True

    except Exception as e:
        print_error(f"特征工程测试失败：{e}")
        import traceback

        traceback.print_exc()
        return False

# ════════════════════════════════════════════════════════════
# 测试 2: LSTM 预测器
# ════════════════════════════════════════════════════════════


def test_lstm_predictor():
    """测试 LSTM 预测器"""
    print_header("测试 2: LSTM 价格预测器")

    try:
        from src.strategies.ml_strategies.lstm_predictor import LSTMPredictor

        # 创建测试数据
        df = create_test_data(500)

        # 创建预测器
        predictor = LSTMPredictor(lookback=20, lstm_units=32, forecast_horizon=3)

        print_success("LSTM 预测器初始化完成")
        print(f"  回溯窗口：{predictor.lookback} 天")
        print(f"  预测周期：{predictor.forecast_horizon} 天")
        print(f"  LSTM 单元：{predictor.lstm_units}")

        # 快速训练（少量 epochs 用于测试）
        print("\n开始快速训练（5 epochs）...")
        history = predictor.train(df, epochs=5, batch_size=32, validation_split=0.2)

        final_loss = history.history["loss"][-1]
        final_acc = history.history["accuracy"][-1]

        print_success("训练完成")
        print(f"  最终损失：{final_loss:.4f}")
        print(f"  最终准确率：{final_acc:.2%}")

        # 预测
        signal = predictor.predict_signal(df)
        print_success(f"预测信号：{signal['action']} (信心度：{signal['confidence']:.2%})")

        return True

    except Exception as e:
        print_warning(f"LSTM 测试跳过（可能需要安装 TensorFlow）: {e}")
        return False

# ════════════════════════════════════════════════════════════
# 测试 3: NLP 情绪分析
# ════════════════════════════════════════════════════════════


def test_sentiment_analyzer():
    """测试 NLP 情绪分析"""
    print_header("测试 3: NLP 情绪分析")

    try:
        from src.strategies.nlp_strategies.sentiment_analyzer import SentimentAnalyzer, NewsMonitor

        # 示例文本
        sample_texts = [
            "Bitcoin surges to new highs as institutional adoption accelerates",
            "Crypto market faces regulatory uncertainty amid government crackdown",
            "Ethereum upgrade promises faster transactions and lower fees",
            "Major exchange reports security breach, users concerned",
            "Analysts predict bullish trend continuation in Q2",
        ]

        print(f"分析 {len(sample_texts)} 条示例文本...")

        # 注意：首次运行会下载模型（约 500MB）
        print_warning("首次运行会下载 FinBERT 模型（约 500MB），可能需要几分钟...")

        analyzer = SentimentAnalyzer()
        analyzer.load_model()

        print_success("模型加载完成")

        # 分析单个文本
        print("\n分析示例文本:")
        for text in sample_texts[:2]:
            result = analyzer.analyze_single(text)
            print(f"  '{text[:50]}...'")
            print(f"    → {result['label']} (信心度：{result['score']:.2f})")

        # 聚合分析
        agg = analyzer.aggregate_sentiment(sample_texts)
        print_success("聚合分析完成")
        print(f"  整体情绪：{agg['overall_sentiment']}")
        print(f"  正面比例：{agg['positive_ratio']:.2%}")
        print(f"  负面比例：{agg['negative_ratio']:.2%}")

        # 新闻监控
        from datetime import datetime

        monitor = NewsMonitor(analyzer)

        monitor.add_news(
            title="Bitcoin Hits New High",
            content="Institutional adoption continues to grow",
            source="CryptoNews",
            published_at=datetime.now(),
            symbols=["BTC"],
        )

        signal = monitor.get_sentiment_signal(hours=24)
        print_success(f"情绪信号：{signal['action']}")

        return True

    except Exception as e:
        print_warning(f"NLP 测试跳过（需要安装 transformers）: {e}")
        return False

# ════════════════════════════════════════════════════════════
# 测试 4: 配对交易
# ════════════════════════════════════════════════════════════


def test_pairs_trading():
    """测试配对交易策略"""
    print_header("测试 4: 配对交易策略")

    try:
        from src.strategies.quant_strategies.pairs_trading import PairsTrading

        # 创建协整序列
        np.random.seed(42)
        n = 500
        base = np.random.randn(n).cumsum()
        price1 = pd.Series(base + np.random.randn(n) * 0.5)
        price2 = pd.Series(base * 0.8 + np.random.randn(n) * 0.3)

        # 创建策略
        pt = PairsTrading(lookback_window=60, entry_zscore=2.0, exit_zscore=0.5)

        print_success("配对交易策略初始化完成")

        # 协整检验
        hedge_ratio, p_value, is_coint = pt.cointegration_test(price1, price2)

        print("\n协整检验结果:")
        print(f"  对冲比率：{hedge_ratio:.4f}")
        print(f"  ADF p-value: {p_value:.6f}")
        print(f"  是否协整：{is_coint}")

        if is_coint:
            print_success("✓ 价格序列存在协整关系")
        else:
            print_warning("⚠ 价格序列不存在协整关系")

        # 生成信号
        signal = pt.generate_signal(price1, price2)
        print_success(f"交易信号：{signal['action']}")
        print(f"  Z-score: {signal['zscore']:.2f}")
        print(f"  对冲比率：{signal['hedge_ratio']}")

        # 回测
        results = pt.backtest(price1, price2, initial_capital=100000)
        if "error" not in results:
            print_success("回测完成")
            print(f"  总收益：{results['total_return']:.2%}")
            print(f"  Sharpe: {results['sharpe_ratio']:.2f}")
            print(f"  最大回撤：{results['max_drawdown']:.2%}")
            print(f"  交易次数：{results['num_trades']}")

        return True

    except Exception as e:
        print_error(f"配对交易测试失败：{e}")
        import traceback

        traceback.print_exc()
        return False

# ════════════════════════════════════════════════════════════
# 测试 5: 多因子策略
# ════════════════════════════════════════════════════════════


def test_multi_factor():
    """测试多因子策略"""
    print_header("测试 5: 多因子策略")

    try:
        from src.strategies.quant_strategies.multi_factor import MultiFactorModel, MultiFactorStrategy

        # 创建示例股票数据
        stocks = ["AAPL", "GOOGL", "MSFT", "AMZN", "META", "NVDA", "TSLA", "JPM", "V", "JNJ"]
        n_stocks = len(stocks)

        stock_data = pd.DataFrame(
            {
                "market_cap": np.random.uniform(50, 2000, n_stocks) * 1e9,
                "pe_ratio": np.random.uniform(10, 50, n_stocks),
                "pb_ratio": np.random.uniform(1, 10, n_stocks),
                "roe": np.random.uniform(0.1, 0.4, n_stocks),
                "debt_to_equity": np.random.uniform(0.1, 2.0, n_stocks),
                "volatility": np.random.uniform(0.15, 0.5, n_stocks),
                "close": np.random.uniform(50, 500, n_stocks),
            },
            index=stocks,
        )

        # 创建模型
        model = MultiFactorModel()

        print_success("多因子模型初始化完成")
        print(f"  因子列表：{', '.join(model.factors)}")

        # 计算因子得分
        print("\n因子得分示例:")
        for stock in stocks[:3]:
            row = stock_data.loc[stock]

            size_score = model.calculate_size_factor(row["market_cap"], stock_data["market_cap"].median())
            value_score = model.calculate_value_factor(
                row["pe_ratio"], row["pb_ratio"], stock_data["pe_ratio"].median(), stock_data["pb_ratio"].median()
            )

            print(f"  {stock}:")
            print(f"    规模因子：{size_score:.2f}")
            print(f"    价值因子：{value_score:.2f}")

        # 策略信号
        strategy = MultiFactorStrategy(model)
        signal = strategy.generate_signal(stock_data, stock_data["close"])

        print_success("交易信号生成完成")
        print(f"  做多股票数：{signal['long_count']}")
        print(f"  做空股票数：{signal['short_count']}")

        return True

    except Exception as e:
        print_error(f"多因子测试失败：{e}")
        import traceback

        traceback.print_exc()
        return False

# ════════════════════════════════════════════════════════════
# 测试 6: 强化学习环境
# ════════════════════════════════════════════════════════════


def test_rl_env():
    """测试强化学习环境"""
    print_header("测试 6: 强化学习环境")

    try:
        from src.strategies.rl_strategies.trading_env import TradingEnv

        # 创建测试数据
        df = create_test_data(500)
        df["rsi"] = 50 + np.random.randn(500) * 10
        df["macd"] = np.random.randn(500)

        # 创建环境
        env = TradingEnv(df, initial_balance=100000, discrete_actions=True)

        print_success("交易环境初始化完成")
        print(f"  状态维度：{env.observation_space.shape[0]}")
        print(f"  动作数量：{env.action_space.n}")
        print(f"  初始资金：${env.initial_balance:,.0f}")

        # 测试随机动作
        obs, info = env.reset()
        print_success("环境重置完成")

        # 执行几步随机动作
        done = False
        steps = 0
        while not done and steps < 10:
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            steps += 1

        print_success(f"执行 {steps} 步随机动作完成")
        print(f"  最终组合价值：${info['total_value']:,.2f}")
        print(f"  收益率：{info['pnl_pct']:.2%}")
        print(f"  交易次数：{info['num_trades']}")

        # 获取回测结果
        results = env.get_results()
        if "error" not in results:
            print_success("回测结果:")
            print(f"  总收益：{results['total_return']:.2%}")
            print(f"  Sharpe: {results['sharpe_ratio']:.2f}")
            print(f"  最大回撤：{results['max_drawdown']:.2%}")

        return True

    except Exception as e:
        print_error(f"强化学习环境测试失败：{e}")
        import traceback

        traceback.print_exc()
        return False

# ════════════════════════════════════════════════════════════
# 测试 7: 策略集成管理器
# ════════════════════════════════════════════════════════════


def test_advanced_strategies():
    """测试高级策略集成"""
    print_header("测试 7: 策略集成管理器")

    try:
        from src.strategies.advanced_strategies import AdvancedStrategiesManager

        # 创建管理器
        manager = AdvancedStrategiesManager()

        print_success("策略集成管理器初始化完成")

        # 获取所有信号
        signals = manager.get_all_signals()
        print("\n可用策略:")
        for strategy_name in signals["signals"].keys():
            print(f"  - {strategy_name}")

        return True

    except Exception as e:
        print_warning(f"策略集成测试跳过（部分依赖可能未安装）: {e}")
        return False

# ════════════════════════════════════════════════════════════
# 主函数
# ════════════════════════════════════════════════════════════


def main():
    """主测试函数"""
    print_header("🧪 StocksX V0 - 策略测试套件")
    print(f"测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = {
        "特征工程": test_feature_engineering(),
        "LSTM 预测": test_lstm_predictor(),
        "NLP 情绪分析": test_sentiment_analyzer(),
        "配对交易": test_pairs_trading(),
        "多因子策略": test_multi_factor(),
        "强化学习环境": test_rl_env(),
        "策略集成": test_advanced_strategies(),
    }

    # 汇总结果
    print_header("📊 测试结果汇总")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = f"{Colors.GREEN}✓ 通过{Colors.NC}" if result else f"{Colors.YELLOW}⚠ 跳过/失败{Colors.NC}"
        print(f"  {name}: {status}")

    print(f"\n总计：{passed}/{total} 测试通过")

    if passed == total:
        print_success("🎉 所有测试通过！")
    elif passed >= total * 0.7:
        print_success("✅ 大部分测试通过，可以继续使用")
    else:
        print_warning("⚠ 部分测试失败，请检查依赖安装")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
