"""
配置驗證模組 — 驗證 .env 設定的安全性與完整性

功能：
- 啟動時檢查必要配置
- 驗證 SECRET_KEY 強度
- 檢查資料庫路徑可寫性
- 檢查 Redis 連通性
- 報告缺失的可選配置

用法：
    from src.utils.config_validator import validate_config, ConfigReport
    report = validate_config()
    if not report.is_valid:
        print(report.summary())
"""

from __future__ import annotations

import os
import string
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class ConfigIssue:
    """配置問題."""

    field: str
    severity: str  # "error", "warning", "info"
    message: str
    suggestion: str = ""


@dataclass(slots=True)
class ConfigReport:
    """配置驗證報告."""

    issues: list[ConfigIssue] = field(default_factory=list)
    checks_passed: int = 0
    checks_total: int = 0

    @property
    def is_valid(self) -> bool:
        return not any(i.severity == "error" for i in self.issues)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "warning")

    def summary(self) -> str:
        lines = [
            f"配置驗證: {'✅ 通過' if self.is_valid else '❌ 失敗'}",
            f"  通過: {self.checks_passed}/{self.checks_total}",
            f"  錯誤: {self.error_count}，警告: {self.warning_count}",
        ]
        for issue in self.issues:
            icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}.get(issue.severity, "•")
            lines.append(f"  {icon} [{issue.field}] {issue.message}")
            if issue.suggestion:
                lines.append(f"      💡 {issue.suggestion}")
        return "\n".join(lines)


def _check_secret_key(report: ConfigReport) -> None:
    """驗證 SECRET_KEY."""
    report.checks_total += 1
    key = os.getenv("SECRET_KEY", "")

    if not key:
        report.issues.append(
            ConfigIssue(
                field="SECRET_KEY",
                severity="error",
                message="SECRET_KEY 未設定",
                suggestion='執行: python -c "import secrets; print(secrets.token_hex(32))"',
            )
        )
        return

    if len(key) < 16:
        report.issues.append(
            ConfigIssue(
                field="SECRET_KEY",
                severity="error",
                message=f"SECRET_KEY 長度不足（{len(key)} 字元，建議 ≥32）",
                suggestion="使用更長的密鑰以增強安全性",
            )
        )
        return

    # 檢查複雜度
    has_lower = any(c in string.ascii_lowercase for c in key)
    has_upper = any(c in string.ascii_uppercase for c in key)
    has_digit = any(c in string.digits for c in key)

    if not (has_lower and has_upper and has_digit):
        report.issues.append(
            ConfigIssue(
                field="SECRET_KEY",
                severity="warning",
                message="SECRET_KEY 複雜度較低",
                suggestion="建議包含大小寫字母和數字",
            )
        )
    else:
        report.checks_passed += 1


def _check_admin_password(report: ConfigReport) -> None:
    """驗證 ADMIN_PASSWORD."""
    report.checks_total += 1
    pw = os.getenv("ADMIN_PASSWORD", "")

    if not pw:
        report.issues.append(
            ConfigIssue(
                field="ADMIN_PASSWORD",
                severity="warning",
                message="ADMIN_PASSWORD 未設定，將自動生成隨機密碼",
                suggestion="在 .env 中設定 ADMIN_PASSWORD 以固定管理員密碼",
            )
        )
    else:
        report.checks_passed += 1


def _check_database(report: ConfigReport) -> None:
    """驗證資料庫路徑."""
    report.checks_total += 1
    db_path = Path("data")

    try:
        db_path.mkdir(parents=True, exist_ok=True)
        test_file = db_path / ".write_test"
        test_file.write_text("test")
        test_file.unlink()
        report.checks_passed += 1
    except OSError as e:
        report.issues.append(
            ConfigIssue(
                field="DATABASE",
                severity="error",
                message=f"資料庫目錄不可寫: {e}",
                suggestion="確保 data/ 目錄存在且有寫入權限",
            )
        )


def _check_redis(report: ConfigReport) -> None:
    """驗證 Redis 連通性."""
    report.checks_total += 1
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    try:
        import redis

        r = redis.from_url(redis_url, socket_connect_timeout=3)
        r.ping()
        report.checks_passed += 1
    except ImportError:
        report.issues.append(
            ConfigIssue(
                field="REDIS",
                severity="info",
                message="redis-py 未安裝，快取功能受限",
                suggestion="pip install redis",
            )
        )
        report.checks_passed += 1  # 非致命
    except Exception as e:
        env = os.getenv("APP_ENV", "production")
        severity = "info" if env == "development" else "warning"
        report.issues.append(
            ConfigIssue(
                field="REDIS",
                severity=severity,
                message=f"Redis 連接失敗: {e}",
                suggestion="確認 Redis 服務已啟動，或使用 Docker Compose",
            )
        )


def _check_exchange_keys(report: ConfigReport) -> None:
    """檢查交易所 API 密鑰（可選）."""
    report.checks_total += 1
    keys = [
        ("BINANCE_API_KEY", "BINANCE_SECRET_KEY"),
        ("BYBIT_API_KEY", "BYBIT_SECRET_KEY"),
    ]

    has_any = False
    for api_key_env, secret_env in keys:
        api_key = os.getenv(api_key_env, "")
        secret = os.getenv(secret_env, "")
        if api_key and not secret:
            report.issues.append(
                ConfigIssue(
                    field=api_key_env,
                    severity="warning",
                    message=f"{api_key_env} 已設定但 {secret_env} 未設定",
                    suggestion=f"請同時設定 {secret_env}",
                )
            )
        elif api_key and secret:
            has_any = True

    if not has_any:
        report.issues.append(
            ConfigIssue(
                field="EXCHANGE_KEYS",
                severity="info",
                message="未設定交易所 API 密鑰，自動交易功能不可用",
                suggestion="如需自動交易，在 .env 中設定 BINANCE_API_KEY 和 BINANCE_SECRET_KEY",
            )
        )

    report.checks_passed += 1


def _check_log_dir(report: ConfigReport) -> None:
    """驗證日誌目錄."""
    report.checks_total += 1
    log_dir = Path("logs")

    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        report.checks_passed += 1
    except OSError as e:
        report.issues.append(
            ConfigIssue(
                field="LOG_DIR",
                severity="warning",
                message=f"日誌目錄不可寫: {e}",
                suggestion="確保 logs/ 目錄存在且有寫入權限",
            )
        )


def _check_timezone(report: ConfigReport) -> None:
    """驗證時區設定."""
    report.checks_total += 1
    tz = os.getenv("TZ", "")
    if not tz:
        report.issues.append(
            ConfigIssue(
                field="TZ",
                severity="info",
                message="未設定時區，使用系統預設",
                suggestion="在 .env 中設定 TZ=Asia/Shanghai",
            )
        )
    report.checks_passed += 1


def validate_config() -> ConfigReport:
    """
    執行完整配置驗證.

    Returns:
        ConfigReport 包含所有問題和通過數
    """
    report = ConfigReport()

    _check_secret_key(report)
    _check_admin_password(report)
    _check_database(report)
    _check_redis(report)
    _check_exchange_keys(report)
    _check_log_dir(report)
    _check_timezone(report)

    return report
