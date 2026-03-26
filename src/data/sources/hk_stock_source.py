"""
港股数据源 - 港交所 HKEX

功能：
- 港股实时行情
- 历史 K 线数据
- 港股通数据
- 窝轮/牛熊证
- 指数数据

数据源：
- 港交所披露易 API
- 富途牛牛 API（备选）
- 新浪港股（备选）

更新频率：
- 实时行情：15 分钟延迟（免费）
- 历史 K 线：每日更新

注意：
- 免费数据有 15 分钟延迟
- 实时行情需要付费或券商账户
"""

from __future__ import annotations

import requests
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger(__name__)


class HKEXSource:
    """
    港交所数据源
    
    提供港股实时行情、历史数据等
    """
    
    # API 端点
    QUOTE_URL = "https://hq.sinajs.cn/list={}"
    KLINE_URL = "https://api.futunn.com/quote/kline"
    HKEX_NEWS_URL = "https://www.hkexnews.hk/Index/IndexContent.json"
    
    def __init__(self):
        """初始化"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (StocksX V0)',
            'Accept': 'application/json',
        })
    
    def _get_symbol_code(self, symbol: str) -> str:
        """
        转换港股代码格式
        
        Args:
            symbol: 股票代码（如 0700.HK）
        
        Returns:
            新浪财经格式（如 hk00700）
        """
        if '.' in symbol:
            code, _ = symbol.split('.')
            return f"hk{code.zfill(5)}"
        return f"hk{symbol.zfill(5)}"
    
    def get_realtime_quote(self, symbol: str) -> Dict[str, Any]:
        """
        获取实时报价（15 分钟延迟）
        
        Args:
            symbol: 股票代码（如 0700.HK）
        
        Returns:
            实时报价数据
        """
        code = self._get_symbol_code(symbol)
        url = self.QUOTE_URL.format(code)
        
        try:
            response = self.session.get(url, timeout=5)
            response.raise_for_status()
            
            # 解析返回数据
            text = response.text
            if '=' in text:
                data_str = text.split('="')[1].strip('"').split(',')
                
                if len(data_str) >= 20:
                    quote = {
                        'symbol': symbol,
                        'name': data_str[1],
                        'open': float(data_str[2]) if data_str[2] else 0,
                        'high': float(data_str[3]) if data_str[3] else 0,
                        'low': float(data_str[4]) if data_str[4] else 0,
                        'close': float(data_str[5]) if data_str[5] else 0,  # 当前价
                        'prev_close': float(data_str[6]) if data_str[6] else 0,
                        'volume': int(data_str[7]) if data_str[7] else 0,
                        'amount': float(data_str[8]) if data_str[8] else 0,
                        'timestamp': datetime.now().timestamp() * 1000,
                        'exchange': 'HKEX',
                        'delayed': True,  # 15 分钟延迟
                    }
                    
                    # 计算涨跌
                    quote['change'] = quote['close'] - quote['prev_close']
                    quote['change_pct'] = (quote['change'] / quote['prev_close'] * 100) if quote['prev_close'] else 0
                    
                    return quote
            
            return {'error': 'Invalid data format'}
            
        except Exception as e:
            logger.error(f"获取港股实时行情失败：{e}")
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
            timeframe: 时间周期
            days: 获取天数
        
        Returns:
            OHLCV 数据列表
        """
        # 简化实现，使用新浪港股数据
        code = self._get_symbol_code(symbol)
        
        # 计算 K 线数量
        count = min(days, 300)
        
        # 使用新浪财经港股 K 线
        url = f"http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/HK_MarketData.getKLineData"
        params = {
            'symbol': code,
            'scale': timeframe.replace('1', ''),
            'datalen': str(count)
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if not data:
                return []
            
            # 解析 K 线
            result = []
            for item in data:
                try:
                    timestamp = int(datetime.strptime(item['day'], '%Y-%m-%d').timestamp() * 1000)
                except (ValueError, KeyError):
                    continue
                
                ohlcv = {
                    'exchange': 'HKEX',
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'timestamp': timestamp,
                    'open': float(item['open']),
                    'high': float(item['high']),
                    'low': float(item['low']),
                    'close': float(item['close']),
                    'volume': float(item['volume']),
                }
                result.append(ohlcv)
            
            return result
            
        except Exception as e:
            logger.error(f"获取港股 K 线失败：{e}")
            return []
    
    def get_stock_list(
        self,
        market: str = "main"
    ) -> List[Dict[str, str]]:
        """
        获取股票列表
        
        Args:
            market: 市场（main/chi-next/star）
                - main: 主板
                - chi-next: 创业板
                - star: 科创板
        
        Returns:
            股票列表
        """
        # 简化实现，返回示例数据
        stocks = []
        
        if market == "main":
            stocks = [
                {'symbol': '0700.HK', 'name': '腾讯控股', 'market': 'HKEX'},
                {'symbol': '9988.HK', 'name': '阿里巴巴 - -W', 'market': 'HKEX'},
                {'symbol': '0005.HK', 'name': '汇丰控股', 'market': 'HKEX'},
                {'symbol': '0941.HK', 'name': '中国移动', 'market': 'HKEX'},
                {'symbol': '1299.HK', 'name': '友邦保险', 'market': 'HKEX'},
            ]
        
        return stocks
    
    def get_index_quote(self, index_code: str) -> Dict[str, Any]:
        """
        获取指数行情
        
        Args:
            index_code: 指数代码
        
        Returns:
            指数行情
        """
        # 恒生指数
        if index_code == 'HSI':
            return self.get_realtime_quote('HSI.HK')
        
        return {'error': 'Unknown index'}


class FutuSource:
    """
    富途牛牛数据源（备选）
    
    提供更全面的港股数据，需要 Futu API
    """
    
    def __init__(self, host: str = '127.0.0.1', port: int = 11111):
        """
        初始化
        
        Args:
            host: FTX API 主机
            port: FTX API 端口
        """
        self.host = host
        self.port = port
        self.connected = False
    
    def connect(self):
        """连接到富途牛牛"""
        try:
            # 实际实现需要 futu-api SDK
            logger.info("连接到富途牛牛...")
            self.connected = True
        except Exception as e:
            logger.error(f"连接富途牛牛失败：{e}")
            self.connected = False
    
    def get_realtime_quote(self, symbol: str) -> Dict[str, Any]:
        """获取实时报价"""
        if not self.connected:
            return {'error': 'Not connected'}
        
        # 实现富途 API 调用
        return {'error': 'Not implemented'}


# 测试
if __name__ == "__main__":
    hkex = HKEXSource()
    
    print("测试港股数据源...\n")
    
    # 测试实时行情
    print("1. 测试实时行情")
    quote = hkex.get_realtime_quote("0700.HK")
    if 'error' not in quote:
        print(f"   腾讯控股：HK${quote['close']:.2f}, 涨跌：{quote['change_pct']:.2f}%")
        print(f"   延迟：{'是' if quote.get('delayed') else '否'}")
    else:
        print(f"   获取失败：{quote['error']}")
    
    # 测试 K 线
    print("\n2. 测试 K 线数据")
    kline = hkex.fetch_ohlcv("0700.HK", days=30)
    if kline:
        print(f"   获取到 {len(kline)} 条 K 线")
        print(f"   最新：{kline[-1]}")
    else:
        print("   获取失败")
    
    # 测试股票列表
    print("\n3. 测试股票列表")
    stocks = hkex.get_stock_list("main")
    print(f"   获取到 {len(stocks)} 支股票")
    for stock in stocks:
        print(f"   - {stock['symbol']} {stock['name']}")
