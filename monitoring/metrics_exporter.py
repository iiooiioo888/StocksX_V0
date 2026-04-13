#!/usr/bin/env python3
"""
StocksX Prometheus 指標導出器
提供交易系統性能指標

作者：StocksX Team
創建日期：2026-03-22
"""

from prometheus_client import start_http_server, Counter, Gauge, Histogram
import time
import random
import logging

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("metrics")

# ============ 指標定義 ============

# 交易指標
trades_total = Counter("stocksx_trades_total", "Total number of trades", ["strategy", "side", "symbol"])

trades_volume = Gauge("stocksx_trades_volume", "Trading volume", ["strategy"])

position_value = Gauge("stocksx_position_value", "Current position value", ["strategy", "symbol"])

pnl_total = Gauge("stocksx_pnl_total", "Total profit and loss", ["strategy"])

pnl_daily = Gauge("stocksx_pnl_daily", "Daily profit and loss")

# 策略指標
strategy_score = Gauge("stocksx_strategy_score", "Strategy performance score", ["strategy", "grade"])

strategy_sharpe = Gauge("stocksx_strategy_sharpe", "Strategy Sharpe ratio", ["strategy"])

strategy_drawdown = Gauge("stocksx_strategy_drawdown", "Strategy maximum drawdown", ["strategy"])

# 風險指標
risk_exposure = Gauge("stocksx_risk_exposure", "Total risk exposure")

risk_utilization = Gauge("stocksx_risk_utilization", "Risk utilization percentage")

# 系統指標
system_uptime = Gauge("stocksx_system_uptime", "System uptime in seconds")

websocket_status = Gauge("stocksx_websocket_status", "WebSocket connection status (1=connected, 0=disconnected)")

api_latency = Histogram("stocksx_api_latency_seconds", "API request latency", ["endpoint"])

# 信號指標
signals_total = Counter("stocksx_signals_total", "Total number of signals", ["strategy", "signal_type"])

signals_active = Gauge("stocksx_signals_active", "Number of active signals")


def simulate_metrics():
    """模擬指標數據（演示用）"""
    strategies = ["sma_cross", "macd_cross", "rsi", "bollinger", "trix"]
    symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"]

    start_time = time.time()

    while True:
        try:
            # 更新系統指標
            system_uptime.set(time.time() - start_time)
            websocket_status.set(1)

            # 隨機更新策略指標
            for strategy in strategies:
                # 評分
                score = random.uniform(60, 90)
                grade = "A" if score > 80 else "B" if score > 70 else "C"
                strategy_score.labels(strategy=strategy, grade=grade).set(score)

                # 夏普比率
                sharpe = random.uniform(0.5, 2.5)
                strategy_sharpe.labels(strategy=strategy).set(sharpe)

                # 回撤
                drawdown = random.uniform(5, 20)
                strategy_drawdown.labels(strategy=strategy).set(drawdown)

                # 盈虧
                pnl = random.uniform(-1000, 3000)
                pnl_total.labels(strategy=strategy).set(pnl)

                # 持倉
                for symbol in symbols[:3]:
                    if random.random() > 0.5:
                        value = random.uniform(5000, 15000)
                        position_value.labels(strategy=strategy, symbol=symbol).set(value)

            # 風險指標
            risk_exposure.set(random.uniform(50000, 80000))
            risk_utilization.set(random.uniform(40, 70))

            # 每日盈虧
            daily_pnl = random.uniform(-2000, 5000)
            pnl_daily.set(daily_pnl)

            # 信號
            signals_active.set(random.randint(5, 20))

            logger.info(f"📊 指標已更新 | Uptime: {time.time() - start_time:.0f}s | PnL: ${daily_pnl:.2f}")

            time.sleep(10)

        except Exception as e:
            logger.error(f"❌ 指標更新錯誤：{e}")
            time.sleep(5)


def main():
    """主函數"""
    logger.info("=" * 80)
    logger.info("📊 StocksX Prometheus Metrics Exporter")
    logger.info("=" * 80)

    # 啟動 HTTP 服務器（Prometheus 抓取端點）
    port = 8001
    start_http_server(port)

    logger.info("✅ 指標服務已啟動")
    logger.info(f"📡 指標端點：http://localhost:{port}/metrics")
    logger.info("📊 Grafana 配置：prometheus.yml")
    logger.info("=" * 80)

    # 開始模擬指標
    simulate_metrics()


if __name__ == "__main__":
    main()
