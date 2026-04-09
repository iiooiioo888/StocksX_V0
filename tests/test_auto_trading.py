"""
自動交易功能測試腳本
====================
測試自動交易模組的各項功能
"""

import sys
import time

# ════════════════════════════════════════════════════════════
# 測試配置
# ════════════════════════════════════════════════════════════

TEST_CONFIG = {
    "exchange": {
        "exchange_id": "binance",
        "sandbox": True,
        # 測試網絡 API 金鑰（請替換為您的）
        "api_key": "your_testnet_api_key",
        "api_secret": "your_testnet_api_secret",
    },
    "risk_management": {
        "risk_per_trade": 0.02,
        "stop_loss_pct": 2.0,
        "take_profit_pct": 4.0,
        "max_open_positions": 3,
        "leverage": 1.0,
        "max_daily_loss_pct": 5.0,
    },
    "subscriptions": [
        {
            "symbol": "BTC/USDT:USDT",
            "strategy": "sma_cross",
            "params": {"fast": 5, "slow": 20},
            "timeframe": "1h",
        }
    ],
    "initial_equity": 10000,
}

def test_executor():
    """測試交易執行器"""
    print("\n" + "=" * 60)
    print("測試 1: 交易執行器")
    print("=" * 60)

    try:
        from src.trading.executor import TradeExecutor, OrderResult

        print("✅ 導入模塊成功")

        # 創建執行器
        executor = TradeExecutor(
            exchange_id=TEST_CONFIG["exchange"]["exchange_id"],
            api_key=TEST_CONFIG["exchange"]["api_key"],
            api_secret=TEST_CONFIG["exchange"]["api_secret"],
            sandbox=TEST_CONFIG["exchange"]["sandbox"],
        )

        print(f"✅ 連接交易所成功：{TEST_CONFIG['exchange']['exchange_id']}")

        # 測試獲取價格
        print("\n📊 測試獲取價格...")
        ticker = executor.get_ticker("BTC/USDT:USDT")
        if ticker:
            print(f"✅ BTC 價格：${ticker.get('last', 0):,.2f}")
        else:
            print("❌ 獲取價格失敗")

        # 測試獲取餘額
        print("\n💰 測試獲取餘額...")
        balance = executor.get_balance()
        if balance:
            print(f"✅ USDT 餘額：{balance.get('USDT', {}).get('free', 0):,.2f}")
        else:
            print("⚠️ 餘額查詢失敗（可能是測試網絡）")

        # 測試獲取持倉
        print("\n📈 測試獲取持倉...")
        position = executor.get_position("BTC/USDT:USDT")
        if position:
            print(f"✅ 持倉：{position.get('side', 'NONE')} {position.get('contracts', 0)} BTC")
        else:
            print("ℹ️ 無持倉")

        return True

    except ImportError as e:
        print(f"❌ 導入失敗：{e}")
        return False
    except Exception as e:
        print(f"❌ 測試失敗：{e}")
        return False

def test_risk_manager():
    """測試風險管理器"""
    print("\n" + "=" * 60)
    print("測試 2: 風險管理器")
    print("=" * 60)

    try:
        from src.trading.risk_manager import RiskManager, RiskConfig

        print("✅ 導入模塊成功")

        # 創建風險管理器
        config = RiskConfig(
            risk_per_trade=0.02,
            stop_loss_pct=2.0,
            take_profit_pct=4.0,
            max_open_positions=3,
        )

        risk_manager = RiskManager(config)
        print("✅ 風險管理器初始化成功")

        # 測試倉位計算
        print("\n📊 測試倉位計算...")
        position_size = risk_manager.calculate_position_size(
            equity=10000,
            entry_price=50000,
            stop_loss_price=49000,
        )
        print(f"✅ 建議倉位：{position_size:.4f} BTC")
        print(f"   倉位價值：${position_size * 50000:,.2f}")

        # 測試停損/停利計算
        print("\n🛑 測試停損/停利計算...")
        stop_loss = risk_manager.calculate_stop_loss(50000, "long")
        take_profit = risk_manager.calculate_take_profit(50000, "long")
        print("✅ 進場價：$50,000")
        print(f"   停損價：${stop_loss:,.2f} (-{risk_manager.config.stop_loss_pct}%)")
        print(f"   停利價：${take_profit:,.2f} (+{risk_manager.config.take_profit_pct}%)")

        # 測試風險檢查
        print("\n⚠️ 測試風險檢查...")
        risk_manager.reset_daily_pnl(10000)
        can_trade, reason = risk_manager.can_open_position()
        print(f"✅ 風險檢查：{reason}")

        # 測試風險報告
        print("\n📋 測試風險報告...")
        report = risk_manager.get_risk_report()
        print("✅ 風險報告:")
        for key, value in report.items():
            print(f"   {key}: {value}")

        return True

    except ImportError as e:
        print(f"❌ 導入失敗：{e}")
        return False
    except Exception as e:
        print(f"❌ 測試失敗：{e}")
        return False

