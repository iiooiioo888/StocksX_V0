#!/usr/bin/env python3
"""
StocksX 性能監控系統

功能：
- 實時監控策略表現
- 自動警報系統
- 性能儀表板
- 日誌記錄
- 郵件/Telegram 通知

使用方式：
    python performance_monitor.py --strategies order_flow,bollinger_squeeze

作者：StocksX Team
日期：2026-03-23
"""

import os
import sys
import json
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import deque
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/performance_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('PerformanceMonitor')


class PerformanceMonitor:
    """性能監控系統"""
    
    def __init__(self, 
                 config_file: str = 'config/monitor_config.json',
                 alert_thresholds: Dict = None):
        """
        初始化監控系統
        
        Args:
            config_file: 配置文件路徑
            alert_thresholds: 警報閾值
        """
        self.config_file = config_file
        self.config = self.load_config()
        self.alert_thresholds = alert_thresholds or {
            'sharpe_min': 0.5,
            'drawdown_max': -0.2,
            'return_min': -0.1,
            'volatility_max': 0.5
        }
        self.strategy_performance = {}
        self.alerts = deque(maxlen=1000)
        self.start_time = datetime.now()
    
    def load_config(self) -> Dict:
        """加載配置文件"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 創建默認配置
            default_config = {
                'email': {
                    'enabled': False,
                    'smtp_server': 'smtp.gmail.com',
                    'smtp_port': 587,
                    'sender': 'your_email@gmail.com',
                    'password': 'your_password',
                    'recipients': ['recipient@example.com']
                },
                'telegram': {
                    'enabled': False,
                    'bot_token': 'your_bot_token',
                    'chat_id': 'your_chat_id'
                },
                'monitoring': {
                    'interval_seconds': 60,
                    'data_points': 1000,
                    'symbols': ['000001.SZ', '000002.SZ', '000300.SZ']
                }
            }
            
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2)
            
            logger.info(f"創建默認配置文件：{self.config_file}")
            return default_config
    
    def calculate_metrics(self, returns: pd.Series) -> Dict:
        """
        計算性能指標
        
        Args:
            returns: 回報序列
            
        Returns:
            指標字典
        """
        if len(returns) == 0 or returns.isna().all():
            return {
                'total_return': 0,
                'sharpe_ratio': 0,
                'sortino_ratio': 0,
                'max_drawdown': 0,
                'volatility': 0,
                'win_rate': 0,
                'profit_factor': 0
            }
        
        # 總回報
        total_return = (1 + returns).prod() - 1
        
        # Sharpe 比率
        sharpe = np.sqrt(252) * returns.mean() / returns.std() if returns.std() > 0 else 0
        
        # Sortino 比率
        downside_returns = returns[returns < 0]
        sortino = np.sqrt(252) * returns.mean() / downside_returns.std() if len(downside_returns) > 0 and downside_returns.std() > 0 else 0
        
        # 最大回撤
        cumulative = (1 + returns).cumprod()
        max_drawdown = ((cumulative - cumulative.cummax()) / cumulative.cummax()).min()
        
        # 波動率
        volatility = returns.std() * np.sqrt(252)
        
        # 勝率
        win_rate = (returns > 0).sum() / len(returns) if len(returns) > 0 else 0
        
        # 盈虧比
        avg_win = returns[returns > 0].mean() if len(returns[returns > 0]) > 0 else 0
        avg_loss = abs(returns[returns < 0].mean()) if len(returns[returns < 0]) > 0 else 0
        profit_factor = avg_win / avg_loss if avg_loss > 0 else 0
        
        return {
            'total_return': total_return,
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino,
            'max_drawdown': max_drawdown,
            'volatility': volatility,
            'win_rate': win_rate,
            'profit_factor': profit_factor
        }
    
    def check_alerts(self, strategy_name: str, metrics: Dict) -> List[Dict]:
        """
        檢查警報條件
        
        Args:
            strategy_name: 策略名稱
            metrics: 性能指標
            
        Returns:
            警報列表
        """
        alerts = []
        
        if metrics['sharpe_ratio'] < self.alert_thresholds['sharpe_min']:
            alert = {
                'timestamp': datetime.now(),
                'strategy': strategy_name,
                'type': 'LOW_SHARPE',
                'message': f"Sharpe 比率過低：{metrics['sharpe_ratio']:.3f} < {self.alert_thresholds['sharpe_min']}",
                'severity': 'WARNING'
            }
            alerts.append(alert)
            self.alerts.append(alert)
        
        if metrics['max_drawdown'] < self.alert_thresholds['drawdown_max']:
            alert = {
                'timestamp': datetime.now(),
                'strategy': strategy_name,
                'type': 'HIGH_DRAWDOWN',
                'message': f"回撤過大：{metrics['max_drawdown']*100:.2f}% < {self.alert_thresholds['drawdown_max']*100:.2f}%",
                'severity': 'CRITICAL'
            }
            alerts.append(alert)
            self.alerts.append(alert)
        
        if metrics['total_return'] < self.alert_thresholds['return_min']:
            alert = {
                'timestamp': datetime.now(),
                'strategy': strategy_name,
                'type': 'LOW_RETURN',
                'message': f"回報過低：{metrics['total_return']*100:.2f}% < {self.alert_thresholds['return_min']*100:.2f}%",
                'severity': 'WARNING'
            }
            alerts.append(alert)
            self.alerts.append(alert)
        
        if metrics['volatility'] > self.alert_thresholds['volatility_max']:
            alert = {
                'timestamp': datetime.now(),
                'strategy': strategy_name,
                'type': 'HIGH_VOLATILITY',
                'message': f"波動率過高：{metrics['volatility']*100:.2f}% > {self.alert_thresholds['volatility_max']*100:.2f}%",
                'severity': 'WARNING'
            }
            alerts.append(alert)
            self.alerts.append(alert)
        
        return alerts
    
    def send_email_alert(self, alerts: List[Dict]):
        """發送郵件警報"""
        if not self.config['email']['enabled']:
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config['email']['sender']
            msg['To'] = ', '.join(self.config['email']['recipients'])
            msg['Subject'] = f"StocksX 警報 - {len(alerts)} 個警報"
            
            body = "StocksX 性能監控警報\n\n"
            for alert in alerts:
                body += f"[{alert['severity']}] {alert['strategy']}: {alert['message']}\n"
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.config['email']['smtp_server'], self.config['email']['smtp_port'])
            server.starttls()
            server.login(self.config['email']['sender'], self.config['email']['password'])
            server.send_message(msg)
            server.quit()
            
            logger.info(f"郵件警報已發送：{len(alerts)} 個警報")
        
        except Exception as e:
            logger.error(f"發送郵件失敗：{e}")
    
    def send_telegram_alert(self, alerts: List[Dict]):
        """發送 Telegram 警報"""
        if not self.config['telegram']['enabled']:
            return
        
        try:
            import requests
            
            for alert in alerts:
                message = f"[{alert['severity']}] {alert['strategy']}: {alert['message']}"
                
                url = f"https://api.telegram.org/bot{self.config['telegram']['bot_token']}/sendMessage"
                data = {
                    'chat_id': self.config['telegram']['chat_id'],
                    'text': message
                }
                
                response = requests.post(url, json=data)
                response.raise_for_status()
            
            logger.info(f"Telegram 警報已發送：{len(alerts)} 個警報")
        
        except Exception as e:
            logger.error(f"發送 Telegram 失敗：{e}")
    
    def update_performance(self, strategy_name: str, returns: pd.Series):
        """
        更新策略性能
        
        Args:
            strategy_name: 策略名稱
            returns: 回報序列
        """
        metrics = self.calculate_metrics(returns)
        self.strategy_performance[strategy_name] = {
            'metrics': metrics,
            'last_update': datetime.now(),
            'returns': returns.tolist()[-100:]  # 保留最近 100 個數據點
        }
        
        # 檢查警報
        alerts = self.check_alerts(strategy_name, metrics)
        
        if alerts:
            logger.warning(f"策略 {strategy_name} 觸發 {len(alerts)} 個警報")
            
            # 發送警報
            self.send_email_alert(alerts)
            self.send_telegram_alert(alerts)
    
    def generate_dashboard(self, output_file: str = 'dashboard/performance_dashboard.html'):
        """
        生成性能儀表板
        
        Args:
            output_file: 輸出文件路徑
        """
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # 生成 HTML 儀表板
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>StocksX 性能監控儀表板</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; }}
        .card {{ border: 1px solid #ddd; padding: 15px; margin: 10px; border-radius: 5px; }}
        .alert {{ background: #ffeb3b; padding: 10px; margin: 5px; border-radius: 3px; }}
        .critical {{ background: #f44336; color: white; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 StocksX 性能監控儀表板</h1>
        <p>更新時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>運行時間：{datetime.now() - self.start_time}</p>
    </div>
    
    <h2>📈 策略表現總覽</h2>
    <table>
        <tr>
            <th>策略</th>
            <th>Sharpe</th>
            <th>Sortino</th>
            <th>總回報</th>
            <th>最大回撤</th>
            <th>波動率</th>
            <th>勝率</th>
            <th>盈虧比</th>
            <th>最後更新</th>
        </tr>
"""
        
        for name, data in sorted(self.strategy_performance.items(), 
                                key=lambda x: x[1]['metrics']['sharpe_ratio'], 
                                reverse=True):
            m = data['metrics']
            html += f"""
        <tr>
            <td>{name}</td>
            <td>{m['sharpe_ratio']:.3f}</td>
            <td>{m['sortino_ratio']:.3f}</td>
            <td>{m['total_return']*100:.2f}%</td>
            <td>{m['max_drawdown']*100:.2f}%</td>
            <td>{m['volatility']*100:.2f}%</td>
            <td>{m['win_rate']*100:.1f}%</td>
            <td>{m['profit_factor']:.2f}</td>
            <td>{data['last_update'].strftime('%H:%M:%S')}</td>
        </tr>
"""
        
        html += """
    </table>
    
    <h2>🚨 最新警報</h2>
"""
        
        for alert in list(self.alerts)[-20:]:
            css_class = 'critical' if alert['severity'] == 'CRITICAL' else ''
            html += f"""
    <div class="alert {css_class}">
        <strong>[{alert['severity']}]</strong> {alert['strategy']}: {alert['message']}
        <br><small>{alert['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}</small>
    </div>
"""
        
        html += """
</body>
</html>
"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        logger.info(f"儀表板已生成：{output_file}")
    
    def run_monitoring(self, strategies: List[str], interval: int = 60):
        """
        運行持續監控
        
        Args:
            strategies: 策略列表
            interval: 監控間隔（秒）
        """
        logger.info(f"開始監控 {len(strategies)} 個策略，間隔 {interval} 秒")
        
        try:
            while True:
                for strategy_name in strategies:
                    # 模擬數據更新（實際應用中從數據源獲取）
                    np.random.seed(int(time.time()) % 1000)
                    returns = pd.Series(np.random.randn(100) * 0.01)
                    
                    self.update_performance(strategy_name, returns)
                
                # 生成儀表板
                self.generate_dashboard()
                
                logger.info(f"監控週期完成，等待 {interval} 秒...")
                time.sleep(interval)
        
        except KeyboardInterrupt:
            logger.info("監控已停止")


def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description='StocksX 性能監控系統')
    parser.add_argument('--strategies', type=str, default='all', help='監控的策略')
    parser.add_argument('--interval', type=int, default=60, help='監控間隔（秒）')
    parser.add_argument('--config', type=str, default='config/monitor_config.json', help='配置文件')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("StocksX 性能監控系統")
    print("=" * 60)
    
    # 初始化監控系統
    monitor = PerformanceMonitor(config_file=args.config)
    
    # 解析策略列表
    if args.strategies == 'all':
        strategies = ['order_flow', 'bollinger_squeeze', 'dual_thrust', 'ichimoku']
    else:
        strategies = args.strategies.split(',')
    
    print(f"\n監控策略：{strategies}")
    print(f"監控間隔：{args.interval} 秒")
    
    # 開始監控
    monitor.run_monitoring(strategies, interval=args.interval)


if __name__ == '__main__':
    main()
