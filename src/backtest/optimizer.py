# 即時最優策略：參數網格搜尋（支援並行窮舉）
from __future__ import annotations

import itertools
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable

from .engine import BacktestResult, run_backtest, _run_backtest_on_rows
from . import strategies


OBJECTIVES = {
    "sharpe_ratio": ("夏普比率", True),   # 越大越好
    "total_return_pct": ("總報酬率 %", True),
    "annual_return_pct": ("年化報酬率 %", True),
    "calmar_ratio": ("Calmar 比率", True),
    "sortino_ratio": ("Sortino 比率", True),
    "max_drawdown_pct": ("最大回撤 %", False),  # 越小越好，取負值比較
}


def _param_grid_to_list(param_grid: dict[str, list[Any]]) -> list[dict[str, Any]]:
    """將 {a: [1,2], b: [3,4]} 展開為 [{a:1,b:3}, {a:1,b:4}, ...]"""
    if not param_grid:
        return [{}]
    keys = list(param_grid.keys())
    values = [param_grid[k] for k in keys]
    combos = list(itertools.product(*values))
    return [dict(zip(keys, c)) for c in combos]


def find_optimal(
    exchange_id: str,
    symbol: str,
    timeframe: str,
    since_ms: int,
    until_ms: int,
    strategy: str,
    param_grid: dict[str, list[Any]] | None = None,
    objective: str = "sharpe_ratio",
    initial_equity: float = 10000.0,
    leverage: float = 1.0,
    take_profit_pct: float | None = None,
    stop_loss_pct: float | None = None,
    exclude_outliers: bool = False,
    max_combos: int = 64,
    on_progress: Callable[
        [int, int, dict[str, Any], BacktestResult | None, BacktestResult | None, list[dict[str, Any]]],
        None,
    ] | None = None,
) -> tuple[BacktestResult | None, list[dict[str, Any]]]:
    """
    在給定策略的參數網格上做網格搜尋，依 objective 回傳最優回測結果與全部結果列表。
    on_progress(done, total, current_params, current_result, best_result_so_far, completed_results) 每完成一組即呼叫；
    completed_results 為目前已完成且成功的 [{params, result}, ...]，可畫每組參數一條線。
    """
    config = strategies.STRATEGY_CONFIG.get(strategy, {})
    grid = param_grid or config.get("param_grid") or {}
    defaults = config.get("defaults") or {}
    combos = _param_grid_to_list(grid)
    if len(combos) > max_combos:
        combos = combos[:max_combos]
    total = len(combos)

    if objective not in OBJECTIVES:
        objective = "sharpe_ratio"

    # 預先抓一次 K 線，後續所有參數組合共用，避免重複 I/O
    from src.data.crypto import CryptoDataFetcher

    fetcher = CryptoDataFetcher(exchange_id)
    try:
        rows = fetcher.get_ohlcv(
            symbol, timeframe, since_ms, until_ms, fill_gaps=True, exclude_outliers=exclude_outliers
        )
    except Exception as e:
        return None, [{"params": {}, "error": str(e)}]
    if not rows:
        return None, [{"params": {}, "error": "無 K 線資料，請先拉取數據或調整時間範圍。"}]

    results_list: list[dict[str, Any]] = []
    best_result: BacktestResult | None = None
    best_score: float = -float("inf")
    done = 0

    for params in combos:
        merged = {**defaults, **params}
        res = _run_backtest_on_rows(
            rows=rows,
            exchange_id=exchange_id,
            symbol=symbol,
            timeframe=timeframe,
            since_ms=since_ms,
            until_ms=until_ms,
            strategy=strategy,
            strategy_params=merged,
            initial_equity=initial_equity,
            leverage=leverage,
            take_profit_pct=take_profit_pct,
            stop_loss_pct=stop_loss_pct,
        )
        done += 1
        if res.error:
            results_list.append({"params": merged, "error": res.error})
            if on_progress:
                on_progress(done, total, merged, res, best_result, results_list)
            continue
        score = res.metrics.get(objective)
        if score is None:
            if on_progress:
                on_progress(done, total, merged, res, best_result, results_list)
            continue
        compare_score = -score if objective == "max_drawdown_pct" else score
        results_list.append({
            "params": merged,
            "result": res,
            "metrics": res.metrics,
            "score": res.metrics.get(objective),
        })
        if compare_score > best_score:
            best_score = compare_score
            best_result = res
        if on_progress:
            on_progress(done, total, merged, res, best_result, results_list)

    return best_result, results_list


