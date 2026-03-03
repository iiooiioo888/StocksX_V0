# 策略參數管理模組
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import streamlit as st
from src.auth import UserDB
from src.config import STRATEGY_LABELS


# ════════════════════════════════════════════════════════════
# 策略參數定義
# ════════════════════════════════════════════════════════════

STRATEGY_PARAMS = {
    "sma_cross": {
        "name": "雙均線交叉",
        "params": {
            "fast_period": {"type": "int", "default": 5, "min": 2, "max": 50, "step": 1},
            "slow_period": {"type": "int", "default": 20, "min": 10, "max": 200, "step": 5},
        }
    },
    "ema_cross": {
        "name": "EMA 交叉",
        "params": {
            "fast_period": {"type": "int", "default": 12, "min": 2, "max": 50, "step": 1},
            "slow_period": {"type": "int", "default": 26, "min": 10, "max": 200, "step": 5},
        }
    },
    "rsi_signal": {
        "name": "RSI 指標",
        "params": {
            "period": {"type": "int", "default": 14, "min": 5, "max": 30, "step": 1},
            "oversold": {"type": "float", "default": 30.0, "min": 10.0, "max": 40.0, "step": 1.0},
            "overbought": {"type": "float", "default": 70.0, "min": 60.0, "max": 90.0, "step": 1.0},
        }
    },
    "macd_cross": {
        "name": "MACD 交叉",
        "params": {
            "fast_period": {"type": "int", "default": 12, "min": 5, "max": 20, "step": 1},
            "slow_period": {"type": "int", "default": 26, "min": 20, "max": 50, "step": 1},
            "signal_period": {"type": "int", "default": 9, "min": 5, "max": 15, "step": 1},
        }
    },
    "bollinger_signal": {
        "name": "布林帶",
        "params": {
            "period": {"type": "int", "default": 20, "min": 10, "max": 50, "step": 1},
            "std_dev": {"type": "float", "default": 2.0, "min": 1.0, "max": 3.0, "step": 0.1},
        }
    },
    "supertrend": {
        "name": "超級趨勢",
        "params": {
            "period": {"type": "int", "default": 10, "min": 5, "max": 20, "step": 1},
            "multiplier": {"type": "float", "default": 3.0, "min": 1.0, "max": 5.0, "step": 0.5},
        }
    },
    "donchian_channel": {
        "name": "唐奇安通道",
        "params": {
            "period": {"type": "int", "default": 20, "min": 10, "max": 100, "step": 1},
        }
    },
    "dual_thrust": {
        "name": "雙推力",
        "params": {
            "lookback": {"type": "int", "default": 4, "min": 1, "max": 20, "step": 1},
            "k1": {"type": "float", "default": 0.5, "min": 0.1, "max": 2.0, "step": 0.1},
            "k2": {"type": "float", "default": 0.5, "min": 0.1, "max": 2.0, "step": 0.1},
        }
    },
    "vwap_reversion": {
        "name": "VWAP 回歸",
        "params": {
            "period": {"type": "int", "default": 20, "min": 10, "max": 50, "step": 1},
            "threshold": {"type": "float", "default": 2.0, "min": 0.5, "max": 5.0, "step": 0.5},
        }
    },
    "ichimoku": {
        "name": "一目均衡表",
        "params": {
            "tenkan_period": {"type": "int", "default": 9, "min": 5, "max": 20, "step": 1},
            "kijun_period": {"type": "int", "default": 26, "min": 15, "max": 50, "step": 1},
            "senkou_b_period": {"type": "int", "default": 52, "min": 30, "max": 100, "step": 1},
        }
    },
    "stochastic": {
        "name": "KD 隨機指標",
        "params": {
            "k_period": {"type": "int", "default": 14, "min": 5, "max": 30, "step": 1},
            "d_period": {"type": "int", "default": 3, "min": 1, "max": 10, "step": 1},
            "oversold": {"type": "float", "default": 20.0, "min": 10.0, "max": 30.0, "step": 5.0},
            "overbought": {"type": "float", "default": 80.0, "min": 70.0, "max": 90.0, "step": 5.0},
        }
    },
    "williams_r": {
        "name": "威廉指標",
        "params": {
            "period": {"type": "int", "default": 14, "min": 5, "max": 30, "step": 1},
            "oversold": {"type": "float", "default": -80.0, "min": -90.0, "max": -70.0, "step": 5.0},
            "overbought": {"type": "float", "default": -20.0, "min": -30.0, "max": -10.0, "step": 5.0},
        }
    },
    "adx_trend": {
        "name": "ADX 趨勢",
        "params": {
            "period": {"type": "int", "default": 14, "min": 7, "max": 30, "step": 1},
            "threshold": {"type": "float", "default": 25.0, "min": 15.0, "max": 40.0, "step": 5.0},
        }
    },
    "parabolic_sar": {
        "name": "拋物線 SAR",
        "params": {
            "acceleration": {"type": "float", "default": 0.02, "min": 0.01, "max": 0.1, "step": 0.01},
            "maximum": {"type": "float", "default": 0.2, "min": 0.1, "max": 0.5, "step": 0.05},
        }
    },
    "buy_and_hold": {
        "name": "買入持有",
        "params": {}
    },
}


