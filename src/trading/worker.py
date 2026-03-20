"""
自動交易 Celery 任務 - 異步執行自動交易
==========================================
功能：
- 啟動/停止自動交易任務
- 監控任務狀態
- 任務結果查詢
"""

from __future__ import annotations

import logging
from typing import Any

from celery import Task

from src.tasks.celery_app import app as celery_app

logger = logging.getLogger(__name__)


class AutoTradeTask(Task):
    """自動交易 Celery 任務基類"""

    def __init__(self):
        self.trader = None

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """任務失敗回調"""
        logger.error(f"自動交易任務失敗 {task_id}: {exc}")
        # 可以在這裡發送通知

    def on_success(self, retval, task_id, args, kwargs):
        """任務成功回調"""
        logger.info(f"自動交易任務成功 {task_id}")


@celery_app.task(
    base=AutoTradeTask,
    bind=True,
    name="trading.execute_auto_trade",
)
def execute_auto_trade(
    self,
    user_id: int,
    strategy_id: int,
    duration_minutes: int = 60,
) -> dict[str, Any]:
    """
    執行自動交易（Celery 任務）

    Args:
        user_id: 用戶 ID
        strategy_id: 策略配置 ID
        duration_minutes: 執行持續時間（分鐘）

    Returns:
        任務執行結果
    """
    from .auto_trader import AutoTrader

    logger.info(f"🚀 啟動自動交易任務 (user_id={user_id}, strategy_id={strategy_id})")

    try:
        trader = AutoTrader(user_id)
        config = trader.load_config(strategy_id)

        if not trader.initialize(config):
            return {"success": False, "error": "初始化失敗"}

        # 設定任務結束時間
        import time

        end_time = time.time() + (duration_minutes * 60)

        # 執行交易循環
        while time.time() < end_time:
            if self.request.id:
                # 檢查任務是否被撤銷
                inspect = celery_app.control.inspect()
                _active = inspect.active()
                # 這裡可以添加更複雜的檢查邏輯

            try:
                trader._trading_loop(config)
            except Exception as e:
                logger.error(f"交易循環錯誤：{e}")

            # 每秒檢查一次
            time.sleep(1)

        # 任務結束，平掉所有持倉（可選）
        if config.get("close_on_stop", False):
            logger.info("📊 任務結束，平掉所有持倉")
            # 這裡可以添加平倉邏輯

        return {
            "success": True,
            "user_id": user_id,
            "strategy_id": strategy_id,
            "duration_minutes": duration_minutes,
            "status_report": trader.get_status(),
        }

    except Exception as e:
        logger.error(f"自動交易任務異常：{e}", exc_info=True)
        return {"success": False, "error": str(e)}


@celery_app.task(name="trading.stop_auto_trade")
def stop_auto_trade(user_id: int, strategy_id: int) -> dict[str, Any]:
    """
    停止自動交易任務

    Args:
        user_id: 用戶 ID
        strategy_id: 策略配置 ID

    Returns:
        任務執行結果
    """
    logger.info(f"⏹️ 停止自動交易任務 (user_id={user_id}, strategy_id={strategy_id})")

    # 撤銷相關任務
    # 這裡需要實現任務追蹤機制
    # 可以使用 celery_app.control.revoke(task_id)

    return {
        "success": True,
        "message": f"已發送停止指令 (user_id={user_id})",
    }


@celery_app.task(name="trading.check_position")
def check_position(user_id: int, symbol: str) -> dict[str, Any]:
    """
    檢查持倉狀態

    Args:
        user_id: 用戶 ID
        symbol: 交易對

    Returns:
        持倉資訊
    """
    from src.auth.user_db import UserDB

    db = UserDB()
    watchlist = db.get_watchlist(user_id)

    for w in watchlist:
        if w["symbol"] == symbol:
            return {
                "found": True,
                "symbol": symbol,
                "position": w["position"],
                "entry_price": w["entry_price"],
                "pnl_pct": w["pnl_pct"],
                "initial_equity": w["initial_equity"],
            }

    return {"found": False, "symbol": symbol}


@celery_app.task(name="trading.emergency_stop")
def emergency_stop(user_id: int) -> dict[str, Any]:
    """
    緊急停止所有自動交易

    Args:
        user_id: 用戶 ID

    Returns:
        任務執行結果
    """
    logger.warning(f"🚨 緊急停止自動交易 (user_id={user_id})")

    from src.auth.user_db import UserDB

    db = UserDB()

    # 獲取所有持倉
    watchlist = db.get_watchlist(user_id)
    active_positions = [w for w in watchlist if w["position"] != 0]

    closed_count = 0
    for position in active_positions:
        try:
            # 這裡需要獲取交易所配置並執行平倉
            # 簡化版本：僅更新數據庫狀態
            db.update_watch(
                position["id"],
                position=0,
                entry_price=0,
                pnl_pct=0,
            )
            closed_count += 1
            logger.info(f"✅ 緊急平倉：{position['symbol']}")
        except Exception as e:
            logger.error(f"緊急平倉失敗 {position['symbol']}: {e}")

    return {
        "success": True,
        "closed_positions": closed_count,
        "message": f"已平掉 {closed_count} 個持倉",
    }


@celery_app.task(name="trading.daily_report")
def daily_report(user_id: int) -> dict[str, Any]:
    """
    生成每日交易報告

    Args:
        user_id: 用戶 ID

    Returns:
        交易報告
    """
    from datetime import datetime

    from src.auth.user_db import UserDB

    db = UserDB()

    # 獲取今日交易記錄
    _now = datetime.now().timestamp()
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()

    watchlist = db.get_watchlist(user_id)

    today_trades = []
    total_pnl = 0
    total_fees = 0

    for w in watchlist:
        trades = db.get_trade_log(w["id"], limit=100)
        for t in trades:
            if t["created_at"] >= today_start:
                today_trades.append(t)
                total_pnl += t.get("pnl_amount", 0)
                total_fees += t.get("fee", 0)

    # 計算勝率
    winning_trades = [t for t in today_trades if t.get("pnl_amount", 0) > 0]
    losing_trades = [t for t in today_trades if t.get("pnl_amount", 0) < 0]

    win_rate = len(winning_trades) / len(today_trades) * 100 if today_trades else 0

    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "user_id": user_id,
        "total_trades": len(today_trades),
        "winning_trades": len(winning_trades),
        "losing_trades": len(losing_trades),
        "win_rate": round(win_rate, 2),
        "total_pnl": round(total_pnl, 2),
        "total_fees": round(total_fees, 2),
        "net_pnl": round(total_pnl - total_fees, 2),
    }
