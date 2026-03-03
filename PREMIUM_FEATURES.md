# StocksX 收費功能方案

## 💎 會員等級

| 功能 | 免費版 | 專業版 | VIP 版 |
|------|--------|--------|-------|
| **價格** | $0/月 | $29.9/月 | $99.9/月 |
| **即時價格** | ✅ 3 個交易對 | ✅ 20 個交易對 | ✅ 無限 |
| **基本信號** | ✅ | ✅ | ✅ |
| **高級信號** | ❌ | ✅ | ✅ |
| **自動交易** | ❌ | ✅ | ✅ |
| **風險管理** | ❌ | ✅ | ✅ |
| **AI 預測** | ❌ | ❌ | ✅ |
| **套利機會** | ❌ | ❌ | ✅ |
| **優先支援** | ❌ | ❌ | ✅ |

---

## 📊 功能詳細說明

### 免費版 (Free)

**適合**: 初學者、觀望中用戶

**包含功能**:
- ✅ 即時價格監控（最多 3 個交易對）
- ✅ 基本交易信號
- ✅ 持倉監控
- ✅ 基礎績效統計
- ✅ 社群支援

**限制**:
- ❌ 無法使用自動交易
- ❌ 無法設定停損/停利
- ❌ 無高級信號
- ❌ 無 AI 預測功能

---

### 專業版 (Premium) - $29.9/月

**適合**: 活躍交易者、需要自動化功能

**包含免費版所有功能，額外增加**:

#### 🤖 自動交易
- 根據信號自動開倉/平倉
- 支援最多 20 個交易對
- 24 小時監控
- 交易日誌記錄

#### 🛡️ 風險管理
- **停損設定**: 自動平倉避免更大損失
- **停利設定**: 自動獲利了結
- **倉位控制**: 限制單一交易最大曝險
- **每日交易上限**: 防止過度交易

#### 📊 高級信號
- 多策略綜合信號
- 信心度評估
- 進出場建議
- 風險報酬比計算

#### 📈 進階分析
- 詳細績效報告
- 交易記錄匯出
- 策略回測整合
- 對比分析

---

### VIP 版 (VIP) - $99.9/月

**適合**: 專業交易者、機構用戶

**包含專業版所有功能，額外增加**:

#### 🤖 AI 預測
- 使用機器學習預測價格走勢
- 短期（1-4 小時）預測
- 中期（1-7 天）預測
- 預測準確度追蹤

#### 💰 套利機會
- 跨交易所價差監控
- 即時套利機會通知
- 預期利潤計算
- 自動執行套利（可選）

#### 👑 專屬服務
- 優先客戶支援
- 專屬客戶經理
- 客製化策略開發
- 定期市場報告

#### 🔔 即時通知
- LINE/Telegram 通知
- 電子郵件報告
- SMS 緊急通知
- 自訂通知條件

---

## 🎯 收費功能技術實作

### 1. 自動交易

**實作邏輯**:
```python
# 檢查是否啟用自動交易
if st.session_state.auto_trading_enabled and is_premium:
    # 監聽信號
    if signal['confidence'] >= min_confidence:
        # 執行交易
        execute_trade(
            symbol=symbol,
            action=signal['action'],
            amount=calculate_position_size(),
            stop_loss=stop_loss_pct,
            take_profit=take_profit_pct
        )
```

**風險控制**:
- 最大倉位限制
- 每日交易次數限制
- 單日最大虧損限制
- 異常交易偵測

---

### 2. 風險管理

**停損/停利計算**:
```python
def check_stop_loss(position, current_price, stop_loss_pct):
    entry_price = position['entry_price']
    pnl_pct = (current_price - entry_price) / entry_price * 100
    
    if position['side'] == 'long':
        if pnl_pct <= -stop_loss_pct:
            return True  # 觸發停損
    else:  # short
        if pnl_pct <= -stop_loss_pct:
            return True  # 觸發停損
    
    return False
```

**倉位計算**:
```python
def calculate_position_size(account_equity, risk_pct, stop_loss_pct):
    """根據風險百分比計算合適倉位"""
    risk_amount = account_equity * (risk_pct / 100)
    position_size = risk_amount / (stop_loss_pct / 100)
    return position_size
```

---

### 3. AI 預測（VIP）

**預測模型**:
```python
# 使用歷史數據訓練
def train_prediction_model(symbol, timeframe='1h'):
    # 取得歷史數據
    data = get_historical_data(symbol, timeframe)
    
    # 特徵工程
    features = create_features(data)
    
    # 訓練模型
    model = LSTM()  # 或 Prophet、XGBoost
    model.fit(features, target='future_price')
    
    return model

# 預測未來價格
def predict_price(model, symbol, periods=4):
    prediction = model.predict(periods=periods)
    return {
        'symbol': symbol,
        'predicted_prices': prediction,
        'confidence': calculate_confidence(prediction),
        'trend': 'bullish' if prediction[-1] > prediction[0] else 'bearish'
    }
```

---

### 4. 套利機會（VIP）

