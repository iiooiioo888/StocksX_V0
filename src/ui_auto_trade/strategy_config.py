"""
策略配置 UI
============
圖形化配置自動交易策略參數
"""

import streamlit as st
import json
import time
from typing import Dict, Optional
from src.auth.user_db import UserDB


def render_strategy_configurator(user_id: int):
    """
    渲染策略配置器
    
    包含：
    - 交易所設定
    - 策略選擇
    - 參數配置
    - 風險設定
    - 配置預覽
    """
    db = UserDB()
    
    st.markdown("### 🤖 策略配置")
    
    # 表單開始
    with st.form("strategy_config_form"):
        st.markdown("#### 1️⃣ 交易所設定")
        
        ex_col1, ex_col2 = st.columns(2)
        
        with ex_col1:
            exchange_id = st.selectbox(
                "交易所",
                options=["binance", "okx", "bybit", "gateio"],
                index=0,
                help="選擇要連接的交易所"
            )
            
            use_sandbox = st.toggle("🧪 使用測試網絡", value=True)
        
        with ex_col2:
            api_key = st.text_input("API Key", type="password", placeholder="輸入 API Key")
            api_secret = st.text_input("API Secret", type="password", placeholder="輸入 API Secret")
        
        st.divider()
        
        # 策略訂閱
        st.markdown("#### 2️⃣ 策略訂閱")
        
        num_subscriptions = st.slider("訂閱數量", min_value=1, max_value=10, value=1)
        
        subscriptions = []
        
        for i in range(num_subscriptions):
            st.markdown(f"**訂閱 #{i+1}**")
            
            sub_col1, sub_col2, sub_col3, sub_col4 = st.columns(4)
            
            with sub_col1:
                symbol = st.text_input(
                    "交易對",
                    placeholder="BTC/USDT:USDT",
                    value="BTC/USDT:USDT" if i == 0 else "",
                    key=f"symbol_{i}"
                )
            
            with sub_col2:
                strategy = st.selectbox(
                    "策略",
                    options=[
                        "sma_cross", "macd_cross", "rsi_signal", "bollinger_signal",
                        "ema_cross", "supertrend", "donchian_channel", "stochastic",
                        "williams_r", "adx_trend", "parabolic_sar", "vwap_reversion",
                        "ichimoku", "dual_thrust", "buy_and_hold"
                    ],
                    index=0,
                    key=f"strategy_{i}"
                )
            
            with sub_col3:
                timeframe = st.selectbox(
                    "時間框架",
                    options=["1m", "5m", "15m", "1h", "4h", "1d"],
                    index=3,
                    key=f"timeframe_{i}"
                )
            
            with sub_col4:
                enabled = st.checkbox("啟用", value=True, key=f"enabled_{i}")
            
            # 策略參數
            with st.expander(f"⚙️ {strategy} 參數設定"):
                params = render_strategy_params(strategy, i)
            
            if enabled and symbol:
                subscriptions.append({
                    "symbol": symbol,
                    "strategy": strategy,
                    "params": params,
                    "timeframe": timeframe,
                })
            
            if i < num_subscriptions - 1:
                st.divider()
        
        st.divider()
        
        # 風險管理
        st.markdown("#### 3️⃣ 風險管理")
        
        risk_col1, risk_col2, risk_col3 = st.columns(3)
        
        with risk_col1:
            risk_per_trade = st.slider(
                "每筆風險 (%)",
                min_value=0.5,
                max_value=5.0,
                value=2.0,
                step=0.5,
                help="每筆交易願意承擔的風險比例"
            ) / 100
            
            stop_loss_pct = st.slider(
                "停損 (%)",
                min_value=1.0,
                max_value=10.0,
                value=2.0,
                step=0.5,
            )
        
        with risk_col2:
            take_profit_pct = st.slider(
                "停利 (%)",
                min_value=2.0,
                max_value=20.0,
                value=4.0,
                step=1.0,
            )
            
            max_open_positions = st.slider(
                "最大持倉數",
                min_value=1,
                max_value=10,
                value=3,
            )
        
        with risk_col3:
            leverage = st.slider(
                "槓桿倍數",
                min_value=1.0,
                max_value=20.0,
                value=1.0,
                step=1.0,
            )
            
            max_daily_loss_pct = st.slider(
                "每日最大虧損 (%)",
                min_value=3.0,
                max_value=15.0,
                value=5.0,
                step=1.0,
            )
        
        # 進階選項
        with st.expander("⚙️ 進階風險設定"):
            adv_col1, adv_col2 = st.columns(2)
            
            with adv_col1:
                position_sizing_method = st.selectbox(
                    "倉位計算方法",
                    options=["fixed_fraction", "kelly", "fixed_amount"],
                    index=0,
                )
                
                trailing_stop = st.toggle("移動停損", value=False)
                
                if trailing_stop:
                    trailing_stop_pct = st.slider(
                        "移動停損 (%)",
                        min_value=0.5,
                        max_value=5.0,
                        value=1.5,
                        step=0.5,
                    )
                else:
                    trailing_stop_pct = 0
            
            with adv_col2:
                max_drawdown_pct = st.slider(
                    "最大回撤 (%)",
                    min_value=5.0,
                    max_value=30.0,
                    value=10.0,
                    step=1.0,
                )
                
                close_on_stop = st.toggle(
                    "任務結束時平倉",
                    value=True,
                    help="自動交易停止時自動平掉所有持倉"
                )
        
        st.divider()
        
        # 資金設定
        st.markdown("#### 4️⃣ 資金設定")
        
        initial_equity = st.number_input(
            "初始資金 (USDT)",
            min_value=100.0,
            value=10000.0,
            step=100.0,
        )
        
        # 表單提交
        st.divider()
        
        submit_col1, submit_col2 = st.columns([3, 1])
        
        with submit_col1:
            submitted = st.form_submit_button("💾 儲存策略配置", type="primary", use_container_width=True)
        
        with submit_col2:
            launched = st.form_submit_button("▶️ 立即啟動", type="secondary", use_container_width=True)
        
        if submitted:
            if not api_key or not api_secret:
                st.error("❌ 請輸入 API Key 和 API Secret")
            elif not subscriptions:
                st.error("❌ 請至少添加一個策略訂閱")
            else:
                # 建立完整配置
                config = {
                    "exchange": {
                        "exchange_id": exchange_id,
                        "api_key": api_key,
                        "api_secret": api_secret,
                        "sandbox": use_sandbox,
                    },
                    "risk_management": {
                        "risk_per_trade": risk_per_trade,
                        "stop_loss_pct": stop_loss_pct,
                        "take_profit_pct": take_profit_pct,
                        "max_open_positions": max_open_positions,
                        "leverage": leverage,
                        "max_daily_loss_pct": max_daily_loss_pct,
                        "position_sizing_method": position_sizing_method,
                        "trailing_stop": trailing_stop,
                        "trailing_stop_pct": trailing_stop_pct,
                        "max_drawdown_pct": max_drawdown_pct,
                    },
                    "subscriptions": subscriptions,
                    "initial_equity": initial_equity,
                    "close_on_stop": close_on_stop,
                }
                
                # 儲存到數據庫
                strategy_id = db.save_auto_strategy(user_id, config)
                
                st.success(f"✅ 策略配置已儲存！ID: {strategy_id}")
                time.sleep(1)
                st.rerun()
        
        if launched:
            if not api_key or not api_secret:
                st.error("❌ 請先輸入 API 金鑰")
            elif not subscriptions:
                st.error("❌ 請至少添加一個策略訂閱")
            else:
                config = {
                    "exchange": {
                        "exchange_id": exchange_id,
                        "api_key": api_key,
                        "api_secret": api_secret,
                        "sandbox": use_sandbox,
                    },
                    "risk_management": {
                        "risk_per_trade": risk_per_trade,
                        "stop_loss_pct": stop_loss_pct,
                        "take_profit_pct": take_profit_pct,
                        "max_open_positions": max_open_positions,
                        "leverage": leverage,
                        "max_daily_loss_pct": max_daily_loss_pct,
                        "position_sizing_method": position_sizing_method,
                        "trailing_stop": trailing_stop,
                        "trailing_stop_pct": trailing_stop_pct,
                        "max_drawdown_pct": max_drawdown_pct,
                    },
                    "subscriptions": subscriptions,
                    "initial_equity": initial_equity,
                    "close_on_stop": close_on_stop,
                }
                
                strategy_id = db.save_auto_strategy(user_id, config)
                
                # 啟動 Celery 任務
                from src.trading.worker import execute_auto_trade
                result = execute_auto_trade.delay(
                    user_id=user_id,
                    strategy_id=strategy_id,
                    duration_minutes=60,
                )
                
                st.success(f"🚀 已啟動自動交易！任務 ID: {result.id}")


