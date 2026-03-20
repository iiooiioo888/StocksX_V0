"""
特征工程模块

为机器学习策略提供特征创建、选择和预处理功能
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.feature_selection import SelectKBest, f_classif, mutual_info_classif
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")


class FeatureEngineer:
    """特征工程器"""

    def __init__(self):
        self.scaler = StandardScaler()
        self.selected_features = []
        self.pca = None

    def create_technical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        创建技术指标特征

        Args:
            df: 包含 OHLCV 的 DataFrame

        Returns:
            包含所有技术指标的 DataFrame
        """
        df = df.copy()

        # ===== 趋势指标 =====
        # 移动平均线
        for window in [5, 10, 20, 50, 60, 200]:
            df[f"ma_{window}"] = df["close"].rolling(window=window).mean()
            df[f"ema_{window}"] = df["close"].ewm(span=window).mean()

        # MA 斜率
        df["ma20_slope"] = df["ma_20"].diff() / df["ma_20"].shift(1)
        df["ma60_slope"] = df["ma_60"].diff() / df["ma_60"].shift(1)

        # 价格与 MA 的距离
        df["price_ma20_dist"] = (df["close"] - df["ma_20"]) / df["ma_20"]
        df["price_ma60_dist"] = (df["close"] - df["ma_60"]) / df["ma_60"]

        # 金叉/死叉信号
        df["golden_cross"] = (df["ma_5"] > df["ma_20"]).astype(int)
        df["death_cross"] = (df["ma_5"] < df["ma_20"]).astype(int)

        # ===== 动量指标 =====
        # RSI
        for window in [7, 14, 21]:
            delta = df["close"].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
            rs = gain / loss
            df[f"rsi_{window}"] = 100 - (100 / (1 + rs))

        # 随机指标 (Stochastic)
        for window in [9, 14]:
            low_min = df["low"].rolling(window=window).min()
            high_max = df["high"].rolling(window=window).max()
            df[f"stoch_k_{window}"] = 100 * (df["close"] - low_min) / (high_max - low_min + 1e-10)
            df[f"stoch_d_{window}"] = df[f"stoch_k_{window}"].rolling(window=3).mean()

        # 价格动量
        for period in [5, 10, 20]:
            df[f"momentum_{period}"] = df["close"].pct_change(periods=period)

        # ROC (Rate of Change)
        df["roc_10"] = (df["close"] - df["close"].shift(10)) / df["close"].shift(10)

        # ===== 波动率指标 =====
        # 历史波动率
        for window in [10, 20, 30]:
            df[f"volatility_{window}"] = df["close"].pct_change().rolling(window=window).std()

        # 真实波动幅度 (ATR)
        high_low = df["high"] - df["low"]
        high_close = np.abs(df["high"] - df["close"].shift())
        low_close = np.abs(df["low"] - df["close"].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df["atr_14"] = true_range.rolling(14).mean()
        df["atr_ratio"] = df["atr_14"] / df["close"]

        # ===== 布林带 =====
        for window in [20]:
            df[f"bb_middle_{window}"] = df["close"].rolling(window=window).mean()
            bb_std = df["close"].rolling(window=window).std()
            df[f"bb_upper_{window}"] = df[f"bb_middle_{window}"] + (bb_std * 2)
            df[f"bb_lower_{window}"] = df[f"bb_middle_{window}"] - (bb_std * 2)
            df[f"bb_width_{window}"] = (df[f"bb_upper_{window}"] - df[f"bb_lower_{window}"]) / df[f"bb_middle_{window}"]
            df["bb_position"] = (df["close"] - df[f"bb_lower_{window}"]) / (
                df[f"bb_upper_{window}"] - df[f"bb_lower_{window}"] + 1e-10
            )

        # ===== MACD =====
        exp12 = df["close"].ewm(span=12).mean()
        exp26 = df["close"].ewm(span=26).mean()
        df["macd"] = exp12 - exp26
        df["macd_signal"] = df["macd"].ewm(span=9).mean()
        df["macd_hist"] = df["macd"] - df["macd_signal"]
        df["macd_cross"] = (df["macd"] > df["macd_signal"]).astype(int)

        # ===== 成交量指标 =====
        # 成交量 MA
        for window in [5, 10, 20]:
            df[f"volume_ma_{window}"] = df["volume"].rolling(window=window).mean()

        # 成交量变化率
        df["volume_change"] = df["volume"].pct_change()
        df["volume_ratio"] = df["volume"] / df["volume_ma_20"]

        # OBV (On-Balance Volume)
        df["obv"] = (np.sign(df["close"].diff()) * df["volume"]).fillna(0).cumsum()
        df["obv_ma"] = df["obv"].rolling(window=20).mean()

        # ===== 价格形态特征 =====
        # 蜡烛图实体大小
        df["body_size"] = np.abs(df["close"] - df["open"]) / df["open"]
        df["upper_shadow"] = (df["high"] - df[["open", "close"]].max(axis=1)) / df["open"]
        df["lower_shadow"] = (df[["open", "close"]].min(axis=1) - df["low"]) / df["open"]

        # 价格缺口
        df["gap"] = (df["open"] - df["close"].shift()) / df["close"].shift()

        # ===== 周期性特征 =====
        if isinstance(df.index, pd.DatetimeIndex):
            df["day_of_week"] = df.index.dayofweek
            df["month"] = df.index.month
            df["quarter"] = df.index.quarter
            df["is_month_start"] = df.index.is_month_start.astype(int)
            df["is_month_end"] = df.index.is_month_end.astype(int)

        # ===== 滞后特征 =====
        for lag in [1, 2, 3, 5]:
            df[f"return_lag_{lag}"] = df["close"].pct_change().shift(lag)

        return df

    def create_target(
        self, df: pd.DataFrame, target_col: str = "close", horizon: int = 5, threshold: float = 0.02
    ) -> pd.Series:
        """
        创建目标变量（多分类）

        Args:
            df: DataFrame
            target_col: 目标列
            horizon: 预测周期
            threshold: 涨跌阈值

        Returns:
            目标变量（0=跌，1=持平，2=涨）
        """
        future_return = df[target_col].shift(-horizon) / df[target_col] - 1

        target = pd.Series(1, index=df.index)  # 默认持平
        target[future_return > threshold] = 2  # 涨
        target[future_return < -threshold] = 0  # 跌

        return target

    def select_features(self, df: pd.DataFrame, target: pd.Series, k: int = 20, method: str = "f_classif") -> list[str]:
        """
        特征选择

        Args:
            df: 特征 DataFrame
            target: 目标变量
            k: 选择的特征数量
            method: 选择方法 ('f_classif' 或 'mutual_info')

        Returns:
            选中的特征名列表
        """
        # 删除常数特征
        constant_cols = df.columns[df.nunique() == 1]
        df = df.drop(columns=constant_cols)

        # 删除高相关特征
        corr_matrix = df.corr().abs()
        upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
        high_corr = [col for col in upper.columns if any(upper[col] > 0.95)]
        df = df.drop(columns=high_corr)

        # 删除缺失值过多的特征
        missing_ratio = df.isnull().sum() / len(df)
        high_missing = missing_ratio[missing_ratio > 0.5].index
        df = df.drop(columns=high_missing)

        # 填充缺失值
        df = df.fillna(method="ffill").fillna(method="bfill").fillna(0)

        # 特征选择
        if method == "f_classif":
            selector = SelectKBest(score_func=f_classif, k=min(k, len(df.columns)))
        else:
            selector = SelectKBest(score_func=mutual_info_classif, k=min(k, len(df.columns)))

        selector.fit(df.values, target.values)

        selected_mask = selector.get_support()
        self.selected_features = df.columns[selected_mask].tolist()

        return self.selected_features

    def fit_scaler(self, df: pd.DataFrame, columns: list[str] | None = None):
        """拟合标准化器"""
        cols = columns if columns else df.columns
        self.scaler.fit(df[cols])
        return self

    def transform(self, df: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
        """转换数据"""
        df = df.copy()
        cols = columns if columns else df.columns
        df[cols] = self.scaler.transform(df[cols])
        return df

    def fit_transform(self, df: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
        """拟合并转换"""
        cols = columns if columns else df.columns
        self.fit_scaler(df, cols)
        return self.transform(df, cols)

    def apply_pca(self, df: pd.DataFrame, n_components: float = 0.95) -> tuple[np.ndarray, PCA]:
        """
        应用 PCA 降维

        Args:
            df: 特征 DataFrame
            n_components: 保留的方差比例或主成分数量

        Returns:
            (降维后的数据，PCA 模型)
        """
        self.pca = PCA(n_components=n_components)
        reduced = self.pca.fit_transform(df)
        return reduced, self.pca

    def get_feature_importance(self, df: pd.DataFrame, target: pd.Series, top_k: int = 20) -> pd.DataFrame:
        """
        使用随机森林计算特征重要性
        """
        from sklearn.ensemble import RandomForestClassifier

        # 填充缺失值
        df_clean = df.fillna(method="ffill").fillna(method="bfill").fillna(0)

        # 训练随机森林
        rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        rf.fit(df_clean.values, target.values)

        # 特征重要性
        importance_df = pd.DataFrame({"feature": df.columns, "importance": rf.feature_importances_}).sort_values(
            "importance", ascending=False
        )

        return importance_df.head(top_k)


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

    # 特征工程
    fe = FeatureEngineer()
    df_features = fe.create_technical_features(df)

    # 创建目标
    target = fe.create_target(df_features, horizon=5, threshold=0.02)

    # 特征选择
    selected = fe.select_features(df_features.dropna(), target.dropna(), k=20)
    print(f"选中的特征数量：{len(selected)}")
    print(f"选中的特征：{selected[:10]}...")

    # 特征重要性
    importance = fe.get_feature_importance(df_features.dropna(), target.dropna())
    print("\nTop 10 重要特征:")
    print(importance)
