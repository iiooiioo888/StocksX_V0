# API 限流器（令牌桶演算法）+ 裝飾器
from __future__ import annotations

import functools
import threading
import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


@dataclass
class TokenBucket:
    """令牌桶實作"""

    capacity: float  # 桶容量（最大令牌數）
    refill_rate: float  # 補充速率（令牌/秒）
    tokens: float = field(default=0.0)
    last_refill: float = field(default_factory=time.time)

    def __post_init__(self):
        self.tokens = self.capacity  # 初始滿桶
        self.last_refill = time.time()

    def _refill(self):
        """補充令牌"""
        now = time.time()
        elapsed = now - self.last_refill
        new_tokens = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now

    def consume(self, tokens: int = 1) -> bool:
        """
        消費令牌

        Args:
            tokens: 需要消費的令牌數

        Returns:
            bool: 是否成功消費
        """
        self._refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def wait_time(self, tokens: int = 1) -> float:
        """計算需要等待的時間（秒）"""
        self._refill()
        if self.tokens >= tokens:
            return 0.0
        needed = tokens - self.tokens
        return needed / self.refill_rate


@dataclass
class RateLimitStats:
    """限流統計"""

    total_requests: int = 0
    allowed_requests: int = 0
    rejected_requests: int = 0
    total_wait_time: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_requests": self.total_requests,
            "allowed_requests": self.allowed_requests,
            "rejected_requests": self.rejected_requests,
            "rejection_rate": self.rejected_requests / max(1, self.total_requests),
            "avg_wait_time": self.total_wait_time / max(1, self.allowed_requests),
        }


