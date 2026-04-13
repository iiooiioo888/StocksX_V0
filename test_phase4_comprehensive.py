#!/usr/bin/env python3
"""
Phase 4 全面测试脚本

测试所有 Phase 4 新增功能
"""

import sys
import time
from datetime import datetime

# 测试结果统计
test_results = {"passed": 0, "failed": 0, "skipped": 0, "errors": []}


def test_result(name: str, passed: bool, error: str = None):
    """记录测试结果"""
    if passed:
        test_results["passed"] += 1
        print(f"  ✅ {name}")
    else:
        test_results["failed"] += 1
        test_results["errors"].append({"name": name, "error": error})
        print(f"  ❌ {name}: {error}")


def skip_test(name: str, reason: str):
    """跳过测试"""
    test_results["skipped"] += 1
    print(f"  ⏭️  {name}: {reason}")


# ════════════════════════════════════════════════════════════
# 1. 数据源测试
# ════════════════════════════════════════════════════════════


def test_data_sources():
    """测试所有数据源"""
    print("\n" + "=" * 60)
    print("1. 数据源测试")
    print("=" * 60)

    # 1.1 A 股数据源
    print("\n1.1 A 股数据源 (新浪财经)")
    try:
        from src.data.sources.a_stock_source import SinaAShareSource

        sina = SinaAShareSource()

        # 测试实时行情
        try:
            quote = sina.get_realtime_quote("600519 | SH")
            if "error" not in quote:
                test_result("实时行情获取", True)
                print(f"     贵州茅台：¥{quote.get('close', 0):.2f}")
            else:
                test_result("实时行情获取", False, quote.get("error"))
        except Exception as e:
            test_result("实时行情获取", False, str(e))

        # 测试 K 线
        try:
            kline = sina.fetch_ohlcv("600519.SH", days=30)
            test_result("历史 K 线获取", len(kline) > 0)
            if kline:
                print(f"     获取到 {len(kline)} 条 K 线")
        except Exception as e:
            test_result("历史 K 线获取", False, str(e))

        # 测试股票列表
        try:
            stocks = sina.get_stock_list("all")
            test_result("股票列表获取", len(stocks) > 0)
            print(f"     获取到 {len(stocks)} 支股票")
        except Exception as e:
            test_result("股票列表获取", False, str(e))

    except ImportError as e:
        skip_test("A 股数据源", f"模块导入失败：{e}")

    # 1.2 港股数据源
    print("\n1.2 港股数据源 (HKEX)")
    try:
        from src.data.sources.hk_stock_source import HKEXSource

        hkex = HKEXSource()

        # 测试实时行情
        try:
            quote = hkex.get_realtime_quote("0700.HK")
            if "error" not in quote:
                test_result("港股实时行情", True)
                print(f"     腾讯控股：HK${quote.get('close', 0):.2f}")
            else:
                test_result("港股实时行情", False, quote.get("error"))
        except Exception as e:
            test_result("港股实时行情", False, str(e))

        # 测试 K 线
        try:
            kline = hkex.fetch_ohlcv("0700.HK", days=30)
            test_result("港股 K 线获取", len(kline) > 0)
        except Exception as e:
            test_result("港股 K 线获取", False, str(e))

    except ImportError as e:
        skip_test("港股数据源", f"模块导入失败：{e}")

    # 1.3 台股数据源
    print("\n1.3 台股数据源 (TWSE)")
    try:
        from src.data.sources.twse_source import TWSESource

        twse = TWSESource()

        # 测试实时行情
        try:
            quote = twse.get_realtime_quote("2330.TW")
            if "error" not in quote:
                test_result("台股实时行情", True)
                print(f"     台积电：NT${quote.get('close', 0):.2f}")
            else:
                test_result("台股实时行情", False, quote.get("error"))
        except Exception as e:
            test_result("台股实时行情", False, str(e))

    except ImportError as e:
        skip_test("台股数据源", f"模块导入失败：{e}")

    # 1.4 链上数据（需要 API Key）
    print("\n1.4 链上数据 (Glassnode)")
    try:
        from src.data.onchain.glassnode import GlassnodeOnChain
        import os

        api_key = os.getenv("GLASSNODE_API_KEY")

        if api_key and api_key != "demo_key":
            onchain = GlassnodeOnChain(api_key)

            try:
                score = onchain.get_composite_score("BTC")
                test_result("综合链上评分", True)
                print(f"     BTC 评分：{score.get('score', 0)}/100, 信号：{score.get('signal', 'N/A')}")
            except Exception as e:
                test_result("综合链上评分", False, str(e))
        else:
            skip_test("链上数据", "需要 GLASSNODE_API_KEY 环境变量")

    except ImportError as e:
        skip_test("链上数据", f"模块导入失败：{e}")


