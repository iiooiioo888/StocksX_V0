"""
AI/ML 策略包
包含 4 個核心 AI/ML 策略：
1. 遺傳演算法優化 (Genetic Optimization)
2. 異常偵測 (Anomaly Detection)
3. 圖神經網路 GNN (Graph Neural Network) - 骨架
4. NLP 事件驅動 (NLP Event Driven) - 骨架

作者：StocksX Team
創建日期：2026-03-21
狀態：🔄 進行中
"""

import pandas as pd
import numpy as np
from typing import Any
import sys
from pathlib import Path

# 添加父目錄到路徑
from src.strategies.base_strategy import BaseStrategy

# ============================================================================
# 1. 遺傳演算法優化策略
# ============================================================================


class GeneticOptimization(BaseStrategy):
    """
    遺傳演算法策略優化

    使用遺傳演算法優化其他策略的參數，
    通過選擇、交叉、變異找到最優參數組合。

    適應度函數：Sharpe Ratio + 最大回撤懲罰

    注意：此策略提供骨架，實際使用時需要：
    1. 定義要優化的基礎策略
    2. 設定參數範圍
    3. 配置遺傳演算法參數（種群大小、代數等）
    """

    def __init__(
        self,
        base_strategy: str = "sma_cross",
        param_ranges: dict[str, tuple[int, int]] = None,
        population_size: int = 20,
        generations: int = 10,
        mutation_rate: float = 0.1,
        crossover_rate: float = 0.8,
    ):
        """
        初始化遺傳演算法策略

        Args:
            base_strategy: 要優化的基礎策略名稱
            param_ranges: 參數範圍字典 {param_name: (min, max)}
            population_size: 種群大小
            generations: 進化代數
            mutation_rate: 變異率
            crossover_rate: 交叉率
        """
        if param_ranges is None:
            param_ranges = {"short": (5, 20), "long": (20, 100)}

        super().__init__(
            "遺傳演算法優化",
            {
                "base_strategy": base_strategy,
                "param_ranges": param_ranges,
                "population_size": population_size,
                "generations": generations,
                "mutation_rate": mutation_rate,
                "crossover_rate": crossover_rate,
            },
            category="ai_ml",
        )

        self.best_params = None
        self.best_fitness = None

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        生成交易信號

        使用優化後的參數生成信號

        Args:
            data: 包含 OHLCV 數據的 DataFrame

        Returns:
            信號 Series
        """
        # 如果還沒有優化參數，先進行優化
        if self.best_params is None:
            self.optimize(data)

        # 使用最優參數生成信號（這裡用 SMA Cross 作為示例）
        short = self.best_params.get("short", 10)
        long_period = self.best_params.get("long", 30)

        # 計算 SMA
        sma_short = data["close"].rolling(window=short).mean()
        sma_long = data["close"].rolling(window=long_period).mean()

        signals = pd.Series(0, index=data.index)

        # 黃金交叉買入
        cross_above = (sma_short > sma_long) & (sma_short.shift(1) < sma_long.shift(1))
        signals[cross_above] = 1

        # 死亡交叉賣出
        cross_below = (sma_short < sma_long) & (sma_short.shift(1) > sma_long.shift(1))
        signals[cross_below] = -1

        return signals

    def optimize(self, data: pd.DataFrame) -> dict[str, Any]:
        """
        執行遺傳演算法優化

        Args:
            data: 歷史數據

        Returns:
            最優參數字典
        """
        np.random.seed(42)

        # 初始化種群
        population = self._initialize_population()

        for generation in range(self.params["generations"]):
            # 計算適應度
            fitness_scores = [self._calculate_fitness(ind, data) for ind in population]

            # 選擇最優個體
            best_idx = np.argmax(fitness_scores)
            best_fitness = fitness_scores[best_idx]
            best_individual = population[best_idx]

            print(f"Generation {generation}: Best Fitness = {best_fitness:.4f}")

            # 選擇（錦標賽選擇）
            selected = self._tournament_selection(population, fitness_scores)

            # 交叉
            offspring = self._crossover(selected)

            # 變異
            population = self._mutate(offspring)

        # 保存最優結果
        self.best_params = self._decode_individual(best_individual)
        self.best_fitness = best_fitness

        print("\nOptimization Complete!")
        print(f"Best Parameters: {self.best_params}")
        print(f"Best Fitness: {self.best_fitness:.4f}")

        return self.best_params

    def _initialize_population(self) -> list[list[float]]:
        """初始化種群"""
        population = []
        param_ranges = self.params["param_ranges"]

        for _ in range(self.params["population_size"]):
            individual = []
            for param_name, (min_val, max_val) in param_ranges.items():
                # 歸一化到 [0, 1]
                individual.append(np.random.random())
            population.append(individual)

        return population

    def _decode_individual(self, individual: list[float]) -> dict[str, int]:
        """將個體解碼為參數"""
        params = {}
        param_names = list(self.params["param_ranges"].keys())

        for i, value in enumerate(individual):
            min_val, max_val = self.params["param_ranges"][param_names[i]]
            # 從 [0,1] 映射到實際範圍
            params[param_names[i]] = int(min_val + value * (max_val - min_val))

        return params

    def _calculate_fitness(self, individual: list[float], data: pd.DataFrame) -> float:
        """
        計算適應度（Sharpe Ratio - 最大回撤懲罰）

        Args:
            individual: 個體（參數組合）
            data: 歷史數據

        Returns:
            適應度分數
        """
        params = self._decode_individual(individual)

        # 計算策略收益（簡化版 SMA Cross）
        short = params.get("short", 10)
        long_period = params.get("long", 30)

        sma_short = data["close"].rolling(window=short).mean()
        sma_long = data["close"].rolling(window=long_period).mean()

        # 生成信號
        signals = pd.Series(0, index=data.index)
        signals[(sma_short > sma_long)] = 1
        signals[(sma_short < sma_long)] = -1

        # 計算收益
        returns = data["close"].pct_change() * signals.shift(1)

        # 計算 Sharpe Ratio
        if returns.std() > 0:
            sharpe = returns.mean() / returns.std() * np.sqrt(252)
        else:
            sharpe = 0

        # 計算最大回撤
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()

        # 適應度 = Sharpe + 回撤懲罰
        fitness = sharpe + 2 * max_drawdown  # 回撤為負，所以是加法

        return fitness

    def _tournament_selection(
        self, population: list[list[float]], fitness_scores: list[float], tournament_size: int = 3
    ) -> list[list[float]]:
        """錦標賽選擇"""
        selected = []

        for _ in range(len(population)):
            # 隨機選擇 tournament_size 個個體
            contestants = np.random.choice(len(population), tournament_size, replace=False)
            # 選擇適應度最高的
            winner_idx = contestants[np.argmax([fitness_scores[i] for i in contestants])]
            selected.append(population[winner_idx])

        return selected

    def _crossover(self, selected: list[list[float]]) -> list[list[float]]:
        """交叉操作"""
        offspring = []

        for i in range(0, len(selected), 2):
            if i + 1 < len(selected):
                parent1 = selected[i]
                parent2 = selected[i + 1]

                if np.random.random() < self.params["crossover_rate"]:
                    # 單點交叉
                    point = np.random.randint(1, len(parent1))
                    child1 = parent1[:point] + parent2[point:]
                    child2 = parent2[:point] + parent1[point:]
                else:
                    child1, child2 = parent1.copy(), parent2.copy()

                offspring.extend([child1, child2])
            else:
                offspring.append(selected[i])

        return offspring

    def _mutate(self, population: list[list[float]]) -> list[list[float]]:
        """變異操作"""
        mutated = []

        for individual in population:
            new_individual = individual.copy()

            for i in range(len(new_individual)):
                if np.random.random() < self.params["mutation_rate"]:
                    # 高斯變異
                    new_individual[i] += np.random.normal(0, 0.1)
                    # 限制在 [0, 1] 範圍
                    new_individual[i] = np.clip(new_individual[i], 0, 1)

            mutated.append(new_individual)

        return mutated

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        """計算倉位大小"""
        if signal == 0:
            return 0

        risk_per_trade = 0.02
        risk_amount = capital * risk_per_trade

        if volatility > 0:
            position_size = risk_amount / (2 * volatility)
        else:
            position_size = 0

        shares = int(position_size / price)
        return max(0, shares)

# ============================================================================
# 2. 異常偵測策略
# ============================================================================


class AnomalyDetection(BaseStrategy):
    """
    異常偵測策略

    使用統計方法（Isolation Forest 或 Z-Score）偵測價格異常，
    在異常低點買入，異常高點賣出。

    方法：
    1. 計算價格的統計特徵（均值、標準差）
    2. 識別異常點（Z-Score > 閾值）
    3. 反向交易：異常低→買，異常高→賣
    """

    def __init__(self, window: int = 20, z_threshold: float = 2.0, method: str = "zscore"):
        """
        初始化異常偵測策略

        Args:
            window: 滾動窗口大小
            z_threshold: Z-Score 閾值
            method: 方法選擇 ('zscore' 或 'isolation')
        """
        super().__init__("異常偵測", {"window": window, "z_threshold": z_threshold, "method": method}, category="ai_ml")

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        生成交易信號

        Args:
            data: 包含 OHLCV 數據的 DataFrame

        Returns:
            信號 Series
        """
        method = self.params["method"]

        if method == "zscore":
            return self._zscore_method(data)
        else:
            # Isolation Forest 需要 sklearn，這裡提供簡化版
            return self._simplified_isolation(data)

    def _zscore_method(self, data: pd.DataFrame) -> pd.Series:
        """Z-Score 方法"""
        window = self.params["window"]
        threshold = self.params["z_threshold"]

        close = data["close"]

        # 計算滾動 Z-Score
        rolling_mean = close.rolling(window=window).mean()
        rolling_std = close.rolling(window=window).std()

        zscore = (close - rolling_mean) / (rolling_std + 1e-10)

        signals = pd.Series(0, index=data.index)

        # 異常低點（Z-Score < -threshold）→ 買入
        signals[zscore < -threshold] = 1

        # 異常高點（Z-Score > threshold）→ 賣出
        signals[zscore > threshold] = -1

        return signals

    def _simplified_isolation(self, data: pd.DataFrame) -> pd.Series:
        """
        簡化版 Isolation Forest 方法

        使用價格偏離度來模擬異常偵測
        """
        window = self.params["window"]

        close = data["close"]

        # 計算價格相對均值的偏離
        rolling_mean = close.rolling(window=window).mean()
        deviation = (close - rolling_mean) / rolling_mean

        # 計算偏離的百分位數
        percentile = deviation.rolling(window=window).apply(lambda x: pd.Series(x).rank(pct=True).iloc[-1])

        signals = pd.Series(0, index=data.index)

        # 極低百分位（< 10%）→ 買入
        signals[percentile < 0.1] = 1

        # 極高百分位（> 90%）→ 賣出
        signals[percentile > 0.9] = -1

        return signals

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        """計算倉位大小"""
        if signal == 0:
            return 0

        # 異常偵測策略使用較小倉位（因為是反向交易）
        risk_per_trade = 0.01
        risk_amount = capital * risk_per_trade

        if volatility > 0:
            position_size = risk_amount / (3 * volatility)  # 更保守
        else:
            position_size = 0

        shares = int(position_size / price)
        return max(0, shares)

