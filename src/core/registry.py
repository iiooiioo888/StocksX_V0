"""
Strategy Registry — 裝飾器註冊模式

取代 _STRATEGY_FUNCS 手動字典。
策略通過 @register_strategy 裝飾器自動註冊，包含元數據。

架構：
  @register_strategy(name="sma_cross", label="雙均線交叉", category="trend")
  def sma_cross(rows, fast=10, slow=30) -> list[int]: ...

  registry.get("sma_cross")  # → StrategyEntry(func, metadata)
  registry.list_by_category("trend")  # → [...]
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(slots=True)
class StrategyMeta:
    """策略元數據."""

    name: str
    label: str
    category: str  # trend / oscillator / breakout / mean_reversion / benchmark
    description: str = ""
    params: list[str] = field(default_factory=list)
    defaults: dict[str, Any] = field(default_factory=dict)
    param_grid: dict[str, list[Any]] = field(default_factory=dict)


@dataclass(slots=True)
class StrategyEntry:
    """策略註冊表條目."""

    func: Callable[..., list[int]]
    meta: StrategyMeta


class StrategyRegistry:
    """策略註冊表."""

    def __init__(self) -> None:
        self._entries: dict[str, StrategyEntry] = {}

    def register(
        self,
        func: Callable[..., list[int]],
        name: str,
        label: str,
        category: str,
        description: str = "",
        params: list[str] | None = None,
        defaults: dict[str, Any] | None = None,
        param_grid: dict[str, list[Any]] | None = None,
    ) -> Callable[..., list[int]]:
        """註冊策略."""
        meta = StrategyMeta(
            name=name,
            label=label,
            category=category,
            description=description or func.__doc__ or "",
            params=params or [],
            defaults=defaults or {},
            param_grid=param_grid or {},
        )
        self._entries[name] = StrategyEntry(func=func, meta=meta)
        return func

    def get(self, name: str) -> StrategyEntry | None:
        return self._entries.get(name)

    def get_signal(self, name: str, rows: list[dict[str, Any]], **kwargs: Any) -> list[int]:
        """取得信號."""
        entry = self._entries.get(name)
        if not entry:
            return [0] * len(rows)
        if not entry.meta.params:
            return entry.func(rows)
        return entry.func(rows, **kwargs)

    def list_all(self) -> list[StrategyMeta]:
        return [e.meta for e in self._entries.values()]

    def list_by_category(self, category: str) -> list[StrategyMeta]:
        return [e.meta for e in self._entries.values() if e.meta.category == category]

    @property
    def names(self) -> list[str]:
        return list(self._entries.keys())


# ─── 全域註冊表 ───

registry = StrategyRegistry()


def register_strategy(
    name: str,
    label: str,
    category: str,
    description: str = "",
    params: list[str] | None = None,
    defaults: dict[str, Any] | None = None,
    param_grid: dict[str, list[Any]] | None = None,
) -> Callable:
    """裝飾器：自動註冊策略."""

    def decorator(func: Callable[..., list[int]]) -> Callable[..., list[int]]:
        registry.register(
            func=func,
            name=name,
            label=label,
            category=category,
            description=description,
            params=params,
            defaults=defaults,
            param_grid=param_grid,
        )
        return func

    return decorator