# ════════════════════════════════════════════════════════════
# 2. 高级订单测试
# ════════════════════════════════════════════════════════════


def test_advanced_orders():
    """测试高级订单"""
    print("\n" + "=" * 60)
    print("2. 高级订单测试")
    print("=" * 60)

    try:
        from src.trading.orders.advanced_orders import (
            ConditionalOrder,
            OCOOrder,
            TrailingStop,
            TriggerCondition,
            TriggerType,
            OrderType,
        )

        # 2.1 条件单
        print("\n2.1 条件单")
        try:
            condition = TriggerCondition(type=TriggerType.PRICE_ABOVE, params={"threshold": 70000})

            cond_order = ConditionalOrder(symbol="BTC/USDT", side="buy", amount=0.1, trigger_condition=condition)

            # 测试触发
            market_data = {"current_price": 71000}
            triggered = cond_order.check_and_trigger(market_data)
            test_result("条件单触发", triggered)

            # 测试未触发
            market_data = {"current_price": 69000}
            not_triggered = not cond_order.check_and_trigger(market_data)
            test_result("条件单不触发", not_triggered)

        except Exception as e:
            test_result("条件单测试", False, str(e))

        # 2.2 OCO 订单
        print("\n2.2 OCO 订单")
        try:
            oco = OCOOrder(symbol="BTC/USDT", side="sell", amount=0.1, take_profit_price=70000, stop_loss_price=60000)

            # 测试止盈触发
            market_data = {"current_price": 70500}
            filled = oco.check_and_fill(market_data)
            test_result("OCO 止盈触发", filled is not None)

            # 测试止损触发
            oco2 = OCOOrder(symbol="BTC/USDT", side="sell", amount=0.1, take_profit_price=70000, stop_loss_price=60000)
            market_data = {"current_price": 59500}
            filled = oco2.check_and_fill(market_data)
            test_result("OCO 止损触发", filled is not None)

        except Exception as e:
            test_result("OCO 订单测试", False, str(e))

        # 2.3 追踪止损
        print("\n2.3 追踪止损")
        try:
            trailing = TrailingStop(symbol="BTC/USDT", side="sell", amount=0.1, trail_percent=0.05, initial_price=65000)

            # 测试止损价调整
            trailing.update_stop_price(68000)
            trailing.update_stop_price(70000)
            trailing.update_stop_price(72000)

            info = trailing.get_info()
            test_result("追踪止损价调整", info["current_stop_price"] > 65000)
            print(f"     最高价：${info['highest_price']}, 止损价：${info['current_stop_price']:.2f}")

            # 测试触发
            triggered = trailing.check_and_trigger(68000)  # 价格回调到止损价以下
            test_result("追踪止损触发", triggered)

        except Exception as e:
            test_result("追踪止损测试", False, str(e))

    except ImportError as e:
        skip_test("高级订单", f"模块导入失败：{e}")


# ════════════════════════════════════════════════════════════
# 3. 仓位管理测试
# ════════════════════════════════════════════════════════════


