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
from typing import Optional, Any
from dataclasses import dataclass
from datetime import datetime

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
        exchanges: list[str],
        api_keys: Optional[dict[str, dict[str, str]]] = None,
        min_profit_pct: float = 0.5,
        max_position_usd: float = 10000,
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
                    self.exchanges[exchange_id] = exchange_class(
                        {
                            "apiKey": keys.get("apiKey"),
                            "secret": keys.get("secret"),
                            "enableRateLimit": True,
                        }
                    )
                else:
                    # 无需 API Key（只读）
                    exchange_class = getattr(ccxt, exchange_id)
                    self.exchanges[exchange_id] = exchange_class(
                        {
                            "enableRateLimit": True,
                        }
                    )

                logger.info(f"初始化交易所：{exchange_id}")
            except Exception as e:
                logger.error(f"初始化交易所 {exchange_id} 失败：{e}")

    def get_price(self, exchange_id: str, symbol: str) -> Optional[float]:
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
            return ticker["last"]
        except Exception as e:
            logger.error(f"获取 {exchange_id} 价格失败：{e}")
            return None

    def scan_opportunities(self, symbols: list[str], min_spread_pct: float = 0.3) -> list[ArbitrageOpportunity]:
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
                timestamp=datetime.now(),
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

    def execute_arbitrage(self, opportunity: ArbitrageOpportunity, amount: Optional[float] = None) -> dict[str, Any]:
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
            "symbol": opportunity.symbol,
            "timestamp": datetime.now(),
            "buy_order": None,
            "sell_order": None,
            "profit_estimate": 0,
            "status": "pending",
        }

        try:
            # 1. 在低价交易所买入
            buy_exchange = self.exchanges[opportunity.buy_exchange]
            buy_order = buy_exchange.create_market_buy_order(opportunity.symbol, amount)
            result["buy_order"] = buy_order
            logger.info(f"买入订单：{opportunity.buy_exchange} {amount}@{opportunity.buy_price}")

            # 2. 在高价交易所卖出
            sell_exchange = self.exchanges[opportunity.sell_exchange]
            sell_order = sell_exchange.create_market_sell_order(opportunity.symbol, amount)
            result["sell_order"] = sell_order
            logger.info(f"卖出订单：{opportunity.sell_exchange} {amount}@{opportunity.sell_price}")

            # 3. 计算实际利润
            buy_cost = buy_order["cost"]
            sell_revenue = sell_order["cost"]
            buy_fee = buy_order.get("fee", {}).get("cost", 0)
            sell_fee = sell_order.get("fee", {}).get("cost", 0)

            profit = sell_revenue - buy_cost - buy_fee - sell_fee
            profit_pct = profit / buy_cost * 100

            result["profit_estimate"] = profit
            result["profit_pct"] = profit_pct
            result["status"] = "completed"

            logger.info(f"套利完成：利润 ${profit:.2f} ({profit_pct:.2f}%)")

        except Exception as e:
            logger.error(f"套利执行失败：{e}")
            result["status"] = "failed"
            result["error"] = str(e)

        return result

    def get_exchange_balances(self) -> dict[str, dict[str, float]]:
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
                        "USDT": balance.get("USDT", {}).get("free", 0),
                        "BTC": balance.get("BTC", {}).get("free", 0),
                        "ETH": balance.get("ETH", {}).get("free", 0),
                    }
                else:
                    balances[exchange_id] = {"USDT": 0, "BTC": 0, "ETH": 0}
            except Exception as e:
                logger.error(f"获取 {exchange_id} 余额失败：{e}")
                balances[exchange_id] = {"error": str(e)}

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

    套利路径类型：
    - 正向循环：A→B→C→A（如 USDT→BTC→ETH→USDT）
    - 反向循环：A→C→B→A（如 USDT→ETH→BTC→USDT）
    """

    def __init__(
        self,
        exchange_id: str,
        api_keys: Optional[dict[str, str]] = None,
        min_profit_pct: float = 0.1,
        max_position_usd: float = 5000,
        fee_rate: float = 0.001,
    ):
        """
        初始化

        Args:
            exchange_id: 交易所 ID
            api_keys: API Keys
            min_profit_pct: 最小利润率
            max_position_usd: 最大仓位
            fee_rate: 单边手续费率
        """
        self.exchange_id = exchange_id
        self.min_profit_pct = min_profit_pct
        self.max_position_usd = max_position_usd
        self.fee_rate = fee_rate

        if api_keys:
            exchange_class = getattr(ccxt, exchange_id)
            self.exchange = exchange_class(
                {
                    "apiKey": api_keys.get("apiKey"),
                    "secret": api_keys.get("secret"),
                    "enableRateLimit": True,
                }
            )
        else:
            exchange_class = getattr(ccxt, exchange_id)
            self.exchange = exchange_class(
                {
                    "enableRateLimit": True,
                }
            )

    def _get_bid_ask(self, symbol: str) -> Optional[tuple[float, float]]:
        """获取买卖价"""
        try:
            orderbook = self.exchange.fetch_order_book(symbol, limit=1)
            bid = orderbook["bids"][0][0] if orderbook["bids"] else None
            ask = orderbook["asks"][0][0] if orderbook["asks"] else None
            if bid and ask:
                return bid, ask
            return None
        except Exception:
            return None

    def find_cycles(
        self, base_currency: str = "USDT", max_depth: int = 3, quote_currencies: Optional[list[str]] = None
    ) -> list[dict[str, Any]]:
        """
        寻找所有三角套利循环

        构建交易对图，寻找所有 base→X→Y→base 的路径

        Args:
            base_currency: 基础货币（套利起点和终点）
            max_depth: 最大搜索深度
            quote_currencies: 候选中间货币

        Returns:
            套利循环列表
        """
        try:
            markets = self.exchange.load_markets()
        except Exception as e:
            logger.error(f"加载市场失败：{e}")
            return []

        # 构建邻接表：base_currency → {中间货币 → 交易对}
        # 同时记录反向
        graph: dict[str, list[tuple[str, str, str]]] = {}  # currency → [(other, symbol, side)]

        for symbol, market in markets.items():
            if not market.get("active", True):
                continue
            if market.get("type") not in ("spot", None):
                continue

            base = market["base"]
            quote = market["quote"]

            # base/quote: 用 quote 买 base = buy side
            if quote not in graph:
                graph[quote] = []
            graph[quote].append((base, symbol, "buy"))

            # 反向：卖 base 得 quote
            if base not in graph:
                graph[base] = []
            graph[base].append((quote, symbol, "sell"))

        if base_currency not in graph:
            logger.warning(f"基础货币 {base_currency} 不在交易所中")
            return []

        # DFS 寻找循环
        cycles = []

        def dfs(path: list[tuple[str, str, str]], visited: set, depth: int):
            current_currency = path[-1][0] if path else base_currency

            if depth == 0:
                # 检查是否能回到 base_currency
                for next_curr, symbol, side in graph.get(current_currency, []):
                    if next_curr == base_currency and len(set(c[0] for c in path)) >= 2:
                        full_path = path + [(base_currency, symbol, side)]
                        cycles.append(full_path)
                return

            for next_curr, symbol, side in graph.get(current_currency, []):
                if next_curr in visited and next_curr != base_currency:
                    continue
                if depth == max_depth - 1 and next_curr == base_currency:
                    continue  # 第一步不能直接回去

                new_visited = visited | {current_currency}
                dfs(path + [(next_curr, symbol, side)], new_visited, depth - 1)

        dfs([(base_currency, "", "")], set(), max_depth - 1)

        return cycles

    def calculate_cycle_profit(self, cycle: list[tuple[str, str, str]], amount: float) -> Optional[dict[str, Any]]:
        """
        计算循环套利的利润

        Args:
            cycle: 循环路径 [(currency, symbol, side), ...]
            amount: 初始金额

        Returns:
            利润计算结果
        """
        if len(cycle) < 3:
            return None

        legs = []
        current_amount = amount
        profitable = True

        for i in range(len(cycle) - 1):
            currency, symbol, side = cycle[i]
            next_currency = cycle[i + 1][0]
            next_symbol = cycle[i + 1][1]
            next_side = cycle[i + 1][2]

            # 获取价格
            bid_ask = self._get_bid_ask(next_symbol)
            if bid_ask is None:
                return None

            bid, ask = bid_ask

            if next_side == "buy":
                # 用 current_currency 买 next_currency
                exec_price = ask  # 买入用 ask
                fee = current_amount * self.fee_rate
                after_fee = current_amount - fee
                next_amount = after_fee / exec_price
            else:
                # 卖 current_currency 得 next_currency
                exec_price = bid  # 卖出用 bid
                next_amount = current_amount * exec_price
                fee = next_amount * self.fee_rate
                next_amount -= fee

            legs.append(
                {
                    "from": currency,
                    "to": next_currency,
                    "symbol": next_symbol,
                    "side": next_side,
                    "price": exec_price,
                    "amount_in": current_amount,
                    "amount_out": next_amount,
                    "fee": fee,
                }
            )

            current_amount = next_amount

        final_amount = current_amount
        profit = final_amount - amount
        profit_pct = profit / amount * 100

        return {
            "cycle": [(c, s) for c, s, _ in cycle],
            "legs": legs,
            "initial_amount": amount,
            "final_amount": final_amount,
            "profit": profit,
            "profit_pct": profit_pct,
            "is_profitable": profit_pct > self.min_profit_pct,
        }

    def scan_opportunities(self, base_currency: str = "USDT", amount: Optional[float] = None) -> list[dict[str, Any]]:
        """
        扫描所有三角套利机会

        Args:
            base_currency: 基础货币
            amount: 交易金额

        Returns:
            套利机会列表（按利润排序）
        """
        amount = amount or self.max_position_usd

        # 寻找所有循环
        cycles = self.find_cycles(base_currency)
        logger.info(f"发现 {len(cycles)} 个潜在循环")

        opportunities = []

        for cycle in cycles:
            result = self.calculate_cycle_profit(cycle, amount)
            if result and result["is_profitable"]:
                opportunities.append(result)

        # 按利润率排序
        opportunities.sort(key=lambda x: x["profit_pct"], reverse=True)

        if opportunities:
            logger.info(f"发现 {len(opportunities)} 个三角套利机会，最高利润：{opportunities[0]['profit_pct']:.3f}%")

        return opportunities

    def execute_cycle(self, cycle: list[tuple[str, str, str]], amount: float) -> dict[str, Any]:
        """
        执行三角套利

        Args:
            cycle: 循环路径
            amount: 初始金额

        Returns:
            执行结果
        """
        result = {
            "cycle": [(c, s) for c, s, _ in cycle],
            "legs": [],
            "initial_amount": amount,
            "final_amount": 0,
            "profit": 0,
            "status": "pending",
        }

        current_amount = amount

        try:
            for i in range(len(cycle) - 1):
                _, symbol, side = cycle[i]
                next_side = cycle[i + 1][2]

                if next_side == "buy":
                    order = self.exchange.create_market_buy_order(symbol, current_amount / self._get_bid_ask(symbol)[1])
                else:
                    order = self.exchange.create_market_sell_order(symbol, current_amount)

                filled = order.get("filled", 0)
                cost = order.get("cost", 0)

                result["legs"].append(
                    {
                        "symbol": symbol,
                        "side": next_side,
                        "order_id": order.get("id"),
                        "filled": filled,
                        "cost": cost,
                    }
                )

                current_amount = cost if next_side == "buy" else filled

            result["final_amount"] = current_amount
            result["profit"] = current_amount - amount
            result["profit_pct"] = result["profit"] / amount * 100
            result["status"] = "completed"

            logger.info(f"三角套利完成：利润 ${result['profit']:.2f} ({result['profit_pct']:.3f}%)")

        except Exception as e:
            logger.error(f"三角套利执行失败：{e}")
            result["status"] = "failed"
            result["error"] = str(e)

        return result


# 测试
if __name__ == "__main__":
    print("测试跨交易所套利...\n")

    # 初始化套利器
    arb = CrossExchangeArbitrage(exchanges=["binance", "okx", "bybit"], min_profit_pct=0.3, max_position_usd=1000)

    # 扫描套利机会
    print("扫描套利机会...")
    symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
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
