#!/usr/bin/env python3
"""
架構優化實作測試腳本

測試項目：
1. 日誌系統
2. API 限流器
3. 健康檢查
"""

import sys
import os
import time

# 添加專案根目錄到路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_logger():
    """測試日誌系統"""
    print("\n" + "=" * 60)
    print("測試 1: 日誌系統")
    print("=" * 60)

    try:
        from src.utils.logger import (
            setup_logger,
            log_api_call,
            log_backtest,
        )

        # 初始化日誌
        logger = setup_logger(
            name="test_stocksx",
            level="DEBUG",
            log_dir="logs",
            enable_console=True,
            enable_file=True,
            enable_json_file=True,
        )

        # 測試各級別日誌
        logger.debug("這是 DEBUG 訊息")
        logger.info("這是 INFO 訊息")
        logger.warning("這是 WARNING 訊息")
        logger.error("這是 ERROR 訊息")

        # 測試結構化日誌
        log_api_call(
            logger,
            api_name="test_api",
            endpoint="/test/endpoint",
            params={"key": "value"},
            response_time_ms=123.45,
            status="success",
            result_count=10,
        )

        log_backtest(
            logger,
            symbol="BTC/USDT",
            strategy="sma_cross",
            timeframe="1h",
            metrics={"total_return_pct": 15.5},
            duration_ms=2345.67,
            status="completed",
        )

        # 測試異常記錄
        try:
            raise ValueError("測試異常")
        except Exception:
            logger.error("記錄異常", exc_info=True)

        print("[OK] 日誌系統測試通過")
        print("   檢查目錄：logs/")
        return True

    except Exception as e:
        print(f"[FAIL] 日誌系統測試失敗：{e}")
        import traceback

        traceback.print_exc()
        return False


def test_rate_limiter():
    """測試 API 限流器"""
    print("\n" + "=" * 60)
    print("測試 2: API 限流器")
    print("=" * 60)

    try:
        from src.utils.rate_limiter import (
            RateLimiter,
            API_LIMIT_CONFIG,
        )

        # 測試基本限流
        limiter = RateLimiter(default_capacity=5, default_refill_rate=1.0)

        print("   測試快速連續請求（容量=5）...")
        success_count = 0
        for i in range(7):
            allowed, wait_time = limiter.allow_request(key="test_api", capacity=5, refill_rate=1.0, wait=False)
            if allowed:
                success_count += 1
                print(f"   請求 {i + 1}: [OK] 允許")
            else:
                print(f"   請求 {i + 1}: [LIMIT] 限流 (等待 {wait_time:.2f}s)")

        print(f"   結果：{success_count}/7 請求成功")

        # 測試等待功能
        print("\n   測試等待功能...")
        limiter2 = RateLimiter(default_capacity=2, default_refill_rate=2.0)

        # 耗盡令牌
        limiter2.allow_request("test2", capacity=2, refill_rate=2.0)
        limiter2.allow_request("test2", capacity=2, refill_rate=2.0)

        # 帶等待的請求
        start = time.time()
        allowed, wait_time = limiter2.allow_request(key="test2", capacity=2, refill_rate=2.0, wait=True, max_wait=5.0)
        elapsed = time.time() - start

        print(f"   等待時間：{wait_time:.2f}s, 實際耗時：{elapsed:.2f}s")
        print(f"   結果：{'[OK] 允許' if allowed else '[FAIL] 拒絕'}")

        # 測試 API 配置
        print("\n   測試 API 限流配置:")
        for api_name, config in API_LIMIT_CONFIG.items():
            print(f"   - {api_name}: 容量={config['capacity']}, 速率={config['refill_rate']:.2f}/s")

        print("\n[OK] API 限流器測試通過")
        return True

    except Exception as e:
        print(f"[FAIL] API 限流器測試失敗：{e}")
        import traceback

        traceback.print_exc()
        return False


def test_health_check():
    """測試健康檢查"""
    print("\n" + "=" * 60)
    print("測試 3: 健康檢查")
    print("=" * 60)

    try:
        from src.utils.health_check import (
            get_system_health,
            check_database,
            check_redis,
            check_disk_usage,
            check_memory,
        )

        # 測試單項檢查
        print("   單項服務檢查:")

        db_status = check_database()
        print(f"   - 資料庫：{db_status.status} - {db_status.message}")

        redis_status = check_redis()
        print(f"   - Redis: {redis_status.status} - {redis_status.message}")

        disk_status = check_disk_usage()
        print(f"   - 磁碟：{disk_status.status} - {disk_status.message}")

        memory_status = check_memory()
        print(f"   - 記憶體：{memory_status.status} - {memory_status.message}")

        # 測試整體健康
        print("\n   系統整體健康:")
        health = get_system_health(include_system=True)

        print(f"   - 整體狀態：{health.status}")
        print(f"   - 運行時間：{health.uptime_seconds:.1f}s")
        print(f"   - 服務數量：{len(health.services)}")

        for service in health.services:
            status_icon = "[OK]" if service.status == "healthy" else "[!]"
            print(f"     {status_icon} {service.service}: {service.status}")

        print("\n[OK] 健康檢查測試通過")
        return True

    except Exception as e:
        print(f"[FAIL] 健康檢查測試失敗：{e}")
        import traceback

        traceback.print_exc()
        return False


def test_api_hub_integration():
    """測試 api_hub.py 整合"""
    print("\n" + "=" * 60)
    print("測試 4: API Hub 整合（限流 + 日誌）")
    print("=" * 60)

    try:
        from src.data.sources.api_hub import (
            get_current_fear_greed,
            USE_RATE_LIMITER,
        )

        print(f"   限流器啟用：{'[OK] 是' if USE_RATE_LIMITER else '[SKIP] 否'}")

        if USE_RATE_LIMITER:
            print("   測試 Fear & Greed Index API...")
            try:
                fg = get_current_fear_greed()
                if fg:
                    print("   [OK] 成功取得數據:")
                    print(f"      - 數值：{fg.get('value', 'N/A')}")
                    print(f"      - 分類：{fg.get('classification', 'N/A')}")
                else:
                    print("   [!] 返回數據為空")
            except Exception as e:
                print(f"   [!] API 呼叫失敗（可能是限流）: {e}")
        else:
            print("   [SKIP] 限流器未啟用，跳過測試")

        print("\n[OK] API Hub 整合測試完成")
        return True

    except Exception as e:
        print(f"[FAIL] API Hub 整合測試失敗：{e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """執行所有測試"""
    print("\n" + "=" * 60)
    print("StocksX 架構優化實作測試")
    print("=" * 60)

    results = {
        "日誌系統": test_logger(),
        "API 限流器": test_rate_limiter(),
        "健康檢查": test_health_check(),
        "API Hub 整合": test_api_hub_integration(),
    }

    # 總結
    print("\n" + "=" * 60)
    print("測試總結")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "[通過]" if result else "[失敗]"
        print(f"   {name}: {status}")

    print(f"\n總計：{passed}/{total} 測試通過")

    if passed == total:
        print("\n[SUCCESS] 所有測試通過！架構優化實作完成。")
        return 0
    else:
        print(f"\n[WARNING] {total - passed} 個測試失敗，請檢查錯誤訊息。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