# ════════════════════════════════════════════════════════════
# 參數輸入渲染
# ════════════════════════════════════════════════════════════

def render_strategy_params(
    strategy: str,
    current_params: Optional[Dict[str, Any]] = None,
    key_prefix: str = "strategy_params"
) -> Dict[str, Any]:
    """
    渲染策略參數輸入
    
    Args:
        strategy: 策略名稱
        current_params: 當前參數值
        key_prefix: 按鍵前綴
    
    Returns:
        參數字典
    """
    if strategy not in STRATEGY_PARAMS:
        st.warning(f"未知策略：{strategy}")
        return {}
    
    strategy_info = STRATEGY_PARAMS[strategy]
    st.markdown(f"##### ⚙️ {strategy_info['name']} 參數設定")
    
    params = {}
    
    if not strategy_info['params']:
        st.info("此策略無需額外參數")
        return {}
    
    # 以網格形式顯示參數
    param_items = list(strategy_info['params'].items())
    cols = st.columns(min(3, len(param_items)))
    
    for idx, (param_name, param_config) in enumerate(param_items):
        col = cols[idx % 3]
        
        # 取得當前值或預設值
        default_value = current_params.get(param_name, param_config["default"]) if current_params else param_config["default"]
        
        # 根據類型渲染輸入
        if param_config["type"] == "int":
            params[param_name] = col.number_input(
                param_name.replace("_", " ").title(),
                min_value=param_config["min"],
                max_value=param_config["max"],
                value=int(default_value),
                step=param_config.get("step", 1),
                key=f"{key_prefix}_{param_name}"
            )
        elif param_config["type"] == "float":
            params[param_name] = col.number_input(
                param_name.replace("_", " ").title(),
                min_value=param_config["min"],
                max_value=param_config["max"],
                value=float(default_value),
                step=param_config.get("step", 0.1),
                key=f"{key_prefix}_{param_name}"
            )
    
    return params


def render_all_strategy_params(
    selected_strategies: List[str],
    params_dict: Optional[Dict[str, Dict[str, Any]]] = None,
    key_prefix: str = "all_strategy_params"
) -> Dict[str, Dict[str, Any]]:
    """
    渲染多個策略的參數
    
    Args:
        selected_strategies: 選中的策略列表
        params_dict: 各策略的參數
        key_prefix: 按鍵前綴
    
    Returns:
        {策略名：參數字典}
    """
    all_params = {}
    
    for strategy in selected_strategies:
        with st.expander(f"⚙️ {STRATEGY_LABELS.get(strategy, strategy)}", expanded=False):
            current_params = params_dict.get(strategy, {}) if params_dict else None
            params = render_strategy_params(strategy, current_params, f"{key_prefix}_{strategy}")
            all_params[strategy] = params
    
    return all_params


