# 健康檢查端點
from __future__ import annotations

import os
import sqlite3
import time
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

import requests


@dataclass
class HealthStatus:
    """健康檢查狀態"""
    service: str
    status: str  # "healthy", "degraded", "unhealthy"
    message: str
    latency_ms: Optional[float] = None
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SystemHealth:
    """系統整體健康狀態"""
    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: float
    services: List[HealthStatus]
    version: str = "1.0.0"
    uptime_seconds: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'status': self.status,
            'timestamp': self.timestamp,
            'uptime_seconds': self.uptime_seconds,
            'version': self.version,
            'services': [s.to_dict() for s in self.services],
        }


# 全局啟動時間
_start_time = time.time()


def check_database(db_path: str = "cache/users.sqlite") -> HealthStatus:
    """檢查資料庫健康狀態"""
    start = time.time()
    try:
        if not os.path.exists(db_path):
            return HealthStatus(
                service="database",
                status="unhealthy",
                message="Database file not found",
            )
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 測試查詢
        cursor.execute("SELECT 1")
        cursor.fetchone()
        
        # 檢查表是否存在
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        )
        if not cursor.fetchone():
            conn.close()
            return HealthStatus(
                service="database",
                status="degraded",
                message="Database tables missing",
            )
        
        # 檢查連接數（SQLite 不支援，但可檢查檔案鎖定）
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_active=1")
        active_users = cursor.fetchone()[0]
        
        conn.close()
        
        latency = (time.time() - start) * 1000
        
        return HealthStatus(
            service="database",
            status="healthy",
            message=f"SQLite database OK ({active_users} active users)",
            latency_ms=latency,
            details={"active_users": active_users, "path": db_path}
        )
        
    except sqlite3.Error as e:
        return HealthStatus(
            service="database",
            status="unhealthy",
            message=f"Database error: {str(e)}",
            latency_ms=(time.time() - start) * 1000,
        )


def check_redis(redis_url: Optional[str] = None) -> HealthStatus:
    """檢查 Redis 健康狀態"""
    start = time.time()
    
    redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    try:
        import redis
        r = redis.from_url(redis_url, decode_responses=True)
        r.ping()
        
        # 測試讀寫
        test_key = "health_check:test"
        r.setex(test_key, 10, str(time.time()))
        value = r.get(test_key)
        
        latency = (time.time() - start) * 1000
        
        return HealthStatus(
            service="redis",
            status="healthy",
            message="Redis connection OK",
            latency_ms=latency,
            details={"url": redis_url}
        )
        
    except ImportError:
        return HealthStatus(
            service="redis",
            status="degraded",
            message="Redis client not installed (redis-py)",
        )
    except Exception as e:
        return HealthStatus(
            service="redis",
            status="unhealthy" if "Connection refused" in str(e) else "degraded",
            message=f"Redis error: {str(e)}",
            latency_ms=(time.time() - start) * 1000,
        )


def check_external_api(
    name: str,
    url: str,
    timeout: float = 5.0,
    expected_status: int = 200,
) -> HealthStatus:
    """檢查外部 API 健康狀態"""
    start = time.time()
    
    try:
        resp = requests.get(url, timeout=timeout)
        latency = (time.time() - start) * 1000
        
        if resp.status_code == expected_status:
            return HealthStatus(
                service=name,
                status="healthy",
                message=f"API OK (status={resp.status_code})",
                latency_ms=latency,
            )
        else:
            return HealthStatus(
                service=name,
                status="degraded",
                message=f"API returned unexpected status: {resp.status_code}",
                latency_ms=latency,
            )
        
    except requests.exceptions.Timeout:
        return HealthStatus(
            service=name,
            status="unhealthy",
            message="API timeout",
            latency_ms=(time.time() - start) * 1000,
        )
    except requests.exceptions.ConnectionError:
        return HealthStatus(
            service=name,
            status="unhealthy",
            message="API connection failed",
            latency_ms=(time.time() - start) * 1000,
        )
    except Exception as e:
        return HealthStatus(
            service=name,
            status="unhealthy",
            message=f"API error: {str(e)}",
            latency_ms=(time.time() - start) * 1000,
        )


def check_yfinance() -> HealthStatus:
    """檢查 Yahoo Finance 數據源"""
    return check_external_api(
        name="yfinance",
        url="https://query1.finance.yahoo.com/v8/finance/chart/AAPL?range=1d&interval=1d",
        timeout=5.0,
    )


def check_ccxt(exchange_id: str = "binance") -> HealthStatus:
    """檢查 CCXT 交易所連接"""
    start = time.time()
    
    try:
        import ccxt
        exchange = getattr(ccxt, exchange_id)()
        
        # 測試 API
        markets = exchange.load_markets()
        latency = (time.time() - start) * 1000
        
        return HealthStatus(
            service=f"ccxt:{exchange_id}",
            status="healthy",
            message=f"Exchange OK ({len(markets)} markets)",
            latency_ms=latency,
            details={"markets_count": len(markets)}
        )
        
    except Exception as e:
        return HealthStatus(
            service=f"ccxt:{exchange_id}",
            status="unhealthy",
            message=f"Exchange error: {str(e)}",
            latency_ms=(time.time() - start) * 1000,
        )


