"""
市場狀態檢測 (Market Regime Detection) — HMM / 聚類 / 規則引擎

功能：
- 隱馬爾可夫模型 (HMM) 市場狀態識別
- 基於 KMeans 的狀態聚類
- 規則引擎（基於波動率 + 動量組合）
- 狀態轉移概率矩陣
- 狀態持續時間統計

狀態分類：
- Bull Market (牛市): 高動量、低波動
- Bear Market (熊市): 負動量、高波動
- High Volatility (高波動): 任意動量、極高波動
- Low Volatility (低波動/震盪): 低動量、低波動

用法：
    from src.utils.regime_detection import RegimeDetector

    detector = RegimeDetector(returns)
    regimes = detector.detect()
    current = detector.current_regime()
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import IntEnum
from typing import Any

import numpy as np


class Regime(IntEnum):
    """市場狀態."""

    BULL = 0  # 牛市
    BEAR = 1  # 熊市
    HIGH_VOL = 2  # 高波動
    LOW_VOL = 3  # 低波動/震盪


REGIME_NAMES = {
    Regime.BULL: "牛市 (Bull)",
    Regime.BEAR: "熊市 (Bear)",
    Regime.HIGH_VOL: "高波動 (High Vol)",
    Regime.LOW_VOL: "震盪 (Sideways)",
}

REGIME_EMOJIS = {
    Regime.BULL: "🐂",
    Regime.BEAR: "🐻",
    Regime.HIGH_VOL: "⚡",
    Regime.LOW_VOL: "😴",
}


@dataclass(slots=True)
class RegimeStats:
    """狀態統計."""

    regime: Regime
    name: str
    count: int
    pct: float
    avg_duration: float  # 平均持續天數
    avg_return: float
    avg_volatility: float


@dataclass(slots=True)
class RegimeResult:
    """檢測結果."""

    regimes: list[Regime]  # 每日狀態
    transition_matrix: dict[str, dict[str, float]]  # 狀態轉移概率
    stats: list[RegimeStats]
    current_regime: Regime
    confidence: float  # 當前狀態信心度

    def to_dict(self) -> dict[str, Any]:
        return {
            "current_regime": REGIME_NAMES[self.current_regime],
            "current_regime_id": int(self.current_regime),
            "confidence": round(self.confidence, 3),
            "regime_distribution": {
                REGIME_NAMES[s.regime]: {
                    "pct": round(s.pct * 100, 1),
                    "avg_duration_days": round(s.avg_duration, 1),
                    "avg_return_pct": round(s.avg_return * 100, 4),
                    "avg_volatility_pct": round(s.avg_volatility * 100, 4),
                }
                for s in self.stats
            },
            "transition_matrix": self.transition_matrix,
        }


class RegimeDetector:
    """
    市場狀態檢測器.

    Args:
        returns: 日報酬率 (n_days,)
        lookback: 波動率計算窗口
        ann_factor: 年化因子
    """

    def __init__(
        self,
        returns: np.ndarray,
        lookback: int = 20,
        ann_factor: int = 252,
    ) -> None:
        self._returns = np.asarray(returns, dtype=np.float64).flatten()
        self._lookback = lookback
        self._ann = ann_factor

    def detect(self, method: str = "rule") -> RegimeResult:
        """
        檢測市場狀態.

        Args:
            method: "rule" (規則引擎) | "kmeans" (KMeans 聚類) | "hmm" (HMM)
        """
        if method == "kmeans":
            return self._detect_kmeans()
        elif method == "hmm":
            return self._detect_hmm()
        else:
            return self._detect_rule()

    def _compute_features(self) -> tuple[np.ndarray, np.ndarray]:
        """計算動量和波動率特徵."""
        n = len(self._returns)
        momentum = np.full(n, np.nan)
        volatility = np.full(n, np.nan)

        for i in range(self._lookback, n):
            window = self._returns[i - self._lookback : i]
            momentum[i] = np.prod(1 + window) - 1
            volatility[i] = np.std(window, ddof=1) * math.sqrt(self._ann)

        return momentum, volatility

    def _detect_rule(self) -> RegimeResult:
        """規則引擎檢測."""
        momentum, volatility = self._compute_features()
        n = len(self._returns)

        # 計算中位數閾值
        valid_mom = momentum[~np.isnan(momentum)]
        valid_vol = volatility[~np.isnan(volatility)]

        if len(valid_mom) < self._lookback * 2:
            # 數據不足，返回默認
            return RegimeResult(
                regimes=[Regime.LOW_VOL] * n,
                transition_matrix={},
                stats=[],
                current_regime=Regime.LOW_VOL,
                confidence=0.0,
            )

        med_mom = np.median(valid_mom)
        med_vol = np.median(valid_vol)
        p75_vol = np.percentile(valid_vol, 75)

        regimes = np.full(n, Regime.LOW_VOL.value, dtype=int)

        for i in range(n):
            if np.isnan(momentum[i]) or np.isnan(volatility[i]):
                regimes[i] = Regime.LOW_VOL.value
                continue

            mom = momentum[i]
            vol = volatility[i]

            if vol > p75_vol:
                regimes[i] = Regime.HIGH_VOL.value
            elif mom > med_mom:
                regimes[i] = Regime.BULL.value
            elif mom < -med_mom:
                regimes[i] = Regime.BEAR.value
            else:
                regimes[i] = Regime.LOW_VOL.value

        return self._build_result(regimes)

    def _detect_kmeans(self) -> RegimeResult:
        """KMeans 聚類檢測."""
        momentum, volatility = self._compute_features()
        n = len(self._returns)

        # 準備特徵
        valid_mask = ~np.isnan(momentum) & ~np.isnan(volatility)
        if np.sum(valid_mask) < 10:
            return self._detect_rule()

        features = np.column_stack(
            [
                momentum[valid_mask],
                volatility[valid_mask],
            ]
        )

        # 標準化
        mean_f = np.mean(features, axis=0)
        std_f = np.std(features, axis=0)
        std_f[std_f == 0] = 1
        features_norm = (features - mean_f) / std_f

        # 簡易 KMeans (k=4)
        k = 4
        rng = np.random.default_rng(42)
        centroids = features_norm[rng.choice(len(features_norm), k, replace=False)]

        for _ in range(50):
            distances = np.array([np.linalg.norm(features_norm - c, axis=1) for c in centroids])
            labels = np.argmin(distances, axis=0)
            new_centroids = np.array(
                [features_norm[labels == i].mean(axis=0) if np.any(labels == i) else centroids[i] for i in range(k)]
            )
            if np.allclose(centroids, new_centroids, atol=1e-6):
                break
            centroids = new_centroids

        # 映射聚類到狀態（基於質心特徵）
        centroids_original = centroids * std_f + mean_f
        centroid_momentum = centroids_original[:, 0]
        centroid_vol = centroids_original[:, 1]

        # 排序：按動量和波動率映射到 BULL/BEAR/HIGH_VOL/LOW_VOL
        sorted_by_vol = np.argsort(centroid_vol)
        low_vol_cluster = sorted_by_vol[0]
        high_vol_cluster = sorted_by_vol[-1]

        remaining = [c for c in range(k) if c not in [low_vol_cluster, high_vol_cluster]]
        if len(remaining) >= 2:
            bull_cluster = (
                remaining[0] if centroid_momentum[remaining[0]] > centroid_momentum[remaining[1]] else remaining[1]
            )
            bear_cluster = remaining[1] if bull_cluster == remaining[0] else remaining[0]
        elif len(remaining) == 1:
            bull_cluster = remaining[0]
            bear_cluster = remaining[0]
        else:
            bull_cluster = 0
            bear_cluster = 1

        cluster_to_regime = {
            bull_cluster: Regime.BULL.value,
            bear_cluster: Regime.BEAR.value,
            high_vol_cluster: Regime.HIGH_VOL.value,
            low_vol_cluster: Regime.LOW_VOL.value,
        }

        # 預測所有點
        all_distances = np.array(
            [
                np.linalg.norm(((np.column_stack([momentum, volatility]) - mean_f) / std_f) - c, axis=1)
                for c in centroids
            ]
        )
        all_labels = np.argmin(all_distances, axis=0)

        regimes = np.array([cluster_to_regime.get(l, Regime.LOW_VOL.value) for l in all_labels])

        # NaN 區域填 LOW_VOL
        regimes[~valid_mask] = Regime.LOW_VOL.value

        return self._build_result(regimes)

    def _detect_hmm(self) -> RegimeResult:
        """
        HMM 檢測（簡化版 Baum-Welch）.
        如果沒有 hmmlearn，回退到規則引擎.
        """
        try:
            from hmmlearn.hmm import GaussianHMM

            returns = self._returns.reshape(-1, 1)
            model = GaussianHMM(n_components=4, covariance_type="full", n_iter=100, random_state=42)
            model.fit(returns)
            regimes = model.predict(returns)

            # 映射隱狀態到 Regime
            state_means = model.means_.flatten()
            state_vars = model.covars_.flatten()

            # 簡單映射：按均值和方差
            sorted_by_var = np.argsort(state_vars)
            cluster_map = {
                sorted_by_var[0]: Regime.LOW_VOL.value,
                sorted_by_var[-1]: Regime.HIGH_VOL.value,
            }
            remaining = [i for i in range(4) if i not in cluster_map]
            if len(remaining) >= 2:
                if state_means[remaining[0]] > state_means[remaining[1]]:
                    cluster_map[remaining[0]] = Regime.BULL.value
                    cluster_map[remaining[1]] = Regime.BEAR.value
                else:
                    cluster_map[remaining[0]] = Regime.BEAR.value
                    cluster_map[remaining[1]] = Regime.BULL.value

            regimes = np.array([cluster_map.get(r, Regime.LOW_VOL.value) for r in regimes])
            return self._build_result(regimes)

        except ImportError:
            return self._detect_rule()

    def _build_result(self, regimes: np.ndarray) -> RegimeResult:
        """構建 RegimeResult."""
        n = len(regimes)

        # 狀態統計
        stats: list[RegimeStats] = []
        for regime_val in [r.value for r in Regime]:
            mask = regimes == regime_val
            count = int(np.sum(mask))
            if count == 0:
                stats.append(
                    RegimeStats(
                        regime=Regime(regime_val),
                        name=REGIME_NAMES[Regime(regime_val)],
                        count=0,
                        pct=0.0,
                        avg_duration=0.0,
                        avg_return=0.0,
                        avg_volatility=0.0,
                    )
                )
                continue

            pct = count / n
            returns_in = self._returns[mask]
            avg_ret = float(np.mean(returns_in)) if len(returns_in) > 0 else 0
            avg_vol = float(np.std(returns_in, ddof=1)) if len(returns_in) > 1 else 0

            # 平均持續時間
            durations = []
            cur_dur = 1
            for i in range(1, n):
                if regimes[i] == regimes[i - 1]:
                    cur_dur += 1
                else:
                    if regimes[i - 1] == regime_val:
                        durations.append(cur_dur)
                    cur_dur = 1
            if regimes[-1] == regime_val:
                durations.append(cur_dur)
            avg_dur = float(np.mean(durations)) if durations else 0

            stats.append(
                RegimeStats(
                    regime=Regime(regime_val),
                    name=REGIME_NAMES[Regime(regime_val)],
                    count=count,
                    pct=pct,
                    avg_duration=avg_dur,
                    avg_return=avg_ret,
                    avg_volatility=avg_vol,
                )
            )

        # 轉移概率矩陣
        transition_counts: dict[int, dict[int, int]] = {r.value: {} for r in Regime}
        for i in range(1, n):
            from_r = int(regimes[i - 1])
            to_r = int(regimes[i])
            transition_counts[from_r][to_r] = transition_counts[from_r].get(to_r, 0) + 1

        transition_matrix: dict[str, dict[str, float]] = {}
        for from_r, tos in transition_counts.items():
            total = sum(tos.values())
            from_name = REGIME_NAMES[Regime(from_r)]
            transition_matrix[from_name] = {}
            for to_r, count in tos.items():
                to_name = REGIME_NAMES[Regime(to_r)]
                transition_matrix[from_name][to_name] = round(count / total, 3) if total > 0 else 0

        # 當前狀態
        current = Regime(int(regimes[-1])) if n > 0 else Regime.LOW_VOL

        # 信心度：最近 window 中當前狀態的佔比
        recent = regimes[-self._lookback :]
        confidence = float(np.mean(recent == current.value)) if len(recent) > 0 else 0

        return RegimeResult(
            regimes=[Regime(int(r)) for r in regimes],
            transition_matrix=transition_matrix,
            stats=stats,
            current_regime=current,
            confidence=confidence,
        )

    def current_regime(self, method: str = "rule") -> Regime:
        """取得當前市場狀態."""
        result = self.detect(method)
        return result.current_regime
