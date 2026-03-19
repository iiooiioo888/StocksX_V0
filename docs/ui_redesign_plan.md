# Phase 2: UI 重构设计

## 🎨 设计原则

### 1. 组件化
- 可复用 UI 组件库
- 统一样式变量
- 响应式布局

### 2. 用户体验
- 加载状态（骨架屏）
- 错误边界处理
- 平滑动画过渡

### 3. 主题系统
- 深色/浅色模式切换
- 自定义配色方案
- 无障碍访问支持

## 📐 新布局结构

```
┌─────────────────────────────────────────┐
│  Header (Logo + Nav + Theme Toggle)     │
├──────────┬──────────────────────────────┤
│ Sidebar  │   Main Content Area          │
│ (可选)   │                              │
│          │  ┌────────────────────────┐  │
│          │  │  Hero / Stats Cards    │  │
│          │  └────────────────────────┘  │
│          │  ┌────────────────────────┐  │
│          │  │  Charts / Tables       │  │
│          │  └────────────────────────┘  │
│          │  ┌────────────────────────┐  │
│          │  │  Action Buttons        │  │
│          │  └────────────────────────┘  │
└──────────┴──────────────────────────────┘
```

## 🧩 核心组件

### 1. 基础组件
- `UIButton` - 统一按钮样式
- `UICard` - 卡片容器
- `UILoading` - 加载动画
- `UIError` - 错误提示
- `UITooltip` - 工具提示

### 2. 数据展示
- `PriceCard` - 价格卡片
- `KlineChart` - K 线图组件
- `OrderBookTable` - 订单簿表格
- `PerformanceMetrics` - 绩效指标
- `TradeLogTable` - 交易记录

### 3. 表单组件
- `StrategySelector` - 策略选择器
- `ParamInput` - 参数输入
- `DateRangePicker` - 日期范围
- `SymbolSearch` - 标的搜索

## 🎨 配色方案

### 深色主题
```css
--bg-primary: #0a0e1a;
--bg-secondary: #151a2d;
--bg-card: rgba(21, 26, 45, 0.8);
--text-primary: #ffffff;
--text-secondary: #a0aec0;
--accent-blue: #3b82f6;
--accent-green: #10b981;
--accent-red: #ef4444;
--border-color: rgba(255, 255, 255, 0.1);
```

### 浅色主题
```css
--bg-primary: #f7fafc;
--bg-secondary: #ffffff;
--bg-card: rgba(255, 255, 255, 0.9);
--text-primary: #1a202c;
--text-secondary: #718096;
--accent-blue: #3182ce;
--accent-green: #38a169;
--accent-red: #e53e3e;
--border-color: rgba(0, 0, 0, 0.1);
```

## 📱 响应式断点

```css
/* Mobile */
@media (max-width: 640px) { ... }

/* Tablet */
@media (min-width: 641px) and (max-width: 1024px) { ... }

/* Desktop */
@media (min-width: 1025px) { ... }
```

## ✨ 动画效果

### 1. 淡入
```css
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
```

### 2. 脉冲
```css
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
```

### 3. 骨架屏
```css
@keyframes shimmer {
  0% { background-position: -1000px 0; }
  100% { background-position: 1000px 0; }
}
```

## 📋 实施清单

- [ ] 1. 创建 src/ui_components/ 目录
- [ ] 2. 实现基础组件（Button, Card, Loading）
- [ ] 3. 实现主题切换逻辑
- [ ] 4. 重构 app.py 使用新组件
- [ ] 5. 重构 pages/ 使用新组件
- [ ] 6. 添加响应式布局
- [ ] 7. 添加骨架屏加载状态
- [ ] 8. 优化错误处理

## 🎯 预期效果

- 页面加载感知速度提升 50%
- 代码复用率提升 60%
- 移动端体验显著改善
- 可维护性大幅提升
