"""
數據驗證模組 — OHLCV 數據品質檢查

功能：
- 完整性檢查（缺失值、NaN）
- 一致性檢查（OHLC 邏輯）
- 異常值檢測（極端跳空、零成交量）
- 時間戳連續性
- 數據清洗建議

用法：
    from src.data.validators import validate_ohlcv, OHLCVReport

    report = validate_ohlcv(rows)
    if not report.is_valid:
        print(report.summary())
    clean_rows = report.clean(rows)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ValidationIssue:
    """數據品質問題."""

    index: int
    field: str
    severity: str  # "error", "warning"
    message: str
    value: Any = None


@dataclass(slots=True)
class OHLCVReport:
    """OHLCV 數據驗證報告."""

    total_bars: int = 0
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not any(i.severity == "error" for i in self.issues)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "warning")

    @property
    def quality_score(self) -> float:
        """數據品質評分 (0~100)."""
        if self.total_bars == 0:
            return 0.0
        error_ratio = self.error_count / self.total_bars
        warning_ratio = self.warning_count / self.total_bars
        return max(0.0, 100 * (1 - error_ratio * 5 - warning_ratio * 1))

    def summary(self) -> str:
        lines = [
            f"OHLCV 數據驗證: {'✅ 通過' if self.is_valid else '❌ 失敗'}",
            f"  總 K 線數: {self.total_bars}",
            f"  錯誤: {self.error_count}，警告: {self.warning_count}",
            f"  品質評分: {self.quality_score:.1f}/100",
        ]
        for issue in self.issues[:20]:
            icon = "❌" if issue.severity == "error" else "⚠️"
            lines.append(f"  {icon} [{issue.field}] #{issue.index}: {issue.message}")
        if len(self.issues) > 20:
            lines.append(f"  ... 還有 {len(self.issues) - 20} 個問題")
        return "\n".join(lines)

    def clean(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        根據驗證結果清洗數據.

        移除有 error 的行，修復 warning 的行.
        """
        error_indices = {i.index for i in self.issues if i.severity == "error"}
        cleaned = []
        for idx, row in enumerate(rows):
            if idx in error_indices:
                continue
            # 修復 NaN
            fixed = {}
            for k, v in row.items():
                if isinstance(v, float) and math.isnan(v):
                    fixed[k] = 0.0
                else:
                    fixed[k] = v
            cleaned.append(fixed)
        return cleaned


def validate_ohlcv(
    rows: list[dict[str, Any]],
    check_timestamps: bool = True,
    check_volume: bool = True,
    outlier_threshold: float = 0.5,
) -> OHLCVReport:
    """
    驗證 OHLCV 數據品質.

    Args:
        rows: K 線數據列表
        check_timestamps: 是否檢查時間戳連續性
        check_volume: 是否檢查成交量
        outlier_threshold: 異常跳空閾值（50%）

    Returns:
        OHLCVReport
    """
    report = OHLCVReport(total_bars=len(rows))

    if not rows:
        report.issues.append(ValidationIssue(0, "data", "error", "無數據"))
        return report

    required_fields = ["timestamp", "open", "high", "low", "close"]

    for i, row in enumerate(rows):
        # 1. 必要欄位檢查
        for req_field in required_fields:
            if req_field not in row:
                report.issues.append(ValidationIssue(i, req_field, "error", f"缺少欄位 {req_field}"))

        if "timestamp" not in row or "open" not in row:
            continue

        o, h, l, c = row.get("open", 0), row.get("high", 0), row.get("low", 0), row.get("close", 0)
        ts = row.get("timestamp", 0)
        vol = row.get("volume", 0)

        # 2. NaN / None 檢查
        for fld, val in [("open", o), ("high", h), ("low", l), ("close", c)]:
            if val is None or (isinstance(val, float) and math.isnan(val)):
                report.issues.append(ValidationIssue(i, fld, "error", f"{fld} 為 NaN/None", val))

        if not isinstance(o, (int, float)) or not isinstance(c, (int, float)):
            continue

        # 3. OHLC 邏輯一致性
        if h < l:
            report.issues.append(ValidationIssue(i, "high/low", "error", f"high({h}) < low({l})"))

        if h < o and h < c:
            report.issues.append(ValidationIssue(i, "high", "warning", f"high({h}) 低於 open({o}) 和 close({c})"))

        if l > o and l > c:
            report.issues.append(ValidationIssue(i, "low", "warning", f"low({l}) 高於 open({o}) 和 close({c})"))

        # 4. 負值檢查
        for fld, val in [("open", o), ("high", h), ("low", l), ("close", c)]:
            if val < 0:
                report.issues.append(ValidationIssue(i, fld, "error", f"{fld} 為負值: {val}"))

        # 5. 成交量檢查
        if check_volume and vol is not None:
            if vol < 0:
                report.issues.append(ValidationIssue(i, "volume", "error", f"成交量為負: {vol}"))

        # 6. 時間戳連續性
        if check_timestamps and i > 0:
            prev_ts = rows[i - 1].get("timestamp", 0)
            if ts <= prev_ts:
                report.issues.append(ValidationIssue(i, "timestamp", "error", f"時間戳未遞增: {ts} <= {prev_ts}"))

        # 7. 異常跳空（開盤價與前一根收盤價差距過大）
        if i > 0 and outlier_threshold > 0:
            prev_close = rows[i - 1].get("close", 0)
            if prev_close and prev_close > 0 and o > 0:
                gap_pct = abs(o - prev_close) / prev_close
                if gap_pct > outlier_threshold:
                    report.issues.append(
                        ValidationIssue(
                            i,
                            "gap",
                            "warning",
                            f"異常跳空: {gap_pct * 100:.1f}% (前收 {prev_close} → 開 {o})",
                            gap_pct,
                        )
                    )

        # 8. 零價格
        if o == 0 and h == 0 and l == 0 and c == 0:
            report.issues.append(ValidationIssue(i, "price", "error", "所有價格為零"))

    return report


def clean_ohlcv(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """快捷清洗函數 — 驗證 + 清洗一步完成."""
    report = validate_ohlcv(rows)
    return report.clean(rows)
