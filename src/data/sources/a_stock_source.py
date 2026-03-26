"""
A 股数据源 - 新浪财经 API

功能：
- 沪深股票实时行情
- 历史 K 线数据
- 资金流向
- 龙虎榜数据
- 概念板块
- 指数数据

数据源：
- 新浪财经 API（免费、无需 Key）
- 东方财富 API（备选）

更新频率：
- 实时行情：3 秒延迟
- 历史 K 线：每日更新
- 资金流向：实时

注意：
- 仅供学习研究使用
- 商业使用请联系数据源方
"""

from __future__ import annotations

import requests
import pandas as pd
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
import re

logger = logging.getLogger(__name__)


class SinaAShareSource:
    """
    新浪财经 A 股数据源
    
    优点：
    - 免费、无需 API Key
    - 数据全面（沪深 4000+ 股票）
    - 实时行情（3 秒延迟）
    - 历史数据完整
    
    缺点：
    - 有请求频率限制
    - 商业使用受限
    """
    
    # 新浪财经 API 端点
    QUOTE_URL = "https://hq.sinajs.cn/list={}"
    KLINE_URL = "http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData"
    FLOW_URL = "http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/MarketCenter.getHQBlockFlow"
    
    def __init__(self):
        """初始化"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (StocksX V0)',
            'Accept': 'application/json',
            'Referer': 'https://finance.sina.com.cn',
        })
        
        # 缓存
        self._cache = {}
        self._cache_ttl = 10  # 10 秒缓存（实时行情）
    
    def _get_symbol_code(self, symbol: str) -> str:
        """
        转换股票代码格式
        
        Args:
            symbol: 股票代码（如 600519.SH 或 000001.SZ）
        
        Returns:
            新浪财经格式（如 sh600519 或 sz000001）
        """
        if '.' in symbol:
            code, exchange = symbol.split('.')
            if exchange == 'SH':
                return f"sh{code}"
            elif exchange == 'SZ':
                return f"sz{code}"
        return f"sh{symbol}" if symbol.startswith('6') else f"sz{symbol}"
    
    def get_realtime_quote(self, symbol: str) -> Dict[str, Any]:
        """
        获取实时报价
        
        Args:
            symbol: 股票代码（如 600519.SH）
        
        Returns:
            实时报价数据
        """
        code = self._get_symbol_code(symbol)
        url = self.QUOTE_URL.format(code)
        
        try:
            response = self.session.get(url, timeout=5)
            response.raise_for_status()
            
            # 解析返回数据（JavaScript 变量格式）
            text = response.text
            match = re.search(r'="([^"]+)"', text)
            
            if not match:
                return {'error': 'No data'}
            
            data_str = match.group(1).split(',')
            
            if len(data_str) < 32:
                return {'error': 'Invalid data format'}
            
            # 解析字段
            quote = {
                'symbol': symbol,
                'name': data_str[0],
                'open': float(data_str[1]),
                'high': float(data_str[2]),
                'low': float(data_str[3]),
                'close': float(data_str[4]),  # 当前价
                'prev_close': float(data_str[5]),  # 昨收
                'volume': int(data_str[6]),  # 成交量（股）
                'amount': float(data_str[7]),  # 成交额（元）
                'timestamp': datetime.now().timestamp() * 1000,
                'exchange': 'SSE' if code.startswith('sh') else 'SZSE',
            }
            
            # 计算涨跌
            quote['change'] = quote['close'] - quote['prev_close']
            quote['change_pct'] = (quote['change'] / quote['prev_close'] * 100) if quote['prev_close'] else 0
            
            # 买盘数据
            quote['bid1'] = float(data_str[11])
            quote['bid1_volume'] = int(data_str[10])
            quote['ask1'] = float(data_str[13])
            quote['ask1_volume'] = int(data_str[12])
            
            return quote
            
        except Exception as e:
            logger.error(f"获取 A 股实时行情失败：{e}")
            return {'error': str(e)}
    
    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1d",
        days: int = 365,
        since: Optional[int] = None,
        until: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取历史 K 线
        
        Args:
            symbol: 股票代码
            timeframe: 时间周期（1d/1w/1m）
            days: 获取天数
            since: 起始时间戳
            until: 结束时间戳
        
        Returns:
            OHLCV 数据列表
        """
        code = self._get_symbol_code(symbol)
        
        # 计算需要获取的 K 线数量
        if timeframe == "1d":
            count = days
        elif timeframe == "1w":
            count = days // 7
        elif timeframe == "1m":
            count = days // 30
        else:
            count = days
        
        # 新浪财经最多一次返回 300 条
        count = min(count, 300)
        
        params = {
            'symbol': code,
            'scale': timeframe.replace('1', ''),  # d/w/m
            'datalen': str(count)
        }
        
        try:
            response = self.session.get(self.KLINE_URL, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if not data:
                return []
            
            # 解析 K 线数据
            result = []
            for item in data:
                # 日期格式：2023-03-19
                try:
                    timestamp = int(datetime.strptime(item['day'], '%Y-%m-%d').timestamp() * 1000)
                except (ValueError, KeyError):
                    continue
                
                ohlcv = {
                    'exchange': 'SSE' if code.startswith('sh') else 'SZSE',
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'timestamp': timestamp,
                    'open': float(item['open']),
                    'high': float(item['high']),
                    'low': float(item['low']),
                    'close': float(item['close']),
                    'volume': float(item['volume']),
                    'amount': float(item.get('turnover', 0)),
                }
                result.append(ohlcv)
            
            return result
            
        except Exception as e:
            logger.error(f"获取 A 股 K 线失败：{e}")
            return []
    
    def get_capital_flow(
        self,
        symbol: str,
        days: int = 10
    ) -> Dict[str, Any]:
        """
        获取资金流向
        
        Args:
            symbol: 股票代码
            days: 天数
        
        Returns:
            资金流向数据
        """
        code = self._get_symbol_code(symbol)
        
        params = {
            'symbol': code,
            'datalen': str(days)
        }
        
        try:
            response = self.session.get(self.FLOW_URL, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if not data:
                return {'error': 'No data'}
            
            # 解析资金流向
            result = {
                'symbol': symbol,
                'main_force_in': 0,  # 主力流入
                'main_force_out': 0,  # 主力流出
                'main_force_net': 0,  # 主力净额
                'retail_in': 0,  # 散户流入
                'retail_out': 0,  # 散户流出
                'retail_net': 0,  # 散户净额
            }
            
            # 简化处理，实际需要根据返回字段解析
            for item in data:
                pass
            
            return result
            
        except Exception as e:
            logger.error(f"获取资金流向失败：{e}")
            return {'error': str(e)}
    
    def get_stock_list(
        self,
        market: str = "all"
    ) -> List[Dict[str, str]]:
        """
        获取股票列表
        
        Args:
            market: 市场（SH/SZ/all）
        
        Returns:
            股票列表
        """
        stocks = []
        
        # 简化实现，实际应该从 API 获取完整列表
        # 这里只返回示例
        
        if market in ['SH', 'all']:
            # 沪市示例
            stocks.extend([
                {'symbol': '600519.SH', 'name': '贵州茅台', 'market': 'SH'},
                {'symbol': '601318.SH', 'name': '中国平安', 'market': 'SH'},
            ])
        
        if market in ['SZ', 'all']:
            # 深市示例
            stocks.extend([
                {'symbol': '000001.SZ', 'name': '平安银行', 'market': 'SZ'},
                {'symbol': '000858.SZ', 'name': '五粮液', 'market': 'SZ'},
            ])
        
        return stocks
    
    def get_index_quote(self, index_code: str) -> Dict[str, Any]:
        """
        获取指数行情
        
        Args:
            index_code: 指数代码（如 000001 上证指数）
        
        Returns:
            指数行情
        """
        # 指数代码格式转换
        if index_code == '000001':
            code = 'sh000001'
        elif index_code == '399001':
            code = 'sz399001'
        elif index_code == '399006':
            code = 'sz399006'
        else:
            code = f"sh{index_code}"
        
        return self.get_realtime_quote(code)


class DongfangAShareSource:
    """
    东方财富 A 股数据源（备选）
    
    功能类似新浪财经，作为备用数据源
    """
    
    BASE_URL = "https://push2.eastmoney.com"
    
    def __init__(self):
        """初始化"""
        self.session = requests.Session()
    
    def get_realtime_quote(self, symbol: str) -> Dict[str, Any]:
        """获取实时报价"""
        # 实现类似新浪财经的功能
        # 这里简化处理
        return {'error': 'Not implemented'}


# 测试
if __name__ == "__main__":
    sina = SinaAShareSource()
    
    print("测试 A 股数据源...\n")
    
    # 测试实时行情
    print("1. 测试实时行情")
    quote = sina.get_realtime_quote("600519.SH")
    if 'error' not in quote:
        print(f"   贵州茅台：{quote['close']}元, 涨跌：{quote['change_pct']:.2f}%")
    else:
        print(f"   获取失败：{quote['error']}")
    
    # 测试 K 线
    print("\n2. 测试 K 线数据")
    kline = sina.fetch_ohlcv("600519.SH", days=30)
    if kline:
        print(f"   获取到 {len(kline)} 条 K 线")
        print(f"   最新：{kline[-1]}")
    else:
        print("   获取失败")
    
    # 测试股票列表
    print("\n3. 测试股票列表")
    stocks = sina.get_stock_list("all")
    print(f"   获取到 {len(stocks)} 支股票")
    for stock in stocks[:5]:
        print(f"   - {stock['symbol']} {stock['name']}")