# ============================================================================
# 3. 圖神經網路 GNN 策略（骨架）
# ============================================================================


class GraphNeuralNetwork(BaseStrategy):
    """
    圖神經網路策略

    使用 GNN 建模資產間的關聯關係，
    捕捉市場傳導效應和相關性變化。

    注意：此為骨架實現，實際使用需要：
    1. 安裝 PyTorch Geometric
    2. 構建資產關聯圖
    3. 訓練 GNN 模型
    """

    def __init__(
        self, assets: list[str] = None, hidden_dim: int = 64, num_layers: int = 2, correlation_window: int = 60
    ):
        """
        初始化 GNN 策略

        Args:
            assets: 資產列表
            hidden_dim: 隱藏層維度
            num_layers: GNN 層數
            correlation_window: 相關性計算窗口
        """
        if assets is None:
            assets = ["AAPL", "GOOGL", "MSFT", "AMZN"]

        super().__init__(
            "圖神經網路 GNN",
            {
                "assets": assets,
                "hidden_dim": hidden_dim,
                "num_layers": num_layers,
                "correlation_window": correlation_window,
            },
            category="ai_ml",
        )

        self.model = None
        self.graph_data = None

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        生成交易信號

        使用資產相關性網絡生成信號

        Args:
            data: 包含 OHLCV 數據的 DataFrame

        Returns:
            信號 Series
        """
        # 簡化實現：使用相關性矩陣代替 GNN
        # 實際應用中應該使用 PyTorch Geometric 構建 GNN

        window = self.params["correlation_window"]

        # 計算滾動相關性（以 BTC 為例）
        returns = data["close"].pct_change()

        # 計算與自身歷史的相關性（自相關）
        autocorr = returns.rolling(window=window).apply(lambda x: x.autocorr() if len(x) > 1 else 0)

        signals = pd.Series(0, index=data.index)

        # 自相關高 → 趨勢持續 → 順勢交易
        # 自相關低 → 均值回歸 → 反向交易

        # 簡化：當自相關從低變高時買入
        signals[autocorr.diff() > 0.1] = 1
        signals[autocorr.diff() < -0.1] = -1

        return signals

    def build_correlation_graph(self, returns_data: pd.DataFrame) -> np.ndarray:
        """
        構建資產相關性圖

        Args:
            returns_data: 多資產收益率數據

        Returns:
            鄰接矩陣
        """
        # 計算相關性矩陣
        corr_matrix = returns_data.corr()

        # 閾值處理，構建鄰接矩陣
        threshold = 0.5
        adjacency = (np.abs(corr_matrix) > threshold).astype(float)

        return adjacency.values

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        """計算倉位大小"""
        if signal == 0:
            return 0

        risk_per_trade = 0.02
        risk_amount = capital * risk_per_trade

        if volatility > 0:
            position_size = risk_amount / (2 * volatility)
        else:
            position_size = 0

        shares = int(position_size / price)
        return max(0, shares)

# ============================================================================
# 4. NLP 事件驅動策略（骨架）
# ============================================================================


class NLPEventDriven(BaseStrategy):
    """
    NLP 事件驅動策略

    使用自然語言處理分析新聞、社群媒體情緒，
    根據情緒變化生成交易信號。

    注意：此為骨架實現，實際使用需要：
    1. 接入新聞 API（如 NewsAPI, Twitter API）
    2. 使用情感分析模型（如 FinBERT）
    3. 構建情緒指標
    """

    def __init__(self, sentiment_threshold: float = 0.3, window: int = 5, source: str = "mock"):
        """
        初始化 NLP 事件驅動策略

        Args:
            sentiment_threshold: 情緒閾值
            window: 情緒平均窗口
            source: 數據源 ('mock', 'newsapi', 'twitter')
        """
        super().__init__(
            "NLP 事件驅動",
            {"sentiment_threshold": sentiment_threshold, "window": window, "source": source},
            category="ai_ml",
        )

        self.sentiment_history = []

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        生成交易信號

        使用模擬情緒數據（實際應用應接入真實新聞 API）

        Args:
            data: 包含 OHLCV 數據的 DataFrame

        Returns:
            信號 Series
        """
        n = len(data)

        # 模擬情緒數據（-1 到 1，0 為中性）
        # 實際應用中應該從新聞 API 獲取
        np.random.seed(42)
        sentiment = np.random.randn(n) * 0.5
        sentiment = np.clip(sentiment, -1, 1)

        # 計算滾動平均情緒
        sentiment_series = pd.Series(sentiment, index=data.index)
        rolling_sentiment = sentiment_series.rolling(window=self.params["window"]).mean()

        signals = pd.Series(0, index=data.index)

        threshold = self.params["sentiment_threshold"]

        # 情緒極度正面 → 買入
        signals[rolling_sentiment > threshold] = 1

        # 情緒極度負面 → 賣出
        signals[rolling_sentiment < -threshold] = -1

        return signals

    def analyze_sentiment(self, text: str) -> float:
        """
        分析文本情緒

        Args:
            text: 新聞或社群文本

        Returns:
            情緒分數（-1 到 1）
        """
        # 簡化實現：使用關鍵詞匹配
        # 實際應用應該使用 FinBERT 或其他情感分析模型

        positive_words = ["beat", "surge", "growth", "profit", "bullish", "upgrade"]
        negative_words = ["miss", "drop", "loss", "bearish", "downgrade", "crash"]

        text_lower = text.lower()

        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)

        total = pos_count + neg_count
        if total > 0:
            sentiment = (pos_count - neg_count) / total
        else:
            sentiment = 0

        return sentiment

    def calculate_position_size(self, signal: int, capital: float, price: float, volatility: float) -> float:
        """計算倉位大小"""
        if signal == 0:
            return 0

        # NLP 策略使用中等倉位
        risk_per_trade = 0.015
        risk_amount = capital * risk_per_trade

        if volatility > 0:
            position_size = risk_amount / (2.5 * volatility)
        else:
            position_size = 0

        shares = int(position_size / price)
        return max(0, shares)

