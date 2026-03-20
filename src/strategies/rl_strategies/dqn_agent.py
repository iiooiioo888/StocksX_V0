"""
DQN 交易 Agent

使用深度 Q 网络学习最优交易策略
- 输入：市场状态（技术指标 + 持仓信息）
- 输出：交易动作（买入/卖出/持有 + 仓位大小）
- 算法：DQN + Experience Replay + Target Network
"""

from __future__ import annotations

import random
from collections import deque

import numpy as np
import pandas as pd

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    import torch.optim as optim

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from .trading_env import TradingEnv


class DQNNetwork(nn.Module):
    """DQN 神经网络"""

    def __init__(self, input_dim: int, output_dim: int, hidden_dims: list[int] = [128, 64, 32], dropout: float = 0.1):
        """
        初始化 DQN 网络

        Args:
            input_dim: 输入维度
            output_dim: 输出维度（动作数量）
            hidden_dims: 隐藏层维度列表
            dropout: Dropout 比例
        """
        super().__init__()

        layers = []
        prev_dim = input_dim

        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.ReLU())
            layers.append(nn.BatchNorm1d(hidden_dim))
            layers.append(nn.Dropout(dropout))
            prev_dim = hidden_dim

        layers.append(nn.Linear(prev_dim, output_dim))

        self.network = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x)