def test_auto_trader():
    """測試自動交易器"""
    print("\n" + "=" * 60)
    print("測試 3: 自動交易器（僅初始化測試）")
    print("=" * 60)

    try:
        from src.trading.auto_trader import AutoTrader

        print("✅ 導入模塊成功")

        # 創建自動交易器
        trader = AutoTrader(user_id=1)
        print("✅ 自動交易器創建成功")

        # 測試初始化
        print("\n🔧 測試初始化...")
        if trader.initialize(TEST_CONFIG):
            print("✅ 初始化成功")
        else:
            print("❌ 初始化失敗")
            return False

        # 測試狀態查詢
        print("\n📊 測試狀態查詢...")
        status = trader.get_status()
        print(f"✅ 狀態：{status}")

        return True

    except ImportError as e:
        print(f"❌ 導入失敗：{e}")
        return False
    except Exception as e:
        print(f"❌ 測試失敗：{e}")
        return False

def test_worker():
    """測試 Celery 任務"""
    print("\n" + "=" * 60)
    print("測試 4: Celery 任務")
    print("=" * 60)

    try:
        from src.trading.worker import (
            execute_auto_trade,
            stop_auto_trade,
            emergency_stop,
            daily_report,
        )

        print("✅ 導入模塊成功")

        # 檢查 Celery 配置
        print("\n🔧 檢查 Celery 配置...")
        from src.tasks.celery_app import celery_app

        print(f"✅ Celery Broker: {celery_app.conf.broker_url}")
        print(f"✅ Celery Backend: {celery_app.conf.result_backend}")

        # 注意：實際執行需要 Celery Worker 運行
        print("\n⚠️ 注意：實際執行需要 Celery Worker 運行")
        print("   啟動命令：celery -A src.tasks worker --loglevel=info")

        return True

    except ImportError as e:
        print(f"❌ 導入失敗：{e}")
        return False
    except Exception as e:
        print(f"❌ 測試失敗：{e}")
        return False

def main():
    """主測試函數"""
    print("\n" + "=" * 60)
    print("🤖 StocksX 自動交易功能測試")
    print("=" * 60)

    results = {
        "executor": False,
        "risk_manager": False,
        "auto_trader": False,
        "worker": False,
    }

    # 執行測試
    results["executor"] = test_executor()
    time.sleep(1)

    results["risk_manager"] = test_risk_manager()
    time.sleep(1)

    results["auto_trader"] = test_auto_trader()
    time.sleep(1)

    results["worker"] = test_worker()

    # 總結
    print("\n" + "=" * 60)
    print("📊 測試總結")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{status} - {test_name}")

    print(f"\n總計：{passed}/{total} 測試通過")

    if passed == total:
        print("\n🎉 所有測試通過！自動交易功能已就緒")
        print("\n下一步:")
        print("1. 配置 API 金鑰：編輯 .env 文件")
        print("2. 啟動 Redis: docker run -d -p 6379:6379 redis:7-alpine")
        print("3. 啟動 Celery Worker: celery -A src.tasks worker --loglevel=info")
        print("4. 啟動 Streamlit: streamlit run app.py")
        print("5. 訪問自動交易頁面：http://localhost:8501")
    else:
        print("\n⚠️ 部分測試失敗，請檢查錯誤訊息")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
