"""
LSTM 价格预测策略

使用长短期记忆网络预测未来价格方向
- 输入：过去 N 天的 OHLCV + 技术指标
- 输出：未来 M 天的价格涨跌概率
"""

from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd

try:
    import tensorflow as tf  # noqa: F401
    from tensorflow import keras
    from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
    from tensorflow.keras.layers import LSTM, BatchNormalization, Dense, Dropout
    from tensorflow.keras.models import Sequential, load_model

    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False


class LSTMPredictor:
    """LSTM 价格预测器"""

    def __init__(self, lookback: int = 60, forecast_horizon: int = 5, lstm_units: int = 50, dropout_rate: float = 0.2):
        """
        初始化 LSTM 预测器

        Args:
            lookback: 回溯天数（使用过去多少天的数据）
            forecast_horizon: 预测 horizon（预测未来多少天）
            lstm_units: LSTM 单元数
            dropout_rate: Dropout 比例
        """
        self.lookback = lookback
        self.forecast_horizon = forecast_horizon
        self.lstm_units = lstm_units
        self.dropout_rate = dropout_rate
        self.model: Sequential | None = None
        self.scaler = None
        self.feature_columns = []

    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        创建技术指标特征

        包括：
        - 移动平均线（MA5, MA10, MA20, MA60）
        - EMA
        - RSI
        - MACD
        - 布林带
        - 波动率
        - 成交量变化
        """
        df = df.copy()

        # 移动平均线
        df["ma5"] = df["close"].rolling(window=5).mean()
        df["ma10"] = df["close"].rolling(window=10).mean()
        df["ma20"] = df["close"].rolling(window=20).mean()
        df["ma60"] = df["close"].rolling(window=60).mean()

        # EMA
        df["ema5"] = df["close"].ewm(span=5).mean()
        df["ema10"] = df["close"].ewm(span=10).mean()

        # RSI
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df["rsi"] = 100 - (100 / (1 + rs))

        # MACD
        exp1 = df["close"].ewm(span=12).mean()
        exp2 = df["close"].ewm(span=26).mean()
        df["macd"] = exp1 - exp2
        df["macd_signal"] = df["macd"].ewm(span=9).mean()
        df["macd_hist"] = df["macd"] - df["macd_signal"]

        # 布林带
        df["bb_middle"] = df["close"].rolling(window=20).mean()
        bb_std = df["close"].rolling(window=20).std()
        df["bb_upper"] = df["bb_middle"] + (bb_std * 2)
        df["bb_lower"] = df["bb_middle"] - (bb_std * 2)
        df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / df["bb_middle"]

        # 波动率
        df["volatility"] = df["close"].pct_change().rolling(window=20).std()

        # 成交量变化
        df["volume_change"] = df["volume"].pct_change()

        # 价格动量
        df["momentum"] = df["close"].pct_change(periods=10)

        # 归一化特征
        self.feature_columns = [
            "ma5",
            "ma10",
            "ma20",
            "ma60",
            "ema5",
            "ema10",
            "rsi",
            "macd",
            "macd_signal",
            "macd_hist",
            "bb_width",
            "volatility",
            "volume_change",
            "momentum",
        ]

        return df

    def prepare_data(self, df: pd.DataFrame, target_col: str = "close") -> tuple[np.ndarray, np.ndarray]:
        """
        准备训练数据

        Returns:
            X: 形状为 (samples, lookback, features) 的输入数据
            y: 形状为 (samples,) 的目标标签（涨跌）
        """
        # 创建特征
        df = self.create_features(df)

        # 删除 NaN
        df = df.dropna()

        if len(df) < self.lookback + self.forecast_horizon:
            raise ValueError(f"数据量不足，需要至少 {self.lookback + self.forecast_horizon} 条数据")

        # 归一化
        from sklearn.preprocessing import MinMaxScaler

        self.scaler = MinMaxScaler()
        df_scaled = df.copy()
        df_scaled[self.feature_columns] = self.scaler.fit_transform(df[self.feature_columns])

        # 创建序列数据
        X, y = [], []
        for i in range(len(df_scaled) - self.lookback - self.forecast_horizon + 1):
            # 输入：过去 lookback 天的特征
            X.append(df_scaled[self.feature_columns].iloc[i : i + self.lookback].values)

            # 输出：未来 forecast_horizon 天的价格变化方向
            current_price = df[target_col].iloc[i + self.lookback - 1]
            future_price = df[target_col].iloc[i + self.lookback + self.forecast_horizon - 1]
            y.append(1 if future_price > current_price else 0)

        return np.array(X), np.array(y)

    def build_model(self, input_shape: tuple[int, int]) -> Sequential:
        """构建 LSTM 模型"""
        if not TF_AVAILABLE:
            raise ImportError("请安装 TensorFlow: pip install tensorflow")

        model = Sequential(
            [
                LSTM(self.lstm_units, return_sequences=True, input_shape=input_shape),
                BatchNormalization(),
                Dropout(self.dropout_rate),
                LSTM(self.lstm_units // 2, return_sequences=False),
                BatchNormalization(),
                Dropout(self.dropout_rate),
                Dense(32, activation="relu"),
                BatchNormalization(),
                Dropout(self.dropout_rate / 2),
                Dense(1, activation="sigmoid"),  # 二分类：涨/跌
            ]
        )

        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss="binary_crossentropy",
            metrics=["accuracy", keras.metrics.AUC(name="auc")],
        )

        self.model = model
        return model

    def train(
        self,
        df: pd.DataFrame,
        epochs: int = 50,
        batch_size: int = 32,
        validation_split: float = 0.2,
        model_path: str | None = None,
    ) -> keras.callbacks.History:
        """
        训练模型

        Args:
            df: 包含 OHLCV 数据的 DataFrame
            epochs: 训练轮数
            batch_size: 批次大小
            validation_split: 验证集比例
            model_path: 模型保存路径

        Returns:
            训练历史
        """
        # 准备数据
        X, y = self.prepare_data(df)

        # 构建模型
        input_shape = (X.shape[1], X.shape[2])
        if self.model is None:
            self.build_model(input_shape)

        # 回调函数
        callbacks = [
            EarlyStopping(monitor="val_loss", patience=10, restore_best_weights=True, verbose=1),
            ModelCheckpoint(
                model_path or "lstm_model.h5", monitor="val_accuracy", save_best_only=True, mode="max", verbose=1
            )
            if model_path
            else None,
        ]
        callbacks = [c for c in callbacks if c is not None]

        # 训练
        history = self.model.fit(
            X,
            y,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            callbacks=callbacks,
            verbose=1,
        )

        return history

    def predict(self, df: pd.DataFrame) -> float:
        """
        预测未来价格方向

        Returns:
            上涨概率（0-1 之间）
        """
        if self.model is None:
            raise ValueError("模型未训练或未加载")

        # 准备数据
        X, _ = self.prepare_data(df)

        # 使用最后一条数据进行预测
        last_sequence = X[-1:].reshape(1, self.lookback, -1)
        probability = self.model.predict(last_sequence, verbose=0)[0, 0]

        return float(probability)

    def predict_signal(self, df: pd.DataFrame, threshold: float = 0.6) -> dict:
        """
        生成交易信号

        Args:
            df: OHLCV 数据
            threshold: 信号阈值

        Returns:
            信号字典
        """
        probability = self.predict(df)

        if probability >= threshold:
            signal = 1  # 买入
            action = "BUY"
        elif probability <= (1 - threshold):
            signal = -1  # 卖出
            action = "SELL"
        else:
            signal = 0  # 持有
            action = "HOLD"

        return {
            "strategy": "lstm_prediction",
            "signal": signal,
            "action": action,
            "confidence": probability if signal == 1 else (1 - probability),
            "probability_up": probability,
            "timestamp": int(datetime.now().timestamp() * 1000),
        }

    def save(self, path: str):
        """保存模型"""
        if self.model:
            self.model.save(path)

    def load(self, path: str):
        """加载模型"""
        if TF_AVAILABLE:
            self.model = load_model(path)


# ════════════════════════════════════════════════════════════
# 使用示例
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # 创建示例数据
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=500, freq="D")
    df = pd.DataFrame(
        {
            "open": np.random.randn(500).cumsum() + 100,
            "high": np.random.randn(500).cumsum() + 101,
            "low": np.random.randn(500).cumsum() + 99,
            "close": np.random.randn(500).cumsum() + 100,
            "volume": np.random.randint(1000, 10000, 500),
        },
        index=dates,
    )

    # 训练模型
    predictor = LSTMPredictor(lookback=60, lstm_units=50)

    print("开始训练 LSTM 模型...")
    history = predictor.train(df, epochs=20, batch_size=32)

    # 预测
    signal = predictor.predict_signal(df)
    print(f"\n预测信号：{signal}")