class ReplayBuffer:
    """经验回放缓冲区"""

    def __init__(self, capacity: int = 100000):
        self.buffer = deque(maxlen=capacity)

    def push(self, state: np.ndarray, action: int, reward: float, next_state: np.ndarray, done: bool):
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size: int) -> tuple:
        batch = random.sample(self.buffer, batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        return (np.array(states), np.array(actions), np.array(rewards), np.array(next_states), np.array(dones))

    def __len__(self) -> int:
        return len(self.buffer)


class DQNAgent:
    """DQN 交易 Agent"""

    def __init__(
        self,
        input_dim: int,
        output_dim: int = 9,
        hidden_dims: list[int] = [128, 64, 32],
        lr: float = 1e-4,
        gamma: float = 0.99,
        epsilon_start: float = 1.0,
        epsilon_end: float = 0.01,
        epsilon_decay: float = 0.995,
        buffer_capacity: int = 100000,
        batch_size: int = 64,
        target_update: int = 10,
        device: str = "cpu",
    ):
        """
        初始化 DQN Agent

        Args:
            input_dim: 输入维度
            output_dim: 动作数量
            hidden_dims: 隐藏层维度
            lr: 学习率
            gamma: 折扣因子
            epsilon_start: 初始探索率
            epsilon_end: 最终探索率
            epsilon_decay: 探索率衰减
            buffer_capacity: 回放缓冲区容量
            batch_size: 批次大小
            target_update: Target network 更新频率
            device: 计算设备
        """
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.gamma = gamma
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size
        self.target_update = target_update

        if not TORCH_AVAILABLE:
            raise ImportError("请安装 PyTorch: pip install torch")

        self.device = torch.device(device if torch.cuda.is_available() else "cpu")

        # 主网络和目标网络
        self.policy_net = DQNNetwork(input_dim, output_dim, hidden_dims).to(self.device)
        self.target_net = DQNNetwork(input_dim, output_dim, hidden_dims).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()

        # 优化器
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=lr)

        # 回放缓冲区
        self.memory = ReplayBuffer(buffer_capacity)

        # 训练统计
        self.steps_done = 0
        self.episode_rewards = []

    def select_action(self, state: np.ndarray, training: bool = True) -> int:
        """
        选择动作（ε-greedy 策略）

        Args:
            state: 当前状态
            training: 是否训练模式

        Returns:
            选择的动作
        """
        if training and random.random() < self.epsilon:
            return random.randint(0, self.output_dim - 1)

        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            q_values = self.policy_net(state_tensor)
            return q_values.max(1)[1].item()

    def optimize_model(self):
        """优化模型（训练一步）"""
        if len(self.memory) < self.batch_size:
            return

        # 采样批次
        states, actions, rewards, next_states, dones = self.memory.sample(self.batch_size)

        # 转换为 Tensor
        state_tensor = torch.FloatTensor(states).to(self.device)
        action_tensor = torch.LongTensor(actions).to(self.device)
        reward_tensor = torch.FloatTensor(rewards).to(self.device)
        next_state_tensor = torch.FloatTensor(next_states).to(self.device)
        done_tensor = torch.FloatTensor(dones).to(self.device)

        # 计算当前 Q 值
        current_q = self.policy_net(state_tensor).gather(1, action_tensor.unsqueeze(1)).squeeze(1)

        # 计算目标 Q 值（Double DQN）
        with torch.no_grad():
            next_actions = self.policy_net(next_state_tensor).max(1)[1]
            next_q = self.target_net(next_state_tensor).gather(1, next_actions.unsqueeze(1)).squeeze(1)
            target_q = reward_tensor + (1 - done_tensor) * self.gamma * next_q

        # 计算损失并优化
        loss = F.smooth_l1_loss(current_q, target_q)

        self.optimizer.zero_grad()
        loss.backward()

        # 梯度裁剪
        for param in self.policy_net.parameters():
            param.grad.data.clamp_(-1, 1)

        self.optimizer.step()

        self.steps_done += 1

        return loss.item()

    def update_target_network(self):
        """更新目标网络"""
        self.target_net.load_state_dict(self.policy_net.state_dict())

    def decay_epsilon(self):
        """衰减探索率"""
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)

    def remember(self, state: np.ndarray, action: int, reward: float, next_state: np.ndarray, done: bool):
        """存储经验"""
        self.memory.push(state, action, reward, next_state, done)

    def train_episode(
        self, env: TradingEnv, num_episodes: int = 100, render: bool = False, verbose: bool = True
    ) -> dict:
        """
        训练多个回合

        Args:
            env: 交易环境
            num_episodes: 训练回合数
            render: 是否渲染
            verbose: 是否打印进度

        Returns:
            训练统计
        """
        episode_rewards = []
        episode_returns = []

        for episode in range(num_episodes):
            state, _ = env.reset()
            total_reward = 0
            done = False

            while not done:
                # 选择动作
                action = self.select_action(state, training=True)

                # 执行动作
                next_state, reward, terminated, truncated, _ = env.step(action)
                done = terminated or truncated

                # 存储经验
                self.remember(state, action, reward, next_state, done)

                # 优化模型
                _loss = self.optimize_model()

                # 更新目标网络
                if self.steps_done % self.target_update == 0:
                    self.update_target_network()

                state = next_state
                total_reward += reward

            # 衰减探索率
            self.decay_epsilon()

            # 记录结果
            episode_rewards.append(total_reward)
            results = env.get_results()
            episode_returns.append(results["total_return"])

            if verbose and (episode + 1) % 10 == 0:
                avg_reward = np.mean(episode_rewards[-10:])
                avg_return = np.mean(episode_returns[-10:])
                print(
                    f"Episode {episode + 1}/{num_episodes}, "
                    f"Avg Reward: {avg_reward:.4f}, "
                    f"Avg Return: {avg_return:.2%}, "
                    f"Epsilon: {self.epsilon:.3f}"
                )

        self.episode_rewards = episode_rewards

        return {
            "total_episodes": num_episodes,
            "final_epsilon": self.epsilon,
            "avg_reward": np.mean(episode_rewards[-10:]),
            "avg_return": np.mean(episode_returns[-10:]),
            "best_return": max(episode_returns),
            "total_steps": self.steps_done,
        }

    def save(self, path: str):
        """保存模型"""
        torch.save(
            {
                "policy_net_state_dict": self.policy_net.state_dict(),
                "target_net_state_dict": self.target_net.state_dict(),
                "optimizer_state_dict": self.optimizer.state_dict(),
                "epsilon": self.epsilon,
                "steps_done": self.steps_done,
            },
            path,
        )

    def load(self, path: str):
        """加载模型"""
        checkpoint = torch.load(path, map_location=self.device)
        self.policy_net.load_state_dict(checkpoint["policy_net_state_dict"])
        self.target_net.load_state_dict(checkpoint["target_net_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        self.epsilon = checkpoint["epsilon"]
        self.steps_done = checkpoint["steps_done"]

    def get_action_meanings(self) -> list[str]:
        """获取动作含义"""
        return ["HOLD", "BUY_10%", "BUY_25%", "BUY_50%", "BUY_100%", "SELL_10%", "SELL_25%", "SELL_50%", "SELL_100%"]


# ════════════════════════════════════════════════════════════
# 使用示例
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # 创建示例数据
    np.random.seed(42)
    n = 1000
    dates = pd.date_range("2023-01-01", periods=n, freq="D")

    df = pd.DataFrame(
        {
            "open": np.random.randn(n).cumsum() + 100,
            "high": np.random.randn(n).cumsum() + 101,
            "low": np.random.randn(n).cumsum() + 99,
            "close": np.random.randn(n).cumsum() + 100,
            "volume": np.random.randint(1000, 10000, n),
        },
        index=dates,
    )

    # 添加技术指标
    df["rsi"] = 50 + np.random.randn(n) * 10
    df["macd"] = np.random.randn(n)
    df["bb_width"] = 0.1 + np.random.randn(n) * 0.02

    # 创建环境和 Agent
    env = TradingEnv(df, initial_balance=100000, discrete_actions=True)
    agent = DQNAgent(input_dim=env.observation_space.shape[0], output_dim=9)

    print("开始训练 DQN Agent...")
    print(f"状态维度：{env.observation_space.shape[0]}")
    print(f"动作数量：{env.action_space.n}")
    print(f"动作含义：{agent.get_action_meanings()}")
    print("-" * 60)

    # 训练
    stats = agent.train_episode(env, num_episodes=50, verbose=True)

    print("-" * 60)
    print("\n训练完成!")
    print(f"  总回合：{stats['total_episodes']}")
    print(f"  最终探索率：{stats['final_epsilon']:.3f}")
    print(f"  平均奖励：{stats['avg_reward']:.4f}")
    print(f"  平均收益：{stats['avg_return']:.2%}")
    print(f"  最佳收益：{stats['best_return']:.2%}")

    # 保存模型
    agent.save("models/dqn_agent.pth")
    print("\n模型已保存至：models/dqn_agent.pth")
