"""
AI/ML 策略最終補全 - Batch 3
包含 7 個 AI/ML 最後策略

作者：StocksX Team
創建日期：2026-03-22
狀態：✅ 批量生成
"""

import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from base_strategy import BaseStrategy


# ============================================================================
# 1. 遷移學習策略
# ============================================================================


class TransferLearning(BaseStrategy):
    """
    遷移學習策略

    將在一個市場訓練的模型應用於另一個相關市場。

    核心思想：
    - 在流動性高的市場（如美股）訓練模型
    - 將學習到的特徵應用於流動性低的市場（如台股）
    - 加速新市場的策略適配

    注意：此為骨架實現，實際使用需要預訓練模型。
    """

    def __init__(self, source_market: str = "US", target_market: str = "TW", lookback: int = 60):
        super().__init__(
            "遷移學習",
            {"source_market": source_market, "target_market": target_market, "lookback": lookback},
            category="ai_ml",
        )

        self.source_model = None  # TODO: 加載源市場預訓練模型

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號（骨架：使用技術指標模擬）"""
        lookback = self.params["lookback"]
        close = data["close"]

        signals = pd.Series(0, index=data.index)

        # 計算多個技術指標（模擬遷移學習的特徵提取）
        ma = close.rolling(window=20).mean()
        std = close.rolling(window=20).std()
        rsi = self._calculate_rsi(close, 14)

        # 標準化特徵
        z_score = (close - ma) / std

        # 生成信號：結合多個特徵
        buy_signal = (z_score < -1.5) & (rsi < 30)
        sell_signal = (z_score > 1.5) & (rsi > 70)

        signals[buy_signal] = 1
        signals[sell_signal] = -1

        return signals

    def _calculate_rsi(self, close: pd.Series, period: int) -> pd.Series:
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0:
            return 0
        risk = capital * 0.02
        return risk / (price * volatility)


# ============================================================================
# 2. 對比學習策略
# ============================================================================


class ContrastiveLearning(BaseStrategy):
    """
    對比學習策略

    通過對比正負樣本學習市場狀態的表示。

    核心思想：
    - 正樣本：相似的市場狀態（都上漲或都下跌）
    - 負樣本：相反的市場狀態（一個上漲一個下跌）
    - 學習使正樣本接近、負樣本遠離的表示

    注意：此為骨架實現，實際使用需要對比學習框架。
    """

    def __init__(self, lookback: int = 60, embedding_dim: int = 64):
        super().__init__("對比學習", {"lookback": lookback, "embedding_dim": embedding_dim}, category="ai_ml")

        self.encoder = None  # TODO: 對比學習編碼器

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號（骨架：使用價格模式匹配模擬）"""
        lookback = self.params["lookback"]
        close = data["close"]

        signals = pd.Series(0, index=data.index)

        # 計算價格變化模式
        returns = close.pct_change()

        # 滾動相關性（模擬對比學習的相似度計算）
        rolling_corr = returns.rolling(window=20).corr(returns.shift(1))

        # 波動率聚類（對比學習可以捕捉的模式）
        volatility = returns.rolling(window=20).std()
        vol_change = volatility.pct_change()

        # 生成信號
        buy_signal = (rolling_corr > 0.3) & (vol_change < 0)
        sell_signal = (rolling_corr < -0.3) & (vol_change > 0)

        signals[buy_signal] = 1
        signals[sell_signal] = -1

        return signals

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0:
            return 0
        risk = capital * 0.015
        return risk / (price * volatility)


# ============================================================================
# 3. LSTM 預測策略
# ============================================================================


