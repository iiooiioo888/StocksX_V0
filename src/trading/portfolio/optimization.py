"""
马科维茨投资组合优化

功能：
- 均值 - 方差优化
- 有效前沿计算
- 最优权重计算
- 夏普比率最大化
- 最小波动率组合

理论：
现代投资组合理论（Modern Portfolio Theory, MPT）
由 Harry Markowitz 于 1952 年提出，获 1990 年诺贝尔经济学奖

核心思想：
- 不要把所有鸡蛋放在一个篮子里
- 通过分散投资降低风险
- 在给定风险水平下最大化收益
- 在给定收益水平下最小化风险
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)


class MarkowitzOptimizer:
    """
    马科维茨投资组合优化器

    优化目标：
    1. 最大化夏普比率
    2. 最小化波动率
    3. 最大化收益（给定风险）
    4. 最小化风险（给定收益）
    """

    def __init__(self, returns: pd.DataFrame, risk_free_rate: float = 0.02):
        """
        初始化

        Args:
            returns: 收益率 DataFrame（每列一个资产）
            risk_free_rate: 无风险利率（年化）
        """
        self.returns = returns
        self.risk_free_rate = risk_free_rate

        # 计算统计量
        self.mean_returns = returns.mean() * 252  # 年化收益
        self.cov_matrix = returns.cov() * 252  # 年化协方差

        # 资产数量
        self.n_assets = len(returns.columns)
        self.assets = returns.columns.tolist()

    def portfolio_return(self, weights: np.ndarray) -> float:
        """
        计算组合收益率

        Args:
            weights: 权重数组

        Returns:
            年化收益率
        """
        return np.sum(self.mean_returns * weights)

    def portfolio_volatility(self, weights: np.ndarray) -> float:
        """
        计算组合波动率

        Args:
            weights: 权重数组

        Returns:
            年化波动率
        """
        return np.sqrt(np.dot(weights.T, np.dot(self.cov_matrix, weights)))

    def portfolio_sharpe_ratio(self, weights: np.ndarray) -> float:
        """
        计算夏普比率

        Args:
            weights: 权重数组

        Returns:
            夏普比率
        """
        p_return = self.portfolio_return(weights)
        p_volatility = self.portfolio_volatility(weights)

        if p_volatility == 0:
            return 0.0

        return (p_return - self.risk_free_rate) / p_volatility

    def negative_sharpe_ratio(self, weights: np.ndarray) -> float:
        """
        负夏普比率（用于最小化）

        Args:
            weights: 权重数组

        Returns:
            负夏普比率
        """
        return -self.portfolio_sharpe_ratio(weights)

    def optimize_max_sharpe(self, constraints: Optional[list[dict]] = None) -> dict[str, Any]:
        """
        优化最大夏普比率

        Args:
            constraints: 额外约束条件

        Returns:
            最优权重和绩效指标
        """
        # 初始猜测（等权重）
        init_guess = self.n_assets * [1.0 / self.n_assets]

        # 约束条件
        bounds = tuple((0.0, 1.0) for _ in range(self.n_assets))
        constraints = constraints or [
            {"type": "eq", "fun": lambda x: np.sum(x) - 1}  # 权重和为 1
        ]

        # 优化
        result = minimize(
            self.negative_sharpe_ratio, init_guess, method="SLSQP", bounds=bounds, constraints=constraints
        )

        if not result.success:
            logger.warning(f"优化失败：{result.message}")

        # 计算最优组合的指标
        optimal_weights = result.x
        optimal_return = self.portfolio_return(optimal_weights)
        optimal_volatility = self.portfolio_volatility(optimal_weights)
        optimal_sharpe = self.portfolio_sharpe_ratio(optimal_weights)

        return {
            "weights": dict(zip(self.assets, optimal_weights)),
            "annual_return": optimal_return,
            "annual_volatility": optimal_volatility,
            "sharpe_ratio": optimal_sharpe,
            "success": result.success,
            "message": result.message,
        }

    def optimize_min_volatility(self, constraints: Optional[list[dict]] = None) -> dict[str, Any]:
        """
        优化最小波动率

        Args:
            constraints: 额外约束条件

        Returns:
            最优权重和绩效指标
        """
        # 初始猜测
        init_guess = self.n_assets * [1.0 / self.n_assets]

        # 约束条件
        bounds = tuple((0.0, 1.0) for _ in range(self.n_assets))
        constraints = constraints or [{"type": "eq", "fun": lambda x: np.sum(x) - 1}]

        # 优化
        result = minimize(self.portfolio_volatility, init_guess, method="SLSQP", bounds=bounds, constraints=constraints)

        if not result.success:
            logger.warning(f"优化失败：{result.message}")

        # 计算最优组合的指标
        optimal_weights = result.x
        optimal_return = self.portfolio_return(optimal_weights)
        optimal_volatility = self.portfolio_volatility(optimal_weights)
        optimal_sharpe = self.portfolio_sharpe_ratio(optimal_weights)

        return {
            "weights": dict(zip(self.assets, optimal_weights)),
            "annual_return": optimal_return,
            "annual_volatility": optimal_volatility,
            "sharpe_ratio": optimal_sharpe,
            "success": result.success,
            "message": result.message,
        }

    def optimize_target_return(self, target_return: float, constraints: Optional[list[dict]] = None) -> dict[str, Any]:
        """
        优化给定目标收益下的最小风险

        Args:
            target_return: 目标年化收益率
            constraints: 额外约束条件

        Returns:
            最优权重和绩效指标
        """
        # 初始猜测
        init_guess = self.n_assets * [1.0 / self.n_assets]

        # 约束条件
        bounds = tuple((0.0, 1.0) for _ in range(self.n_assets))
        base_constraints = [
            {"type": "eq", "fun": lambda x: np.sum(x) - 1},
            {"type": "eq", "fun": lambda x: self.portfolio_return(x) - target_return},
        ]

        if constraints:
            base_constraints.extend(constraints)

        # 优化
        result = minimize(
            self.portfolio_volatility, init_guess, method="SLSQP", bounds=bounds, constraints=base_constraints
        )

        if not result.success:
            logger.warning(f"优化失败：{result.message}")

        # 计算最优组合的指标
        optimal_weights = result.x
        optimal_return = self.portfolio_return(optimal_weights)
        optimal_volatility = self.portfolio_volatility(optimal_weights)
        optimal_sharpe = self.portfolio_sharpe_ratio(optimal_weights)

        return {
            "weights": dict(zip(self.assets, optimal_weights)),
            "annual_return": optimal_return,
            "annual_volatility": optimal_volatility,
            "sharpe_ratio": optimal_sharpe,
            "target_return": target_return,
            "success": result.success,
            "message": result.message,
        }

    def efficient_frontier(self, n_points: int = 50) -> pd.DataFrame:
        """
        计算有效前沿

        Args:
            n_points: 前沿上的点数

        Returns:
            有效前沿数据
        """
        # 获取最小和最大可能收益
        min_vol_result = self.optimize_min_volatility()
        max_sharpe_result = self.optimize_max_sharpe()

        min_return = min_vol_result["annual_return"]
        max_return = max_sharpe_result["annual_return"]

        # 生成一系列目标收益
        target_returns = np.linspace(min_return, max_return, n_points)

        frontier_data = []

        for target in target_returns:
            try:
                result = self.optimize_target_return(target)
                if result["success"]:
                    frontier_data.append(
                        {
                            "return": result["annual_return"],
                            "volatility": result["annual_volatility"],
                            "sharpe": result["sharpe_ratio"],
                            "weights": result["weights"],
                        }
                    )
            except (ValueError, KeyError):
                continue

        return pd.DataFrame(frontier_data)

    def plot_efficient_frontier(self):
        """
        绘制有效前沿图

        需要 matplotlib 和 seaborn

        Returns:
            matplotlib figure
        """
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns

            # 计算有效前沿
            frontier = self.efficient_frontier()

            # 创建图表
            fig, ax = plt.subplots(figsize=(10, 6))

            # 绘制有效前沿
            ax.plot(frontier["volatility"], frontier["return"], "b-", label="有效前沿", linewidth=2)

            # 标记最小方差组合
            min_vol = self.optimize_min_volatility()
            ax.plot(min_vol["annual_volatility"], min_vol["annual_return"], "go", markersize=10, label="最小方差组合")

            # 标记最大夏普组合
            max_sharpe = self.optimize_max_sharpe()
            ax.plot(
                max_sharpe["annual_volatility"], max_sharpe["annual_return"], "r*", markersize=15, label="最大夏普组合"
            )

            # 设置标签和标题
            ax.set_xlabel("年化波动率", fontsize=12)
            ax.set_ylabel("年化收益率", fontsize=12)
            ax.set_title("马科维茨有效前沿", fontsize=14)
            ax.legend()
            ax.grid(True, alpha=0.3)

            return fig

        except ImportError:
            logger.error("需要安装 matplotlib 和 seaborn")
            return None


class RiskParityOptimizer:
    """
    风险平价优化器

    理念：
    - 每个资产贡献相同的风险
    - 而不是相同的资金

    优势：
    - 真正的风险分散
    - 避免单一资产主导风险
    - 在危机期间表现更好
    """

    def __init__(self, returns: pd.DataFrame):
        """
        初始化

        Args:
            returns: 收益率 DataFrame
        """
        self.returns = returns
        self.cov_matrix = returns.cov() * 252
        self.n_assets = len(returns.columns)
        self.assets = returns.columns.tolist()

    def risk_contribution(self, weights: np.ndarray) -> np.ndarray:
        """
        计算每个资产的风险贡献

        Args:
            weights: 权重数组

        Returns:
            风险贡献数组
        """
        # 组合波动率
        portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(self.cov_matrix, weights)))

        # 边际风险贡献
        marginal_contrib = np.dot(self.cov_matrix, weights)

        # 风险贡献
        risk_contrib = weights * marginal_contrib / portfolio_vol

        return risk_contrib

    def optimize_risk_parity(self, target_risk: Optional[float] = None) -> dict[str, Any]:
        """
        优化风险平价组合

        Args:
            target_risk: 目标组合风险（可选）

        Returns:
            最优权重和指标
        """
        # 初始猜测
        init_guess = self.n_assets * [1.0 / self.n_assets]

        # 约束条件
        bounds = tuple((0.0, 1.0) for _ in range(self.n_assets))
        constraints = [{"type": "eq", "fun": lambda x: np.sum(x) - 1}]

        # 目标函数：最小化风险贡献的差异
        def objective(weights):
            risk_contrib = self.risk_contribution(weights)
            target_contrib = np.mean(risk_contrib)
            return np.sum((risk_contrib - target_contrib) ** 2)

        # 优化
        result = minimize(objective, init_guess, method="SLSQP", bounds=bounds, constraints=constraints)

        if not result.success:
            logger.warning(f"优化失败：{result.message}")

        # 计算最优组合的指标
        optimal_weights = result.x
        portfolio_vol = np.sqrt(np.dot(optimal_weights.T, np.dot(self.cov_matrix, optimal_weights)))
        risk_contrib = self.risk_contribution(optimal_weights)

        return {
            "weights": dict(zip(self.assets, optimal_weights)),
            "annual_volatility": portfolio_vol,
            "risk_contributions": dict(zip(self.assets, risk_contrib)),
            "success": result.success,
            "message": result.message,
        }


class BlackLittermanOptimizer:
    """
    Black-Litterman 模型优化器

    核心思想：
    - 将市场均衡收益（先验）与投资者观点（后验）结合
    - 解决 Markowitz 模型对输入参数过度敏感的问题
    - 产生更稳定、更直观的资产配置

    理论：
    Fischer Black & Robert Litterman (1992) 在 Goldman Sachs 提出

    输入：
    - 市值权重（隐含均衡收益）
    - 协方差矩阵
    - 投资者观点 + 置信度

    输出：
    - 调整后的预期收益
    - 最优组合权重
    """

    def __init__(
        self,
        returns: pd.DataFrame,
        market_cap_weights: Optional[dict[str, float]] = None,
        risk_free_rate: float = 0.02,
        tau: float = 0.05,
    ):
        """
        初始化

        Args:
            returns: 收益率 DataFrame（每列一个资产）
            market_cap_weights: 市值权重字典（None = 等权重近似）
            risk_free_rate: 无风险利率（年化）
            tau: 不确定性缩放因子（通常 0.025 ~ 0.1）
        """
        self.returns = returns
        self.risk_free_rate = risk_free_rate
        self.tau = tau

        self.assets = returns.columns.tolist()
        self.n_assets = len(self.assets)

        # 协方差矩阵（年化）
        self.cov_matrix = returns.cov().values * 252

        # 市场权重（默认等权重）
        if market_cap_weights:
            self.market_weights = np.array([market_cap_weights.get(a, 1.0 / self.n_assets) for a in self.assets])
        else:
            self.market_weights = np.ones(self.n_assets) / self.n_assets

        # 归一化
        self.market_weights = self.market_weights / self.market_weights.sum()

        # 风险厌恶系数
        self.delta = self._estimate_risk_aversion()

        # 隐含均衡收益 (Π)
        self.pi = self._implied_equilibrium_returns()

    def _estimate_risk_aversion(self) -> float:
        """估计市场风险厌恶系数"""
        # δ = (E[R_m] - R_f) / σ²_m
        market_return = np.dot(self.market_weights, self.returns.mean() * 252)
        market_var = np.dot(self.market_weights.T, np.dot(self.cov_matrix, self.market_weights))

        if market_var <= 0:
            return 2.5  # 默认值

        return (market_return - self.risk_free_rate) / market_var

    def _implied_equilibrium_returns(self) -> np.ndarray:
        """
        计算隐含均衡收益
        Π = δ * Σ * w_mkt
        """
        return self.delta * np.dot(self.cov_matrix, self.market_weights)

    def add_views(self, views: list[dict[str, Any]]) -> tuple:
        """
        构建观点矩阵

        Args:
            views: 观点列表，每个观点包含：
                - assets: 资产列表
                - weights: 权重列表（相对观点）或单个资产（绝对观点）
                - expected_return: 预期超额收益
                - confidence: 置信度（0~1，越高 Ω 越小）

        Returns:
            (P, Q, Ω) — 观点矩阵、观点收益、观点不确定性

        示例：
        ```python
        views = [
            {
                'assets': ['BTC', 'ETH'],
                'weights': [0.6, -0.4],  # BTC 比 ETH 多赚 3%
                'expected_return': 0.03,
                'confidence': 0.7
            },
            {
                'assets': ['SOL'],
                'weights': [1.0],  # SOL 绝对收益 5%
                'expected_return': 0.05,
                'confidence': 0.5
            }
        ]
        ```
        """
        n_views = len(views)

        # P 矩阵（n_views × n_assets）
        P = np.zeros((n_views, self.n_assets))
        # Q 向量（n_views）
        Q = np.zeros(n_views)
        # Ω 对角矩阵（观点不确定性）
        omega_diag = np.zeros(n_views)

        for i, view in enumerate(views):
            view_assets = view["assets"]
            view_weights = view["weights"]
            expected_return = view["expected_return"]
            confidence = view.get("confidence", 0.5)

            for j, asset in enumerate(view_assets):
                if asset in self.assets:
                    idx = self.assets.index(asset)
                    P[i, idx] = view_weights[j]

            Q[i] = expected_return

            # Ω = (1 - confidence) * P * τΣ * P'
            # 置信度越高，Ω 越小（观点越确定）
            p_row = P[i, :]
            omega_diag[i] = (1 - confidence) * np.dot(p_row, np.dot(self.tau * self.cov_matrix, p_row))

        # 确保 Ω 非零
        omega_diag = np.maximum(omega_diag, 1e-10)
        Omega = np.diag(omega_diag)

        return P, Q, Omega

    def optimize_with_views(self, views: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Black-Litterman 优化

        Args:
            views: 观点列表

        Returns:
            最优权重和调整后的预期收益
        """
        P, Q, Omega = self.add_views(views)

        # 新的协方差矩阵
        tau_sigma = self.tau * self.cov_matrix

        # Black-Litterman 公式
        # μ_BL = [(τΣ)⁻¹ + P'Ω⁻¹P]⁻¹ × [(τΣ)⁻¹Π + P'Ω⁻¹Q]

        tau_sigma_inv = np.linalg.inv(tau_sigma)
        omega_inv = np.linalg.inv(Omega)

        # 后验协方差
        M_inv = np.linalg.inv(tau_sigma_inv + P.T @ omega_inv @ P)

        # 后验收益
        mu_bl = M_inv @ (tau_sigma_inv @ self.pi + P.T @ omega_inv @ Q)

        # 后验协方差矩阵
        cov_bl = M_inv + self.cov_matrix

        # 使用调整后的收益做 Markowitz 优化
        # 最大夏普比率权重：w = Σ⁻¹μ / 1'Σ⁻¹μ
        cov_bl_inv = np.linalg.inv(cov_bl)
        ones = np.ones(self.n_assets)

        raw_weights = np.dot(cov_bl_inv, mu_bl)
        optimal_weights = raw_weights / raw_weights.sum()

        # 计算组合指标
        port_return = np.dot(optimal_weights, mu_bl)
        port_vol = np.sqrt(np.dot(optimal_weights.T, np.dot(cov_bl, optimal_weights)))
        sharpe = (port_return - self.risk_free_rate) / port_vol if port_vol > 0 else 0

        # 对比均衡收益 vs 调整后收益
        return {
            "weights": dict(zip(self.assets, optimal_weights)),
            "expected_return": port_return,
            "expected_volatility": port_vol,
            "sharpe_ratio": sharpe,
            "implied_returns": dict(zip(self.assets, self.pi)),
            "adjusted_returns": dict(zip(self.assets, mu_bl)),
            "market_weights": dict(zip(self.assets, self.market_weights)),
        }

    def optimize_no_views(self) -> dict[str, Any]:
        """无观点时，返回市场均衡权重"""
        port_return = np.dot(self.market_weights, self.pi)
        port_vol = np.sqrt(np.dot(self.market_weights.T, np.dot(self.cov_matrix, self.market_weights)))
        sharpe = (port_return - self.risk_free_rate) / port_vol if port_vol > 0 else 0

        return {
            "weights": dict(zip(self.assets, self.market_weights)),
            "expected_return": port_return,
            "expected_volatility": port_vol,
            "sharpe_ratio": sharpe,
            "implied_returns": dict(zip(self.assets, self.pi)),
        }


