"""
跨交易所套利策略

功能：
- 监控多个交易所价差
- 发现套利机会
- 自动执行套利交易
- 风险控制

套利类型：
- 现货套利（低价买入 + 高价卖出）
- 期现套利（期货 - 现货基差）
- 三角套利（三个币种循环）

支持交易所：
- Binance
- OKX
- Bybit
- Gate.io
- Huobi

注意：
- 需要考虑交易手续费
- 需要考虑提币时间和费用
- 需要考虑滑点风险
"""

from __future__ import annotations

import ccxt
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ArbitrageOpportunity:
    """套利机会"""
    symbol: str
    buy_exchange: str
    sell_exchange: str
    buy_price: float
    sell_price: float
    spread: float  # 价差（百分比）
    spread_usd: float  # 价差（美元）
    profit_pct: float  # 扣除手续费后的利润率
    volume_usd: float  # 可交易金额
    timestamp: datetime


class CrossExchangeArbitrage:
    """
    跨交易所套利
    
    逻辑：
    1. 监控多个交易所的价格
    2. 发现价差超过阈值的机会
    3. 计算扣除手续费后的利润
    4. 执行套利（同时买入和卖出）
    5. 转移资产平衡仓位
    
    风险：
    - 提币时间风险（价格波动）
    - 交易所风险（宕机、冻结）
    - 滑点风险（执行价格偏离）
    - 手续费风险（侵蚀利润）
    """
    
    def __init__(
        self,
        exchanges: List[str],
        api_keys: Optional[Dict[str, Dict[str, str]]] = None,
        min_profit_pct: float = 0.5,
        max_position_usd: float = 10000
    ):
        """
        初始化
        
        Args:
            exchanges: 交易所列表
            api_keys: API Keys 字典
            min_profit_pct: 最小利润率（百分比）
            max_position_usd: 最大仓位（美元）
        """
        self.exchanges = {}
        self.api_keys = api_keys or {}
        self.min_profit_pct = min_profit_pct
        self.max_position_usd = max_position_usd
        
        # 手续费率（默认 0.1%）
        self.fee_rate = 0.001
        
        # 初始化交易所
        for exchange_id in exchanges:
            try:
                if exchange_id in self.api_keys:
                    keys = self.api_keys[exchange_id]
                    exchange_class = getattr(ccxt, exchange_id)
                    self.exchanges[exchange_id] = exchange_class({
                        'apiKey': keys.get('apiKey'),
                        'secret': keys.get('secret'),
                        'enableRateLimit': True,
                    })
                else:
                    # 无需 API Key（只读）
                    exchange_class = getattr(ccxt, exchange_id)
                    self.exchanges[exchange_id] = exchange_class({
                        'enableRateLimit': True,
                    })
                
                logger.info(f"初始化交易所：{exchange_id}")
            except Exception as e:
                logger.error(f"初始化交易所 {exchange_id} 失败：{e}")
    
    def get_price(
        self,
        exchange_id: str,
        symbol: str
    ) -> Optional[float]:
        """
        获取价格
        
        Args:
            exchange_id: 交易所 ID
            symbol: 交易对
        
        Returns:
            价格
        """
        if exchange_id not in self.exchanges:
            return None
        
        try:
            exchange = self.exchanges[exchange_id]
            ticker = exchange.fetch_ticker(symbol)
            return ticker['last']
        except Exception as e:
            logger.error(f"获取 {exchange_id} 价格失败：{e}")
            return None
    
    def scan_opportunities(
        self,
        symbols: List[str],
        min_spread_pct: float = 0.3
    ) -> List[ArbitrageOpportunity]:
        """
        扫描套利机会
        
        Args:
            symbols: 交易对列表
            min_spread_pct: 最小价差（百分比）
        
        Returns:
            套利机会列表
        """
        opportunities = []
        
        for symbol in symbols:
            # 获取所有交易所的价格
            prices = {}
            for exchange_id in self.exchanges.keys():
                price = self.get_price(exchange_id, symbol)
                if price:
                    prices[exchange_id] = price
            
            # 至少需要 2 个交易所的价格
            if len(prices) < 2:
                continue
            
            # 找出最低价和最高价
            min_exchange = min(prices, key=prices.get)
            max_exchange = max(prices, key=prices.get)
            
            buy_price = prices[min_exchange]
            sell_price = prices[max_exchange]
            
            # 计算价差
            spread_pct = (sell_price - buy_price) / buy_price * 100
            
            # 检查是否超过最小价差
            if spread_pct < min_spread_pct:
                continue
            
            # 计算利润率（扣除双边手续费）
            total_fee = self.fee_rate * 2 * 100  # 双边手续费（百分比）
            profit_pct = spread_pct - total_fee
            
            # 检查是否有利润
            if profit_pct < self.min_profit_pct:
                continue
            
            # 创建套利机会
            opp = ArbitrageOpportunity(
                symbol=symbol,
                buy_exchange=min_exchange,
                sell_exchange=max_exchange,
                buy_price=buy_price,
                sell_price=sell_price,
                spread=spread_pct,
                spread_usd=sell_price - buy_price,
                profit_pct=profit_pct,
                volume_usd=self.max_position_usd,
                timestamp=datetime.now()
            )
            
            opportunities.append(opp)
            
            logger.info(
                f"发现套利机会：{symbol} | "
                f"买：{min_exchange}@{buy_price} | "
                f"卖：{max_exchange}@{sell_price} | "
                f"利润：{profit_pct:.2f}%"
            )
        
        # 按利润率排序
        opportunities.sort(key=lambda x: x.profit_pct, reverse=True)
        
        return opportunities
    
    def execute_arbitrage(
        self,
        opportunity: ArbitrageOpportunity,
        amount: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        执行套利
        
        Args:
            opportunity: 套利机会
            amount: 交易数量（可选，默认使用最大仓位）
        
        Returns:
            执行结果
        """
        if amount is None:
            # 根据最大仓位计算数量
            amount = self.max_position_usd / opportunity.buy_price
        
        result = {
            'symbol': opportunity.symbol,
            'timestamp': datetime.now(),
            'buy_order': None,
            'sell_order': None,
            'profit_estimate': 0,
            'status': 'pending'
        }
        
        try:
            # 1. 在低价交易所买入
            buy_exchange = self.exchanges[opportunity.buy_exchange]
            buy_order = buy_exchange.create_market_buy_order(
                opportunity.symbol,
                amount
            )
            result['buy_order'] = buy_order
            logger.info(f"买入订单：{opportunity.buy_exchange} {amount}@{opportunity.buy_price}")
            
            # 2. 在高价交易所卖出
            sell_exchange = self.exchanges[opportunity.sell_exchange]
            sell_order = sell_exchange.create_market_sell_order(
                opportunity.symbol,
                amount
            )
            result['sell_order'] = sell_order
            logger.info(f"卖出订单：{opportunity.sell_exchange} {amount}@{opportunity.sell_price}")
            
            # 3. 计算实际利润
            buy_cost = buy_order['cost']
            sell_revenue = sell_order['cost']
            buy_fee = buy_order.get('fee', {}).get('cost', 0)
            sell_fee = sell_order.get('fee', {}).get('cost', 0)
            
            profit = sell_revenue - buy_cost - buy_fee - sell_fee
            profit_pct = profit / buy_cost * 100
            
            result['profit_estimate'] = profit
            result['profit_pct'] = profit_pct
            result['status'] = 'completed'
            
            logger.info(
                f"套利完成：利润 ${profit:.2f} ({profit_pct:.2f}%)"
            )
            
        except Exception as e:
            logger.error(f"套利执行失败：{e}")
            result['status'] = 'failed'
            result['error'] = str(e)
        
        return result
    
    def get_exchange_balances(self) -> Dict[str, Dict[str, float]]:
        """
        获取各交易所余额
        
        Returns:
            余额字典
        """
        balances = {}
        
        for exchange_id, exchange in self.exchanges.items():
            try:
                if exchange_id in self.api_keys:
                    balance = exchange.fetch_balance()
                    balances[exchange_id] = {
                        'USDT': balance.get('USDT', {}).get('free', 0),
                        'BTC': balance.get('BTC', {}).get('free', 0),
                        'ETH': balance.get('ETH', {}).get('free', 0),
                    }
                else:
                    balances[exchange_id] = {'USDT': 0, 'BTC': 0, 'ETH': 0}
            except Exception as e:
                logger.error(f"获取 {exchange_id} 余额失败：{e}")
                balances[exchange_id] = {'error': str(e)}
        
        return balances


class TriangularArbitrage:
    """
    三角套利
    
    逻辑：
    1. 在同一交易所内
    2. 通过三个交易对循环交易
    3. 利用定价错误获利
    
    示例路径：
    USDT → BTC → ETH → USDT
    
    条件：
    - 汇率乘积 > 1 + 手续费
    """
    
    def __init__(
        self,
        exchange_id: str,
        api_keys: Optional[Dict[str, str]] = None,
        min_profit_pct: float = 0.1
    ):
        """
        初始化
        
        Args:
            exchange_id: 交易所 ID
            api_keys: API Keys
            min_profit_pct: 最小利润率
        """
        self.min_profit_pct = min_profit_pct
        
        if api_keys:
            exchange_class = getattr(ccxt, exchange_id)
            self.exchange = exchange_class({
                'apiKey': api_keys.get('apiKey'),
                'secret': api_keys.get('secret'),
                'enableRateLimit': True,
            })
        else:
            exchange_class = getattr(ccxt, exchange_id)
            self.exchange = exchange_class({
                'enableRateLimit': True,
            })
        
        self.exchange_id = exchange_id
    
    def find_cycles(
        self,
        base_currency: str = "USDT"
    ) -> List[Dict[str, Any]]:
        """
        寻找套利循环
        
        Args:
            base_currency: 基础货币
        
        Returns:
            套利循环列表
        """
        # 简化实现
        # 实际应该构建完整的交易对图并寻找循环
        
        cycles = []
        
        # 示例：USDT → BTC → ETH → USDT
        # 需要获取三个交易对的价格
        
        return cycles
    
    def calculate_profit(
        self,
        path: List[str],
        amount: float
    ) -> float:
        """
        计算循环利润
        
        Args:
            path: 交易路径
            amount: 初始金额
        
        Returns:
            利润率
        """
        # 简化实现
        return 0.0


# 测试
if __name__ == "__main__":
    print("测试跨交易所套利...\n")
    
    # 初始化套利器
    arb = CrossExchangeArbitrage(
        exchanges=['binance', 'okx', 'bybit'],
        min_profit_pct=0.3,
        max_position_usd=1000
    )
    
    # 扫描套利机会
    print("扫描套利机会...")
    symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
    opportunities = arb.scan_opportunities(symbols, min_spread_pct=0.3)
    
    if opportunities:
        print(f"\n发现 {len(opportunities)} 个套利机会：")
        for opp in opportunities[:3]:
            print(f"\n{opp.symbol}:")
            print(f"  买入：{opp.buy_exchange} @ ${opp.buy_price:,.2f}")
            print(f"  卖出：{opp.sell_exchange} @ ${opp.sell_price:,.2f}")
            print(f"  价差：{opp.spread:.2f}%")
            print(f"  利润：{opp.profit_pct:.2f}%")
    else:
        print("未发现套利机会")
    
    # 获取余额
    print("\n获取交易所余额...")
    balances = arb.get_exchange_balances()
    for exchange, balance in balances.items():
        print(f"{exchange}: {balance}")