class LSTMPredictor(BaseStrategy):
    """
    LSTM 長期短期記憶預測策略

    使用 LSTM 神經網絡預測價格趨勢。

    核心思想：
    - LSTM 可以捕捉時間序列的長期依賴
    - 輸入：過去 N 天的價格、成交量等特徵
    - 輸出：未來 M 天的價格方向預測

    注意：此為骨架實現，實際使用需要訓練 LSTM 模型。
    """

    def __init__(self, lookback: int = 60, hidden_units: int = 128):
        super().__init__("LSTM 預測", {"lookback": lookback, "hidden_units": hidden_units}, category="ai_ml")

        self.lstm_model = None  # TODO: 加載訓練好的 LSTM 模型

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號（骨架：使用技術指標模擬 LSTM 預測）"""
        lookback = self.params["lookback"]
        close = data["close"]
        volume = data.get("volume", pd.Series(1, index=data.index))

        signals = pd.Series(0, index=data.index)

        # 計算多個特徵（模擬 LSTM 的輸入）
        ma5 = close.rolling(5).mean()
        ma10 = close.rolling(10).mean()
        ma20 = close.rolling(20).mean()

        # 價格相對均線的位置
        price_vs_ma5 = (close - ma5) / ma5
        price_vs_ma10 = (close - ma10) / ma10
        price_vs_ma20 = (close - ma20) / ma20

        # 成交量變化
        vol_ma = volume.rolling(20).mean()
        vol_ratio = volume / vol_ma

        # 綜合信號（模擬 LSTM 輸出）
        trend_score = price_vs_ma5 + price_vs_ma10 * 0.5 + price_vs_ma20 * 0.25
        vol_confirm = vol_ratio > 1.2

        signals[trend_score > 0.05] = 1
        signals[trend_score < -0.05] = -1

        return signals

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0:
            return 0
        risk = capital * 0.02
        return risk / (price * volatility)


# ============================================================================
# 4. 強化學習 DQN 策略
# ============================================================================


class DQNAgent(BaseStrategy):
    """
    深度 Q 網絡強化學習策略

    使用 DQN 學習最優交易策略。

    核心思想：
    - 狀態：市場特徵（價格、指標、持倉等）
    - 動作：買入、賣出、持有
    - 獎勵：交易收益
    - 通過試錯學習最優策略

    注意：此為骨架實現，實際使用需要訓練 DQN 模型。
    """

    def __init__(self, lookback: int = 60, gamma: float = 0.99, epsilon: float = 0.1):
        super().__init__(
            "DQN 強化學習",
            {
                "lookback": lookback,
                "gamma": gamma,  # 折扣因子
                "epsilon": epsilon,  # 探索率
            },
            category="ai_ml",
        )

        self.q_network = None  # TODO: 加載訓練好的 Q 網絡
        self.position = 0  # 當前持倉

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號（骨架：使用規則模擬 DQN）"""
        lookback = self.params["lookback"]
        close = data["close"]

        signals = pd.Series(0, index=data.index)

        # 計算狀態特徵
        ma20 = close.rolling(20).mean()
        ma50 = close.rolling(50).mean()
        rsi = self._calculate_rsi(close, 14)

        # 趨勢判斷
        uptrend = (close > ma20) & (ma20 > ma50)
        downtrend = (close < ma20) & (ma20 < ma50)

        # 超買超賣
        oversold = rsi < 30
        overbought = rsi > 70

        # DQN 策略（模擬）：
        # - 趨勢 + 超賣 → 買入
        # - 趨勢向下 + 超買 → 賣出
        buy_signal = uptrend & oversold
        sell_signal = downtrend & overbought

        signals[buy_signal] = 1
        signals[sell_signal] = -1

        return signals

    def _calculate_rsi(self, close: pd.Series, period: int) -> pd.Series:
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0:
            return 0
        risk = capital * 0.025
        return risk / (price * volatility)


# ============================================================================
# 5. 多因子模型策略
# ============================================================================


class MultiFactorModel(BaseStrategy):
    """
    多因子模型策略

    結合多個因子（價值、動量、質量等）預測收益。

    核心思想：
    - 價值因子：低估值股票表現更好
    - 動量因子：過去表現好的繼續表現好
    - 質量因子：高質量公司表現更穩健
    - 通過回歸或 ML 模型組合因子

    注意：此為骨架實現，實際使用需要因子數據。
    """

    def __init__(self, factors: list[str] = None, lookback: int = 252):
        if factors is None:
            factors = ["momentum", "volatility", "volume"]

        super().__init__("多因子模型", {"factors": factors, "lookback": lookback}, category="ai_ml")

        self.factor_weights = None  # TODO: 從回歸或 ML 模型獲取

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號"""
        lookback = self.params["lookback"]
        close = data["close"]
        volume = data.get("volume", pd.Series(1, index=data.index))

        signals = pd.Series(0, index=data.index)

        # 因子 1: 動量因子（過去收益）
        momentum = close.pct_change(lookback)
        momentum_z = (momentum - momentum.rolling(252).mean()) / momentum.rolling(252).std()

        # 因子 2: 波動率因子（低波動異象）
        volatility = close.pct_change().rolling(20).std()
        vol_z = -(volatility - volatility.rolling(252).mean()) / volatility.rolling(252).std()

        # 因子 3: 成交量因子
        vol_ma = volume.rolling(20).mean()
        vol_factor = volume / vol_ma
        vol_z = (vol_factor - vol_factor.rolling(252).mean()) / vol_factor.rolling(252).std()

        # 等權重組合因子
        composite_score = momentum_z * 0.4 + vol_z * 0.3 + vol_z * 0.3

        # 生成信號
        signals[composite_score > 1.0] = 1
        signals[composite_score < -1.0] = -1

        return signals

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0:
            return 0
        risk = capital * 0.02
        return risk / (price * volatility)


# ============================================================================
# 6. 配對交易策略
# ============================================================================


class PairTrading(BaseStrategy):
    """
    配對交易策略

    尋找兩隻高度相關的股票，當價差偏離時進行套利。

    核心思想：
    - 找到歷史高度相關的股票對
    - 計算價差（spread）
    - 當價差偏離均值時：買入弱勢股，賣出強勢股
    - 當價差回歸均值時：平倉獲利

    注意：此為骨架實現，實際使用需要兩隻股票的數據。
    """

    def __init__(self, partner_symbol: str = "PARTNER", lookback: int = 60, entry_z: float = 2.0, exit_z: float = 0.5):
        super().__init__(
            "配對交易",
            {"partner_symbol": partner_symbol, "lookback": lookback, "entry_z": entry_z, "exit_z": exit_z},
            category="ai_ml",
        )

        self.hedge_ratio = None  # TODO: 從回歸計算
        self.spread_mean = None
        self.spread_std = None

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號（骨架：使用單股票模擬）"""
        lookback = self.params["lookback"]
        entry_z = self.params["entry_z"]
        close = data["close"]

        signals = pd.Series(0, index=data.index)

        # 計算價格與均線的偏離（模擬價差）
        ma = close.rolling(lookback).mean()
        spread = close - ma

        # 計算 Z-Score
        spread_mean = spread.rolling(lookback).mean()
        spread_std = spread.rolling(lookback).std()
        z_score = (spread - spread_mean) / spread_std

        # 生成信號
        # Z > 2: 價格過高，賣出
        # Z < -2: 價格過低，買入
        signals[z_score < -entry_z] = 1
        signals[z_score > entry_z] = -1

        return signals

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0:
            return 0
        risk = capital * 0.015  # 配對交易風險較低
        return risk / (price * volatility)


