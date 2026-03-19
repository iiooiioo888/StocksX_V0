"""
Alert System — 監控告警

支持多種通知渠道（Bark、日誌、Webhook）。
通過規則引擎自動觸發告警。

用法：
    alert_mgr = get_alert_manager()
    alert_mgr.add_rule(AlertRule(
        name="high_drawdown",
        condition=lambda m: m.get("max_drawdown_pct", 0) > 20,
        message="⚠️ 最大回撤超過 20%: {max_drawdown_pct}%",
    ))
    alert_mgr.check(metrics_dict)
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass(slots=True)
class Alert:
    """告警記錄."""

    rule_name: str
    severity: AlertSeverity
    message: str
    timestamp: float = 0.0
    data: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = time.time()

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule": self.rule_name,
            "severity": self.severity.value,
            "message": self.message,
            "time": datetime.fromtimestamp(self.timestamp).isoformat(),
            "data": self.data,
        }


# ─── 告警規則 ───


@dataclass(slots=True)
class AlertRule:
    """告警規則."""

    name: str
    condition: Callable[[dict[str, Any]], bool]
    message_template: str = "Alert: {name}"
    severity: AlertSeverity = AlertSeverity.WARNING
    cooldown_seconds: float = 300  # 5 分鐘冷卻
    enabled: bool = True


# ─── 通知渠道 ───


class AlertChannel:
    """通知渠道基類."""

    def send(self, alert: Alert) -> None:
        pass


class LogChannel(AlertChannel):
    """日誌通知."""

    def send(self, alert: Alert) -> None:
        level = {
            AlertSeverity.INFO: logging.INFO,
            AlertSeverity.WARNING: logging.WARNING,
            AlertSeverity.CRITICAL: logging.CRITICAL,
        }.get(alert.severity, logging.WARNING)
        logger.log(level, "🚨 ALERT [%s] %s", alert.rule_name, alert.message)


class BarkChannel(AlertChannel):
    """iOS Bark 推播."""

    def send(self, alert: Alert) -> None:
        key = os.getenv("BARK_KEY")
        if not key:
            return
        try:
            import requests

            server = os.getenv("BARK_SERVER", "https://api.day.app").rstrip("/")
            emoji = {"info": "ℹ️", "warning": "⚠️", "critical": "🚨"}.get(alert.severity, "📢")
            url = f"{server}/{key}/{emoji} {alert.rule_name}/{alert.message}"
            requests.get(url, timeout=5)
        except Exception as e:
            logger.warning("Bark send failed: %s", e)


class WebhookChannel(AlertChannel):
    """Webhook 通知 (POST JSON)."""

    def __init__(self, url: str) -> None:
        self._url = url

    def send(self, alert: Alert) -> None:
        try:
            import requests

            requests.post(self._url, json=alert.to_dict(), timeout=5)
        except Exception as e:
            logger.warning("Webhook send failed: %s", e)


# ─── 告警管理器 ───


class AlertManager:
    """告警管理器."""

    def __init__(self) -> None:
        self._rules: dict[str, AlertRule] = {}
        self._channels: list[AlertChannel] = [LogChannel()]  # 默認日誌通知
        self._history: list[Alert] = []
        self._last_fired: dict[str, float] = {}
        self._max_history = 500

    def add_rule(self, rule: AlertRule) -> None:
        self._rules[rule.name] = rule

    def add_channel(self, channel: AlertChannel) -> None:
        self._channels.append(channel)

    def check(self, data: dict[str, Any]) -> list[Alert]:
        """檢查所有規則，觸發告警."""
        fired: list[Alert] = []
        now = time.time()

        for rule in self._rules.values():
            if not rule.enabled:
                continue

            # 冷卻檢查
            last = self._last_fired.get(rule.name, 0)
            if now - last < rule.cooldown_seconds:
                continue

            try:
                if rule.condition(data):
                    msg = rule.message_template.format(name=rule.name, **data)
                    alert = Alert(
                        rule_name=rule.name,
                        severity=rule.severity,
                        message=msg,
                        data=data,
                    )
                    fired.append(alert)
                    self._fire(alert)
                    self._last_fired[rule.name] = now
            except Exception:
                logger.exception("Alert rule [%s] check failed", rule.name)

        return fired

    def _fire(self, alert: Alert) -> None:
        """觸發告警."""
        self._history.append(alert)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        for ch in self._channels:
            try:
                ch.send(alert)
            except Exception:
                logger.exception("Alert channel send failed")

    def history(self, limit: int = 50) -> list[Alert]:
        return self._history[-limit:]

    @property
    def rules(self) -> dict[str, AlertRule]:
        return dict(self._rules)


# ─── 預設規則 ───


def create_default_rules() -> list[AlertRule]:
    """建立預設告警規則."""
    return [
        AlertRule(
            name="high_drawdown",
            condition=lambda m: m.get("max_drawdown_pct", 0) > 20,
            message_template="⚠️ 最大回撤 {max_drawdown_pct:.1f}% 超過 20%",
            severity=AlertSeverity.CRITICAL,
            cooldown_seconds=600,
        ),
        AlertRule(
            name="low_winrate",
            condition=lambda m: m.get("win_rate_pct", 100) < 30 and m.get("num_trades", 0) > 10,
            message_template="⚠️ 勝率僅 {win_rate_pct:.1f}% ({num_trades} 筆交易)",
            severity=AlertSeverity.WARNING,
            cooldown_seconds=1800,
        ),
        AlertRule(
            name="negative_sharpe",
            condition=lambda m: m.get("sharpe_ratio", 0) < -1,
            message_template="🚨 Sharpe Ratio {sharpe_ratio:.2f} 過低",
            severity=AlertSeverity.CRITICAL,
            cooldown_seconds=3600,
        ),
        AlertRule(
            name="high_consecutive_loss",
            condition=lambda m: m.get("max_consec_loss", 0) > 5,
            message_template="⚠️ 連續虧損 {max_consec_loss} 次",
            severity=AlertSeverity.WARNING,
            cooldown_seconds=600,
        ),
    ]


# ─── 全域實例 ───

_alert_manager: AlertManager | None = None


def get_alert_manager() -> AlertManager:
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
        # 加載預設規則
        for rule in create_default_rules():
            _alert_manager.add_rule(rule)
        # 嘗試加載 Bark
        if os.getenv("BARK_KEY"):
            _alert_manager.add_channel(BarkChannel())
    return _alert_manager
