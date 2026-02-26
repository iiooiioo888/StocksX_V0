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
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    name TEXT DEFAULT '',
    exchange TEXT DEFAULT '',
    market_type TEXT DEFAULT 'crypto',
    category TEXT DEFAULT '',
    is_system INTEGER DEFAULT 0,
    user_id INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_at REAL NOT NULL,
    UNIQUE(symbol, exchange, user_id)
);
CREATE TABLE IF NOT EXISTS login_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    ip TEXT DEFAULT '',
    success INTEGER NOT NULL,
    reason TEXT DEFAULT '',
    created_at REAL NOT NULL
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


_MAX_LOGIN_ATTEMPTS = 5
_LOCKOUT_SECONDS = 300
_SESSION_TIMEOUT = 3600
_MIN_PASSWORD_LEN = 6


def _hash_pw(password: str, salt: str = "") -> str:
    if not salt:
        salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
    return f"pbkdf2:{salt}:{h}"


def _verify_pw(password: str, stored: str) -> bool:
    if stored.startswith("pbkdf2:"):
        _, salt, h = stored.split(":", 2)
        return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex() == h
    salt = stored.split(":")[0]
    old_h = hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()
    return f"{salt}:{old_h}" == stored


def _sanitize(text: str, max_len: int = 200) -> str:
    """輸入消毒：去除危險字符，防 XSS/注入"""
    if not isinstance(text, str):
        return ""
    text = text.strip()[:max_len]
    for ch in ["<", ">", "'", '"', ";", "--", "/*", "*/", "\\", "\x00"]:
        text = text.replace(ch, "")
    return text


def _validate_password(password: str) -> str | None:
    """密碼強度檢查，回傳錯誤訊息或 None"""
    if len(password) < _MIN_PASSWORD_LEN:
        return f"密碼至少 {_MIN_PASSWORD_LEN} 個字元"
    if password.isdigit():
        return "密碼不能全是數字"
    if password.isalpha():
        return "密碼需包含數字"
    return None


