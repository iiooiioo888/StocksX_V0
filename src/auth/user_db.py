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
        self._ensure_admin()

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
                      strategy: str, params: dict, metrics: dict, notes: str = "") -> int:
        cur = self._conn.execute(
            """INSERT INTO backtest_history (user_id, created_at, symbol, exchange, timeframe, strategy, params, metrics, notes)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (user_id, time.time(), symbol, exchange, timeframe, strategy,
             json.dumps(params, ensure_ascii=False), json.dumps(metrics, ensure_ascii=False), notes),
        )
        self._conn.commit()
        return cur.lastrowid or 0

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