class HRPOptimizer:
    """
     层级风险平价（Hierarchical Risk Parity, HRP）

     核心思想：
     - 使用机器学习（层次聚类）对资产分组
     - 在聚类树上自顶向下分配权重
     - 不需要协方差矩阵求逆 → 更稳定

     优势：
     - 对估计误差不敏感
     - 不需要二次规划求解器
     - 权重更分散、更稳健

     理论：
     Marcos López de Prado (2016)

     算法步骤：
     1. 计算距离矩阵（相关性 → 距离）
     2. 层次聚类（Ward linkage）
     3. 准对角化（Quasi-Diagonalization）
    4. 递归二分风险平价
    """

    def __init__(self, returns: pd.DataFrame):
        """
        初始化

        Args:
            returns: 收益率 DataFrame
        """
        self.returns = returns
        self.assets = returns.columns.tolist()
        self.n_assets = len(self.assets)
        self.cov_matrix = returns.cov().values * 252
        self.corr_matrix = returns.corr().values

    def _correlation_to_distance(self) -> np.ndarray:
        """相关性矩阵 → 距离矩阵"""
        # d = sqrt(0.5 * (1 - ρ))
        dist = np.sqrt(0.5 * (1 - self.corr_matrix))
        np.fill_diagonal(dist, 0)
        return dist

    def _quasi_diagonalization(self, linkage_matrix: np.ndarray) -> list[int]:
        """
        准对角化：重排资产使相关的资产相邻

        Args:
            linkage_matrix: 层次聚类连接矩阵

        Returns:
            重排后的资产索引
        """
        from scipy.cluster.hierarchy import leaves_list

        # 获取叶子节点顺序
        return leaves_list(linkage_matrix).tolist()

    def _get_cluster_variance(self, cov: np.ndarray, weights: np.ndarray) -> float:
        """计算聚类方差"""
        return np.dot(weights.T, np.dot(cov, weights))

    def _recursive_bisection(self, sorted_indices: list[int]) -> np.ndarray:
        """
        递归二分风险平价

        Args:
            sorted_indices: 准对角化后的资产索引

        Returns:
            最优权重
        """
        weights = np.ones(self.n_assets)
        clusters = [sorted_indices]

        while clusters:
            new_clusters = []
            for cluster in clusters:
                if len(cluster) <= 1:
                    continue

                # 二分
                mid = len(cluster) // 2
                left = cluster[:mid]
                right = cluster[mid:]

                # 计算左/右的协方差子矩阵
                left_cov = self.cov_matrix[np.ix_(left, left)]
                right_cov = self.cov_matrix[np.ix_(right, right)]

                left_w = weights[left]
                right_w = weights[right]

                # 计算方差
                left_var = np.dot(left_w.T, np.dot(left_cov, left_w))
                right_var = np.dot(right_w.T, np.dot(right_cov, right_w))

                # 按方差的反比分配权重
                total_var = left_var + right_var
                if total_var > 0:
                    alpha = 1 - left_var / total_var
                    weights[left] *= alpha
                    weights[right] *= 1 - alpha

                new_clusters.extend([left, right])

            clusters = new_clusters

        # 归一化
        weights = weights / weights.sum()
        return weights

    def optimize(self) -> dict[str, Any]:
        """
        HRP 优化

        Returns:
            最优权重和指标
        """
        from scipy.cluster.hierarchy import linkage

        # 1. 距离矩阵
        dist = self._correlation_to_distance()

        # 2. 层次聚类（Ward linkage）
        # condensed distance matrix
        from scipy.spatial.distance import squareform

        dist_condensed = squareform(dist, checks=False)
        link = linkage(dist_condensed, method="ward")

        # 3. 准对角化
        sorted_idx = self._quasi_diagonalization(link)

        # 4. 递归二分
        weights = self._recursive_bisection(sorted_idx)

        # 按原始资产顺序返回
        full_weights = np.zeros(self.n_assets)
        for i, idx in enumerate(sorted_idx):
            full_weights[idx] = weights[i]

        # 归一化（数值误差修正）
        full_weights = np.maximum(full_weights, 0)
        full_weights = full_weights / full_weights.sum()

        # 计算指标
        port_vol = np.sqrt(np.dot(full_weights.T, np.dot(self.cov_matrix, full_weights)))

        return {
            "weights": dict(zip(self.assets, full_weights)),
            "annual_volatility": port_vol,
            "sorted_assets": [self.assets[i] for i in sorted_idx],
            "linkage_matrix": link,
        }


