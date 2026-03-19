"""
高级策略集成模块

整合所有新技术策略，提供统一的接口
- LSTM 价格预测
- NLP 情绪分析
- 配对交易
- 多因子策略
"""
from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime

from .ml_strategies.lstm_predictor import LSTMPredictor
from .ml_strategies.feature_engineering import FeatureEngineer
from .nlp_strategies.sentiment_analyzer import SentimentAnalyzer, NewsMonitor
from .quant_strategies.pairs_trading import PairsTrading


class AdvancedStrategiesManager:
    """高级策略管理器"""
    
    def __init__(self):
        """初始化策略管理器"""
        # LSTM 策略
        self.lstm_predictor = LSTMPredictor(
            lookback=60,
            forecast_horizon=5,
            lstm_units=50,
            dropout_rate=0.2
        )
        
        # 特征工程
        self.feature_engineer = FeatureEngineer()
        
        # 情绪分析
        self.sentiment_analyzer = SentimentAnalyzer()
        self.news_monitor = NewsMonitor(self.sentiment_analyzer)
        
        # 配对交易
        self.pairs_trading = PairsTrading(
            lookback_window=60,
            entry_zscore=2.0,
            exit_zscore=0.5,
            stoploss_zscore=3.0
        )
        
        # 策略状态
        self.strategy_states = {}
    
    def add_news(
        self,
        title: str,
        content: str,
        source: str,
        symbols: Optional[List[str]] = None
    ):
        """添加新闻"""
        self.news_monitor.add_news(
            title=title,
            content=content,
            source=source,
            published_at=datetime.now(),
            symbols=symbols
        )
    
    def get_lstm_signal(self, df: pd.DataFrame) -> Dict:
        """
        获取 LSTM 预测信号
        
        Args:
            df: OHLCV 数据
        
        Returns:
            交易信号
        """
        try:
            if self.lstm_predictor.model is None:
                return {
                    "strategy": "lstm",
                    "status": "model_not_trained",
                    "message": "请先训练 LSTM 模型"
                }
            
            signal = self.lstm_predictor.predict_signal(df)
            self.strategy_states['lstm'] = signal
            return signal
        
        except Exception as e:
            return {
                "strategy": "lstm",
                "status": "error",
                "error": str(e)
            }
    
    def get_sentiment_signal(self, hours: int = 24) -> Dict:
        """
        获取情绪分析信号
        
        Args:
            hours: 回溯小时数
        
        Returns:
            交易信号
        """
        try:
            signal = self.news_monitor.get_sentiment_signal(hours=hours)
            self.strategy_states['sentiment'] = signal
            return signal
        
        except Exception as e:
            return {
                "strategy": "sentiment",
                "status": "error",
                "error": str(e)
            }
    
    def get_pairs_trading_signal(
        self,
        price1: pd.Series,
        price2: pd.Series
    ) -> Dict:
        """
        获取配对交易信号
        
        Args:
            price1: 价格序列 1
            price2: 价格序列 2
        
        Returns:
            交易信号
        """
        try:
            signal = self.pairs_trading.generate_signal(price1, price2)
            self.strategy_states['pairs_trading'] = signal
            return signal
        
        except Exception as e:
            return {
                "strategy": "pairs_trading",
                "status": "error",
                "error": str(e)
            }
    
    def get_ensemble_signal(
        self,
        df: pd.DataFrame,
        price1: Optional[pd.Series] = None,
        price2: Optional[pd.Series] = None,
        weights: Optional[Dict[str, float]] = None
    ) -> Dict:
        """
        集成多个策略的信号
        
        Args:
            df: OHLCV 数据
            price1: 配对交易价格 1（可选）
            price2: 配对交易价格 2（可选）
            weights: 策略权重（可选）
        
        Returns:
            集成信号
        """
        if weights is None:
            weights = {
                'lstm': 0.4,
                'sentiment': 0.3,
                'pairs_trading': 0.3
            }
        
        signals = []
        
        # LSTM 信号
        lstm_signal = self.get_lstm_signal(df)
        if lstm_signal.get('status') != 'error':
            signals.append({
                'strategy': 'lstm',
                'signal': lstm_signal.get('signal', 0),
                'confidence': lstm_signal.get('confidence', 0.5),
                'weight': weights.get('lstm', 0.4)
            })
        
        # 情绪信号
        sentiment_signal = self.get_sentiment_signal()
        if sentiment_signal.get('status') != 'error':
            # 转换情绪信号为 -1, 0, 1
            action_to_signal = {'BUY': 1, 'SELL': -1, 'HOLD': 0}
            sig = action_to_signal.get(sentiment_signal.get('action', 'HOLD'), 0)
            signals.append({
                'strategy': 'sentiment',
                'signal': sig,
                'confidence': sentiment_signal.get('confidence', 0.5),
                'weight': weights.get('sentiment', 0.3)
            })
        
        # 配对交易信号
        if price1 is not None and price2 is not None:
            pairs_signal = self.get_pairs_trading_signal(price1, price2)
            if pairs_signal.get('status') != 'error':
                signals.append({
                    'strategy': 'pairs_trading',
                    'signal': pairs_signal.get('signal', 0),
                    'confidence': abs(pairs_signal.get('zscore', 0)) / 3.0,
                    'weight': weights.get('pairs_trading', 0.3)
                })
        
        if not signals:
            return {
                "strategy": "ensemble",
                "status": "no_signals",
                "message": "没有可用的策略信号"
            }
        
        # 加权平均
        total_weight = sum(s['weight'] for s in signals)
        weighted_signal = sum(s['signal'] * s['weight'] * s['confidence'] for s in signals) / total_weight
        
        # 转换为最终信号
        if weighted_signal > 0.3:
            final_signal = 1
            action = "BUY"
        elif weighted_signal < -0.3:
            final_signal = -1
            action = "SELL"
        else:
            final_signal = 0
            action = "HOLD"
        
        result = {
            "strategy": "ensemble",
            "signal": final_signal,
            "action": action,
            "weighted_score": weighted_signal,
            "num_strategies": len(signals),
            "individual_signals": signals,
            "timestamp": int(datetime.now().timestamp() * 1000)
        }
        
        self.strategy_states['ensemble'] = result
        return result
    
    def train_lstm(
        self,
        df: pd.DataFrame,
        epochs: int = 50,
        batch_size: int = 32,
        model_path: Optional[str] = None
    ) -> Dict:
        """
        训练 LSTM 模型
        
        Args:
            df: OHLCV 数据
            epochs: 训练轮数
            batch_size: 批次大小
            model_path: 模型保存路径
        
        Returns:
            训练结果
        """
        try:
            history = self.lstm_predictor.train(
                df,
                epochs=epochs,
                batch_size=batch_size,
                model_path=model_path
            )
            
            return {
                "status": "success",
                "message": "LSTM 模型训练完成",
                "final_loss": float(history.history['loss'][-1]),
                "final_accuracy": float(history.history['accuracy'][-1]),
                "epochs_trained": len(history.history['loss'])
            }
        
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def find_cointegrated_pairs(
        self,
        price_data: Dict[str, pd.Series],
        p_value_threshold: float = 0.05
    ) -> List[Dict]:
        """
        寻找协整的股票对
        
        Args:
            price_data: {symbol: price_series} 字典
            p_value_threshold: p 值阈值
        
        Returns:
            协整对列表
        """
        symbols = list(price_data.keys())
        cointegrated_pairs = []
        
        for i in range(len(symbols)):
            for j in range(i + 1, len(symbols)):
                sym1, sym2 = symbols[i], symbols[j]
                price1, price2 = price_data[sym1], price_data[sym2]
                
                _, p_value, is_coint = self.pairs_trading.cointegration_test(price1, price2)
                
                if is_coint:
                    cointegrated_pairs.append({
                        "pair": f"{sym1}/{sym2}",
                        "symbol1": sym1,
                        "symbol2": sym2,
                        "hedge_ratio": float(self.pairs_trading.hedge_ratio),
                        "p_value": p_value
                    })
        
        return cointegrated_pairs
    
    def get_all_signals(self) -> Dict:
        """获取所有策略的当前信号"""
        return {
            "timestamp": datetime.now().isoformat(),
            "signals": self.strategy_states.copy()
        }


