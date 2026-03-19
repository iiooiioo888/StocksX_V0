# Phase 1: 性能提升实施计划

## 🔍 当前瓶颈分析

### 1. 数据获取层
- ❌ 串行请求多个交易所数据
- ❌ 缓存策略简单（仅内存，无 Redis）
- ❌ 无批量请求优化
- ❌ 超时重试机制缺失

### 2. 图表渲染
- ❌ 大数据量无降采样
- ❌ 所有指标同时渲染
- ❌ 无懒加载机制

### 3. 数据库
- ❌ SQLite 无连接池
- ❌ 查询无索引优化
- ❌ 频繁 I/O 操作

## 🚀 优化方案

### 1. Redis 缓存层
```python
# 新增 src/cache/redis_cache.py
- Ticker 数据：TTL=5 秒
- K 线数据：TTL=5 分钟
- 订单簿：TTL=1 秒
- 用户数据：TTL=30 秒
```

### 2. 并行数据获取
```python
# 使用 asyncio + aiohttp
async def fetch_all_symbols(symbols):
    tasks = [fetch_symbol(s) for s in symbols]
    return await asyncio.gather(*tasks)
```

### 3. 图表降采样
```python
# LTTB 算法降采样
def downsample_ohlcv(df, max_points=500):
    if len(df) > max_points:
        return lttb_downsample(df, max_points)
    return df
```

### 4. 数据库优化
```python
# 添加索引
CREATE INDEX idx_trade_log_user_id ON trade_log(user_id);
CREATE INDEX idx_trade_log_symbol ON trade_log(symbol);
CREATE INDEX idx_backtest_history_date ON backtest_history(backtest_date);
```

## 📝 实施步骤

- [ ] 1. 添加 Redis 依赖到 requirements.txt
- [ ] 2. 创建 src/cache/redis_cache.py
- [ ] 3. 重构 src/data/service.py 使用 Redis
- [ ] 4. 添加 asyncio 并行获取
- [ ] 5. 实现图表降采样
- [ ] 6. 添加数据库索引迁移脚本

## 📊 预期提升

| 指标 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| Ticker 加载 | 2-3 秒 | 200-500ms | 5-10x |
| K 线加载 | 5-8 秒 | 1-2 秒 | 4-5x |
| 图表渲染 | 3-5 秒 | 500ms-1s | 5-6x |
| 并发请求 | 1 个/秒 | 10 个/秒 | 10x |