# ============================================================================
# 7. 集成投票策略
# ============================================================================


class EnsembleVotingFinal(BaseStrategy):
    """
    集成投票策略（最終版）

    結合多個模型的預測進行投票。

    核心思想：
    - 多個獨立模型（LSTM、RF、XGBoost 等）各自預測
    - 多數投票決定最終信號
    - 降低單模型風險，提高穩定性

    注意：此為骨架實現，實際使用需要多個訓練好的模型。
    """

    def __init__(self, num_models: int = 5, threshold: float = 0.6):
        super().__init__("集成投票", {"num_models": num_models, "threshold": threshold}, category="ai_ml")

        self.models = []  # TODO: 加載多個模型

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信號（骨架：使用多個技術指標模擬多模型投票）"""
        close = data["close"]
        volume = data.get("volume", pd.Series(1, index=data.index))
        threshold = self.params["threshold"]

        signals = pd.Series(0, index=data.index)

        # 模型 1: 趨勢跟隨（均線交叉）
        ma20 = close.rolling(20).mean()
        ma50 = close.rolling(50).mean()
        model1 = pd.Series(0, index=data.index)
        model1[ma20 > ma50] = 1
        model1[ma20 < ma50] = -1

        # 模型 2: 動量（RSI）
        rsi = self._calculate_rsi(close, 14)
        model2 = pd.Series(0, index=data.index)
        model2[rsi < 30] = 1
        model2[rsi > 70] = -1

        # 模型 3: 波動率突破（布林帶）
        bb_upper = close.rolling(20).mean() + 2 * close.rolling(20).std()
        bb_lower = close.rolling(20).mean() - 2 * close.rolling(20).std()
        model3 = pd.Series(0, index=data.index)
        model3[close < bb_lower] = 1
        model3[close > bb_upper] = -1

        # 模型 4: 成交量確認
        vol_ma = volume.rolling(20).mean()
        model4 = pd.Series(0, index=data.index)
        model4[(close > close.shift(1)) & (volume > vol_ma)] = 1
        model4[(close < close.shift(1)) & (volume > vol_ma)] = -1

        # 模型 5: 均值回歸
        z_score = (close - close.rolling(20).mean()) / close.rolling(20).std()
        model5 = pd.Series(0, index=data.index)
        model5[z_score < -2] = 1
        model5[z_score > 2] = -1

        # 投票
        votes = model1 + model2 + model3 + model4 + model5
        num_models = 5

        # 買入：超過 60% 模型看漲
        # 賣出：超過 60% 模型看跌
        signals[votes >= num_models * threshold] = 1
        signals[votes <= -num_models * threshold] = -1

        return signals

    def _calculate_rsi(self, close: pd.Series, period: int) -> pd.Series:
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        if signal == 0:
            return 0
        risk = capital * 0.02
        return risk / (price * volatility)


# ============================================================================
# 註冊所有 AI/ML 最終策略
# ============================================================================

AI_ML_FINAL_STRATEGIES = {
    "transfer_learning": TransferLearning,
    "contrastive_learning": ContrastiveLearning,
    "lstm_predictor": LSTMPredictor,
    "dqn_agent": DQNAgent,
    "multi_factor": MultiFactorModel,
    "pair_trading": PairTrading,
    "ensemble_voting_final": EnsembleVotingFinal,
}

__all__ = [
    "AI_ML_FINAL_STRATEGIES",
    "TransferLearning",
    "ContrastiveLearning",
    "LSTMPredictor",
    "DQNAgent",
    "MultiFactorModel",
    "PairTrading",
    "EnsembleVotingFinal",
]
