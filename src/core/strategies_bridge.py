"""
策略橋接 — 將舊版 strategies.py 的策略自動遷移到新 Registry

這個模組在 import 時自動將 src.backtest.strategies 中的策略
註冊到 src.core.registry 中，保持向後兼容。
"""

from __future__ import annotations

from src.core.registry import registry


def _import_strategies():
    """安全導入舊版策略，避免循環依賴."""
    try:
        from src.backtest import strategies as _strategies

        return _strategies
    except Exception:
        # 直接從文件導入函數，繞過 __init__.py 的循環依賴
        import importlib.util
        import os

        path = os.path.join(os.path.dirname(__file__), "..", "backtest", "strategies.py")
        path = os.path.normpath(path)
        if os.path.exists(path):
            spec = importlib.util.spec_from_file_location("strategies_mod", path)
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                try:
                    spec.loader.exec_module(mod)
                    return mod
                except Exception:
                    pass
        return None


# ─── 策略元數據定義 ───

_STRATEGY_META: dict[str, dict] = {
    "sma_cross": {
        "label": "雙均線交叉",
        "category": "trend",
        "params": ["fast", "slow"],
        "defaults": {"fast": 10, "slow": 30},
        "param_grid": {"fast": [5, 10, 15, 20], "slow": [20, 30, 40, 50]},
    },
    "buy_and_hold": {
        "label": "買入持有",
        "category": "benchmark",
        "params": [],
        "defaults": {},
        "param_grid": {},
    },
    "rsi_signal": {
        "label": "RSI",
        "category": "oscillator",
        "params": ["period", "oversold", "overbought"],
        "defaults": {"period": 14, "oversold": 30, "overbought": 70},
        "param_grid": {"period": [10, 14, 20], "oversold": [25, 30], "overbought": [70, 75]},
    },
    "macd_cross": {
        "label": "MACD 交叉",
        "category": "trend",
        "params": ["fast", "slow", "signal"],
        "defaults": {"fast": 12, "slow": 26, "signal": 9},
        "param_grid": {"fast": [8, 12], "slow": [26], "signal": [9]},
    },
    "bollinger_signal": {
        "label": "布林帶",
        "category": "oscillator",
        "params": ["period", "std_dev"],
        "defaults": {"period": 20, "std_dev": 2.0},
        "param_grid": {"period": [15, 20, 25], "std_dev": [1.5, 2.0, 2.5]},
    },
    "ema_cross": {
        "label": "EMA 交叉",
        "category": "trend",
        "params": ["fast", "slow"],
        "defaults": {"fast": 12, "slow": 26},
        "param_grid": {"fast": [8, 12, 15], "slow": [21, 26, 34]},
    },
    "donchian_channel": {
        "label": "唐奇安通道",
        "category": "breakout",
        "params": ["period", "breakout_mode"],
        "defaults": {"period": 20, "breakout_mode": 1},
        "param_grid": {"period": [10, 20, 30], "breakout_mode": [1]},
    },
    "supertrend": {
        "label": "超級趨勢",
        "category": "trend",
        "params": ["period", "multiplier"],
        "defaults": {"period": 10, "multiplier": 3.0},
        "param_grid": {"period": [7, 10, 14], "multiplier": [2.0, 3.0, 4.0]},
    },
    "dual_thrust": {
        "label": "雙推力",
        "category": "breakout",
        "params": ["period", "k1", "k2"],
        "defaults": {"period": 4, "k1": 0.5, "k2": 0.5},
        "param_grid": {"period": [3, 4, 5], "k1": [0.4, 0.5, 0.6], "k2": [0.4, 0.5, 0.6]},
    },
    "vwap_reversion": {
        "label": "VWAP 回歸",
        "category": "mean_reversion",
        "params": ["period", "threshold"],
        "defaults": {"period": 20, "threshold": 2.0},
        "param_grid": {"period": [15, 20, 30], "threshold": [1.5, 2.0, 2.5]},
    },
    "ichimoku": {
        "label": "一目均衡表",
        "category": "trend",
        "params": ["tenkan", "kijun", "senkou_b"],
        "defaults": {"tenkan": 9, "kijun": 26, "senkou_b": 52},
        "param_grid": {"tenkan": [9], "kijun": [26], "senkou_b": [52]},
    },
    "stochastic": {
        "label": "KD 隨機指標",
        "category": "oscillator",
        "params": ["k_period", "d_period", "oversold", "overbought"],
        "defaults": {"k_period": 14, "d_period": 3, "oversold": 20.0, "overbought": 80.0},
        "param_grid": {"k_period": [9, 14], "d_period": [3], "oversold": [20], "overbought": [80]},
    },
    "williams_r": {
        "label": "威廉指標",
        "category": "oscillator",
        "params": ["period", "oversold", "overbought"],
        "defaults": {"period": 14, "oversold": -80.0, "overbought": -20.0},
        "param_grid": {"period": [10, 14, 21], "oversold": [-80], "overbought": [-20]},
    },
    "adx_trend": {
        "label": "ADX 趨勢",
        "category": "trend",
        "params": ["period", "threshold"],
        "defaults": {"period": 14, "threshold": 25.0},
        "param_grid": {"period": [10, 14, 20], "threshold": [20, 25, 30]},
    },
    "parabolic_sar": {
        "label": "拋物線 SAR",
        "category": "trend",
        "params": ["af_start", "af_step", "af_max"],
        "defaults": {"af_start": 0.02, "af_step": 0.02, "af_max": 0.20},
        "param_grid": {"af_start": [0.02], "af_step": [0.02], "af_max": [0.20]},
    },
}


# ─── 自動註冊 ───


def _register_all() -> None:
    """從舊版策略模組自動遷移到新 Registry."""
    _strategies = _import_strategies()
    if _strategies is None:
        return

    for name, meta in _STRATEGY_META.items():
        func = (
            getattr(_strategies, "_STRATEGY_FUNCS", {}).get(name) if hasattr(_strategies, "_STRATEGY_FUNCS") else None
        )
        if func is None:
            # 嘗試直接從模組取函數
            func = getattr(_strategies, name, None)
        if func:
            registry.register(
                func=func,
                name=name,
                label=meta["label"],
                category=meta["category"],
                params=meta.get("params", []),
                defaults=meta.get("defaults", {}),
                param_grid=meta.get("param_grid", {}),
            )


# 模組 import 時自動執行
_register_all()