class UserDB:
    def __init__(self, db_path: str = _DB_PATH) -> None:
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()
        self._migrate()
        self._ensure_admin()
        self._init_system_products()
        self._rate_limits: dict[str, list[float]] = {}

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

    def _init_system_products(self) -> None:
        cur = self._conn.execute("SELECT COUNT(*) as c FROM products WHERE is_system=1")
        if cur.fetchone()["c"] > 0:
            return
        now = time.time()
        _sys = [
            # 加密主流
            ("BTC/USDT:USDT", "Bitcoin 永續", "binance", "crypto", "主流永續"),
            ("ETH/USDT:USDT", "Ethereum 永續", "binance", "crypto", "主流永續"),
            ("SOL/USDT:USDT", "Solana 永續", "binance", "crypto", "主流永續"),
            ("BNB/USDT:USDT", "BNB 永續", "binance", "crypto", "主流永續"),
            ("XRP/USDT:USDT", "XRP 永續", "binance", "crypto", "主流永續"),
            ("DOGE/USDT:USDT", "Dogecoin 永續", "binance", "crypto", "主流永續"),
            ("ADA/USDT:USDT", "Cardano 永續", "binance", "crypto", "主流永續"),
            # 加密現貨
            ("BTC/USDT", "Bitcoin 現貨", "binance", "crypto", "主流現貨"),
            ("ETH/USDT", "Ethereum 現貨", "binance", "crypto", "主流現貨"),
            ("SOL/USDT", "Solana 現貨", "binance", "crypto", "主流現貨"),
            # DeFi
            ("UNI/USDT", "Uniswap", "binance", "crypto", "DeFi"),
            ("AAVE/USDT", "Aave", "binance", "crypto", "DeFi"),
            ("LINK/USDT", "Chainlink", "binance", "crypto", "DeFi"),
            # Meme
            ("PEPE/USDT", "Pepe", "binance", "crypto", "Meme"),
            ("SHIB/USDT", "Shiba Inu", "binance", "crypto", "Meme"),
            ("WIF/USDT", "dogwifhat", "binance", "crypto", "Meme"),
            ("BONK/USDT", "Bonk", "binance", "crypto", "Meme"),
            # Layer2
            ("ARB/USDT", "Arbitrum", "binance", "crypto", "Layer2"),
            ("OP/USDT", "Optimism", "binance", "crypto", "Layer2"),
            ("SUI/USDT", "Sui", "binance", "crypto", "Layer2"),
            # 美股
            ("AAPL", "Apple", "yfinance", "traditional", "美股"),
            ("MSFT", "Microsoft", "yfinance", "traditional", "美股"),
            ("GOOGL", "Google", "yfinance", "traditional", "美股"),
            ("AMZN", "Amazon", "yfinance", "traditional", "美股"),
            ("NVDA", "NVIDIA", "yfinance", "traditional", "美股"),
            ("TSLA", "Tesla", "yfinance", "traditional", "美股"),
            ("META", "Meta", "yfinance", "traditional", "美股"),
            # 台股
            ("2330.TW", "台積電", "yfinance", "traditional", "台股"),
            ("2317.TW", "鴻海", "yfinance", "traditional", "台股"),
            ("2454.TW", "聯發科", "yfinance", "traditional", "台股"),
            # ETF
            ("SPY", "S&P 500 ETF", "yfinance", "traditional", "ETF"),
            ("QQQ", "Nasdaq 100 ETF", "yfinance", "traditional", "ETF"),
            ("GLD", "黃金 ETF", "yfinance", "traditional", "ETF"),
            ("0050.TW", "元大台灣50", "yfinance", "traditional", "ETF"),
            # 期貨
            ("GC=F", "黃金期貨", "yfinance", "traditional", "期貨"),
            ("CL=F", "原油期貨", "yfinance", "traditional", "期貨"),
            ("ES=F", "S&P 500 期貨", "yfinance", "traditional", "期貨"),
        ]
        for sym, name, ex, mt, cat in _sys:
            try:
                self._conn.execute(
                    "INSERT OR IGNORE INTO products (symbol, name, exchange, market_type, category, is_system, user_id, is_active, created_at) VALUES (?,?,?,?,?,1,0,1,?)",
                    (sym, name, ex, mt, cat, now))
            except Exception:
                pass
        self._conn.commit()

    # ─── 產品庫 CRUD ───
    def get_products(self, user_id: int = 0, market_type: str = "", category: str = "") -> list[dict]:
        q = "SELECT * FROM products WHERE is_active=1 AND (is_system=1 OR user_id=?)"
        params: list = [user_id]
        if market_type:
            q += " AND market_type=?"
            params.append(market_type)
        if category:
            q += " AND category=?"
            params.append(category)
        q += " ORDER BY is_system DESC, category, symbol"
        return [dict(r) for r in self._conn.execute(q, params).fetchall()]

    def get_product_categories(self, market_type: str = "") -> list[str]:
        q = "SELECT DISTINCT category FROM products WHERE is_active=1"
        params: list = []
        if market_type:
            q += " AND market_type=?"
            params.append(market_type)
        q += " ORDER BY category"
        return [r["category"] for r in self._conn.execute(q, params).fetchall()]

    def add_product(self, symbol: str, name: str, exchange: str, market_type: str,
                    category: str, user_id: int = 0, is_system: bool = False) -> int | str:
        try:
            cur = self._conn.execute(
                "INSERT INTO products (symbol, name, exchange, market_type, category, is_system, user_id, is_active, created_at) VALUES (?,?,?,?,?,?,?,1,?)",
                (_sanitize(symbol, 50), _sanitize(name, 100), _sanitize(exchange, 20),
                 _sanitize(market_type, 20), _sanitize(category, 50),
                 1 if is_system else 0, user_id, time.time()))
            self._conn.commit()
            return cur.lastrowid or 0
        except sqlite3.IntegrityError:
            return "產品已存在"

    def delete_product(self, product_id: int) -> None:
        self._conn.execute("UPDATE products SET is_active=0 WHERE id=?", (product_id,))
        self._conn.commit()

    def get_all_products_admin(self) -> list[dict]:
        return [dict(r) for r in self._conn.execute("SELECT * FROM products ORDER BY market_type, category, symbol").fetchall()]

    def check_rate_limit(self, key: str, max_calls: int = 10, period: float = 60) -> bool:
        """回傳 True 表示未超限，False 表示已超限"""
        now = time.time()
        calls = self._rate_limits.get(key, [])
        calls = [t for t in calls if now - t < period]
        if len(calls) >= max_calls:
            return False
        calls.append(now)
        self._rate_limits[key] = calls
        return True

    @staticmethod
    def validate_session(user: dict | None) -> bool:
        if not user:
            return False
        login_time = user.get("last_login", 0)
        if login_time and time.time() - login_time > _SESSION_TIMEOUT:
            return False
        return True

    def register(self, username: str, password: str, display_name: str = "", role: str = "user") -> dict | str:
        """註冊，成功回傳 user dict，失敗回傳錯誤字串"""
        username = _sanitize(username, 50)
        display_name = _sanitize(display_name, 100)
        if not username or len(username) < 3:
            return "帳號至少 3 個字元"
        if not username.replace("_", "").replace("-", "").isalnum():
            return "帳號只能包含字母、數字、底線、減號"
        pw_err = _validate_password(password)
        if pw_err:
            return pw_err
        try:
            pw_hash = _hash_pw(password)
            self._conn.execute(
                "INSERT INTO users (username, password_hash, display_name, role, created_at) VALUES (?,?,?,?,?)",
                (username, pw_hash, display_name or username, role, time.time()),
            )
            self._conn.commit()
            return self.get_user(username)
        except sqlite3.IntegrityError:
            return "帳號已存在"

    def _log_login(self, username: str, success: bool, reason: str = "", ip: str = "") -> None:
        self._conn.execute(
            "INSERT INTO login_log (username, ip, success, reason, created_at) VALUES (?,?,?,?,?)",
            (_sanitize(username), ip, 1 if success else 0, reason, time.time()),
        )
        self._conn.commit()

    def _is_locked(self, username: str) -> bool:
        cutoff = time.time() - _LOCKOUT_SECONDS
        cur = self._conn.execute(
            "SELECT COUNT(*) as c FROM login_log WHERE username=? AND success=0 AND created_at>?",
            (username, cutoff),
        )
        return cur.fetchone()["c"] >= _MAX_LOGIN_ATTEMPTS

    def login(self, username: str, password: str, ip: str = "") -> dict | str:
        """登入，成功回傳 user dict，失敗回傳錯誤訊息字串"""
        username = _sanitize(username, 50)
        if not username or not password:
            return "帳號和密碼不能為空"
        if self._is_locked(username):
            self._log_login(username, False, "帳號已鎖定", ip)
            return f"帳號已鎖定，請 {_LOCKOUT_SECONDS // 60} 分鐘後再試"
        cur = self._conn.execute("SELECT * FROM users WHERE username=? AND is_active=1", (username,))
        row = cur.fetchone()
        if not row:
            self._log_login(username, False, "帳號不存在", ip)
            return "帳號或密碼錯誤"
        if not _verify_pw(password, row["password_hash"]):
            self._log_login(username, False, "密碼錯誤", ip)
            remaining = _MAX_LOGIN_ATTEMPTS - self._get_recent_failures(username)
            return f"帳號或密碼錯誤（剩餘 {max(0, remaining)} 次嘗試）"
        self._log_login(username, True, "", ip)
        self._conn.execute("UPDATE users SET last_login=? WHERE id=?", (time.time(), row["id"]))
        if row["password_hash"].startswith("pbkdf2:") is False:
            self._conn.execute("UPDATE users SET password_hash=? WHERE id=?", (_hash_pw(password), row["id"]))
        self._conn.commit()
        return dict(row)

    def _get_recent_failures(self, username: str) -> int:
        cutoff = time.time() - _LOCKOUT_SECONDS
        cur = self._conn.execute(
            "SELECT COUNT(*) as c FROM login_log WHERE username=? AND success=0 AND created_at>?",
            (username, cutoff),
        )
        return cur.fetchone()["c"]

    def get_login_log(self, limit: int = 50) -> list[dict]:
        cur = self._conn.execute("SELECT * FROM login_log ORDER BY created_at DESC LIMIT ?", (limit,))
        return [dict(r) for r in cur.fetchall()]

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
            (user_id, time.time(), _sanitize(symbol, 50), _sanitize(exchange, 20), _sanitize(timeframe, 10),
             _sanitize(strategy, 50), json.dumps(params, ensure_ascii=False),
             json.dumps(metrics, ensure_ascii=False), _sanitize(notes, 500), _sanitize(tags, 200)),
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
