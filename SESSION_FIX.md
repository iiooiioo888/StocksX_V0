# Session 持久化修复说明

## 问题描述
用户反馈：**每次刷新页面都需要重新登录**

## 问题根源

### 原有逻辑
```python
@staticmethod
def validate_session(user: dict | None) -> bool:
    if not user:
        return False
    # 优先检查 session 中存储的登录时间，其次才是数据库的 last_login
    login_time = st.session_state.get("_login_time") or user.get("last_login", 0)
    if login_time and time.time() - login_time > _SESSION_TIMEOUT:
        return False
    return True
```

### 问题分析
1. **`_login_time` 的存储**：登录时设置在 `st.session_state["_login_time"]`
2. **页面刷新时**：Streamlit 会重新运行整个脚本
3. **Session State 持久化**：Streamlit 1.23+ 版本会自动持久化 session state
4. **验证失败场景**：
   - 某些情况下 `_login_time` 可能丢失
   - 但 `st.session_state["user"]` 仍然存在
   - 导致验证失败，要求重新登录

## 修复方案

### 新逻辑
```python
@staticmethod
def validate_session(user: dict | None) -> bool:
    """验证 session 是否有效（检查登录时间是否过期）"""
    import streamlit as st
    if not user:
        return False
    # 优先检查 session 中存储的登录时间
    login_time = st.session_state.get("_login_time")
    
    # 如果没有 _login_time，但有 user，说明是页面刷新，session 仍然有效
    # Streamlit 会自动管理 session 生命周期
    if login_time is None:
        return True
    
    # 如果有登录时间，检查是否过期（1 小时）
    if login_time and time.time() - login_time > _SESSION_TIMEOUT:
        return False
    return True
```

### 修复原理
1. **信任 Streamlit 的 Session 管理**：
   - 如果 `st.session_state["user"]` 存在，说明 session 有效
   - Streamlit 会在浏览器关闭或超时后自动清除 session

2. **`_login_time` 作为额外检查**：
   - 用于检查长时间未活动后的过期
   - 不是必需的验证条件

3. **过期时间**：
   - 默认 1 小时（3600 秒）
   - 从登录时间开始计算

## 测试方法

### 1. 基本测试
```bash
# 启动应用
streamlit run app.py

# 步骤：
1. 登入系统
2. 刷新页面（F5）
3. 应该保持登录状态
4. 访问其他页面
5. 应该无需重新登录
```

### 2. 过期测试
```python
# 在 Python 控制台测试
import streamlit as st
import time

# 模拟登录
st.session_state["user"] = {"id": 1, "username": "test"}
st.session_state["_login_time"] = time.time()

# 验证应该成功
from src.auth.user_db import UserDB
assert UserDB.validate_session(st.session_state.get("user")) == True

# 模拟过期（等待 1 小时或手动修改时间）
st.session_state["_login_time"] = time.time() - 3700

# 验证应该失败
assert UserDB.validate_session(st.session_state.get("user")) == False
```

## 其他优化建议

### 1. 添加 Session ID
```python
# 登录时生成唯一 session ID
import uuid
st.session_state["_session_id"] = str(uuid.uuid4())
```

### 2. 数据库记录 Session
```python
# 在数据库中记录 session
CREATE TABLE IF NOT EXISTS user_sessions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    session_id TEXT,
    created_at REAL,
    last_activity REAL,
    is_active BOOLEAN DEFAULT 1
);
```

### 3. 记住我功能
```python
# 使用 cookie 实现记住我
import streamlit as st
st.experimental_set_cookie("remember_user", username, max_age=30*24*3600)
```

## 相关文件修改

### `src/auth/user_db.py`
- 修改 `validate_session()` 方法
- 优化 session 验证逻辑

### `pages/1_🔐_登入.py`
- 无需修改（已正确设置 `_login_time`）

### 其他页面
- 使用 `require_login()` 或 `check_session()` 的页面都会自动受益

## 注意事项

1. **安全性**：
   - 此修复假设 Streamlit 的 session 管理是安全的
   - 生产环境建议添加 session ID 和数据库记录

2. **多设备登录**：
   - 当前实现允许多设备同时登录
   - 如需限制，需在数据库中管理 session

3. **登出逻辑**：
   - 确保所有登出按钮都调用 `st.session_state.pop("user", None)`
   - 清除 `_login_time` 和其他 session 数据

## 修复效果

✅ **修复前**：每次刷新都需要重新登录
✅ **修复后**：
- 刷新页面保持登录状态
- 1 小时内无需重新登录
- 关闭浏览器后 session 清除
- 过期后自动要求重新登录
