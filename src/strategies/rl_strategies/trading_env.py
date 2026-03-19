"""
强化学习环境 - 股票/加密货币交易环境

基于 Gymnasium 框架，支持 DQN、PPO 等强化学习算法
- State: 市场状态 + 持仓状态 + 技术指标
- Action: 买入/卖出/持有 + 仓位大小
- Reward: PnL + Sharpe ratio + 风险调整收益
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import gymnasium as gym
from gymnasium import spaces
import warnings
warnings.filterwarnings('ignore')


class TradingEnv(gym.Env):
    """
    股票/加密货币交易环境
    
    支持离散动作空间（DQN）和连续动作空间（PPO）
    """
    
    metadata = {'render_modes': ['human', 'rgb_array']}
    
    def __init__(
        self,
        df: pd.DataFrame,
        initial_balance: float = 100000,
        commission: float = 0.001,
        slippage: float = 0.0005,
        lookback_window: int = 20,
        max_steps: Optional[int] = None,
        discrete_actions: bool = True,
        reward_type: str = 'pnl'  # 'pnl', 'sharpe', 'sortino'
    ):
        """
        初始化交易环境
        
        Args:
            df: 包含 OHLCV 和技术指标的 DataFrame
            initial_balance: 初始资金
            commission: 交易手续费
            slippage: 滑点
            lookback_window: 观察窗口大小
            max_steps: 最大步数（None 表示到数据末尾）
            discrete_actions: 是否使用离散动作空间
            reward_type: 奖励类型
        """
        super().__init__()
        
        self.df = df.reset_index(drop=True)
        self.initial_balance = initial_balance
        self.commission = commission
        self.slippage = slippage
        self.lookback_window = lookback_window
        self.max_steps = max_steps or len(self.df) - lookback_window
        self.discrete_actions = discrete_actions
        self.reward_type = reward_type
        
        # 特征列
        self.feature_cols = [c for c in df.columns if c not in ['open', 'high', 'low', 'close', 'volume']]
        if not self.feature_cols:
            # 如果没有技术指标，使用价格衍生特征
            self.feature_cols = ['open', 'high', 'low', 'close', 'volume']
        
        self.n_features = len(self.feature_cols)
        
        # 动作空间
        if discrete_actions:
            # 离散动作：0=持有，1=买入 10%, 2=买入 25%, 3=买入 50%, 4=买入 100%
            #           5=卖出 10%, 6=卖出 25%, 7=卖出 50%, 8=卖出 100%
            self.action_space = spaces.Discrete(9)
        else:
            # 连续动作：[-1, 1]，-1=全卖，1=全买，0=持有
            self.action_space = spaces.Box(low=-1, high=1, shape=(1,), dtype=np.float32)
        
        # 观察空间
        # State 包括：lookback 窗口的价格 + 技术指标 + 持仓信息
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(lookback_window * (len(self.feature_cols) + 3),),  # +3 for position info
            dtype=np.float32
        )
        
        # 状态变量
        self.current_step = 0
        self.balance = 0
        self.shares = 0
        self.position_value = 0
        self.total_value = 0
        self.trades = []
        self.portfolio_values = []
        self.returns = []
        
        # 归一化器
        self.price_scaler = None
        self._init_normalizer()
    
    def _init_normalizer(self):
        """初始化价格归一化器"""
        close_prices = self.df['close'].values
        self.price_mean = np.mean(close_prices)
        self.price_std = np.std(close_prices) + 1e-10
    
    def _normalize_price(self, price: float) -> float:
        """归一化价格"""
        return (price - self.price_mean) / self.price_std
    
    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[Dict] = None
    ) -> Tuple[np.ndarray, Dict]:
        """重置环境"""
        super().reset(seed=seed)
        
        self.current_step = self.lookback_window
        self.balance = self.initial_balance
        self.shares = 0
        self.position_value = 0
        self.total_value = self.initial_balance
        self.trades = []
        self.portfolio_values = [self.initial_balance]
        self.returns = []
        
        obs = self._get_observation()
        info = self._get_info()
        
        return obs, info
    
    def _get_observation(self) -> np.ndarray:
        """获取当前观察"""
        # 获取 lookback 窗口的数据
        start_idx = self.current_step - self.lookback_window
        end_idx = self.current_step
        
        window_data = self.df.iloc[start_idx:end_idx].copy()
        
        # 归一化特征
        obs_features = []
        for col in self.feature_cols:
            if col in ['open', 'high', 'low', 'close']:
                obs_features.append(self._normalize_price(window_data[col].values))
            elif col == 'volume':
                obs_features.append(np.log1p(window_data[col].values) / 10)
            else:
                # 技术指标，直接归一化
                vals = window_data[col].values
                obs_features.append((vals - np.mean(vals)) / (np.std(vals) + 1e-10))
        
        obs_array = np.stack(obs_features, axis=1).flatten()
        
        # 添加持仓信息
        position_info = np.array([
            self.shares / (self.initial_balance / self.price_mean),  # 相对持仓
            self.balance / self.initial_balance,  # 现金比例
            self.current_step / len(self.df)  # 时间进度
        ])
        
        obs = np.concatenate([obs_array, position_info]).astype(np.float32)
        
        return obs
    
    def _get_info(self) -> Dict:
        """获取环境信息"""
        return {
            'step': self.current_step,
            'balance': self.balance,
            'shares': self.shares,
            'total_value': self.total_value,
            'current_price': self.df['close'].iloc[self.current_step],
            'pnl': self.total_value - self.initial_balance,
            'pnl_pct': (self.total_value - self.initial_balance) / self.initial_balance,
            'num_trades': len(self.trades)
        }
    
    def step(self, action: int | float) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        """
        执行一步动作
        
        Args:
            action: 动作（离散或连续）
        
        Returns:
            (observation, reward, terminated, truncated, info)
        """
        # 获取当前价格
        current_price = self.df['close'].iloc[self.current_step]
        
        # 解析动作
        if self.discrete_actions:
            action_type, action_size = self._decode_discrete_action(action)
        else:
            action_type, action_size = self._decode_continuous_action(action[0])
        
        # 执行交易
        self._execute_trade(action_type, action_size, current_price)
        
        # 更新组合价值
        self.position_value = self.shares * current_price
        self.total_value = self.balance + self.position_value
        self.portfolio_values.append(self.total_value)
        
        # 计算收益
        if len(self.portfolio_values) > 1:
            ret = (self.portfolio_values[-1] - self.portfolio_values[-2]) / self.portfolio_values[-2]
            self.returns.append(ret)
        
        # 计算奖励
        reward = self._calculate_reward()
        
        # 检查是否结束
        terminated = self.balance <= 0 or self.total_value <= self.initial_balance * 0.5
        truncated = self.current_step >= len(self.df) - 1
        
        # 前进一步
        self.current_step += 1
        
        obs = self._get_observation()
        info = self._get_info()
        
        return obs, reward, terminated, truncated, info
    
    def _decode_discrete_action(self, action: int) -> Tuple[str, float]:
        """解码离散动作"""
        action_map = {
            0: ('hold', 0),
            1: ('buy', 0.1),
            2: ('buy', 0.25),
            3: ('buy', 0.5),
            4: ('buy', 1.0),
            5: ('sell', 0.1),
            6: ('sell', 0.25),
            7: ('sell', 0.5),
            8: ('sell', 1.0)
        }
        return action_map.get(action, ('hold', 0))
    
    def _decode_continuous_action(self, action: float) -> Tuple[str, float]:
        """解码连续动作"""
        if action > 0.1:
            return ('buy', min(action, 1.0))
        elif action < -0.1:
            return ('sell', min(abs(action), 1.0))
        else:
            return ('hold', 0)
    
    def _execute_trade(self, action_type: str, action_size: float, price: float):
        """执行交易"""
        if action_type == 'hold' or action_size == 0:
            return
        
        # 考虑滑点的价格
        if action_type == 'buy':
            exec_price = price * (1 + self.slippage)
            max_shares = int(self.balance / (exec_price * (1 + self.commission)))
            target_shares = int((self.initial_balance * action_size) / exec_price)
            actual_shares = min(target_shares, max_shares)
            
            if actual_shares > 0:
                cost = actual_shares * exec_price * (1 + self.commission)
                self.balance -= cost
                self.shares += actual_shares
                self.trades.append({
                    'step': self.current_step,
                    'type': 'BUY',
                    'shares': actual_shares,
                    'price': exec_price,
                    'cost': cost
                })
        
        elif action_type == 'sell':
            exec_price = price * (1 - self.slippage)
            max_shares = self.shares
            target_shares = int(self.shares * action_size)
            actual_shares = min(target_shares, max_shares)
            
            if actual_shares > 0:
                revenue = actual_shares * exec_price * (1 - self.commission)
                self.balance += revenue
                self.shares -= actual_shares
                self.trades.append({
                    'step': self.current_step,
                    'type': 'SELL',
                    'shares': actual_shares,
                    'price': exec_price,
                    'revenue': revenue
                })
    
    def _calculate_reward(self) -> float:
        """计算奖励"""
        if len(self.returns) < 2:
            return 0.0
        
        if self.reward_type == 'pnl':
            # 简单 PnL 奖励
            reward = self.returns[-1]
        
        elif self.reward_type == 'sharpe':
            # Sharpe 比率奖励
            mean_ret = np.mean(self.returns[-20:])
            std_ret = np.std(self.returns[-20:]) + 1e-10
            reward = mean_ret / std_ret * np.sqrt(252)  # 年化 Sharpe
        
        elif self.reward_type == 'sortino':
            # Sortino 比率奖励（只惩罚下行波动）
            mean_ret = np.mean(self.returns[-20:])
            downside_returns = [r for r in self.returns[-20:] if r < 0]
            downside_std = np.std(downside_returns) + 1e-10 if downside_returns else 1e-10
            reward = mean_ret / downside_std * np.sqrt(252)
        
        else:
            reward = self.returns[-1]
        
        # 惩罚过度交易
        if len(self.trades) > 0:
            recent_trades = sum(1 for t in self.trades if t['step'] > self.current_step - 50)
            if recent_trades > 10:
                reward -= 0.01 * (recent_trades - 10)
        
        # 破产惩罚
        if self.total_value < self.initial_balance * 0.5:
            reward -= 1.0
        
        return float(reward)
    
    def render(self, mode: str = 'human'):
        """渲染环境"""
        if mode == 'human':
            print(f"Step: {self.current_step}, "
                  f"Total: ${self.total_value:.2f}, "
                  f"PnL: {self._get_info()['pnl_pct']:.2%}, "
                  f"Trades: {len(self.trades)}")
    
    def get_results(self) -> Dict:
        """获取回测结果"""
        if len(self.portfolio_values) < 2:
            return {'error': 'No data'}
        
        portfolio_values = np.array(self.portfolio_values)
        returns = np.diff(portfolio_values) / portfolio_values[:-1]
        
        total_return = (portfolio_values[-1] - self.initial_balance) / self.initial_balance
        
        # 年化 Sharpe
        if len(returns) > 1:
            sharpe = np.mean(returns) / (np.std(returns) + 1e-10) * np.sqrt(252)
        else:
            sharpe = 0
        
        # 最大回撤
        cummax = np.maximum.accumulate(portfolio_values)
        drawdowns = (cummax - portfolio_values) / cummax
        max_drawdown = np.max(drawdowns)
        
        # 胜率
        winning_trades = sum(1 for t in self.trades if t['type'] == 'SELL' and t.get('revenue', 0) > t.get('cost', 0))
        total_sell_trades = sum(1 for t in self.trades if t['type'] == 'SELL')
        win_rate = winning_trades / total_sell_trades if total_sell_trades > 0 else 0
        
        return {
            'total_return': total_return,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'final_value': portfolio_values[-1],
            'num_trades': len(self.trades),
            'win_rate': win_rate,
            'trades': self.trades,
            'portfolio_values': portfolio_values.tolist()
        }


# ════════════════════════════════════════════════════════════
# 使用示例
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # 创建示例数据
    np.random.seed(42)
    n = 500
    dates = pd.date_range('2023-01-01', periods=n, freq='D')
    
    df = pd.DataFrame({
        'open': np.random.randn(n).cumsum() + 100,
        'high': np.random.randn(n).cumsum() + 101,
        'low': np.random.randn(n).cumsum() + 99,
        'close': np.random.randn(n).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, n)
    }, index=dates)
    
    # 添加技术指标
    df['rsi'] = 50 + np.random.randn(n) * 10
    df['macd'] = np.random.randn(n)
    df['bb_width'] = 0.1 + np.random.randn(n) * 0.02
    
    # 创建环境
    env = TradingEnv(df, initial_balance=100000, discrete_actions=True)
    
    # 测试随机动作
    obs, info = env.reset()
    print(f"初始观察形状：{obs.shape}")
    print(f"初始状态：{info}")
    
    done = False
    while not done:
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        done = terminated or truncated
        
        if env.current_step % 100 == 0:
            env.render()
    
    # 获取结果
    results = env.get_results()
    print(f"\n回测结果:")
    print(f"  总收益：{results['total_return']:.2%}")
    print(f"  Sharpe: {results['sharpe_ratio']:.2f}")
    print(f"  最大回撤：{results['max_drawdown']:.2%}")
    print(f"  交易次数：{results['num_trades']}")
