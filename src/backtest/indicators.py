"""
進階技術指標 — 擴展策略庫

新增指標：
- ATR (Average True Range)
- OBV (On-Balance Volume)
- CCI (Commodity Channel Index)
- MFI (Money Flow Index)
- Aroon Oscillator
- Stochastic RSI
- Keltner Channel
- Heikin-Ashi
- Volume Profile
- Pivot Points

用法：
    from src.backtest.indicators import atr, obv, cci, heikin_ashi
"""

from __future__ import annotations

from typing import Any


def true_range(rows: list[dict[str, Any]]) -> list[float]:
    """真實波幅 (TR)."""
    if not rows:
        return []
    tr = [rows[0]["high"] - rows[0]["low"]]
    for i in range(1, len(rows)):
        h = rows[i]["high"]
        l = rows[i]["low"]
        prev_close = rows[i - 1]["close"]
        tr.append(max(h - l, abs(h - prev_close), abs(l - prev_close)))
    return tr


def atr(rows: list[dict[str, Any]], period: int = 14) -> list[float]:
    """平均真實波幅 (ATR)."""
    tr = true_range(rows)
    if len(tr) < period:
        return [0.0] * len(tr)
    result = [0.0] * (period - 1)
    # 初始 ATR = TR 的簡單平均
    result.append(sum(tr[:period]) / period)
    # Wilder 平滑
    for i in range(period, len(tr)):
        result.append((result[-1] * (period - 1) + tr[i]) / period)
    return result


def obv(rows: list[dict[str, Any]]) -> list[float]:
    """能量潮指標 (OBV)."""
    if not rows:
        return []
    result = [0.0]
    for i in range(1, len(rows)):
        if rows[i]["close"] > rows[i - 1]["close"]:
            result.append(result[-1] + rows[i]["volume"])
        elif rows[i]["close"] < rows[i - 1]["close"]:
            result.append(result[-1] - rows[i]["volume"])
        else:
            result.append(result[-1])
    return result


def cci(rows: list[dict[str, Any]], period: int = 20) -> list[float]:
    """商品通道指標 (CCI)."""
    if len(rows) < period:
        return [0.0] * len(rows)
    result = [0.0] * (period - 1)
    for i in range(period - 1, len(rows)):
        typical = [(rows[j]["high"] + rows[j]["low"] + rows[j]["close"]) / 3 for j in range(i - period + 1, i + 1)]
        sma = sum(typical) / period
        mad = sum(abs(t - sma) for t in typical) / period
        if mad == 0:
            result.append(0.0)
        else:
            result.append((typical[-1] - sma) / (0.015 * mad))
    return result


def mfi(rows: list[dict[str, Any]], period: int = 14) -> list[float]:
    """資金流量指標 (MFI)."""
    if len(rows) < period + 1:
        return [50.0] * len(rows)
    result = [50.0] * period
    for i in range(period, len(rows)):
        pos_mf = 0.0
        neg_mf = 0.0
        for j in range(i - period + 1, i + 1):
            tp = (rows[j]["high"] + rows[j]["low"] + rows[j]["close"]) / 3
            prev_tp = (rows[j - 1]["high"] + rows[j - 1]["low"] + rows[j - 1]["close"]) / 3
            mf = tp * rows[j]["volume"]
            if tp > prev_tp:
                pos_mf += mf
            elif tp < prev_tp:
                neg_mf += mf
        if neg_mf == 0:
            result.append(100.0)
        else:
            mfi_ratio = pos_mf / neg_mf
            result.append(100 - (100 / (1 + mfi_ratio)))
    return result


def aroon(rows: list[dict[str, Any]], period: int = 25) -> tuple[list[float], list[float], list[float]]:
    """
    Aroon 指標.

    Returns: (aroon_up, aroon_down, aroon_osc)
    """
    n = len(rows)
    if n < period:
        zeros = [0.0] * n
        return zeros, zeros, zeros

    up = [0.0] * (period - 1)
    down = [0.0] * (period - 1)
    osc = [0.0] * (period - 1)

    for i in range(period - 1, n):
        window = rows[i - period + 1 : i + 1]
        highs = [r["high"] for r in window]
        lows = [r["low"] for r in window]
        max_idx = highs.index(max(highs))
        min_idx = lows.index(min(lows))
        days_since_high = period - 1 - max_idx
        days_since_low = period - 1 - min_idx
        a_up = ((period - days_since_high) / period) * 100
        a_down = ((period - days_since_low) / period) * 100
        up.append(a_up)
        down.append(a_down)
        osc.append(a_up - a_down)

    return up, down, osc


