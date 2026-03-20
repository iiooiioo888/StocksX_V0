"""
组合风险监控模块

功能：
- VaR（Value at Risk）计算
- CVaR（Conditional VaR）计算
- 最大回撤监控
- 波动率监控
- 相关性风险
- 压力测试
- 黑天鹅检测

使用场景：
- 实时监控组合风险
- 风险限额管理
- 压力测试场景分析
- 黑天鹅事件预警
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class RiskMetrics:
    """风险指标"""
    var_95: float  # 95% VaR
    var_99: float  # 99% VaR
    cvar_95: float  # 95% CVaR
    cvar_99: float  # 99% CVaR
    max_drawdown: float  # 最大回撤
    current_drawdown: float  # 当前回撤
    volatility: float  # 波动率
    sharpe_ratio: float  # 夏普比率
    timestamp: datetime


class RiskMonitor:
    """
    组合风险监控器
    
    实时监控组合的各项风险指标
    """
    
    def __init__(
        self,
        portfolio_value: float,
        confidence_levels: List[float] = [0.95, 0.99]
    ):
        """
        初始化
        
        Args:
            portfolio_value: 组合价值
            confidence_levels: 置信水平列表
        """
        self.portfolio_value = portfolio_value
        self.confidence_levels = confidence_levels
        
        # 历史数据
        self.returns_history: List[float] = []
        self.value_history: List[float] = [portfolio_value]
        self.peak_value = portfolio_value
        
        # 风险限额
        self.var_limit: Optional[float] = None
        self.drawdown_limit: Optional[float] = None
        self.volatility_limit: Optional[float] = None
    
    def add_return(self, return_pct: float):
        """
        添加收益率数据
        
        Args:
            return_pct: 收益率（小数）
        """
        self.returns_history.append(return_pct)
        
        # 更新组合价值
        if len(self.value_history) > 0:
            new_value = self.value_history[-1] * (1 + return_pct)
            self.value_history.append(new_value)
            
            # 更新峰值
            if new_value > self.peak_value:
                self.peak_value = new_value
    
    def calculate_var(
        self,
        confidence: float = 0.95,
        method: str = "historical"
    ) -> float:
        """
        计算 VaR（Value at Risk）
        
        Args:
            confidence: 置信水平
            method: 计算方法
                - historical: 历史模拟法
                - parametric: 参数法（正态分布）
                - monte_carlo: 蒙特卡洛模拟
        
        Returns:
            VaR 值（百分比）
        """
        if len(self.returns_history) < 10:
            logger.warning("数据不足，无法计算 VaR")
            return 0.0
        
        returns = np.array(self.returns_history)
        
        if method == "historical":
            # 历史模拟法
            var = np.percentile(returns, (1 - confidence) * 100)
        
        elif method == "parametric":
            # 参数法（假设正态分布）
            mu = np.mean(returns)
            sigma = np.std(returns)
            var = mu - sigma * stats.norm.ppf(confidence)
        
        elif method == "monte_carlo":
            # 蒙特卡洛模拟
            mu = np.mean(returns)
            sigma = np.std(returns)
            simulated = np.random.normal(mu, sigma, 10000)
            var = np.percentile(simulated, (1 - confidence) * 100)
        
        else:
            raise ValueError(f"未知的 VaR 计算方法：{method}")
        
        return var
    
    def calculate_cvar(self, confidence: float = 0.95) -> float:
        """
        计算 CVaR（Conditional VaR）/ Expected Shortfall
        
        Args:
            confidence: 置信水平
        
        Returns:
            CVaR 值（百分比）
        """
        if len(self.returns_history) < 10:
            logger.warning("数据不足，无法计算 CVaR")
            return 0.0
        
        returns = np.array(self.returns_history)
        var = self.calculate_var(confidence)
        
        # CVaR 是超过 VaR 的损失的期望值
        cvar = np.mean(returns[returns <= var])
        
        return cvar
    
    def calculate_max_drawdown(self) -> float:
        """
        计算最大回撤
        
        Returns:
            最大回撤（百分比）
        """
        if len(self.value_history) < 2:
            return 0.0
        
        values = np.array(self.value_history)
        peak = np.maximum.accumulate(values)
        drawdown = (values - peak) / peak
        
        return np.min(drawdown)
    
    def calculate_current_drawdown(self) -> float:
        """
        计算当前回撤
        
        Returns:
            当前回撤（百分比）
        """
        if len(self.value_history) < 2:
            return 0.0
        
        current_value = self.value_history[-1]
        drawdown = (current_value - self.peak_value) / self.peak_value
        
        return drawdown
    
    def calculate_volatility(self, annualize: bool = True) -> float:
        """
        计算波动率
        
        Args:
            annualize: 是否年化
        
        Returns:
            波动率
        """
        if len(self.returns_history) < 2:
            return 0.0
        
        volatility = np.std(self.returns_history)
        
        if annualize:
            # 年化（假设日收益率）
            volatility *= np.sqrt(252)
        
        return volatility
    
    def calculate_sharpe_ratio(self, risk_free_rate: float = 0.02) -> float:
        """
        计算夏普比率
        
        Args:
            risk_free_rate: 无风险利率
        
        Returns:
            夏普比率
        """
        if len(self.returns_history) < 2:
            return 0.0
        
        returns = np.array(self.returns_history)
        excess_returns = returns - risk_free_rate / 252  # 日化
        
        if np.std(excess_returns) == 0:
            return 0.0
        
        # 年化夏普比率
        sharpe = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
        
        return sharpe
    
    def check_risk_limits(self) -> Dict[str, bool]:
        """
        检查风险限额
        
        Returns:
            检查结果
        """
        current_var = self.calculate_var(0.95)
        current_drawdown = self.calculate_current_drawdown()
        current_volatility = self.calculate_volatility()
        
        return {
            'var_ok': self.var_limit is None or abs(current_var) <= self.var_limit,
            'drawdown_ok': self.drawdown_limit is None or abs(current_drawdown) <= self.drawdown_limit,
            'volatility_ok': self.volatility_limit is None or current_volatility <= self.volatility_limit,
        }
    
    def get_risk_metrics(self) -> RiskMetrics:
        """
        获取所有风险指标
        
        Returns:
            风险指标
        """
        return RiskMetrics(
            var_95=self.calculate_var(0.95),
            var_99=self.calculate_var(0.99),
            cvar_95=self.calculate_cvar(0.95),
            cvar_99=self.calculate_cvar(0.99),
            max_drawdown=self.calculate_max_drawdown(),
            current_drawdown=self.calculate_current_drawdown(),
            volatility=self.calculate_volatility(),
            sharpe_ratio=self.calculate_sharpe_ratio(),
            timestamp=datetime.now()
        )


class StressTester:
    """
    压力测试
    
    测试组合在极端市场情况下的表现
    """
    
    # 预定义压力场景
    SCENARIOS = {
        '2008_financial_crisis': {
            'name': '2008 金融危机',
            'shock': -0.50,
            'description': '全球金融危机，市场下跌 50%'
        },
        '2020_covid_crash': {
            'name': '2020 新冠崩盘',
            'shock': -0.30,
            'description': '新冠疫情爆发，市场快速下跌 30%'
        },
        'flash_crash': {
            'name': '闪崩',
            'shock': -0.10,
            'description': '瞬间下跌 10%'
        },
        'crypto_winter': {
            'name': '加密寒冬',
            'shock': -0.70,
            'description': '加密市场长期下跌 70%'
        },
        'interest_rate_shock': {
            'name': '利率冲击',
            'shock': -0.20,
            'description': '美联储大幅加息，市场下跌 20%'
        },
    }
    
    def __init__(self, portfolio_value: float):
        """
        初始化
        
        Args:
            portfolio_value: 组合价值
        """
        self.portfolio_value = portfolio_value
    
    def run_scenario(
        self,
        scenario_name: str,
        custom_shock: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        运行压力测试场景
        
        Args:
            scenario_name: 场景名称
            custom_shock: 自定义冲击（覆盖预定义）
        
        Returns:
            压力测试结果
        """
        if scenario_name not in self.SCENARIOS and custom_shock is None:
            raise ValueError(f"未知场景：{scenario_name}")
        
        # 获取冲击值
        if custom_shock is not None:
            shock = custom_shock
            scenario_info = {'name': '自定义场景', 'description': f'自定义冲击 {shock:.0%}'}
        else:
            scenario = self.SCENARIOS[scenario_name]
            shock = scenario['shock']
            scenario_info = scenario
        
        # 计算损失
        loss = self.portfolio_value * abs(shock)
        remaining_value = self.portfolio_value * (1 + shock)
        
        return {
            'scenario': scenario_info['name'],
            'description': scenario_info['description'],
            'shock': shock,
            'initial_value': self.portfolio_value,
            'loss': loss,
            'loss_pct': abs(shock),
            'remaining_value': remaining_value,
            'recovery_needed': -shock / (1 + shock) if shock < 0 else 0,  # 恢复所需涨幅
        }
    
    def run_all_scenarios(self) -> List[Dict[str, Any]]:
        """
        运行所有预定义场景
        
        Returns:
            所有场景的测试结果
        """
        results = []
        for name in self.SCENARIOS.keys():
            result = self.run_scenario(name)
            results.append(result)
        
        # 按损失排序
        results.sort(key=lambda x: x['loss'], reverse=True)
        
        return results
    
    def sensitivity_analysis(
        self,
        shock_range: Tuple[float, float] = (-0.5, 0.5),
        steps: int = 11
    ) -> pd.DataFrame:
        """
        敏感性分析
        
        Args:
            shock_range: 冲击范围（最小，最大）
            steps: 步数
        
        Returns:
            敏感性分析表
        """
        shocks = np.linspace(shock_range[0], shock_range[1], steps)
        
        results = []
        for shock in shocks:
            loss = self.portfolio_value * abs(shock) if shock < 0 else 0
            remaining = self.portfolio_value * (1 + shock)
            
            results.append({
                '冲击': f'{shock:.0%}',
                '损失': loss,
                '剩余价值': remaining,
                '恢复所需': -shock / (1 + shock) if shock < 0 else 0
            })
        
        return pd.DataFrame(results)


