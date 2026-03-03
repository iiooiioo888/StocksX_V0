# 回測相關 Celery 任務
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from celery import Task

from src.backtest.engine import BacktestResult, run_backtest as sync_run_backtest
from src.backtest.optimizer import optimize_params
from src.data.crypto import CryptoDataFetcher
from src.data.traditional import TradDataFetcher


class BacktestTask(Task):
    """回測任務基類"""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """任務失敗時的回調"""
        from src.utils.logger import get_logger
        logger = get_logger('stocksx.celery')
        logger.error(
            f"Backtest task {task_id} failed",
            exc_info=True,
            extra={'task_id': task_id, 'args': args, 'kwargs': kwargs}
        )


def run_backtest(
    symbol: str,
    exchange: str,
    timeframe: str,
    strategy: str,
    params: Dict[str, Any],
    start_date: str,
    end_date: str,
    initial_equity: float = 10000,
    leverage: float = 1.0,
    fee_rate: float = 0.001,
    user_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    執行回測任務（非同步）
    
    Args:
        symbol: 交易對（如 BTC/USDT:USDT 或 AAPL）
        exchange: 交易所（如 binance, yfinance）
        timeframe: 時間框架（如 1h, 1d）
        strategy: 策略名稱
        params: 策略參數
        start_date: 開始日期（YYYY-MM-DD）
        end_date: 結束日期（YYYY-MM-DD）
        initial_equity: 初始資金
        leverage: 槓桿
        fee_rate: 手續費率
        user_id: 用戶 ID（可選）
    
    Returns:
        回測結果字典
    
    Example:
        ```python
        result = run_backtest.delay(
            symbol="BTC/USDT:USDT",
            exchange="binance",
            timeframe="1h",
            strategy="sma_cross",
            params={"fast_period": 5, "slow_period": 20},
            start_date="2024-01-01",
            end_date="2024-03-01",
            user_id=1
        )
        ```
    """
    from src.utils.logger import log_backtest, get_logger
    logger = get_logger('stocksx.celery')
    
    # 記錄任務開始
    log_backtest(
        logger,
        symbol=symbol,
        strategy=strategy,
        timeframe=timeframe,
        user_id=user_id,
        status='started',
        start_date=start_date,
        end_date=end_date
    )
    
    start_time = time.time()
    
    try:
        # 執行回測
        result = sync_run_backtest(
            symbol=symbol,
            exchange=exchange,
            timeframe=timeframe,
            strategy=strategy,
            params=params,
            start_date=start_date,
            end_date=end_date,
            initial_equity=initial_equity,
            leverage=leverage,
            fee_rate=fee_rate,
        )
        
        duration_ms = (time.time() - start_time) * 1000
        
        # 記錄任務完成
        log_backtest(
            logger,
            symbol=symbol,
            strategy=strategy,
            timeframe=timeframe,
            metrics=result.metrics if not result.error else None,
            duration_ms=duration_ms,
            user_id=user_id,
            status='completed' if not result.error else 'failed'
        )
        
        # 轉換為可序列化的字典
        return {
            'success': result.error is None,
            'error': result.error,
            'metrics': result.metrics,
            'trades': result.trades,
            'equity_curve': result.equity_curve,
            'duration_ms': duration_ms,
            'config': {
                'symbol': symbol,
                'exchange': exchange,
                'timeframe': timeframe,
                'strategy': strategy,
                'params': params,
                'initial_equity': initial_equity,
                'leverage': leverage,
            }
        }
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_backtest(
            logger,
            symbol=symbol,
            strategy=strategy,
            timeframe=timeframe,
            duration_ms=duration_ms,
            user_id=user_id,
            status='failed',
            error=str(e)
        )
        raise


def run_param_optimizer(
    symbol: str,
    exchange: str,
    timeframe: str,
    strategy: str,
    param_grid: Dict[str, List[Any]],
    start_date: str,
    end_date: str,
    initial_equity: float = 10000,
    leverage: float = 1.0,
    fee_rate: float = 0.001,
    metric: str = 'total_return_pct',
    n_best: int = 10,
    user_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    執行參數優化任務（非同步）
    
    Args:
        symbol: 交易對
        exchange: 交易所
        timeframe: 時間框架
        strategy: 策略名稱
        param_grid: 參數網格（如 {"fast_period": [5, 10, 20], "slow_period": [20, 50, 100]}）
        start_date: 開始日期
        end_date: 結束日期
        initial_equity: 初始資金
        leverage: 槓桿
        fee_rate: 手續費率
        metric: 優化指標
        n_best: 回傳前 N 個最佳結果
        user_id: 用戶 ID
    
    Returns:
        優化結果字典
    
    Example:
        ```python
        result = run_param_optimizer.delay(
            symbol="BTC/USDT:USDT",
            exchange="binance",
            timeframe="1h",
            strategy="sma_cross",
            param_grid={"fast_period": [5, 10, 20], "slow_period": [20, 50, 100]},
            start_date="2024-01-01",
            end_date="2024-03-01",
            metric="sharpe",
            n_best=5
        )
        ```
    """
    from src.utils.logger import get_logger, log_backtest
    logger = get_logger('stocksx.celery')
    
    log_backtest(
        logger,
        symbol=symbol,
        strategy=f"{strategy}_optimizer",
        timeframe=timeframe,
        user_id=user_id,
        status='started',
        param_grid=param_grid,
        metric=metric
    )
    
    start_time = time.time()
    
    try:
        # 執行參數優化
        results = optimize_params(
            symbol=symbol,
            exchange=exchange,
            timeframe=timeframe,
            strategy=strategy,
            param_grid=param_grid,
            start_date=start_date,
            end_date=end_date,
            initial_equity=initial_equity,
            leverage=leverage,
            fee_rate=fee_rate,
            metric=metric,
            n_best=n_best,
        )
        
        duration_ms = (time.time() - start_time) * 1000
        
        log_backtest(
            logger,
            symbol=symbol,
            strategy=f"{strategy}_optimizer",
            timeframe=timeframe,
            duration_ms=duration_ms,
            user_id=user_id,
            status='completed',
            total_runs=len(results)
        )
        
        return {
            'success': True,
            'results': results,
            'best_params': results[0] if results else None,
            'total_runs': len(results),
            'duration_ms': duration_ms,
            'config': {
                'symbol': symbol,
                'strategy': strategy,
                'param_grid': param_grid,
                'metric': metric,
            }
        }
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_backtest(
            logger,
            symbol=symbol,
            strategy=f"{strategy}_optimizer",
            timeframe=timeframe,
            duration_ms=duration_ms,
            user_id=user_id,
            status='failed',
            error=str(e)
        )
        raise


def run_walk_forward_analysis(
    symbol: str,
    exchange: str,
    timeframe: str,
    strategy: str,
    params: Dict[str, Any],
    train_periods: int = 3,
    test_ratio: float = 0.3,
    start_date: str = None,
    end_date: str = None,
    initial_equity: float = 10000,
    user_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    執行向前分析（Walk-Forward Analysis）
    
    Args:
        symbol: 交易對
        exchange: 交易所
        timeframe: 時間框架
        strategy: 策略名稱
        params: 策略參數
        train_periods: 訓練期數量
        test_ratio: 測試集比例
        start_date: 開始日期
        end_date: 結束日期
        initial_equity: 初始資金
        user_id: 用戶 ID
    
    Returns:
        向前分析結果
    """
    from src.utils.logger import get_logger, log_backtest
    from src.backtest.walk_forward import walk_forward_analysis
    logger = get_logger('stocksx.celery')
    
    log_backtest(
        logger,
        symbol=symbol,
        strategy=f"{strategy}_walk_forward",
        timeframe=timeframe,
        user_id=user_id,
        status='started',
        train_periods=train_periods,
        test_ratio=test_ratio
    )
    
    start_time = time.time()
    
    try:
        results = walk_forward_analysis(
            symbol=symbol,
            exchange=exchange,
            timeframe=timeframe,
            strategy=strategy,
            params=params,
            train_periods=train_periods,
            test_ratio=test_ratio,
            start_date=start_date,
            end_date=end_date,
            initial_equity=initial_equity,
        )
        
        duration_ms = (time.time() - start_time) * 1000
        
        log_backtest(
            logger,
            symbol=symbol,
            strategy=f"{strategy}_walk_forward",
            timeframe=timeframe,
            duration_ms=duration_ms,
            user_id=user_id,
            status='completed',
            periods=len(results)
        )
        
        return {
            'success': True,
            'results': results,
            'duration_ms': duration_ms,
        }
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_backtest(
            logger,
            symbol=symbol,
            strategy=f"{strategy}_walk_forward",
            timeframe=timeframe,
            duration_ms=duration_ms,
            user_id=user_id,
            status='failed',
            error=str(e)
        )
        raise