def stochastic_rsi(
    rows: list[dict[str, Any]],
    rsi_period: int = 14,
    stoch_period: int = 14,
    k_period: int = 3,
    d_period: int = 3,
) -> tuple[list[float], list[float]]:
    """
    Stochastic RSI.

    Returns: (%K, %D)
    """
    closes = [r["close"] for r in rows]
    n = len(closes)

    # 先算 RSI
    if n < rsi_period + 1:
        return [50.0] * n, [50.0] * n

    rsi_vals = [50.0] * rsi_period
    for i in range(rsi_period, n):
        gains = []
        losses = []
        for j in range(i - rsi_period + 1, i + 1):
            chg = closes[j] - closes[j - 1]
            gains.append(max(chg, 0))
            losses.append(max(-chg, 0))
        avg_g = sum(gains) / rsi_period
        avg_l = sum(losses) / rsi_period
        if avg_l == 0:
            rsi_vals.append(100.0)
        else:
            rsi_vals.append(100 - 100 / (1 + avg_g / avg_l))

    # Stochastic of RSI
    if len(rsi_vals) < stoch_period:
        return [50.0] * n, [50.0] * n

    stoch_k = [50.0] * (rsi_period + stoch_period - 1)
    for i in range(rsi_period + stoch_period - 1, n):
        window = rsi_vals[i - stoch_period + 1 : i + 1]
        lowest = min(window)
        highest = max(window)
        if highest == lowest:
            stoch_k.append(50.0)
        else:
            stoch_k.append((rsi_vals[i] - lowest) / (highest - lowest) * 100)

    # %D = SMA of %K
    stoch_d = [50.0] * (len(stoch_k) - k_period + 1)
    if len(stoch_k) >= k_period:
        stoch_d = []
        for i in range(k_period - 1, len(stoch_k)):
            stoch_d.append(sum(stoch_k[i - k_period + 1 : i + 1]) / k_period)
        stoch_d = [50.0] * (len(stoch_k) - len(stoch_d)) + stoch_d

    return stoch_k, stoch_d