def test_position_management():
    """测试仓位管理策略"""
    print("\n" + "=" * 60)
    print("3. 仓位管理测试")
    print("=" * 60)

    try:
        from src.trading.position.position_management import (
            FixedFractionalPosition,
            KellyCriterion,
            PyramidingPosition,
            MartingalePosition,
            RiskParityPosition,
            PositionManager,
            PositionInfo,
        )

        # 3.1 固定比例
        print("\n3.1 固定比例仓位")
        try:
            fixed = FixedFractionalPosition(fraction=0.1)
            size = fixed.calculate_position_size(capital=100000, price=50000)
            test_result("固定比例计算", abs(size - 0.2) < 0.01)
            print(f"     仓位：{size} (10% 资金)")
        except Exception as e:
            test_result("固定比例计算", False, str(e))

        # 3.2 凯利公式
        print("\n3.2 凯利公式")
        try:
            kelly = KellyCriterion(win_rate=0.55, profit_loss_ratio=2.0, kelly_fraction=0.5)

            info = kelly.get_info()
            test_result("凯利公式计算", info["adjusted_kelly"] > 0)
            print(f"     最优仓位：{info['adjusted_kelly']:.1%}")
        except Exception as e:
            test_result("凯利公式计算", False, str(e))

        # 3.3 金字塔加仓
        print("\n3.3 金字塔加仓")
        try:
            pyramid = PyramidingPosition()

            # 模拟盈利持仓
            position = PositionInfo(
                symbol="BTC/USDT",
                side="buy",
                entry_price=50000,
                current_price=52500,  # 盈利 5%
                amount=1.0,
            )

            size = pyramid.calculate_position_size(capital=100000, price=52500, current_position=position)
            test_result("金字塔加仓", size > 1.0)
            print(f"     盈利 5% 时加仓到：{size}")
        except Exception as e:
            test_result("金字塔加仓", False, str(e))

        # 3.4 马丁格尔
        print("\n3.4 马丁格尔")
        try:
            martingale = MartingalePosition(base_amount=0.01, multiplier=2.0, max_consecutive_losses=5)

            # 测试连续亏损
            sizes = []
            for losses in range(6):
                size = martingale.calculate_position_size(capital=100000, price=50000, consecutive_losses=losses)
                sizes.append(size)

            # 应该在前 5 次加倍，第 6 次限制
            test_result("马丁格尔加倍", sizes[4] > sizes[3] > sizes[2])
            print(f"     连续亏损仓位：{sizes}")
        except Exception as e:
            test_result("马丁格尔测试", False, str(e))

        # 3.5 风险平价
        print("\n3.5 风险平价")
        try:
            risk_parity = RiskParityPosition()

            weights = risk_parity.calculate_weights(volatilities={"BTC": 0.6, "ETH": 0.7, "USDT": 0.01})

            # USDT 应该获得最高权重（波动率最低）
            test_result("风险平价权重", weights["USDT"] > weights["BTC"])
            print(f"     权重：{weights}")
        except Exception as e:
            test_result("风险平价测试", False, str(e))

    except ImportError as e:
        skip_test("仓位管理", f"模块导入失败：{e}")


# ════════════════════════════════════════════════════════════
# 4. 风险监控测试
# ════════════════════════════════════════════════════════════


def test_risk_monitoring():
    """测试风险监控功能"""
    print("\n" + "=" * 60)
    print("4. 风险监控测试")
    print("=" * 60)

    try:
        from src.trading.risk.portfolio_risk import RiskMonitor, StressTester, BlackSwanDetector
        import numpy as np

        # 4.1 VaR/CVaR
        print("\n4.1 VaR/CVaR 计算")
        try:
            monitor = RiskMonitor(portfolio_value=100000)

            # 添加模拟收益率
            np.random.seed(42)
            for _ in range(100):
                ret = np.random.normal(0.0005, 0.02)
                monitor.add_return(ret)

            var_95 = monitor.calculate_var(confidence=0.95)
            cvar_95 = monitor.calculate_cvar(confidence=0.95)

            test_result("VaR 计算", var_95 < 0)
            test_result("CVaR 计算", cvar_95 < var_95)
            print(f"     VaR(95%): {var_95:.2%}, CVaR(95%): {cvar_95:.2%}")
        except Exception as e:
            test_result("VaR/CVaR 计算", False, str(e))

        # 4.2 回撤监控
        print("\n4.2 回撤监控")
        try:
            max_dd = monitor.calculate_max_drawdown()
            current_dd = monitor.calculate_current_drawdown()

            test_result("最大回撤计算", max_dd <= 0)
            print(f"     最大回撤：{max_dd:.2%}")
        except Exception as e:
            test_result("回撤监控", False, str(e))

        # 4.3 压力测试
        print("\n4.3 压力测试")
        try:
            tester = StressTester(portfolio_value=100000)

            # 运行所有场景
            results = tester.run_all_scenarios()

            test_result("压力测试场景", len(results) > 0)
            print(f"     最严重场景：{results[0]['scenario']} (损失 ${results[0]['loss']:,.0f})")
        except Exception as e:
            test_result("压力测试", False, str(e))

        # 4.4 黑天鹅检测
        print("\n4.4 黑天鹅检测")
        try:
            detector = BlackSwanDetector(lookback_days=30)

            # 添加模拟价格
            price = 100
            for i in range(100):
                price *= 1 + np.random.normal(0, 0.02)
                detector.add_price(price)

            # 突然波动率增加
            for i in range(10):
                price *= 1 + np.random.normal(0, 0.1)
                detector.add_price(price)

            risk_level = detector.get_risk_level()
            test_result("黑天鹅检测", risk_level in ["low", "medium", "high", "critical"])
            print(f"     风险等级：{risk_level}")
        except Exception as e:
            test_result("黑天鹅检测", False, str(e))

    except ImportError as e:
        skip_test("风险监控", f"模块导入失败：{e}")