class RateLimiter:
    """
    速率限制器（支援記憶體/Redis 後端）

    使用場景：
    1. 防止觸發外部 API 頻率限制
    2. 保護系統資源不被單一用戶耗盡
    3. 公平分配資源
    """

    def __init__(
        self,
        redis_url: str | None = None,
        default_capacity: int = 10,
        default_refill_rate: float = 1.0,
    ):
        """
        Args:
            redis_url: Redis 連接 URL（如 redis://localhost:6379/0）
            default_capacity: 預設桶容量
            default_refill_rate: 預設補充速率
        """
        self.default_capacity = default_capacity
        self.default_refill_rate = default_refill_rate

        # 記憶體後端
        self._buckets: dict[str, TokenBucket] = {}
        self._stats: dict[str, RateLimitStats] = defaultdict(RateLimitStats)
        self._lock = threading.Lock()

        # Redis 後端（分散式環境）
        self._redis: redis.Redis | None = None
        self._redis_prefix = "stocksx:ratelimit:"

        if redis_url and REDIS_AVAILABLE:
            try:
                self._redis = redis.from_url(redis_url, decode_responses=True)
                self._redis.ping()
                print(f"[RateLimiter] Connected to Redis: {redis_url}")
            except Exception as e:
                print(f"[RateLimiter] Redis connection failed: {e}")
                self._redis = None

    def _get_bucket_key(self, key: str) -> str:
        return f"{self._redis_prefix}{key}"

    def _get_bucket(self, key: str) -> TokenBucket:
        """取得令牌桶（記憶體模式）"""
        with self._lock:
            if key not in self._buckets:
                self._buckets[key] = TokenBucket(capacity=self.default_capacity, refill_rate=self.default_refill_rate)
            return self._buckets[key]

    def _get_redis_bucket(self, key: str) -> tuple[float, float]:
        """取得令牌桶狀態（Redis 模式）"""
        if not self._redis:
            raise RuntimeError("Redis not available")

        bucket_key = self._get_bucket_key(key)
        tokens_key = f"{bucket_key}:tokens"
        time_key = f"{bucket_key}:time"

        pipe = self._redis.pipeline()
        pipe.get(tokens_key)
        pipe.get(time_key)
        results = pipe.execute()

        tokens = float(results[0]) if results[0] else float(self.default_capacity)
        last_refill = float(results[1]) if results[1] else time.time()

        return tokens, last_refill

    def _set_redis_bucket(self, key: str, tokens: float, last_refill: float):
        """設定令牌桶狀態（Redis 模式）"""
        if not self._redis:
            return

        bucket_key = self._get_bucket_key(key)
        pipe = self._redis.pipeline()
        pipe.set(f"{bucket_key}:tokens", tokens)
        pipe.set(f"{bucket_key}:time", last_refill)
        pipe.expire(bucket_key, 3600)  # 1 小時過期
        pipe.execute()

    def allow_request(
        self,
        key: str,
        tokens: int = 1,
        capacity: int | None = None,
        refill_rate: float | None = None,
        wait: bool = False,
        max_wait: float = 30.0,
    ) -> tuple[bool, float]:
        """
        檢查請求是否允許

        Args:
            key: 限流鍵（如 API 名稱、用戶 ID）
            tokens: 需要的令牌數
            capacity: 桶容量（覆蓋預設）
            refill_rate: 補充速率（覆蓋預設）
            wait: 是否等待令牌
            max_wait: 最大等待時間（秒）

        Returns:
            Tuple[是否允許，等待時間]
        """
        capacity = capacity or self.default_capacity
        refill_rate = refill_rate or self.default_refill_rate

        with self._lock:
            self._stats[key].total_requests += 1

        if self._redis:
            # Redis 模式（分散式）
            return self._allow_request_redis(key, tokens, capacity, refill_rate, wait, max_wait)
        else:
            # 記憶體模式
            return self._allow_request_memory(key, tokens, capacity, refill_rate, wait, max_wait)

    def _allow_request_memory(
        self,
        key: str,
        tokens: int,
        capacity: int,
        refill_rate: float,
        wait: bool,
        max_wait: float,
    ) -> tuple[bool, float]:
        """記憶體模式實作"""
        bucket = self._get_bucket(key)

        # 動態調整容量（如果設定改變）
        if bucket.capacity != capacity:
            bucket.capacity = capacity
        if bucket.refill_rate != refill_rate:
            bucket.refill_rate = refill_rate

        wait_time = bucket.wait_time(tokens)

        if wait and wait_time > 0 and wait_time <= max_wait:
            time.sleep(wait_time)
            bucket._refill()

        if bucket.consume(tokens):
            with self._lock:
                self._stats[key].allowed_requests += 1
                self._stats[key].total_wait_time += wait_time
            return True, wait_time
        else:
            with self._lock:
                self._stats[key].rejected_requests += 1
            return False, wait_time

    def _allow_request_redis(
        self,
        key: str,
        tokens: int,
        capacity: int,
        refill_rate: float,
        wait: bool,
        max_wait: float,
    ) -> tuple[bool, float]:
        """Redis 模式實作（使用 Lua 腳本保證原子性）"""
        if not self._redis:
            return self._allow_request_memory(key, tokens, capacity, refill_rate, wait, max_wait)

        bucket_key = self._get_bucket_key(key)
        tokens_key = f"{bucket_key}:tokens"
        time_key = f"{bucket_key}:time"

        # Lua 腳本：原子性地檢查並消費令牌
        lua_script = """
        local tokens_key = KEYS[1]
        local time_key = KEYS[2]
        local capacity = tonumber(ARGV[1])
        local refill_rate = tonumber(ARGV[2])
        local needed = tonumber(ARGV[3])
        local now = tonumber(ARGV[4])

        local tokens = tonumber(redis.call('GET', tokens_key)) or capacity
        local last_refill = tonumber(redis.call('GET', time_key)) or now

        -- 補充令牌
        local elapsed = now - last_refill
        local new_tokens = math.min(capacity, tokens + elapsed * refill_rate)

        -- 檢查是否足夠
        if new_tokens >= needed then
            redis.call('SET', tokens_key, new_tokens - needed)
            redis.call('SET', time_key, now)
            redis.call('EXPIRE', tokens_key, 3600)
            redis.call('EXPIRE', time_key, 3600)
            return {1, 0}  -- 成功，等待時間 0
        else
            local wait_time = (needed - new_tokens) / refill_rate
            return {0, wait_time}  -- 失敗，需要等待
        end
        """

        now = time.time()
        result = self._redis.eval(lua_script, 2, tokens_key, time_key, capacity, refill_rate, tokens, now)

        allowed = bool(result[0])
        wait_time = float(result[1])

        if wait and wait_time > 0 and wait_time <= max_wait:
            time.sleep(wait_time)
            # 重試
            return self._allow_request_redis(key, tokens, capacity, refill_rate, False, max_wait)

        with self._lock:
            if allowed:
                self._stats[key].allowed_requests += 1
                self._stats[key].total_wait_time += wait_time
            else:
                self._stats[key].rejected_requests += 1

        return allowed, wait_time

    def get_stats(self, key: str | None = None) -> dict[str, Any]:
        """取得統計資訊"""
        with self._lock:
            if key:
                return {key: self._stats[key].to_dict()}
            return {k: v.to_dict() for k, v in self._stats.items()}

    def reset_stats(self, key: str | None = None):
        """重置統計"""
        with self._lock:
            if key:
                del self._stats[key]
            else:
                self._stats.clear()

    def get_bucket_info(self, key: str) -> dict[str, Any]:
        """取得桶子當前狀態"""
        if self._redis:
            tokens, last_refill = self._get_redis_bucket(key)
            return {"tokens": tokens, "last_refill": last_refill, "mode": "redis"}
        else:
            bucket = self._get_bucket(key)
            bucket._refill()
            return {
                "tokens": bucket.tokens,
                "capacity": bucket.capacity,
                "refill_rate": bucket.refill_rate,
                "last_refill": bucket.last_refill,
                "mode": "memory",
            }


