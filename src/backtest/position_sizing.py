# 倉位管理模塊 — 凱利公式 + 固定比例 + 固定金額
from __future__ import annotations

import math
from typing import Any


def kelly_fraction(win_rate: float, avg_win: float, avg_loss: float, max_fraction: float = 0.25) -> float:
    """
    凱利公式計算最優倉位比例。
    win_rate: 勝率 (0~1)
    avg_win: 平均盈利金額
    avg_loss: 平均虧損金額（正數）
    max_fraction: 上限（防止過度集中）
    回傳: 建議投入資金比例 (0~max_fraction)
    """
    if avg_loss <= 0 or avg_win <= 0 or win_rate <= 0:
        return 0.0
    b = avg_win / avg_loss
    q = 1 - win_rate
    kelly = (win_rate * b - q) / b
    return max(0.0, min(kelly, max_fraction))


def fixed_fraction(equity: float, risk_pct: float = 2.0) -> float:
    """固定比例倉位：每次交易風險不超過 equity 的 risk_pct%"""
    return equity * risk_pct / 100


def fixed_amount(amount: float = 1000.0) -> float:
    """固定金額倉位"""
    return amount


def compute_position_size(
    method: str,
    equity: float,
    entry_price: float,
    stop_loss_price: float | None = None,
    win_rate: float = 0.5,
    avg_win: float = 1.0,
    avg_loss: float = 1.0,
    risk_pct: float = 2.0,
    fixed_amt: float = 1000.0,
    leverage: float = 1.0,
) -> dict[str, Any]:
    """
    統一倉位計算接口。
    method: "kelly", "fixed_fraction", "fixed_amount", "full"
    回傳: {"size": 金額, "fraction": 比例, "lots": 合約數}
    """
    if method == "kelly":
        frac = kelly_fraction(win_rate, avg_win, avg_loss)
        size = equity * frac * leverage
    elif method == "fixed_fraction":
        if stop_loss_price and entry_price and stop_loss_price != entry_price:
            risk_per_unit = abs(entry_price - stop_loss_price)
            risk_amount = fixed_fraction(equity, risk_pct)
            units = risk_amount / risk_per_unit if risk_per_unit > 0 else 0
            size = units * entry_price
            frac = size / equity if equity > 0 else 0
        else:
            frac = risk_pct / 100
            size = equity * frac * leverage
    elif method == "fixed_amount":
        size = min(fixed_amt * leverage, equity)
        frac = size / equity if equity > 0 else 0
    else:  # "full"
        size = equity * leverage
        frac = 1.0

    lots = size / entry_price if entry_price > 0 else 0

    return {
        "method": method,
        "size": round(size, 2),
        "fraction": round(frac, 4),
        "lots": round(lots, 6),
        "equity": equity,
        "leverage": leverage,
    }


def analyze_position_from_history(trades: list[dict]) -> dict[str, Any]:
    """從歷史交易計算凱利公式建議"""
    if not trades:
        return {"kelly_fraction": 0, "win_rate": 0, "avg_win": 0, "avg_loss": 0, "recommendation": "數據不足"}

    wins = [t["profit"] for t in trades if t.get("profit", 0) > 0]
    losses = [abs(t["profit"]) for t in trades if t.get("profit", 0) < 0]

    win_rate = len(wins) / len(trades) if trades else 0
    avg_win = sum(wins) / len(wins) if wins else 0
    avg_loss = sum(losses) / len(losses) if losses else 0

    kf = kelly_fraction(win_rate, avg_win, avg_loss)

    if kf <= 0:
        rec = "⛔ 凱利公式建議不交易（期望值為負）"
    elif kf < 0.05:
        rec = "⚠️ 建議極輕倉（<5% 資金）"
    elif kf < 0.15:
        rec = "✅ 建議適度倉位"
    else:
        rec = f"🟢 凱利建議 {kf*100:.1f}%（已限制上限 25%）"

    return {
        "kelly_fraction": round(kf, 4),
        "win_rate": round(win_rate, 4),
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "total_trades": len(trades),
        "recommendation": rec,
    }
