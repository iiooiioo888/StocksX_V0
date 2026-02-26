# Walk-Forward Analysis — 防止過擬合的樣本外驗證框架
from __future__ import annotations

from typing import Any

from .engine import _run_backtest_on_rows, BacktestResult
from . import strategies as _strat_mod
from .optimizer import _param_grid_to_list


def walk_forward_analysis(
    rows: list[dict[str, Any]],
    exchange_id: str,
    symbol: str,
    timeframe: str,
    since_ms: int,
    until_ms: int,
    strategy: str,
    n_splits: int = 5,
    train_ratio: float = 0.7,
    objective: str = "sharpe_ratio",
    initial_equity: float = 10000.0,
    leverage: float = 1.0,
    fee_rate: float = 0.0,
    slippage: float = 0.0,
) -> dict[str, Any]:
    """
    Walk-Forward Analysis：
    1. 將數據切成 n_splits 段
    2. 每段用前 train_ratio 做 in-sample 優化，後面做 out-of-sample 驗證
    3. 彙總 out-of-sample 結果，避免過擬合
    """
    if not rows or len(rows) < 50:
        return {"error": "數據不足（至少 50 根 K 線）", "splits": []}

    n = len(rows)
    split_size = n // n_splits
    if split_size < 20:
        return {"error": f"每段太短（{split_size} 根），請增加數據量或減少分段數", "splits": []}

    config = _strat_mod.STRATEGY_CONFIG.get(strategy, {})
    param_grid = config.get("param_grid", {})
    defaults = config.get("defaults", {})
    combos = _param_grid_to_list(param_grid)

    results = []
    oos_equities = []

    for fold in range(n_splits):
        start_idx = fold * split_size
        end_idx = min(start_idx + split_size, n)
        fold_rows = rows[start_idx:end_idx]

        train_end = int(len(fold_rows) * train_ratio)
        train_rows = fold_rows[:train_end]
        test_rows = fold_rows[train_end:]

        if len(train_rows) < 10 or len(test_rows) < 5:
            continue

        train_since = train_rows[0]["timestamp"]
        train_until = train_rows[-1]["timestamp"]
        test_since = test_rows[0]["timestamp"]
        test_until = test_rows[-1]["timestamp"]

        # In-sample: 找最優參數
        best_score = -float("inf")
        best_params = dict(defaults)

        for params in combos:
            merged = {**defaults, **params}
            res = _run_backtest_on_rows(
                rows=train_rows, exchange_id=exchange_id, symbol=symbol, timeframe=timeframe,
                since_ms=train_since, until_ms=train_until, strategy=strategy, strategy_params=merged,
                initial_equity=initial_equity, leverage=leverage,
                take_profit_pct=None, stop_loss_pct=None, fee_rate=fee_rate, slippage=slippage,
            )
            if res.error:
                continue
            score = res.metrics.get(objective, 0)
            if score is not None and score > best_score:
                best_score = score
                best_params = merged

        # Out-of-sample: 用最優參數測試
        oos_res = _run_backtest_on_rows(
            rows=test_rows, exchange_id=exchange_id, symbol=symbol, timeframe=timeframe,
            since_ms=test_since, until_ms=test_until, strategy=strategy, strategy_params=best_params,
            initial_equity=initial_equity, leverage=leverage,
            take_profit_pct=None, stop_loss_pct=None, fee_rate=fee_rate, slippage=slippage,
        )

        oos_metrics = oos_res.metrics if not oos_res.error else {}
        results.append({
            "fold": fold + 1,
            "train_bars": len(train_rows),
            "test_bars": len(test_rows),
            "best_params": best_params,
            "in_sample_score": round(best_score, 4) if best_score > -float("inf") else None,
            "oos_return_pct": oos_metrics.get("total_return_pct", 0),
            "oos_sharpe": oos_metrics.get("sharpe_ratio", 0),
            "oos_drawdown_pct": oos_metrics.get("max_drawdown_pct", 0),
            "oos_trades": oos_metrics.get("num_trades", 0),
        })

        if oos_res.equity_curve:
            oos_equities.extend(oos_res.equity_curve)

    if not results:
        return {"error": "所有分段均失敗", "splits": []}

    avg_oos_return = sum(r["oos_return_pct"] for r in results) / len(results)
    avg_oos_sharpe = sum(r["oos_sharpe"] for r in results) / len(results)
    avg_oos_dd = sum(r["oos_drawdown_pct"] for r in results) / len(results)

    return {
        "strategy": strategy,
        "n_splits": n_splits,
        "train_ratio": train_ratio,
        "splits": results,
        "avg_oos_return_pct": round(avg_oos_return, 2),
        "avg_oos_sharpe": round(avg_oos_sharpe, 2),
        "avg_oos_drawdown_pct": round(avg_oos_dd, 2),
        "oos_equity_curve": oos_equities,
    }