**價差監控**:
```python
def monitor_arbitrage_opportunities():
    exchanges = ['binance', 'okx', 'bybit']
    symbols = ['BTC/USDT', 'ETH/USDT']
    
    for symbol in symbols:
        prices = {}
        for exchange in exchanges:
            prices[exchange] = get_price(exchange, symbol)
        
        # 找出最大價差
        min_exchange = min(prices, key=prices.get)
        max_exchange = max(prices, key=prices.get)
        
        spread = (prices[max_exchange] - prices[min_exchange]) / prices[min_exchange] * 100
        
        # 如果價差超過閾值（考慮手續費）
        if spread > ARBITRAGE_THRESHOLD:
            send_arbitrage_alert({
                'symbol': symbol,
                'buy_exchange': min_exchange,
                'sell_exchange': max_exchange,
                'spread_pct': spread,
                'expected_profit': calculate_profit(spread)
            })
```

---

## 💳 訂閱管理

### 升級流程

1. **選擇方案**: 在設定頁面選擇專業版或 VIP 版
2. **支付**: 支援信用卡、PayPal、加密貨幣
3. **啟用**: 支付成功後立即啟用
4. **發票**: 自動發送電子郵件發票

### 取消訂閱

- 可隨時取消訂閱
- 取消後持續使用至當期結束
- 不會退還剩餘費用
- 可重新訂閱

---

## 📈 定價策略

### 早鳥優惠

**前 100 名用戶**:
- 專業版：$19.9/月（原價$29.9）
- VIP 版：$69.9/月（原價$99.9）
- 年繳額外 8 折

### 團體優惠

**5 人以上團體**:
- 專業版：8 折優惠
- VIP 版：洽詢專屬方案

### 學生優惠

**憑學生證**:
- 專業版：5 折優惠
- 需提供學生證明

---

## 🔒 權限驗證

### JWT 令牌擴充

```python
# 在 JWT 中加入用戶等級
def create_access_token(user_id, role):
    payload = {
        "sub": user_id,
        "role": role,  # "free", "premium", "vip"
        "exp": datetime.utcnow() + timedelta(days=30),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")
```

### API 端點保護

```python
@app.websocket("/ws/premium")
async def premium_websocket(
    websocket: WebSocket,
    token: str = Query(...)
):
    # 驗證令牌
    payload = verify_token(token)
    
    # 檢查用戶等級
    if payload['role'] not in ['premium', 'vip']:
        await websocket.close(code=4003, reason="Premium required")
        return
    
    # 接受連接
    await websocket.accept()
    # ... 高級功能
```

---

## 📊 營收預測

### 保守估計

| 用戶類型 | 用戶數 | 月收入 |
|----------|--------|--------|
| 免費版 | 1000 | $0 |
| 專業版 | 100 | $2,990 |
| VIP 版 | 20 | $1,998 |
| **總計** | **1120** | **$4,988/月** |

### 積極估計

| 用戶類型 | 用戶數 | 月收入 |
|----------|--------|--------|
| 免費版 | 5000 | $0 |
| 專業版 | 500 | $14,950 |
| VIP 版 | 100 | $9,990 |
| **總計** | **5600** | **$24,940/月** |

---

## 🎯 轉換策略

### 免費 → 專業版

1. **功能限制**: 讓用戶體驗到限制的痛點
2. **信號預覽**: 顯示部分高級信號（模糊處理）
3. **限時優惠**: 提供 7 天專業版免費試用
4. **成功案例**: 分享專業版用戶的獲利案例

### 專業版 → VIP 版

1. **AI 預測預覽**: 顯示簡易版 AI 預測
2. **套利通知**: 每週發送套利機會摘要
3. **專屬報告**: 提供進階市場分析
4. **升級優惠**: 提供 VIP 版 14 天免費體驗

---

## 📱 通知系統

### 通知類型

| 通知類型 | 免費版 | 專業版 | VIP 版 |
|----------|--------|--------|-------|
| 基本信號 | ✅ App | ✅ App | ✅ App + LINE |
| 高級信號 | ❌ | ✅ App | ✅ App + LINE |
| 自動交易執行 | ❌ | ✅ App | ✅ App + LINE + SMS |
| 風險警示 | ❌ | ✅ App | ✅ App + LINE + SMS |
| AI 預測 | ❌ | ❌ | ✅ App + LINE + Email |
| 套利機會 | ❌ | ❌ | ✅ App + LINE + Email |

---

## ⚠️ 注意事項

### 合規性

1. **投資建議免責**: 所有信號僅供參考，不構成投資建議
2. **風險揭露**: 明確告知交易風險
3. **數據準確性**: 不保證數據 100% 準確
4. **服務可用性**: 不保證 100% 無中斷

### 退款政策

- 訂閱後 7 天內可全額退款
- 超過 7 天按比例退還
- 違反使用條款不予退費

### 隱私保護

- 嚴格保護用戶數據
- 不向第三方出售個資
- 符合 GDPR 規範

---

**更新日期**: 2024-03-03
**版本**: v1.0
**狀態**: 生產就緒