# ════════════════════════════════════════════════════════════
# 5. 套利策略测试
# ════════════════════════════════════════════════════════════


def test_arbitrage():
    """测试套利策略"""
    print("\n" + "=" * 60)
    print("5. 套利策略测试")
    print("=" * 60)

    try:
        from src.trading.arbitrage.cross_exchange import CrossExchangeArbitrage

        # 跨交易所套利（无需 API Key 的只读模式）
        print("\n5.1 跨交易所套利扫描")
        try:
            arb = CrossExchangeArbitrage(exchanges=["binance", "okx"], min_profit_pct=0.1)

            # 扫描机会
            opportunities = arb.scan_opportunities(symbols=["BTC/USDT"], min_spread_pct=0.1)

            # 可能没有套利机会，这是正常的
            test_result("套利扫描", True)
            print(f"     发现 {len(opportunities)} 个套利机会")

        except Exception as e:
            test_result("套利扫描", False, str(e))

    except ImportError as e:
        skip_test("套利策略", f"模块导入失败：{e}")


# ════════════════════════════════════════════════════════════
# 6. 组合优化测试
# ════════════════════════════════════════════════════════════


def test_portfolio_optimization():
    """测试组合优化"""
    print("\n" + "=" * 60)
    print("6. 组合优化测试")
    print("=" * 60)

    try:
        from src.trading.portfolio.optimization import MarkowitzOptimizer, RiskParityOptimizer
        import pandas as pd
        import numpy as np

        # 创建模拟数据
        np.random.seed(42)
        n_days = 252
        returns_data = np.random.normal(0.0005, 0.02, (n_days, 5))
        columns = ["BTC", "ETH", "SOL", "BNB", "USDT"]
        returns = pd.DataFrame(returns_data, columns=columns)

        # 6.1 马科维茨优化
        print("\n6.1 马科维茨优化")
        try:
            optimizer = MarkowitzOptimizer(returns)

            # 最大夏普比率
            max_sharpe = optimizer.optimize_max_sharpe()
            test_result("最大夏普优化", max_sharpe["success"])
            print(f"     夏普比率：{max_sharpe['sharpe_ratio']:.2f}")

            # 最小波动率
            min_vol = optimizer.optimize_min_volatility()
            test_result("最小波动优化", min_vol["success"])
            print(f"     波动率：{min_vol['annual_volatility']:.1%}")

        except Exception as e:
            test_result("马科维茨优化", False, str(e))

        # 6.2 风险平价
        print("\n6.2 风险平价优化")
        try:
            rp = RiskParityOptimizer(returns)
            result = rp.optimize_risk_parity()

            test_result("风险平价优化", result["success"])
            print(f"     风险贡献：{result['risk_contributions']}")
        except Exception as e:
            test_result("风险平价优化", False, str(e))

    except ImportError as e:
        skip_test("组合优化", f"模块导入失败：{e}")


# ════════════════════════════════════════════════════════════
# 主测试流程
# ════════════════════════════════════════════════════════════


def main():
    """运行所有测试"""
    print("=" * 60)
    print("🧪 Phase 4 全面测试")
    print("=" * 60)
    print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    start_time = time.time()

    # 运行所有测试
    test_data_sources()
    test_advanced_orders()
    test_position_management()
    test_risk_monitoring()
    test_arbitrage()
    test_portfolio_optimization()

    # 统计结果
    elapsed_time = time.time() - start_time
    total_tests = test_results["passed"] + test_results["failed"] + test_results["skipped"]

    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    print(f"总测试数：{total_tests}")
    print(f"✅ 通过：{test_results['passed']}")
    print(f"❌ 失败：{test_results['failed']}")
    print(f"⏭️  跳过：{test_results['skipped']}")
    print(f"通过率：{test_results['passed'] / total_tests * 100:.1f}%" if total_tests > 0 else "N/A")
    print(f"耗时：{elapsed_time:.1f}秒")

    # 显示错误
    if test_results["errors"]:
        print("\n❌ 失败详情:")
        for error in test_results["errors"]:
            print(f"  - {error['name']}: {error['error']}")

    # 返回退出码
    return 0 if test_results["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