def heikin_ashi(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Heikin-Ashi K 線 — 平滑趨勢的蠟燭圖變體.

    Returns: [{"open", "high", "low", "close", "timestamp"}, ...]
    """
    if not rows:
        return []

    ha_rows = []
    for i, r in enumerate(rows):
        ha_close = (r["open"] + r["high"] + r["low"] + r["close"]) / 4
        if i == 0:
            ha_open = (r["open"] + r["close"]) / 2
        else:
            ha_open = (ha_rows[i - 1]["open"] + ha_rows[i - 1]["close"]) / 2
        ha_high = max(r["high"], ha_open, ha_close)
        ha_low = min(r["low"], ha_open, ha_close)
        ha_rows.append(
            {
                "open": ha_open,
                "high": ha_high,
                "low": ha_low,
                "close": ha_close,
                "timestamp": r["timestamp"],
                "volume": r.get("volume", 0),
            }
        )
    return ha_rows


def keltner_channel(
    rows: list[dict[str, Any]],
    ema_period: int = 20,
    atr_period: int = 10,
    multiplier: float = 2.0,
) -> tuple[list[float], list[float], list[float]]:
    """
    Keltner Channel.

    Returns: (upper, middle, lower)
    """
    closes = [r["close"] for r in rows]
    n = len(closes)

    if n < max(ema_period, atr_period):
        return [0.0] * n, closes[:], [0.0] * n

    # Middle = EMA of close
    middle = [closes[0]]
    k = 2.0 / (ema_period + 1)
    for i in range(1, n):
        middle.append(closes[i] * k + middle[-1] * (1 - k))

    # ATR
    atr_vals = atr(rows, atr_period)

    upper = [middle[i] + multiplier * atr_vals[i] for i in range(n)]
    lower = [middle[i] - multiplier * atr_vals[i] for i in range(n)]

    return upper, middle, lower


def pivot_points(rows: list[dict[str, Any]], method: str = "classic") -> dict[str, list[float]]:
    """
    樞紐點 (Pivot Points).

    method: "classic", "fibonacci", "camarilla", "woodie"

    Returns: {"pivot", "r1", "r2", "r3", "s1", "s2", "s3"}
    """
    n = len(rows)
    result = {k: [0.0] * n for k in ["pivot", "r1", "r2", "r3", "s1", "s2", "s3"]}

    for i in range(1, n):
        prev = rows[i - 1]
        h, l, c = prev["high"], prev["low"], prev["close"]

        if method == "classic":
            p = (h + l + c) / 3
            result["pivot"][i] = p
            result["r1"][i] = 2 * p - l
            result["s1"][i] = 2 * p - h
            result["r2"][i] = p + (h - l)
            result["s2"][i] = p - (h - l)
            result["r3"][i] = h + 2 * (p - l)
            result["s3"][i] = l - 2 * (h - p)
        elif method == "fibonacci":
            p = (h + l + c) / 3
            rng = h - l
            result["pivot"][i] = p
            result["r1"][i] = p + 0.382 * rng
            result["s1"][i] = p - 0.382 * rng
            result["r2"][i] = p + 0.618 * rng
            result["s2"][i] = p - 0.618 * rng
            result["r3"][i] = p + 1.0 * rng
            result["s3"][i] = p - 1.0 * rng
        elif method == "camarilla":
            p = (h + l + c) / 3
            rng = h - l
            result["pivot"][i] = p
            result["r1"][i] = c + rng * 1.1 / 12
            result["r2"][i] = c + rng * 1.1 / 6
            result["r3"][i] = c + rng * 1.1 / 4
            result["s1"][i] = c - rng * 1.1 / 12
            result["s2"][i] = c - rng * 1.1 / 6
            result["s3"][i] = c - rng * 1.1 / 4
        elif method == "woodie":
            p = (h + l + 2 * rows[i]["open"]) / 4 if i > 0 else (h + l + c) / 3
            result["pivot"][i] = p
            result["r1"][i] = 2 * p - l
            result["s1"][i] = 2 * p - h
            result["r2"][i] = p + (h - l)
            result["s2"][i] = p - (h - l)
            result["r3"][i] = h + 2 * (p - l)
            result["s3"][i] = l - 2 * (h - p)

    return result


def volume_profile(rows: list[dict[str, Any]], n_bins: int = 20) -> dict[str, Any]:
    """
    成交量分佈 (Volume Profile).

    Returns: {"bins": [{"price_low", "price_high", "volume", "pct"}], "poc": float, "vah": float, "val": float}
    """
    if not rows:
        return {"bins": [], "poc": 0, "vah": 0, "val": 0}

    prices = [(r["high"] + r["low"] + r["close"]) / 3 for r in rows]
    volumes = [r.get("volume", 0) for r in rows]

    p_min = min(prices)
    p_max = max(prices)
    if p_max == p_min:
        return {"bins": [], "poc": p_max, "vah": p_max, "val": p_min}

    bin_width = (p_max - p_min) / n_bins
    bins = [
        {"price_low": p_min + i * bin_width, "price_high": p_min + (i + 1) * bin_width, "volume": 0.0}
        for i in range(n_bins)
    ]

    for price, vol in zip(prices, volumes):
        idx = min(int((price - p_min) / bin_width), n_bins - 1)
        bins[idx]["volume"] += vol

    total_vol = sum(b["volume"] for b in bins)
    for b in bins:
        b["pct"] = (b["volume"] / total_vol * 100) if total_vol > 0 else 0

    # POC = Point of Control (最高量價位)
    poc_bin = max(bins, key=lambda b: b["volume"])
    poc = (poc_bin["price_low"] + poc_bin["price_high"]) / 2

    # VAH/VAL = Value Area High/Low (70% 成交量區域)
    sorted_bins = sorted(bins, key=lambda b: b["volume"], reverse=True)
    va_vol = 0.0
    va_prices = []
    for b in sorted_bins:
        va_vol += b["volume"]
        va_prices.extend([b["price_low"], b["price_high"]])
        if va_vol >= total_vol * 0.7:
            break

    vah = max(va_prices) if va_prices else p_max
    val = min(va_prices) if va_prices else p_min

    return {"bins": bins, "poc": poc, "vah": vah, "val": val}
