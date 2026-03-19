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
from typing import Dict, List, Optional, Any, Tuple
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
    
    def __init__(
        self,
        returns: pd.DataFrame,
        risk_free_rate: float = 0.02
    ):
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
    
    def portfolio_return(
        self,
        weights: np.ndarray
    ) -> float:
        """
        计算组合收益率
        
        Args:
            weights: 权重数组
        
        Returns:
            年化收益率
        """
        return np.sum(self.mean_returns * weights)
    
    def portfolio_volatility(
        self,
        weights: np.ndarray
    ) -> float:
        """
        计算组合波动率
        
        Args:
            weights: 权重数组
        
        Returns:
            年化波动率
        """
        return np.sqrt(np.dot(weights.T, np.dot(self.cov_matrix, weights)))
    
    def portfolio_sharpe_ratio(
        self,
        weights: np.ndarray
    ) -> float:
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
    
    def negative_sharpe_ratio(
        self,
        weights: np.ndarray
    ) -> float:
        """
        负夏普比率（用于最小化）
        
        Args:
            weights: 权重数组
        
        Returns:
            负夏普比率
        """
        return -self.portfolio_sharpe_ratio(weights)
    
    def optimize_max_sharpe(
        self,
        constraints: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        优化最大夏普比率
        
        Args:
            constraints: 额外约束条件
        
        Returns:
            最优权重和绩效指标
        """
        # 初始猜测（等权重）
        init_guess = self.n_assets * [1. / self.n_assets]
        
        # 约束条件
        bounds = tuple((0., 1.) for _ in range(self.n_assets))
        constraints = constraints or [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}  # 权重和为 1
        ]
        
        # 优化
        result = minimize(
            self.negative_sharpe_ratio,
            init_guess,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        
        if not result.success:
            logger.warning(f"优化失败：{result.message}")
        
        # 计算最优组合的指标
        optimal_weights = result.x
        optimal_return = self.portfolio_return(optimal_weights)
        optimal_volatility = self.portfolio_volatility(optimal_weights)
        optimal_sharpe = self.portfolio_sharpe_ratio(optimal_weights)
        
        return {
            'weights': dict(zip(self.assets, optimal_weights)),
            'annual_return': optimal_return,
            'annual_volatility': optimal_volatility,
            'sharpe_ratio': optimal_sharpe,
            'success': result.success,
            'message': result.message
        }
    
    def optimize_min_volatility(
        self,
        constraints: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        优化最小波动率
        
        Args:
            constraints: 额外约束条件
        
        Returns:
            最优权重和绩效指标
        """
        # 初始猜测
        init_guess = self.n_assets * [1. / self.n_assets]
        
        # 约束条件
        bounds = tuple((0., 1.) for _ in range(self.n_assets))
        constraints = constraints or [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
        ]
        
        # 优化
        result = minimize(
            self.portfolio_volatility,
            init_guess,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        
        if not result.success:
            logger.warning(f"优化失败：{result.message}")
        
        # 计算最优组合的指标
        optimal_weights = result.x
        optimal_return = self.portfolio_return(optimal_weights)
        optimal_volatility = self.portfolio_volatility(optimal_weights)
        optimal_sharpe = self.portfolio_sharpe_ratio(optimal_weights)
        
        return {
            'weights': dict(zip(self.assets, optimal_weights)),
            'annual_return': optimal_return,
            'annual_volatility': optimal_volatility,
            'sharpe_ratio': optimal_sharpe,
            'success': result.success,
            'message': result.message
        }
    
    def optimize_target_return(
        self,
        target_return: float,
        constraints: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        优化给定目标收益下的最小风险
        
        Args:
            target_return: 目标年化收益率
            constraints: 额外约束条件
        
        Returns:
            最优权重和绩效指标
        """
        # 初始猜测
        init_guess = self.n_assets * [1. / self.n_assets]
        
        # 约束条件
        bounds = tuple((0., 1.) for _ in range(self.n_assets))
        base_constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
            {'type': 'eq', 'fun': lambda x: self.portfolio_return(x) - target_return}
        ]
        
        if constraints:
            base_constraints.extend(constraints)
        
        # 优化
        result = minimize(
            self.portfolio_volatility,
            init_guess,
            method='SLSQP',
            bounds=bounds,
            constraints=base_constraints
        )
        
        if not result.success:
            logger.warning(f"优化失败：{result.message}")
        
        # 计算最优组合的指标
        optimal_weights = result.x
        optimal_return = self.portfolio_return(optimal_weights)
        optimal_volatility = self.portfolio_volatility(optimal_weights)
        optimal_sharpe = self.portfolio_sharpe_ratio(optimal_weights)
        
        return {
            'weights': dict(zip(self.assets, optimal_weights)),
            'annual_return': optimal_return,
            'annual_volatility': optimal_volatility,
            'sharpe_ratio': optimal_sharpe,
            'target_return': target_return,
            'success': result.success,
            'message': result.message
        }
    
    def efficient_frontier(
        self,
        n_points: int = 50
    ) -> pd.DataFrame:
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
        
        min_return = min_vol_result['annual_return']
        max_return = max_sharpe_result['annual_return']
        
        # 生成一系列目标收益
        target_returns = np.linspace(min_return, max_return, n_points)
        
        frontier_data = []
        
        for target in target_returns:
            try:
                result = self.optimize_target_return(target)
                if result['success']:
                    frontier_data.append({
                        'return': result['annual_return'],
                        'volatility': result['annual_volatility'],
                        'sharpe': result['sharpe_ratio'],
                        'weights': result['weights']
                    })
            except:
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
            ax.plot(
                frontier['volatility'],
                frontier['return'],
                'b-',
                label='有效前沿',
                linewidth=2
            )
            
            # 标记最小方差组合
            min_vol = self.optimize_min_volatility()
            ax.plot(
                min_vol['annual_volatility'],
                min_vol['annual_return'],
                'go',
                markersize=10,
                label='最小方差组合'
            )
            
            # 标记最大夏普组合
            max_sharpe = self.optimize_max_sharpe()
            ax.plot(
                max_sharpe['annual_volatility'],
                max_sharpe['annual_return'],
                'r*',
                markersize=15,
                label='最大夏普组合'
            )
            
            # 设置标签和标题
            ax.set_xlabel('年化波动率', fontsize=12)
            ax.set_ylabel('年化收益率', fontsize=12)
            ax.set_title('马科维茨有效前沿', fontsize=14)
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
    
    def risk_contribution(
        self,
        weights: np.ndarray
    ) -> np.ndarray:
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
    
    def optimize_risk_parity(
        self,
        target_risk: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        优化风险平价组合
        
        Args:
            target_risk: 目标组合风险（可选）
        
        Returns:
            最优权重和指标
        """
        # 初始猜测
        init_guess = self.n_assets * [1. / self.n_assets]
        
        # 约束条件
        bounds = tuple((0., 1.) for _ in range(self.n_assets))
        constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
        ]
        
        # 目标函数：最小化风险贡献的差异
        def objective(weights):
            risk_contrib = self.risk_contribution(weights)
            target_contrib = np.mean(risk_contrib)
            return np.sum((risk_contrib - target_contrib) ** 2)
        
        # 优化
        result = minimize(
            objective,
            init_guess,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        
        if not result.success:
            logger.warning(f"优化失败：{result.message}")
        
        # 计算最优组合的指标
        optimal_weights = result.x
        portfolio_vol = np.sqrt(np.dot(optimal_weights.T, np.dot(self.cov_matrix, optimal_weights)))
        risk_contrib = self.risk_contribution(optimal_weights)
        
        return {
            'weights': dict(zip(self.assets, optimal_weights)),
            'annual_volatility': portfolio_vol,
            'risk_contributions': dict(zip(self.assets, risk_contrib)),
            'success': result.success,
            'message': result.message
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
    columns = ['BTC', 'ETH', 'SOL', 'BNB', 'USDT']
    returns = pd.DataFrame(returns_data, columns=columns)
    
    print("1. 最大夏普比率组合")
    optimizer = MarkowitzOptimizer(returns)
    max_sharpe = optimizer.optimize_max_sharpe()
    
    print(f"   权重：")
    for asset, weight in max_sharpe['weights'].items():
        print(f"      {asset}: {weight:.1%}")
    print(f"   年化收益：{max_sharpe['annual_return']:.1%}")
    print(f"   年化波动：{max_sharpe['annual_volatility']:.1%}")
    print(f"   夏普比率：{max_sharpe['sharpe_ratio']:.2f}")
    
    print("\n2. 最小波动率组合")
    min_vol = optimizer.optimize_min_volatility()
    print(f"   权重：")
    for asset, weight in min_vol['weights'].items():
        print(f"      {asset}: {weight:.1%}")
    print(f"   年化波动：{min_vol['annual_volatility']:.1%}")
    
    print("\n3. 风险平价组合")
    rp_optimizer = RiskParityOptimizer(returns)
    risk_parity = rp_optimizer.optimize_risk_parity()
    print(f"   权重：")
    for asset, weight in risk_parity['weights'].items():
        print(f"      {asset}: {weight:.1%}")
    print(f"   风险贡献：")
    for asset, contrib in risk_parity['risk_contributions'].items():
        print(f"      {asset}: {contrib:.1%}")