def check_celery_broker(broker_url: Optional[str] = None) -> HealthStatus:
    """檢查 Celery Broker（Redis）"""
    broker_url = broker_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    start = time.time()
    
    try:
        import redis
        r = redis.from_url(broker_url, decode_responses=True)
        
        # 檢查 Celery 相關 key
        keys = r.keys("celery:*")
        latency = (time.time() - start) * 1000
        
        return HealthStatus(
            service="celery_broker",
            status="healthy" if keys else "degraded",
            message=f"Celery broker OK ({len(keys)} keys)",
            latency_ms=latency,
            details={"keys_count": len(keys)}
        )
        
    except ImportError:
        return HealthStatus(
            service="celery_broker",
            status="degraded",
            message="Celery/Redis not installed",
        )
    except Exception as e:
        return HealthStatus(
            service="celery_broker",
            status="unhealthy",
            message=f"Celery broker error: {str(e)}",
            latency_ms=(time.time() - start) * 1000,
        )


def check_disk_usage(path: str = ".") -> HealthStatus:
    """檢查磁碟使用量"""
    try:
        import shutil
        total, used, free = shutil.disk_usage(path)
        usage_percent = (used / total) * 100
        
        status = "healthy"
        if usage_percent > 90:
            status = "unhealthy"
        elif usage_percent > 75:
            status = "degraded"
        
        return HealthStatus(
            service="disk",
            status=status,
            message=f"Disk usage: {usage_percent:.1f}%",
            details={
                "total_gb": total / (1024**3),
                "used_gb": used / (1024**3),
                "free_gb": free / (1024**3),
                "usage_percent": usage_percent,
            }
        )
        
    except Exception as e:
        return HealthStatus(
            service="disk",
            status="degraded",
            message=f"Disk check error: {str(e)}",
        )


def check_memory() -> HealthStatus:
    """檢查記憶體使用量"""
    try:
        import psutil
        mem = psutil.virtual_memory()
        usage_percent = mem.percent
        
        status = "healthy"
        if usage_percent > 90:
            status = "unhealthy"
        elif usage_percent > 75:
            status = "degraded"
        
        return HealthStatus(
            service="memory",
            status=status,
            message=f"Memory usage: {usage_percent:.1f}%",
            details={
                "total_mb": mem.total / (1024**2),
                "used_mb": mem.used / (1024**2),
                "available_mb": mem.available / (1024**2),
                "usage_percent": usage_percent,
            }
        )
        
    except ImportError:
        return HealthStatus(
            service="memory",
            status="degraded",
            message="psutil not installed",
        )
    except Exception as e:
        return HealthStatus(
            service="memory",
            status="degraded",
            message=f"Memory check error: {str(e)}",
        )


def get_system_health(
    include_external: bool = False,
    include_system: bool = False,
) -> SystemHealth:
    """
    取得系統整體健康狀態
    
    Args:
        include_external: 是否包含外部 API 檢查
        include_system: 是否包含系統資源檢查
    
    Returns:
        SystemHealth 物件
    """
    services: List[HealthStatus] = []
    
    # 核心服務檢查
    services.append(check_database())
    services.append(check_redis())
    services.append(check_celery_broker())
    
    # 外部 API 檢查（可選）
    if include_external:
        services.append(check_yfinance())
    
    # 系統資源檢查（可選）
    if include_system:
        services.append(check_disk_usage())
        services.append(check_memory())
    
    # 決定整體狀態
    unhealthy_count = sum(1 for s in services if s.status == "unhealthy")
    degraded_count = sum(1 for s in services if s.status == "degraded")
    
    if unhealthy_count > 0:
        overall_status = "unhealthy"
    elif degraded_count > 0:
        overall_status = "degraded"
    else:
        overall_status = "healthy"
    
    return SystemHealth(
        status=overall_status,
        timestamp=time.time(),
        services=services,
        uptime_seconds=time.time() - _start_time,
    )


# Streamlit 健康檢查頁面
def render_health_page():
    """在 Streamlit 中渲染健康檢查頁面"""
    import streamlit as st
    
    st.set_page_config(
        page_title="StocksX - 健康檢查",
        page_icon="🏥",
        layout="wide"
    )
    
    st.title("🏥 系統健康檢查")
    
    # 重新整理按鈕
    if st.button("🔄 重新檢查"):
        st.rerun()
    
    # 取得健康狀態
    health = get_system_health(include_external=True, include_system=True)
    
    # 整體狀態
    status_colors = {
        "healthy": "🟢",
        "degraded": "🟡",
        "unhealthy": "🔴",
    }
    
    st.markdown(
        f"### 整體狀態：{status_colors.get(health['status'], '⚪')} {health['status'].upper()}"
    )
    
    # 運行時間
    if health.get('uptime_seconds'):
        uptime = health['uptime_seconds']
        if uptime > 3600:
            uptime_str = f"{uptime / 3600:.1f} 小時"
        else:
            uptime_str = f"{uptime / 60:.1f} 分鐘"
        st.info(f"⏱️ 系統運行時間：{uptime_str}")
    
    st.divider()
    
    # 服務狀態詳情
    st.subheader("📊 服務狀態")
    
    for service in health.get('services', []):
        icon = status_colors.get(service['status'], '⚪')
        
        with st.expander(
            f"{icon} **{service['service']}**: {service['status']} - {service['message']}",
            expanded=(service['status'] != 'healthy')
        ):
            if service.get('latency_ms'):
                st.metric("延遲", f"{service['latency_ms']:.1f} ms")
            
            if service.get('details'):
                st.json(service['details'])
    
    # 自動重新整理（如果有服務不健康）
    if health['status'] == 'unhealthy':
        st.warning("⚠️ 系統將每 30 秒自動重新檢查...")
        time.sleep(30)
        st.rerun()