# ════════════════════════════════════════════════════════════
# 參數預設管理
# ════════════════════════════════════════════════════════════

def save_params_preset(
    user_id: int,
    strategy: str,
    preset_name: str,
    params: Dict[str, Any]
) -> bool:
    """
    儲存參數預設
    
    Args:
        user_id: 用戶 ID
        strategy: 策略名稱
        preset_name: 預設名稱
        params: 參數字典
    
    Returns:
        是否成功
    """
    db = UserDB()
    config = {
        "strategy": strategy,
        "params": params,
        "created_at": __import__('time').time()
    }
    result = db.save_preset(user_id, preset_name, config)
    return isinstance(result, int) and result > 0


def load_params_preset(user_id: int, preset_id: int) -> Optional[Dict[str, Any]]:
    """
    載入參數預設
    
    Args:
        user_id: 用戶 ID
        preset_id: 預設 ID
    
    Returns:
        參數字典
    """
    db = UserDB()
    presets = db.get_presets(user_id)
    
    for preset in presets:
        if preset["id"] == preset_id:
            config = preset.get("config", {})
            if isinstance(config, str):
                config = json.loads(config)
            return config.get("params", {})
    
    return None


def delete_params_preset(user_id: int, preset_id: int) -> bool:
    """
    刪除參數預設
    
    Args:
        user_id: 用戶 ID
        preset_id: 預設 ID
    
    Returns:
        是否成功
    """
    db = UserDB()
    try:
        db.delete_preset(preset_id)
        return True
    except Exception:
        return False


def render_preset_manager(
    user_id: int,
    strategy: str,
    current_params: Dict[str, Any],
    key_prefix: str = "preset"
) -> Optional[Dict[str, Any]]:
    """
    渲染預設管理器
    
    Args:
        user_id: 用戶 ID
        strategy: 策略名稱
        current_params: 當前參數
        key_prefix: 按鍵前綴
    
    Returns:
        選擇的參數或 None
    """
    db = UserDB()
    presets = db.get_presets(user_id)
    
    # 過濾出當前策略的預設
    strategy_presets = []
    for preset in presets:
        config = preset.get("config", {})
        if isinstance(config, str):
            config = json.loads(config)
        if config.get("strategy") == strategy:
            strategy_presets.append(preset)
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        # 載入預設
        if strategy_presets:
            preset_options = {preset["name"]: preset["id"] for preset in strategy_presets}
            selected_name = st.selectbox(
                "載入預設",
                options=list(preset_options.keys()),
                key=f"{key_prefix}_load_select"
            )
            
            if st.button("📥 載入", key=f"{key_prefix}_load_btn", use_container_width=True):
                preset_id = preset_options[selected_name]
                params = load_params_preset(user_id, preset_id)
                if params:
                    # 將參數寫入 session state
                    for param_name, value in params.items():
                        st.session_state[f"strategy_params_{param_name}"] = value
                    st.success(f"已載入預設：{selected_name}")
                    return params
        else:
            st.info("尚無預設")
    
    with col2:
        # 儲存新預設
        new_preset_name = st.text_input(
            "新預設名稱",
            placeholder=f"{strategy}_preset_1",
            key=f"{key_prefix}_new_name"
        )
        
        if st.button("💾 儲存預設", key=f"{key_prefix}_save_btn", use_container_width=True):
            if new_preset_name:
                if save_params_preset(user_id, strategy, new_preset_name, current_params):
                    st.success(f"已儲存預設：{new_preset_name}")
                    st.rerun()
            else:
                st.warning("請輸入預設名稱")
    
    with col3:
        # 刪除預設
        if strategy_presets:
            delete_name = st.selectbox(
                "刪除",
                options=list(preset_options.keys()),
                key=f"{key_prefix}_delete_select"
            )
            
            if st.button("🗑️", key=f"{key_prefix}_delete_btn", use_container_width=True):
                preset_id = preset_options[delete_name]
                if delete_params_preset(user_id, preset_id):
                    st.success(f"已刪除：{delete_name}")
                    st.rerun()
    
    return None


