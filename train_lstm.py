#!/usr/bin/env python3
"""
LSTM 模型训练脚本

使用历史数据训练 LSTM 价格预测模型
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime

# 添加项目路径
from src.strategies.ml_strategies.lstm_predictor import LSTMPredictor

def load_data(symbol: str = "BTC/USDT", days: int = 365) -> pd.DataFrame:
    """
    加载历史数据

    Args:
        symbol: 交易对
        days: 天数

    Returns:
        OHLCV DataFrame
    """
    # 尝试从数据服务加载
    try:
        from src.data.service import DataService

        ds = DataService()
        end_date = datetime.now()
        start_date = pd.Timestamp(end_date) - pd.Timedelta(days=days)

        df = ds.get_historical_data(symbol=symbol, start_date=start_date, end_date=end_date, timeframe="1d")

        if df is not None and len(df) > 0:
            print(f"✓ 从数据服务加载 {len(df)} 条数据")
            return df

    except Exception as e:
        print(f"数据服务加载失败：{e}")

    # 备用：使用 CCXT 直接获取
    try:
        import ccxt

        exchange = ccxt.binance()
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe="1d", limit=days)

        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)

        print(f"✓ 从 CCXT 加载 {len(df)} 条数据")
        return df

    except Exception as e:
        print(f"CCXT 加载失败：{e}")

    # 最后备用：生成示例数据
    print("⚠ 使用示例数据（请连接真实数据源）")
    dates = pd.date_range(end=datetime.now(), periods=days, freq="D")
    df = pd.DataFrame(
        {
            "open": np.random.randn(days).cumsum() + 100,
            "high": np.random.randn(days).cumsum() + 101,
            "low": np.random.randn(days).cumsum() + 99,
            "close": np.random.randn(days).cumsum() + 100,
            "volume": np.random.randint(1000, 10000, days),
        },
        index=dates,
    )

    return df

def train_model(
    symbol: str = "BTC/USDT",
    days: int = 365,
    epochs: int = 50,
    batch_size: int = 32,
    output_path: str = "models/lstm_model.h5",
):
    """
    训练 LSTM 模型

    Args:
        symbol: 交易对
        days: 历史天数
        epochs: 训练轮数
        batch_size: 批次大小
        output_path: 模型保存路径
    """
    print("=" * 60)
    print("LSTM 模型训练")
    print("=" * 60)

    # 加载数据
    print(f"\n1️⃣  加载数据：{symbol}, {days}天")
    df = load_data(symbol, days)
    print(f"   数据范围：{df.index[0]} 至 {df.index[-1]}")
    print(f"   数据量：{len(df)} 条")

    # 检查数据质量
    if len(df) < 100:
        print("❌ 数据量不足，需要至少 100 条数据")
        return

    # 创建预测器
    print("\n2️⃣  创建 LSTM 预测器")
    predictor = LSTMPredictor(lookback=60, forecast_horizon=5, lstm_units=50, dropout_rate=0.2)

    # 训练模型
    print(f"\n3️⃣  开始训练：{epochs} epochs, batch_size={batch_size}")
    print("-" * 60)

    try:
        history = predictor.train(
            df, epochs=epochs, batch_size=batch_size, validation_split=0.2, model_path=output_path
        )

        print("-" * 60)
        print("\n✅ 训练完成!")

        # 打印训练结果
        final_loss = history.history["loss"][-1]
        final_acc = history.history["accuracy"][-1]
        final_val_loss = history.history["val_loss"][-1]
        final_val_acc = history.history["accuracy"][-1]

        print("\n📊 训练结果:")
        print(f"   最终损失：{final_loss:.4f}")
        print(f"   最终准确率：{final_acc:.2%}")
        print(f"   验证损失：{final_val_loss:.4f}")
        print(f"   验证准确率：{final_val_acc:.2%}")

        # 测试预测
        print("\n4️⃣  测试预测")
        signal = predictor.predict_signal(df)
        print(f"   预测信号：{signal['action']}")
        print(f"   上涨概率：{signal['probability_up']:.2%}")
        print(f"   信心度：{signal['confidence']:.2%}")

        print(f"\n💾 模型已保存至：{output_path}")

        return predictor

    except Exception as e:
        print(f"\n❌ 训练失败：{e}")
        import traceback

        traceback.print_exc()
        return None

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="训练 LSTM 价格预测模型")
    parser.add_argument("--symbol", type=str, default="BTC/USDT", help="交易对")
    parser.add_argument("--days", type=int, default=365, help="历史天数")
    parser.add_argument("--epochs", type=int, default=50, help="训练轮数")
    parser.add_argument("--batch-size", type=int, default=32, help="批次大小")
    parser.add_argument("--output", type=str, default="models/lstm_model.h5", help="模型保存路径")

    args = parser.parse_args()

    # 创建模型目录
    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    # 训练
    train_model(
        symbol=args.symbol, days=args.days, epochs=args.epochs, batch_size=args.batch_size, output_path=args.output
    )

if __name__ == "__main__":
    main()