# ============================================================================
# 策略註冊表
# ============================================================================

AI_ML_STRATEGIES = {
    "genetic_opt": GeneticOptimization,
    "anomaly": AnomalyDetection,
    "gnn": GraphNeuralNetwork,
    "nlp_event": NLPEventDriven,
}

# ============================================================================
# 測試代碼
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("AI/ML 策略測試")
    print("=" * 60)

    # 創建測試數據
    np.random.seed(42)
    n = 300
    dates = pd.date_range("2024-01-01", periods=n, freq="D")

    returns = np.random.randn(n) * 0.02
    close = 100 * np.cumprod(1 + returns)

    data = pd.DataFrame(
        {
            "open": close,
            "high": close * 1.02,
            "low": close * 0.98,
            "close": close,
            "volume": np.random.randint(1000000, 10000000, n),
        },
        index=dates,
    )

    # 測試遺傳演算法
    print("\n1. 遺傳演算法優化")
    genetic = GeneticOptimization(generations=5, population_size=10)
    signals = genetic.generate_signals(data)
    print(f"   信號數量：{signals.sum()}")

    # 測試異常偵測
    print("\n2. 異常偵測")
    anomaly = AnomalyDetection()
    signals = anomaly.generate_signals(data)
    print(f"   信號數量：{signals.sum()}")

    # 測試 GNN
    print("\n3. 圖神經網路")
    gnn = GraphNeuralNetwork()
    signals = gnn.generate_signals(data)
    print(f"   信號數量：{signals.sum()}")

    # 測試 NLP
    print("\n4. NLP 事件驅動")
    nlp = NLPEventDriven()
    signals = nlp.generate_signals(data)
    print(f"   信號數量：{signals.sum()}")

    print("\n" + "=" * 60)
    print("測試完成！")
    print("=" * 60)