# ════════════════════════════════════════════════════════════
# 參數驗證
# ════════════════════════════════════════════════════════════

def validate_params(strategy: str, params: Dict[str, Any]) -> tuple[bool, str]:
    """
    驗證參數
    
    Args:
        strategy: 策略名稱
        params: 參數字典
    
    Returns:
        (是否有效，錯誤訊息)
    """
    if strategy not in STRATEGY_PARAMS:
        return False, f"未知策略：{strategy}"
    
    strategy_info = STRATEGY_PARAMS[strategy]
    
    # 檢查必要參數
    for param_name, param_config in strategy_info['params'].items():
        if param_name not in params:
            return False, f"缺少參數：{param_name}"
        
        value = params[param_name]
        
        # 檢查範圍
        if value < param_config["min"]:
            return False, f"{param_name} 不能小於 {param_config['min']}"
        if value > param_config["max"]:
            return False, f"{param_name} 不能大於 {param_config['max']}"
    
    return True, ""


# ════════════════════════════════════════════════════════════
# 參數快捷方式
# ════════════════════════════════════════════════════════════

def render_param_shortcuts(
    strategy: str,
    key_prefix: str = "shortcuts"
) -> Optional[Dict[str, Any]]:
    """
    渲染參數快捷方式
    
    Args:
        strategy: 策略名稱
        key_prefix: 按鍵前綴
    
    Returns:
        選擇的參數或 None
    """
    if strategy not in STRATEGY_PARAMS:
        return None
    
    strategy_info = STRATEGY_PARAMS[strategy]
    
    if not strategy_info['params']:
        return None
    
    st.markdown("**快捷設定**")
    
    cols = st.columns(3)
    
    # 根據策略提供快捷設定
    shortcuts = {}
    
    if strategy == "sma_cross":
        shortcuts = {
            "快速 (5/20)": {"fast_period": 5, "slow_period": 20},
            "標準 (10/50)": {"fast_period": 10, "slow_period": 50},
            "慢速 (20/100)": {"fast_period": 20, "slow_period": 100},
        }
    elif strategy == "rsi_signal":
        shortcuts = {
            "標準 (14/30/70)": {"period": 14, "oversold": 30.0, "overbought": 70.0},
            "寬鬆 (14/20/80)": {"period": 14, "oversold": 20.0, "overbought": 80.0},
            "嚴格 (14/25/75)": {"period": 14, "oversold": 25.0, "overbought": 75.0},
        }
    elif strategy == "macd_cross":
        shortcuts = {
            "標準 (12/26/9)": {"fast_period": 12, "slow_period": 26, "signal_period": 9},
            "快速 (6/13/5)": {"fast_period": 6, "slow_period": 13, "signal_period": 5},
            "慢速 (24/52/18)": {"fast_period": 24, "slow_period": 52, "signal_period": 18},
        }
    elif strategy == "bollinger_signal":
        shortcuts = {
            "標準 (20/2.0)": {"period": 20, "std_dev": 2.0},
            "寬鬆 (20/2.5)": {"period": 20, "std_dev": 2.5},
            "緊縮 (20/1.5)": {"period": 20, "std_dev": 1.5},
        }
    
    if shortcuts:
        for idx, (name, params) in enumerate(shortcuts.items()):
            if cols[idx].button(name, key=f"{key_prefix}_{name}", use_container_width=True):
                # 將參數寫入 session state
                for param_name, value in params.items():
                    st.session_state[f"strategy_params_{param_name}"] = value
                return params
    
    return None
