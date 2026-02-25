# 用戶認證與數據管理（SQLite）
from __future__ import annotations

import hashlib
import json
import os
import secrets
import sqlite3
import time
from typing import Any


_DB_PATH = os.path.join("cache", "users.sqlite")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    display_name TEXT DEFAULT '',
    role TEXT DEFAULT 'user',
    created_at REAL NOT NULL,
    last_login REAL DEFAULT 0,
    is_active INTEGER DEFAULT 1
);
CREATE TABLE IF NOT EXISTS backtest_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    created_at REAL NOT NULL,
    symbol TEXT NOT NULL,
    exchange TEXT DEFAULT '',
    timeframe TEXT DEFAULT '',
    strategy TEXT DEFAULT '',
    params TEXT DEFAULT '{}',
    metrics TEXT DEFAULT '{}',
    notes TEXT DEFAULT '',
    is_favorite INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS user_settings (
    user_id INTEGER PRIMARY KEY,
    settings TEXT DEFAULT '{}',
    FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS strategy_presets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    config TEXT NOT NULL,
    created_at REAL NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS watchlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    exchange TEXT DEFAULT 'okx',
    timeframe TEXT DEFAULT '1h',
    strategy TEXT NOT NULL,
    strategy_params TEXT DEFAULT '{}',
    initial_equity REAL DEFAULT 10000,
    is_active INTEGER DEFAULT 1,
    created_at REAL NOT NULL,
    last_check REAL DEFAULT 0,
    last_signal INTEGER DEFAULT 0,
    last_price REAL DEFAULT 0,
    entry_price REAL DEFAULT 0,
    position INTEGER DEFAULT 0,
    pnl_pct REAL DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    condition_type TEXT NOT NULL,
    threshold REAL NOT NULL,
    message TEXT DEFAULT '',
    is_triggered INTEGER DEFAULT 0,
    created_at REAL NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
"""


def _hash_pw(password: str, salt: str = "") -> str:
    if not salt:
        salt = secrets.token_hex(16)
    h = hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()
    return f"{salt}:{h}"


def _verify_pw(password: str, stored: str) -> bool:
    salt = stored.split(":")[0]
    return _hash_pw(password, salt) == stored


class UserDB:
    def __init__(self, db_path: str = _DB_PATH) -> None:
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()
        self._migrate()
        self._ensure_admin()

    def _migrate(self) -> None:
        try:
            self._conn.execute("ALTER TABLE backtest_history ADD COLUMN tags TEXT DEFAULT ''")
            self._conn.commit()
        except sqlite3.OperationalError:
            pass

    def _ensure_admin(self) -> None:
        cur = self._conn.execute("SELECT id FROM users WHERE username='admin'")
        if not cur.fetchone():
            self.register("admin", "admin123", display_name="管理員", role="admin")

    def register(self, username: str, password: str, display_name: str = "", role: str = "user") -> dict | None:
        try:
            pw_hash = _hash_pw(password)
            self._conn.execute(
                "INSERT INTO users (username, password_hash, display_name, role, created_at) VALUES (?,?,?,?,?)",
                (username, pw_hash, display_name or username, role, time.time()),
            )
            self._conn.commit()
            return self.get_user(username)
        except sqlite3.IntegrityError:
            return None

    def login(self, username: str, password: str) -> dict | None:
        cur = self._conn.execute("SELECT * FROM users WHERE username=? AND is_active=1", (username,))
        row = cur.fetchone()
        if not row:
            return None
        if not _verify_pw(password, row["password_hash"]):
            return None
        self._conn.execute("UPDATE users SET last_login=? WHERE id=?", (time.time(), row["id"]))
        self._conn.commit()
        return dict(row)

    def get_user(self, username: str) -> dict | None:
        cur = self._conn.execute("SELECT * FROM users WHERE username=?", (username,))
        row = cur.fetchone()
        return dict(row) if row else None

    def list_users(self) -> list[dict]:
        cur = self._conn.execute("SELECT id, username, display_name, role, created_at, last_login, is_active FROM users ORDER BY id")
        return [dict(r) for r in cur.fetchall()]

    def update_user(self, user_id: int, **kwargs: Any) -> None:
        allowed = {"display_name", "role", "is_active"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return
        set_clause = ", ".join(f"{k}=?" for k in updates)
        self._conn.execute(f"UPDATE users SET {set_clause} WHERE id=?", (*updates.values(), user_id))
        self._conn.commit()

    def change_password(self, user_id: int, new_password: str) -> None:
        pw_hash = _hash_pw(new_password)
        self._conn.execute("UPDATE users SET password_hash=? WHERE id=?", (pw_hash, user_id))
        self._conn.commit()

    def delete_user(self, user_id: int) -> None:
        self._conn.execute("DELETE FROM backtest_history WHERE user_id=?", (user_id,))
        self._conn.execute("DELETE FROM user_settings WHERE user_id=?", (user_id,))
        self._conn.execute("DELETE FROM users WHERE id=?", (user_id,))
        self._conn.commit()

    # ─── 回測歷史 ───
    def save_backtest(self, user_id: int, symbol: str, exchange: str, timeframe: str,
                      strategy: str, params: dict, metrics: dict, notes: str = "", tags: str = "") -> int:
        cur = self._conn.execute(
            """INSERT INTO backtest_history (user_id, created_at, symbol, exchange, timeframe, strategy, params, metrics, notes, tags)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (user_id, time.time(), symbol, exchange, timeframe, strategy,
             json.dumps(params, ensure_ascii=False), json.dumps(metrics, ensure_ascii=False), notes, tags),
        )
        self._conn.commit()
        return cur.lastrowid or 0

    def update_notes(self, record_id: int, notes: str, tags: str = "") -> None:
        self._conn.execute("UPDATE backtest_history SET notes=?, tags=? WHERE id=?", (notes, tags, record_id))
        self._conn.commit()

    def get_history(self, user_id: int, limit: int = 50) -> list[dict]:
        cur = self._conn.execute(
            "SELECT * FROM backtest_history WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        )
        rows = []
        for r in cur.fetchall():
            d = dict(r)
            d["params"] = json.loads(d.get("params") or "{}")
            d["metrics"] = json.loads(d.get("metrics") or "{}")
            rows.append(d)
        return rows

    def toggle_favorite(self, record_id: int) -> None:
        self._conn.execute(
            "UPDATE backtest_history SET is_favorite = 1 - is_favorite WHERE id=?", (record_id,))
        self._conn.commit()

    def delete_history(self, record_id: int) -> None:
        self._conn.execute("DELETE FROM backtest_history WHERE id=?", (record_id,))
        self._conn.commit()

    def get_favorites(self, user_id: int) -> list[dict]:
        cur = self._conn.execute(
            "SELECT * FROM backtest_history WHERE user_id=? AND is_favorite=1 ORDER BY created_at DESC",
            (user_id,),
        )
        rows = []
        for r in cur.fetchall():
            d = dict(r)
            d["params"] = json.loads(d.get("params") or "{}")
            d["metrics"] = json.loads(d.get("metrics") or "{}")
            rows.append(d)
        return rows

    # ─── 用戶設定 ───
    def get_settings(self, user_id: int) -> dict:
        cur = self._conn.execute("SELECT settings FROM user_settings WHERE user_id=?", (user_id,))
        row = cur.fetchone()
        return json.loads(row["settings"]) if row else {}

    def save_settings(self, user_id: int, settings: dict) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO user_settings (user_id, settings) VALUES (?,?)",
            (user_id, json.dumps(settings, ensure_ascii=False)),
        )
        self._conn.commit()

    # ─── 統計 ───
    def get_stats(self) -> dict:
        total_users = self._conn.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
        active_users = self._conn.execute("SELECT COUNT(*) as c FROM users WHERE is_active=1").fetchone()["c"]
        total_backtests = self._conn.execute("SELECT COUNT(*) as c FROM backtest_history").fetchone()["c"]
        recent_backtests = self._conn.execute(
            "SELECT COUNT(*) as c FROM backtest_history WHERE created_at > ?", (time.time() - 86400,)
        ).fetchone()["c"]
        top_symbols = self._conn.execute(
            "SELECT symbol, COUNT(*) as cnt FROM backtest_history GROUP BY symbol ORDER BY cnt DESC LIMIT 10"
        ).fetchall()
        return {
            "total_users": total_users,
            "active_users": active_users,
            "total_backtests": total_backtests,
            "recent_backtests_24h": recent_backtests,
            "top_symbols": [{"symbol": r["symbol"], "count": r["cnt"]} for r in top_symbols],
        }

    # ─── 策略預設 ───
    def save_preset(self, user_id: int, name: str, config: dict) -> int:
        cur = self._conn.execute(
            "INSERT INTO strategy_presets (user_id, name, config, created_at) VALUES (?,?,?,?)",
            (user_id, name, json.dumps(config, ensure_ascii=False), time.time()),
        )
        self._conn.commit()
        return cur.lastrowid or 0

    def get_presets(self, user_id: int) -> list[dict]:
        cur = self._conn.execute("SELECT * FROM strategy_presets WHERE user_id=? ORDER BY created_at DESC", (user_id,))
        rows = []
        for r in cur.fetchall():
            d = dict(r)
            d["config"] = json.loads(d.get("config") or "{}")
            rows.append(d)
        return rows

    def delete_preset(self, preset_id: int) -> None:
        self._conn.execute("DELETE FROM strategy_presets WHERE id=?", (preset_id,))
        self._conn.commit()

    # ─── 提醒 ───
    def add_alert(self, user_id: int, symbol: str, condition_type: str, threshold: float, message: str = "") -> int:
        cur = self._conn.execute(
            "INSERT INTO alerts (user_id, symbol, condition_type, threshold, message, created_at) VALUES (?,?,?,?,?,?)",
            (user_id, symbol, condition_type, threshold, message, time.time()),
        )
        self._conn.commit()
        return cur.lastrowid or 0

    def get_alerts(self, user_id: int) -> list[dict]:
        cur = self._conn.execute("SELECT * FROM alerts WHERE user_id=? ORDER BY created_at DESC", (user_id,))
        return [dict(r) for r in cur.fetchall()]

    def delete_alert(self, alert_id: int) -> None:
        self._conn.execute("DELETE FROM alerts WHERE id=?", (alert_id,))
        self._conn.commit()

    def check_alerts(self, user_id: int, results: dict) -> list[dict]:
        """檢查回測結果是否觸發用戶設定的提醒"""
        alerts = self.get_alerts(user_id)
        triggered = []
        for a in alerts:
            for strategy, res in results.items():
                if res.error:
                    continue
                m = res.metrics
                val = None
                if a["condition_type"] == "return_above":
                    val = m.get("total_return_pct", 0)
                    if val and val >= a["threshold"]:
                        triggered.append({**a, "actual": val, "strategy": strategy})
                elif a["condition_type"] == "return_below":
                    val = m.get("total_return_pct", 0)
                    if val and val <= a["threshold"]:
                        triggered.append({**a, "actual": val, "strategy": strategy})
                elif a["condition_type"] == "drawdown_above":
                    val = m.get("max_drawdown_pct", 0)
                    if val and val >= a["threshold"]:
                        triggered.append({**a, "actual": val, "strategy": strategy})
                elif a["condition_type"] == "sharpe_above":
                    val = m.get("sharpe_ratio", 0)
                    if val and val >= a["threshold"]:
                        triggered.append({**a, "actual": val, "strategy": strategy})
        return triggered

    # ─── 策略訂閱 (Watchlist) ───
    def add_watch(self, user_id: int, symbol: str, exchange: str, timeframe: str,
                  strategy: str, strategy_params: dict, initial_equity: float = 10000) -> int:
        cur = self._conn.execute(
            """INSERT INTO watchlist (user_id, symbol, exchange, timeframe, strategy, strategy_params, initial_equity, created_at)
               VALUES (?,?,?,?,?,?,?,?)""",
            (user_id, symbol, exchange, timeframe, strategy,
             json.dumps(strategy_params, ensure_ascii=False), initial_equity, time.time()),
        )
        self._conn.commit()
        return cur.lastrowid or 0

    def get_watchlist(self, user_id: int) -> list[dict]:
        cur = self._conn.execute("SELECT * FROM watchlist WHERE user_id=? ORDER BY created_at DESC", (user_id,))
        rows = []
        for r in cur.fetchall():
            d = dict(r)
            d["strategy_params"] = json.loads(d.get("strategy_params") or "{}")
            rows.append(d)
        return rows

    def update_watch(self, watch_id: int, **kwargs: Any) -> None:
        allowed = {"last_check", "last_signal", "last_price", "entry_price", "position", "pnl_pct", "is_active"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return
        set_clause = ", ".join(f"{k}=?" for k in updates)
        self._conn.execute(f"UPDATE watchlist SET {set_clause} WHERE id=?", (*updates.values(), watch_id))
        self._conn.commit()

    def delete_watch(self, watch_id: int) -> None:
        self._conn.execute("DELETE FROM watchlist WHERE id=?", (watch_id,))
        self._conn.commit()

    def toggle_watch(self, watch_id: int) -> None:
        self._conn.execute("UPDATE watchlist SET is_active = 1 - is_active WHERE id=?", (watch_id,))
        self._conn.commit()