# 裝飾器
def rate_limit(
    limiter: RateLimiter,
    key: str,
    capacity: int = 10,
    refill_rate: float = 1.0,
    tokens: int = 1,
    wait: bool = False,
    max_wait: float = 30.0,
    on_limit: Callable | None = None,
):
    """
    速率限制裝飾器

    Args:
        limiter: RateLimiter 實例
        key: 限流鍵
        capacity: 桶容量
        refill_rate: 補充速率
        tokens: 每次呼叫消耗的令牌數
        wait: 是否等待
        max_wait: 最大等待時間
        on_limit: 被限流時的回調函數

    Returns:
        裝飾器

    Example:
        ```python
        limiter = RateLimiter(default_capacity=5, default_refill_rate=0.5)

        @rate_limit(limiter, key="polymarket_api", capacity=10, refill_rate=1.0)
        def fetch_polymarket_data():
            return requests.get(url)
        ```
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            allowed, wait_time = limiter.allow_request(
                key=key, tokens=tokens, capacity=capacity, refill_rate=refill_rate, wait=wait, max_wait=max_wait
            )

            if not allowed:
                if on_limit:
                    return on_limit()
                raise RateLimitExceeded(f"Rate limit exceeded for {key}. Wait time: {wait_time:.2f}s")

            return func(*args, **kwargs)

        return wrapper

    return decorator


def async_rate_limit(
    limiter: RateLimiter,
    key: str,
    capacity: int = 10,
    refill_rate: float = 1.0,
    tokens: int = 1,
    wait: bool = False,
    max_wait: float = 30.0,
    on_limit: Callable | None = None,
):
    """非同步版本的速率限制裝飾器"""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            allowed, wait_time = limiter.allow_request(
                key=key, tokens=tokens, capacity=capacity, refill_rate=refill_rate, wait=wait, max_wait=max_wait
            )

            if not allowed:
                if on_limit:
                    return on_limit()
                raise RateLimitExceeded(f"Rate limit exceeded for {key}. Wait time: {wait_time:.2f}s")

            return await func(*args, **kwargs)

        return wrapper

    return decorator


class RateLimitExceeded(Exception):
    """速率限制異常"""

    def __init__(self, message: str, retry_after: float | None = None):
        super().__init__(message)
        self.retry_after = retry_after


# 預設限流器實例
_default_limiter: RateLimiter | None = None


def get_default_limiter() -> RateLimiter:
    """取得預設限流器"""
    global _default_limiter
    if _default_limiter is None:
        _default_limiter = RateLimiter(default_capacity=10, default_refill_rate=1.0)
    return _default_limiter


# API 特定限流配置
API_LIMIT_CONFIG = {
    # Polymarket: 免費層級約 10 次/分鐘
    "polymarket": {"capacity": 10, "refill_rate": 1.0 / 6},
    # Alpha Vantage: 免費層級 5 次/分鐘
    "alpha_vantage": {"capacity": 5, "refill_rate": 1.0 / 12},
    # FRED: 免費層級 600 次/天
    "fred": {"capacity": 100, "refill_rate": 1.0 / 144},
    # Polygon.io: 免費層級 5 次/分鐘
    "polygon": {"capacity": 5, "refill_rate": 1.0 / 12},
    # CoinGecko: 免費層級 10-50 次/分鐘
    "coingecko": {"capacity": 30, "refill_rate": 0.5},
    # CoinMarketCap: 免費層級 333 次/天
    "coinmarketcap": {"capacity": 20, "refill_rate": 1.0 / 4320},
    # Glassnode: 免費層級 10 次/天
    "glassnode": {"capacity": 10, "refill_rate": 1.0 / 8640},
    # yfinance: 無官方限制，但建議保守使用
    "yfinance": {"capacity": 20, "refill_rate": 1.0},
    # CCXT: 依交易所而定，預設保守
    "ccxt": {"capacity": 10, "refill_rate": 1.0},
}


def get_api_limiter(api_name: str) -> tuple[RateLimiter, dict[str, Any]]:
    """
    取得特定 API 的限流器與配置

    Args:
        api_name: API 名稱

    Returns:
        Tuple[RateLimiter, 配置字典]
    """
    limiter = get_default_limiter()
    config = API_LIMIT_CONFIG.get(api_name, {"capacity": 10, "refill_rate": 1.0})
    return limiter, config