class BlackSwanDetector:
    """
    黑天鹅事件检测器
    
    检测市场异常波动和极端事件
    """
    
    def __init__(self, lookback_days: int = 30):
        """
        初始化
        
        Args:
            lookback_days: 回溯天数
        """
        self.lookback_days = lookback_days
        self.price_history: List[float] = []
        self.volatility_history: List[float] = []
    
    def add_price(self, price: float):
        """
        添加价格数据
        
        Args:
            price: 当前价格
        """
        self.price_history.append(price)
        
        # 计算波动率
        if len(self.price_history) >= self.lookback_days:
            returns = np.diff(np.log(self.price_history[-self.lookback_days:]))
            volatility = np.std(returns) * np.sqrt(252)
            self.volatility_history.append(volatility)
    
    def detect_volatility_spike(
        self,
        threshold: float = 3.0
    ) -> bool:
        """
        检测波动率突增
        
        Args:
            threshold: 阈值（标准差倍数）
        
        Returns:
            是否检测到突增
        """
        if len(self.volatility_history) < self.lookback_days:
            return False
        
        recent_vol = self.volatility_history[-1]
        historical_mean = np.mean(self.volatility_history[:-1])
        historical_std = np.std(self.volatility_history[:-1])
        
        if historical_std == 0:
            return False
        
        z_score = (recent_vol - historical_mean) / historical_std
        
        return z_score > threshold
    
    def detect_correlation_breakdown(
        self,
        asset_returns: Dict[str, List[float]],
        threshold: float = 0.5
    ) -> bool:
        """
        检测相关性崩溃
        
        在危机期间，资产间的相关性会突然上升
        
        Args:
            asset_returns: 各资产收益率字典
            threshold: 相关性变化阈值
        
        Returns:
            是否检测到相关性崩溃
        """
        if len(asset_returns) < 2:
            return False
        
        # 计算当前相关性
        assets = list(asset_returns.keys())
        returns_data = np.array([asset_returns[asset] for asset in assets])
        
        if returns_data.shape[1] < 10:
            return False
        
        corr_matrix = np.corrcoef(returns_data)
        
        # 计算平均相关性（去掉对角线）
        n = len(assets)
        avg_corr = (np.sum(corr_matrix) - n) / (n * (n - 1))
        
        # 如果平均相关性突然上升到很高水平
        return avg_corr > threshold
    
    def detect_liquidity_crisis(
        self,
        volume_history: List[float],
        threshold: float = 0.5
    ) -> bool:
        """
        检测流动性危机
        
        Args:
            volume_history: 成交量历史
            threshold: 成交量下降阈值
        
        Returns:
            是否检测到流动性危机
        """
        if len(volume_history) < self.lookback_days:
            return False
        
        recent_avg = np.mean(volume_history[-7:])  # 最近 7 天平均
        historical_avg = np.mean(volume_history[:-7])
        
        if historical_avg == 0:
            return False
        
        volume_decline = (historical_avg - recent_avg) / historical_avg
        
        return volume_decline > threshold
    
    def get_risk_level(self) -> str:
        """
        获取当前风险等级
        
        Returns:
            风险等级（low/medium/high/critical）
        """
        if len(self.volatility_history) < self.lookback_days:
            return "unknown"
        
        # 检查波动率突增
        vol_spike = self.detect_volatility_spike(threshold=2.0)
        vol_spike_severe = self.detect_volatility_spike(threshold=3.0)
        
        if vol_spike_severe:
            return "critical"
        elif vol_spike:
            return "high"
        else:
            return "low"