# 测试
if __name__ == "__main__":
    print("测试马科维茨组合优化...\n")

    # 创建模拟数据
    np.random.seed(42)
    n_days = 252 * 3  # 3 年数据
    n_assets = 5

    # 生成随机收益率
    returns_data = np.random.normal(0.0005, 0.02, (n_days, n_assets))

    # 创建 DataFrame
    columns = ["BTC", "ETH", "SOL", "BNB", "USDT"]
    returns = pd.DataFrame(returns_data, columns=columns)

    print("1. 最大夏普比率组合")
    optimizer = MarkowitzOptimizer(returns)
    max_sharpe = optimizer.optimize_max_sharpe()

    print("   权重：")
    for asset, weight in max_sharpe["weights"].items():
        print(f"      {asset}: {weight:.1%}")
    print(f"   年化收益：{max_sharpe['annual_return']:.1%}")
    print(f"   年化波动：{max_sharpe['annual_volatility']:.1%}")
    print(f"   夏普比率：{max_sharpe['sharpe_ratio']:.2f}")

    print("\n2. 最小波动率组合")
    min_vol = optimizer.optimize_min_volatility()
    print("   权重：")
    for asset, weight in min_vol["weights"].items():
        print(f"      {asset}: {weight:.1%}")
    print(f"   年化波动：{min_vol['annual_volatility']:.1%}")

    print("\n3. 风险平价组合")
    rp_optimizer = RiskParityOptimizer(returns)
    risk_parity = rp_optimizer.optimize_risk_parity()
    print("   权重：")
    for asset, weight in risk_parity["weights"].items():
        print(f"      {asset}: {weight:.1%}")
    print("   风险贡献：")
    for asset, contrib in risk_parity["risk_contributions"].items():
        print(f"      {asset}: {contrib:.1%}")

    print("\n4. Black-Litterman 优化")
    bl_optimizer = BlackLittermanOptimizer(returns, risk_free_rate=0.02)

    # 无观点
    no_views = bl_optimizer.optimize_no_views()
    print("   均衡权重（无观点）：")
    for asset, weight in no_views["weights"].items():
        print(f"      {asset}: {weight:.1%}")

    # 添加观点
    views = [
        {
            "assets": ["BTC"],
            "weights": [1.0],
            "expected_return": 0.15,  # BTC 年化 15%
            "confidence": 0.8,
        },
        {
            "assets": ["ETH", "SOL"],
            "weights": [0.6, -0.4],  # ETH 比 SOL 多赚 5%
            "expected_return": 0.05,
            "confidence": 0.6,
        },
    ]

    bl_result = bl_optimizer.optimize_with_views(views)
    print("\n   调整后权重（有观点）：")
    for asset, weight in bl_result["weights"].items():
        adj_ret = bl_result["adjusted_returns"][asset]
        print(f"      {asset}: {weight:.1%} (预期收益: {adj_ret:.1%})")
    print(f"   组合预期收益: {bl_result['expected_return']:.1%}")
    print(f"   组合波动率: {bl_result['expected_volatility']:.1%}")
    print(f"   夏普比率: {bl_result['sharpe_ratio']:.2f}")

    print("\n5. 层级风险平价 (HRP)")
    hrp_optimizer = HRPOptimizer(returns)
    hrp_result = hrp_optimizer.optimize()
    print("   权重：")
    for asset, weight in hrp_result["weights"].items():
        print(f"      {asset}: {weight:.1%}")
    print(f"   年化波动: {hrp_result['annual_volatility']:.1%}")
    print(f"   聚类顺序: {hrp_result['sorted_assets']}")