# 全窮舉最優：策略 × K線週期 × 參數 一併搜尋（不截斷參數組合）
DEFAULT_STRATEGIES_GLOBAL = ["sma_cross", "rsi_signal", "macd_cross", "bollinger_signal", "buy_and_hold"]
DEFAULT_TIMEFRAMES_GLOBAL = ["1m", "5m", "15m", "1h", "4h", "1d"]


def _run_single_backtest_worker(args: tuple) -> tuple[str, str, dict[str, Any], BacktestResult]:
    """
    單次回測 worker，供 ThreadPoolExecutor 並行呼叫。
    參數: (exchange_id, symbol, since_ms, until_ms, strategy, timeframe, merged_params,
           initial_equity, leverage, take_profit_pct, stop_loss_pct, exclude_outliers)
    回傳: (strategy, timeframe, params, BacktestResult)
    """
    (
        exchange_id,
        symbol,
        since_ms,
        until_ms,
        strategy,
        timeframe,
        merged_params,
        initial_equity,
        leverage,
        take_profit_pct,
        stop_loss_pct,
        exclude_outliers,
    ) = args
    from .engine import run_backtest
    res = run_backtest(
        exchange_id=exchange_id,
        symbol=symbol,
        timeframe=timeframe,
        since_ms=since_ms,
        until_ms=until_ms,
        strategy=strategy,
        strategy_params=merged_params,
        initial_equity=initial_equity,
        leverage=leverage,
        take_profit_pct=take_profit_pct,
        stop_loss_pct=stop_loss_pct,
        exclude_outliers=exclude_outliers,
    )
    return (strategy, timeframe, merged_params, res)


def _build_full_grid(
    strategies_list: list[str],
    timeframes: list[str],
    max_combos_per_strategy: int = 999,
) -> list[tuple[str, str, dict[str, Any]]]:
    """產生 (strategy, timeframe, merged_params) 的完整窮舉清單。"""
    grid = []
    for strategy in strategies_list:
        config = strategies.STRATEGY_CONFIG.get(strategy, {})
        defaults = config.get("defaults") or {}
        param_grid = config.get("param_grid") or {}
        combos = _param_grid_to_list(param_grid)
        if len(combos) > max_combos_per_strategy:
            combos = combos[:max_combos_per_strategy]
        for timeframe in timeframes:
            for params in combos:
                merged = {**defaults, **params}
                grid.append((strategy, timeframe, merged))
    return grid


def _best_params_from_results(best_result: BacktestResult | None, results_list: list[dict[str, Any]]) -> dict[str, Any]:
    """從 results_list 中找出對應 best_result 的 params。"""
    if not best_result:
        return {}
    for item in results_list:
        if item.get("result") is best_result:
            return item.get("params", {})
    return {}


