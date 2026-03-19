"""
報告匯出模組 — 生成回測報告（HTML/JSON）

功能：
- 生成結構化 HTML 報告
- 匯出回測結果為 JSON
- 生成策略對比報告

用法：
    from src.utils.report import BacktestReportGenerator

    gen = BacktestReportGenerator(report, strategy_name="SMA Cross")
    html = gen.to_html()
    gen.save_html("report.html")
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from datetime import datetime
from typing import Any


class BacktestReportGenerator:
    """回測報告生成器."""

    def __init__(self, report_data: dict[str, Any], strategy_name: str = "Unknown", symbol: str = "") -> None:
        self._data = report_data
        self._strategy = strategy_name
        self._symbol = symbol
        self._generated_at = datetime.now().isoformat()

    def to_json(self, indent: int = 2) -> str:
        """匯出為 JSON."""
        output = {
            "meta": {
                "strategy": self._strategy,
                "symbol": self._symbol,
                "generated_at": self._generated_at,
                "version": "5.2",
            },
            "metrics": self._data.get("metrics", {}),
            "trades_count": len(self._data.get("trades", [])),
            "equity_curve_length": len(self._data.get("equity_curve", [])),
            "trades": self._data.get("trades", [])[-50:],  # 最近 50 筆
            "error": self._data.get("error"),
        }
        return json.dumps(output, ensure_ascii=False, indent=indent, default=str)

    def to_html(self) -> str:
        """生成 HTML 報告."""
        m = self._data.get("metrics", {})
        trades = self._data.get("trades", [])
        error = self._data.get("error")

        if error:
            return f"<html><body><h1>❌ 回測錯誤</h1><p>{error}</p></body></html>"

        # 指標卡片
        metrics_html = ""
        metric_items = [
            ("總報酬", f"{m.get('total_return_pct', 0):+.2f}%", "#00cc96" if m.get('total_return_pct', 0) > 0 else "#ef553b"),
            ("年化報酬", f"{m.get('annual_return_pct', 0):+.2f}%", "#00cc96" if m.get('annual_return_pct', 0) > 0 else "#ef553b"),
            ("最大回撤", f"{m.get('max_drawdown_pct', 0):.2f}%", "#ef553b"),
            ("Sharpe", f"{m.get('sharpe_ratio', 0):.2f}", "#667eea"),
            ("Sortino", f"{m.get('sortino_ratio', 0):.2f}", "#667eea"),
            ("勝率", f"{m.get('win_rate_pct', 0):.1f}%", "#00cc96" if m.get('win_rate_pct', 0) > 50 else "#ef553b"),
            ("交易次數", str(m.get('num_trades', 0)), "#8b949e"),
            ("利潤因子", f"{m.get('profit_factor', 0):.2f}", "#667eea"),
        ]

        for label, value, color in metric_items:
            metrics_html += f"""
            <div style="display:inline-block;width:22%;margin:1%;padding:16px;background:rgba(255,255,255,0.05);border-radius:12px;text-align:center;">
                <div style="color:#8b949e;font-size:12px;">{label}</div>
                <div style="color:{color};font-size:24px;font-weight:700;margin:8px 0;">{value}</div>
            </div>"""

        # 交易明細
        trades_html = ""
        for t in trades[-20:]:  # 最近 20 筆
            pnl = t.get("pnl_pct", 0)
            color = "#00cc96" if pnl > 0 else "#ef553b"
            side = "多" if t.get("side", 0) == 1 else "空"
            reason = t.get("exit_reason", "signal")
            trades_html += f"""
            <tr>
                <td style="padding:8px;border-bottom:1px solid #30363d;">{side}</td>
                <td style="padding:8px;border-bottom:1px solid #30363d;">{t.get('entry_price', 0):.2f}</td>
                <td style="padding:8px;border-bottom:1px solid #30363d;">{t.get('exit_price', 0):.2f}</td>
                <td style="padding:8px;border-bottom:1px solid #30363d;color:{color};">{pnl:+.4f}%</td>
                <td style="padding:8px;border-bottom:1px solid #30363d;color:{color};">{t.get('profit', 0):+.2f}</td>
                <td style="padding:8px;border-bottom:1px solid #30363d;">{reason}</td>
            </tr>"""

        html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StocksX 回測報告 — {self._strategy}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background: #0e1117; color: #e0e0e0;
            font-family: 'Segoe UI', system-ui, sans-serif;
            padding: 40px 20px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{
            font-size: 28px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
        }}
        .meta {{ color: #8b949e; margin-bottom: 24px; }}
        .section {{ margin: 32px 0; }}
        .section h2 {{ font-size: 20px; color: #58a6ff; margin-bottom: 16px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ text-align: left; padding: 12px 8px; border-bottom: 2px solid #30363d; color: #8b949e; font-size: 12px; text-transform: uppercase; }}
        .footer {{ text-align: center; color: #484f58; font-size: 12px; margin-top: 40px; padding-top: 20px; border-top: 1px solid #21262d; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 回測報告 — {self._strategy}</h1>
        <div class="meta">
            交易對: {self._symbol or 'N/A'} · 生成時間: {self._generated_at} · StocksX v5.2
        </div>

        <div class="section">
            <h2>📈 績效指標</h2>
            {metrics_html}
        </div>

        <div class="section">
            <h2>📋 最近交易明細</h2>
            <table>
                <thead>
                    <tr>
                        <th>方向</th><th>進場價</th><th>出場價</th>
                        <th>報酬率</th><th>損益</th><th>出場原因</th>
                    </tr>
                </thead>
                <tbody>{trades_html}</tbody>
            </table>
        </div>

        <div class="section">
            <h2>📊 風險指標</h2>
            <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;">
                <div style="background:rgba(255,255,255,0.05);padding:16px;border-radius:12px;">
                    <div style="color:#8b949e;font-size:12px;">手續費總計</div>
                    <div style="color:#f0f0f0;font-size:20px;">${m.get('total_fees', 0):,.2f}</div>
                </div>
                <div style="background:rgba(255,255,255,0.05);padding:16px;border-radius:12px;">
                    <div style="color:#8b949e;font-size:12px;">Omega Ratio</div>
                    <div style="color:#667eea;font-size:20px;">{m.get('omega_ratio', 0):.2f}</div>
                </div>
                <div style="background:rgba(255,255,255,0.05);padding:16px;border-radius:12px;">
                    <div style="color:#8b949e;font-size:12px;">Tail Ratio</div>
                    <div style="color:#667eea;font-size:20px;">{m.get('tail_ratio', 0):.2f}</div>
                </div>
            </div>
        </div>

        <div class="footer">
            StocksX v5.2 · 回測結果基於歷史數據，不代表未來表現 · 僅供研究用途
        </div>
    </div>
</body>
</html>"""
        return html

    def save_html(self, filepath: str) -> str:
        """儲存 HTML 報告到檔案."""
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.to_html())
        return filepath

    def save_json(self, filepath: str) -> str:
        """儲存 JSON 報告到檔案."""
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.to_json())
        return filepath