def render_strategy_params(strategy: str, index: int) -> dict:
    """
    渲染策略參數設定
    
    Args:
        strategy: 策略名稱
        index: 索引（用於生成唯一 key）
        
    Returns:
        參數字典
    """
    params = {}
    
    col1, col2, col3 = st.columns(3)
    
    if strategy == "sma_cross":
        with col1:
            params["fast"] = st.number_input("快線週期", min_value=1, max_value=100, value=5, key=f"p_fast_{index}")
        with col2:
            params["slow"] = st.number_input("慢線週期", min_value=1, max_value=200, value=20, key=f"p_slow_{index}")
    
    elif strategy == "macd_cross":
        with col1:
            params["fast_period"] = st.number_input("快線", min_value=1, max_value=50, value=12, key=f"p_macd_f_{index}")
        with col2:
            params["slow_period"] = st.number_input("慢線", min_value=1, max_value=100, value=26, key=f"p_macd_s_{index}")
        with col3:
            params["signal_period"] = st.number_input("信號線", min_value=1, max_value=50, value=9, key=f"p_macd_sig_{index}")
    
    elif strategy == "rsi_signal":
        with col1:
            params["period"] = st.number_input("週期", min_value=5, max_value=50, value=14, key=f"p_rsi_p_{index}")
        with col2:
            params["oversold"] = st.number_input("超賣線", min_value=10, max_value=40, value=30, key=f"p_rsi_os_{index}")
        with col3:
            params["overbought"] = st.number_input("超買線", min_value=60, max_value=90, value=70, key=f"p_rsi_ob_{index}")
    
    elif strategy == "bollinger_signal":
        with col1:
            params["period"] = st.number_input("週期", min_value=10, max_value=50, value=20, key=f"p_bb_p_{index}")
        with col2:
            params["std_dev"] = st.number_input("標準差", min_value=1.0, max_value=3.0, value=2.0, step=0.1, key=f"p_bb_s_{index}")
    
    elif strategy == "ema_cross":
        with col1:
            params["fast_period"] = st.number_input("快線", min_value=1, max_value=100, value=9, key=f"p_ema_f_{index}")
        with col2:
            params["slow_period"] = st.number_input("慢線", min_value=1, max_value=200, value=21, key=f"p_ema_s_{index}")
    
    elif strategy == "supertrend":
        with col1:
            params["period"] = st.number_input("週期", min_value=5, max_value=50, value=10, key=f"p_st_p_{index}")
        with col2:
            params["multiplier"] = st.number_input("倍數", min_value=1.0, max_value=5.0, value=3.0, step=0.1, key=f"p_st_m_{index}")
    
    elif strategy == "stochastic":
        with col1:
            params["k_period"] = st.number_input("K 週期", min_value=5, max_value=50, value=14, key=f"p_kd_k_{index}")
        with col2:
            params["d_period"] = st.number_input("D 週期", min_value=5, max_value=50, value=3, key=f"p_kd_d_{index}")
        with col3:
            params["oversold"] = st.number_input("超賣", min_value=10, max_value=40, value=20, key=f"p_kd_os_{index}")
    
    elif strategy == "williams_r":
        with col1:
            params["period"] = st.number_input("週期", min_value=5, max_value=50, value=14, key=f"p_wr_p_{index}")
        with col2:
            params["oversold"] = st.number_input("超賣", min_value=-90, max_value=-50, value=-80, key=f"p_wr_os_{index}")
        with col3:
            params["overbought"] = st.number_input("超買", min_value=-50, max_value=-10, value=-20, key=f"p_wr_ob_{index}")
    
    elif strategy == "adx_trend":
        with col1:
            params["period"] = st.number_input("週期", min_value=5, max_value=50, value=14, key=f"p_adx_p_{index}")
        with col2:
            params["threshold"] = st.number_input("閾值", min_value=10, max_value=50, value=25, key=f"p_adx_t_{index}")
    
    elif strategy == "parabolic_sar":
        with col1:
            params["af_start"] = st.number_input("初始 AF", min_value=0.01, max_value=0.1, value=0.02, step=0.01, key=f"p_sar_s_{index}")
        with col2:
            params["af_step"] = st.number_input("AF 步長", min_value=0.01, max_value=0.1, value=0.02, step=0.01, key=f"p_sar_i_{index}")
        with col3:
            params["af_max"] = st.number_input("最大 AF", min_value=0.1, max_value=0.5, value=0.2, step=0.05, key=f"p_sar_m_{index}")
    
    elif strategy == "donchian_channel":
        with col1:
            params["period"] = st.number_input("週期", min_value=10, max_value=100, value=20, key=f"p_dc_p_{index}")
    
    elif strategy == "dual_thrust":
        with col1:
            params["period"] = st.number_input("週期", min_value=5, max_value=50, value=5, key=f"p_dt_p_{index}")
        with col2:
            params["k1"] = st.number_input("K1 (多頭)", min_value=0.1, max_value=2.0, value=0.5, step=0.1, key=f"p_dt_k1_{index}")
        with col3:
            params["k2"] = st.number_input("K2 (空頭)", min_value=0.1, max_value=2.0, value=0.5, step=0.1, key=f"p_dt_k2_{index}")
    
    elif strategy == "vwap_reversion":
        with col1:
            params["period"] = st.number_input("週期", min_value=10, max_value=100, value=20, key=f"p_vwap_p_{index}")
        with col2:
            params["threshold"] = st.number_input("閾值", min_value=0.5, max_value=5.0, value=2.0, step=0.1, key=f"p_vwap_t_{index}")
    
    elif strategy == "ichimoku":
        with col1:
            params["tenkan_period"] = st.number_input("轉換線", min_value=5, max_value=50, value=9, key=f"p_ichi_t_{index}")
        with col2:
            params["kijun_period"] = st.number_input("基準線", min_value=10, max_value=100, value=26, key=f"p_ichi_k_{index}")
        with col3:
            params["senkou_b_period"] = st.number_input("先行線 B", min_value=20, max_value=200, value=52, key=f"p_ichi_s_{index}")
    
    else:
        st.info(f"ℹ️ 策略 '{strategy}' 使用預設參數")
    
    return params