# ════════════════════════════════════════════════════════════
# 使用示例
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # 创建示例数据
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=500, freq='D')
    
    df = pd.DataFrame({
        'open': np.random.randn(500).cumsum() + 100,
        'high': np.random.randn(500).cumsum() + 101,
        'low': np.random.randn(500).cumsum() + 99,
        'close': np.random.randn(500).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, 500)
    }, index=dates)
    
    # 创建管理器
    manager = AdvancedStrategiesManager()
    
    print("=== 高级策略管理器测试 ===\n")
    
    # 添加新闻
    manager.add_news(
        title="Bitcoin surges to new highs",
        content="Institutional adoption accelerates as major companies add BTC to treasury",
        source="CryptoNews",
        symbols=["BTC", "ETH"]
    )
    
    # 获取情绪信号
    sentiment_signal = manager.get_sentiment_signal()
    print(f"情绪信号：{sentiment_signal}")
    
    # 获取配对交易信号
    price1 = df['close']
    price2 = pd.Series(np.random.randn(500).cumsum() + 100, index=dates)
    pairs_signal = manager.get_pairs_trading_signal(price1, price2)
    print(f"\n配对交易信号：{pairs_signal}")
    
    # 集成信号
    ensemble_signal = manager.get_ensemble_signal(df, price1, price2)
    print(f"\n集成信号：{ensemble_signal}")