# 测试
if __name__ == "__main__":
    print("测试组合风险监控...\n")
    
    # 1. 风险指标计算
    print("1. 风险指标计算")
    monitor = RiskMonitor(portfolio_value=100000)
    
    # 模拟收益率数据
    np.random.seed(42)
    for _ in range(100):
        ret = np.random.normal(0.0005, 0.02)  # 日均收益 0.05%，波动 2%
        monitor.add_return(ret)
    
    metrics = monitor.get_risk_metrics()
    print(f"   VaR(95%): {metrics.var_95:.2%}")
    print(f"   VaR(99%): {metrics.var_99:.2%}")
    print(f"   CVaR(95%): {metrics.cvar_95:.2%}")
    print(f"   最大回撤：{metrics.max_drawdown:.2%}")
    print(f"   波动率：{metrics.volatility:.2%}")
    print(f"   夏普比率：{metrics.sharpe_ratio:.2f}")
    
    # 2. 压力测试
    print("\n2. 压力测试")
    tester = StressTester(portfolio_value=100000)
    
    # 运行所有场景
    results = tester.run_all_scenarios()
    for result in results[:3]:  # 显示前 3 个最严重场景
        print(f"   {result['scenario']}: 损失 ${result['loss']:,.0f} ({result['loss_pct']:.0%})")
        print(f"      剩余价值：${result['remaining_value']:,.0f}")
        print(f"      恢复所需：{result['recovery_needed']:.1%}")
    
    # 3. 黑天鹅检测
    print("\n3. 黑天鹅检测")
    detector = BlackSwanDetector(lookback_days=30)
    
    # 模拟价格数据
    price = 100
    for i in range(100):
        # 正常波动
        price *= (1 + np.random.normal(0, 0.02))
        detector.add_price(price)
    
    # 突然波动率上升
    for i in range(10):
        price *= (1 + np.random.normal(0, 0.1))  # 波动率增加到 10%
        detector.add_price(price)
    
    risk_level = detector.get_risk_level()
    print(f"   当前风险等级：{risk_level}")
    
    vol_spike = detector.detect_volatility_spike()
    print(f"   波动率突增：{'是' if vol_spike else '否'}")
