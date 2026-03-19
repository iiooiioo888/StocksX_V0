"""test_alerts.py — AlertManager 單元測試."""

import os
import sys
import time

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.core.alerts import (
    Alert,
    AlertChannel,
    AlertManager,
    AlertRule,
    AlertSeverity,
    LogChannel,
    create_default_rules,
)


# ─── Alert 測試 ───


class TestAlert:
    """測試 Alert 資料類別."""

    def test_timestamp_auto_set(self):
        """timestamp 應自動設定."""
        alert = Alert(rule_name="test", severity=AlertSeverity.INFO, message="hello")
        assert alert.timestamp > 0

    def test_to_dict(self):
        """to_dict 應返回正確字典."""
        alert = Alert(
            rule_name="test",
            severity=AlertSeverity.WARNING,
            message="warn",
            data={"key": "value"},
        )
        d = alert.to_dict()
        assert d["rule"] == "test"
        assert d["severity"] == "warning"
        assert "time" in d


# ─── AlertRule 測試 ───


class TestAlertRule:
    """測試 AlertRule."""

    def test_default_cooldown(self):
        """預設冷卻時間應為 300 秒."""
        rule = AlertRule(name="test", condition=lambda m: True)
        assert rule.cooldown_seconds == 300

    def test_enabled_by_default(self):
        """規則預設啟用."""
        rule = AlertRule(name="test", condition=lambda m: True)
        assert rule.enabled is True


# ─── AlertManager 測試 ───


class TestAlertManager:
    """測試 AlertManager."""

    def _make_manager(self) -> AlertManager:
        """建立不帶預設規則的 AlertManager."""
        return AlertManager()

    def test_add_rule(self):
        """add_rule 應註冊規則."""
        mgr = self._make_manager()
        rule = AlertRule(name="test", condition=lambda m: True)
        mgr.add_rule(rule)
        assert "test" in mgr.rules

    def test_check_triggers_alert(self):
        """滿足條件時 check 應觸發告警."""
        mgr = self._make_manager()
        mgr.add_rule(AlertRule(
            name="high_value",
            condition=lambda m: m.get("value", 0) > 100,
            message_template="Value too high: {value}",
            cooldown_seconds=0,
        ))

        fired = mgr.check({"value": 150})
        assert len(fired) == 1
        assert fired[0].rule_name == "high_value"

    def test_check_no_trigger(self):
        """不滿足條件時不觸發."""
        mgr = self._make_manager()
        mgr.add_rule(AlertRule(
            name="high_value",
            condition=lambda m: m.get("value", 0) > 100,
            cooldown_seconds=0,
        ))

        fired = mgr.check({"value": 50})
        assert len(fired) == 0

    def test_cooldown(self):
        """冷卻期內不重複觸發."""
        mgr = self._make_manager()
        mgr.add_rule(AlertRule(
            name="test",
            condition=lambda m: True,
            cooldown_seconds=999,
        ))

        mgr.check({})
        fired = mgr.check({})
        assert len(fired) == 0

    def test_disabled_rule(self):
        """已停用的規則不應觸發."""
        mgr = self._make_manager()
        mgr.add_rule(AlertRule(
            name="disabled",
            condition=lambda m: True,
            enabled=False,
            cooldown_seconds=0,
        ))

        fired = mgr.check({})
        assert len(fired) == 0

    def test_history(self):
        """觸發的告警應記錄在 history 中."""
        mgr = self._make_manager()
        mgr.add_rule(AlertRule(
            name="test",
            condition=lambda m: True,
            cooldown_seconds=0,
        ))

        mgr.check({})
        mgr.check({})
        history = mgr.history()
        assert len(history) == 2

    def test_history_limit(self):
        """history 應遵守 limit."""
        mgr = self._make_manager()
        mgr.add_rule(AlertRule(
            name="test",
            condition=lambda m: True,
            cooldown_seconds=0,
        ))

        for _ in range(10):
            mgr.check({})

        history = mgr.history(limit=3)
        assert len(history) == 3


# ─── AlertChannel 測試 ───


class TestAlertChannel:
    """測試通知渠道."""

    def test_log_channel(self):
        """LogChannel 應可正常發送."""
        channel = LogChannel()
        alert = Alert(rule_name="test", severity=AlertSeverity.INFO, message="hello")
        # 不應拋出異常
        channel.send(alert)

    def test_custom_channel(self):
        """自定義渠道應被呼叫."""
        sent = []

        class CaptureChannel(AlertChannel):
            def send(self, alert):
                sent.append(alert)

        mgr = AlertManager()
        mgr.add_rule(AlertRule(name="t", condition=lambda m: True, cooldown_seconds=0))
        mgr.add_channel(CaptureChannel())
        mgr.check({})

        assert len(sent) == 1
        assert sent[0].rule_name == "t"


# ─── 預設規則測試 ───


class TestDefaultRules:
    """測試預設告警規則."""

    def test_create_default_rules(self):
        """create_default_rules 應返回多個規則."""
        rules = create_default_rules()
        assert len(rules) >= 3
        names = {r.name for r in rules}
        assert "high_drawdown" in names
        assert "low_winrate" in names
        assert "negative_sharpe" in names