class StrategyComparisonGenerator:
    """多策略對比報告生成器."""

    def __init__(self, results: dict[str, dict[str, Any]], symbol: str = "") -> None:
        self._results = results
        self._symbol = symbol

    def to_html(self) -> str:
        """生成策略對比 HTML."""
        rows_html = ""
        sorted_results = sorted(
            self._results.items(),
            key=lambda x: x[1].get("metrics", {}).get("sharpe_ratio", 0),
            reverse=True,
        )

        for rank, (name, data) in enumerate(sorted_results, 1):
            m = data.get("metrics", {})
            ret = m.get("total_return_pct", 0)
            dd = m.get("max_drawdown_pct", 0)
            sharpe = m.get("sharpe_ratio", 0)
            wr = m.get("win_rate_pct", 0)

            ret_color = "#00cc96" if ret > 0 else "#ef553b"
            medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"

            rows_html += f"""
            <tr>
                <td style="padding:12px 8px;border-bottom:1px solid #30363d;font-size:18px;">{medal}</td>
                <td style="padding:12px 8px;border-bottom:1px solid #30363d;font-weight:600;">{name}</td>
                <td style="padding:12px 8px;border-bottom:1px solid #30363d;color:{ret_color};">{ret:+.2f}%</td>
                <td style="padding:12px 8px;border-bottom:1px solid #30363d;color:#ef553b;">{dd:.2f}%</td>
                <td style="padding:12px 8px;border-bottom:1px solid #30363d;color:#667eea;">{sharpe:.2f}</td>
                <td style="padding:12px 8px;border-bottom:1px solid #30363d;">{wr:.1f}%</td>
                <td style="padding:12px 8px;border-bottom:1px solid #30363d;">{m.get('num_trades', 0)}</td>
            </tr>"""

        html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>StocksX 策略對比報告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ background: #0e1117; color: #e0e0e0; font-family: system-ui, sans-serif; padding: 40px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ background: linear-gradient(135deg, #667eea, #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 24px; }}
        th {{ text-align: left; padding: 12px 8px; border-bottom: 2px solid #30363d; color: #8b949e; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 策略對比報告</h1>
        <p style="color:#8b949e;">交易對: {self._symbol or 'N/A'} · {len(self._results)} 個策略</p>
        <table>
            <thead>
                <tr><th>#</th><th>策略</th><th>總報酬</th><th>最大回撤</th><th>Sharpe</th><th>勝率</th><th>交易數</th></tr>
            </thead>
            <tbody>{rows_html}</tbody>
        </table>
    </div>
</body>
</html>"""
        return html

    def save_html(self, filepath: str) -> str:
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.to_html())
        return filepath
