# 系統健康檢查頁面
import time

import streamlit as st

from src.core import get_orchestrator
from src.utils.health_check import (
    get_system_health,
)

st.set_page_config(page_title="🏥 系統健康檢查", page_icon="🏥", layout="wide")

st.title("🏥 系統健康檢查")
st.markdown("*即時監控系統服務狀態與資源使用量*")

# 重新整理按鈕
col1, col2 = st.columns([1, 4])
with col1:
    if st.button("🔄 重新檢查", use_container_width=True):
        st.rerun()

# 取得健康狀態
with st.spinner("正在檢查系統健康狀態..."):
    health = get_system_health(include_external=True, include_system=True)

# 整體狀態
status_colors = {
    "healthy": "🟢",
    "degraded": "🟡",
    "unhealthy": "🔴",
}
status_emoji = status_colors.get(health.status, "⚪")

# 整體狀態卡片
if health.status == "healthy":
    st.success(f"### {status_emoji} 系統狀態：{health.status.upper()}")
elif health.status == "degraded":
    st.warning(f"### {status_emoji} 系統狀態：{health.status.upper()}")
else:
    st.error(f"### {status_emoji} 系統狀態：{health.status.upper()}")

# 運行時間
if health.uptime_seconds:
    uptime = health.uptime_seconds
    if uptime > 86400:
        uptime_str = f"{uptime / 86400:.1f} 天"
    elif uptime > 3600:
        uptime_str = f"{uptime / 3600:.1f} 小時"
    else:
        uptime_str = f"{uptime / 60:.1f} 分鐘"
    st.info(f"⏱️ 系統運行時間：{uptime_str}")

st.divider()

# 服務狀態詳情
st.subheader("📊 服務狀態")

for service in health.services:
    icon = status_colors.get(service.status, "⚪")

    # 根據狀態決定展開與否
    expanded = service.status != "healthy"

    with st.expander(f"{icon} **{service.service}**: {service.status} - {service.message}", expanded=expanded):
        if service.latency_ms:
            st.metric("延遲", f"{service.latency_ms:.1f} ms")

        if service.details:
            st.json(service.details if isinstance(service.details, dict) else {"info": service.details})

st.divider()

# 快速診斷建議
st.subheader("🔧 快速診斷建議")

issues = [s for s in health.services if s.status != "healthy"]

if not issues:
    st.success("✅ 所有服務運行正常！")
else:
    for issue in issues:
        with st.container():
            st.markdown(f"**{issue.service}**: {issue.message}")

            if issue.service == "redis":
                st.code(
                    """
# 啟動 Redis
docker run -d -p 6379:6379 --name stocksx_redis redis:7-alpine

# 或檢查 Redis 狀態
redis-cli ping
                """,
                    language="bash",
                )

            elif issue.service == "database":
                st.code(
                    """
# 檢查資料庫檔案
ls -la cache/users.sqlite

# 重建資料庫（會清除用戶數據）
rm cache/users.sqlite
                """,
                    language="bash",
                )

            elif issue.service == "celery_broker":
                st.code(
                    """
# 啟動 Celery Worker
celery -A src.tasks worker --loglevel=info -Q backtest,optimizer,notify

# 檢查 Redis 連接
redis-cli ping
                """,
                    language="bash",
                )

            elif issue.service == "disk":
                st.warning("磁碟空間不足，建議清理日誌或擴充磁碟")

            elif issue.service == "memory":
                st.warning("記憶體使用量過高，建議重啟應用或增加記憶體")

# 自動重新整理（如果有嚴重問題）
if health.status == "unhealthy":
    st.warning("⚠️ 系統將每 30 秒自動重新檢查...")
    time.sleep(30)
    st.rerun()