def find_optimal_global(
    exchange_id: str,
    symbol: str,
    since_ms: int,
    until_ms: int,
    strategies: list[str] | None = None,
    timeframes: list[str] | None = None,
    objective: str = "sharpe_ratio",
    initial_equity: float = 10000.0,
    leverage: float = 1.0,
    take_profit_pct: float | None = None,
    stop_loss_pct: float | None = None,
    exclude_outliers: bool = False,
    max_combos_per_strategy: int = 999,
    use_async: bool = True,
    max_workers: int | None = None,
    on_global_progress: Callable[[str, str, int, int, BacktestResult | None, dict], None] | None = None,
) -> tuple[BacktestResult | None, str, str, dict[str, Any], list[dict[str, Any]]]:
    """
    在「策略 × K線週期 × 參數」上做全域搜尋，回傳全局最優。
    use_async=True 時以 ProcessPoolExecutor 並行窮舉，加快計算。
    回傳: (best_result, best_strategy, best_timeframe, best_params, results_by_combo).
    """
    strategies_list = strategies or DEFAULT_STRATEGIES_GLOBAL
    timeframes = timeframes or DEFAULT_TIMEFRAMES_GLOBAL
    if objective not in OBJECTIVES:
        objective = "sharpe_ratio"

    full_grid = _build_full_grid(strategies_list, timeframes, max_combos_per_strategy)
    total_tasks = len(full_grid)
    if total_tasks == 0:
        return None, "", "", {}, []

    # 組裝 worker 參數：(exchange_id, symbol, since_ms, until_ms, strategy, timeframe, merged_params,
    #                 initial_equity, leverage, take_profit_pct, stop_loss_pct, exclude_outliers)
    task_args = [
        (exchange_id, symbol, since_ms, until_ms, s, tf, params, initial_equity, leverage, take_profit_pct, stop_loss_pct, exclude_outliers)
        for (s, tf, params) in full_grid
    ]

    if use_async and total_tasks > 1:
        workers = max_workers or min(32, (os.cpu_count() or 4))
        workers = min(workers, total_tasks)
        # 每個 (strategy, timeframe) 的當地最優，用 (s, tf) 為 key
        best_per_combo: dict[tuple[str, str], tuple[float, dict, BacktestResult]] = {}
        global_best_result: BacktestResult | None = None
        global_best_strategy = ""
        global_best_timeframe = ""
        global_best_params: dict[str, Any] = {}
        global_best_score = -float("inf")
        done = 0

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(_run_single_backtest_worker, arg): arg for arg in task_args}
            for future in as_completed(futures):
                done += 1
                try:
                    strategy, timeframe, params, res = future.result()
                except Exception:
                    continue
                if res.error:
                    continue
                score = res.metrics.get(objective)
                if score is None:
                    continue
                compare_score = -score if objective == "max_drawdown_pct" else score
                key = (strategy, timeframe)
                if key not in best_per_combo or compare_score > best_per_combo[key][0]:
                    best_per_combo[key] = (compare_score, params, res)
                if compare_score > global_best_score:
                    global_best_score = compare_score
                    global_best_result = res
                    global_best_strategy = strategy
                    global_best_timeframe = timeframe
                    global_best_params = params
                if on_global_progress and done % max(1, total_tasks // 20) == 0:
                    try:
                        on_global_progress(strategy, timeframe, done, total_tasks, global_best_result, global_best_params)
                    except Exception:
                        pass
        if on_global_progress:
            try:
                on_global_progress(global_best_strategy, global_best_timeframe, total_tasks, total_tasks, global_best_result, global_best_params)
            except Exception:
                pass
        results_by_combo = [
            {"strategy": s, "timeframe": tf, "params": p, "result": r, "score": r.metrics.get(objective)}
            for (s, tf), (_, p, r) in best_per_combo.items()
        ]
        return global_best_result, global_best_strategy, global_best_timeframe, global_best_params, results_by_combo

    # 同步路徑（沿用原邏輯）
    results_by_combo = []
    global_best_result = None
    global_best_strategy = ""
    global_best_timeframe = ""
    global_best_params = {}
    global_best_score = -float("inf")
    total_combos = len(strategies_list) * len(timeframes)
    done_combos = 0

    for strategy in strategies_list:
        for timeframe in timeframes:
            best_result, results_list = find_optimal(
                exchange_id=exchange_id,
                symbol=symbol,
                timeframe=timeframe,
                since_ms=since_ms,
                until_ms=until_ms,
                strategy=strategy,
                param_grid=None,
                objective=objective,
                initial_equity=initial_equity,
                leverage=leverage,
                take_profit_pct=take_profit_pct,
                stop_loss_pct=stop_loss_pct,
                exclude_outliers=exclude_outliers,
                max_combos=max_combos_per_strategy,
                on_progress=None,
            )
            done_combos += 1
            best_params = _best_params_from_results(best_result, results_list)
            score = best_result.metrics.get(objective) if best_result else None
            if score is not None:
                compare_score = -score if objective == "max_drawdown_pct" else score
                results_by_combo.append({
                    "strategy": strategy,
                    "timeframe": timeframe,
                    "params": best_params,
                    "result": best_result,
                    "score": score,
                })
                if compare_score > global_best_score:
                    global_best_score = compare_score
                    global_best_result = best_result
                    global_best_strategy = strategy
                    global_best_timeframe = timeframe
                    global_best_params = best_params
            if on_global_progress:
                try:
                    on_global_progress(strategy, timeframe, done_combos, total_combos, global_best_result, global_best_params)
                except Exception:
                    pass

    return global_best_result, global_best_strategy, global_best_timeframe, global_best_params, results_by_combo
