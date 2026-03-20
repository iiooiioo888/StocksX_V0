"""middleware.py 單元測試 — MiddlewarePipeline, LoggingMiddleware, TimingMiddleware, RateLimitMiddleware."""

import os
import sys
import time
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.core.middleware import (
    LoggingMiddleware,
    Middleware,
    MiddlewarePipeline,
    RateLimitMiddleware,
    RetryMiddleware,
    TimingMiddleware,
    with_middleware,
)


# ─── Middleware 基類測試 ───


class TestMiddleware:
    """測試 Middleware 基類預設行為."""

    def test_before_does_nothing(self):
        """before 預設不執行任何操作."""
        mw = Middleware()
        mw.before({})  # 不應拋出異常

    def test_after_returns_result(self):
        """after 預設返回原始 result."""
        mw = Middleware()
        assert mw.after({}, "result") == "result"

    def test_error_returns_none(self):
        """error 預設返回 None（繼續拋出異常）."""
        mw = Middleware()
        assert mw.error({}, RuntimeError()) is None


# ─── MiddlewarePipeline 測試 ───


class TestMiddlewarePipeline:
    """測試 MiddlewarePipeline 管道."""

    def test_execute_no_middleware(self):
        """無中間件時直接執行函式."""
        pipe = MiddlewarePipeline()
        result = pipe.execute(lambda: 42)
        assert result == 42

    def test_execute_with_before_hook(self):
        """before hook 應在執行前呼叫."""
        order = []

        class TrackMiddleware(Middleware):
            def before(self, ctx):
                order.append("before")

            def after(self, ctx, result):
                order.append("after")
                return result

        pipe = MiddlewarePipeline()
        pipe.use(TrackMiddleware())
        pipe.execute(lambda: order.append("func") or "done")
        assert order == ["before", "func", "after"]

    def test_after_hooks_reverse_order(self):
        """after hooks 應以逆序執行."""
        order = []

        class MW1(Middleware):
            def after(self, ctx, result):
                order.append("mw1_after")
                return result

        class MW2(Middleware):
            def after(self, ctx, result):
                order.append("mw2_after")
                return result

        pipe = MiddlewarePipeline()
        pipe.use(MW1())
        pipe.use(MW2())
        pipe.execute(lambda: "result")
        assert order == ["mw2_after", "mw1_after"]

    def test_error_recovery(self):
        """error hook 返回非 None 時應替代異常."""

        class RecoveryMiddleware(Middleware):
            def error(self, ctx, exc):
                return "recovered"

        pipe = MiddlewarePipeline()
        pipe.use(RecoveryMiddleware())
        result = pipe.execute(lambda: (_ for _ in ()).throw(ValueError("boom")))
        assert result == "recovered"

    def test_error_no_recovery_raises(self):
        """error hook 返回 None 時異常應繼續拋出."""
        pipe = MiddlewarePipeline()
        pipe.use(Middleware())  # 預設 error 返回 None
        with pytest.raises(ValueError, match="boom"):
            pipe.execute(lambda: (_ for _ in ()).throw(ValueError("boom")))

    def test_chaining_use(self):
        """use() 應支持鏈式呼叫."""
        pipe = MiddlewarePipeline()
        result = pipe.use(Middleware()).use(Middleware())
        assert result is pipe

    def test_context_kwargs(self):
        """execute 可傳入額外 context 參數."""
        received = []

        class CtxMiddleware(Middleware):
            def before(self, ctx):
                received.append(ctx.get("custom_key"))

        pipe = MiddlewarePipeline()
        pipe.use(CtxMiddleware())
        pipe.execute(lambda: None, custom_key="hello")
        assert received == ["hello"]


# ─── LoggingMiddleware 測試 ───


class TestLoggingMiddleware:
    """測試 LoggingMiddleware."""

    def test_before_sets_start_time(self):
        """before 應設定 _start_time 到 context."""
        mw = LoggingMiddleware()
        ctx = {}
        mw.before(ctx)
        assert "_start_time" in ctx
        assert isinstance(ctx["_start_time"], float)

    def test_after_returns_result(self):
        """after 應返回原始 result."""
        mw = LoggingMiddleware()
        ctx = {"_start_time": time.monotonic()}
        assert mw.after(ctx, "hello") == "hello"

    def test_error_returns_none(self):
        """error 應返回 None（不攔截異常）."""
        mw = LoggingMiddleware()
        ctx = {"_start_time": time.monotonic()}
        assert mw.error(ctx, RuntimeError()) is None


# ─── TimingMiddleware 測試 ───


class TestTimingMiddleware:
    """測試 TimingMiddleware."""

    def test_sets_elapsed_in_context(self):
        """after 應在 context 中設定 elapsed_ms."""
        mw = TimingMiddleware()
        ctx = {}
        mw.before(ctx)
        time.sleep(0.01)  # 至少 10ms
        result = mw.after(ctx, "ok")
        assert result == "ok"
        assert "elapsed_ms" in ctx
        assert ctx["elapsed_ms"] >= 10  # 至少 10ms


# ─── RateLimitMiddleware 測試 ───


class TestRateLimitMiddleware:
    """測試 RateLimitMiddleware."""

    def test_no_wait_when_rps_zero(self):
        """rps=0 時不應等待."""
        mw = RateLimitMiddleware(rps=0)
        ctx = {}
        start = time.monotonic()
        mw.before(ctx)
        elapsed = time.monotonic() - start
        assert elapsed < 0.1  # 幾乎不等待

    def test_rate_limiting_delay(self):
        """速率限制應引入延遲."""
        mw = RateLimitMiddleware(rps=10)  # min_interval = 0.1s
        ctx = {}
        mw.before(ctx)  # 第一次不等
        start = time.monotonic()
        mw.before(ctx)  # 第二次應等待
        elapsed = time.monotonic() - start
        # 應等待接近 0.1 秒
        assert elapsed >= 0.05  # 允許一些誤差


# ─── with_middleware 裝飾器測試 ───


class TestWithMiddleware:
    """測試 with_middleware 裝飾器."""

    def test_decorator_applies_middleware(self):
        """裝飾器應為函式應用中間件."""
        called = []

        class TrackMiddleware(Middleware):
            def before(self, ctx):
                called.append("before")

            def after(self, ctx, result):
                called.append("after")
                return result

        @with_middleware(TrackMiddleware())
        def my_func():
            return 42

        result = my_func()
        assert result == 42
        assert "before" in called
        assert "after" in called


# ─── RetryMiddleware 測試 ───


class TestRetryMiddleware:
    """測試 RetryMiddleware 重試邏輯."""

    def test_retry_succeeds_after_failures(self):
        """前幾次失敗後成功應返回結果."""
        call_count = 0

        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError(f"attempt {call_count}")
            return "success"

        pipe = MiddlewarePipeline()
        pipe.use(RetryMiddleware(max_retries=3, delay=0.01, backoff=1.0))
        result = pipe.execute(flaky)
        assert result == "success"
        assert call_count == 3

    def test_retry_exhausted_raises(self):
        """重試耗盡應拋出最後的異常."""

        def always_fail():
            raise RuntimeError("always")

        pipe = MiddlewarePipeline()
        pipe.use(RetryMiddleware(max_retries=2, delay=0.01))
        with pytest.raises(RuntimeError, match="always"):
            pipe.execute(always_fail)

    def test_retry_only_matching_exceptions(self):
        """只重試指定的異常類型."""
        call_count = 0

        def wrong_error():
            nonlocal call_count
            call_count += 1
            raise TypeError("wrong type")

        pipe = MiddlewarePipeline()
        pipe.use(RetryMiddleware(max_retries=3, delay=0.01, exceptions=(ValueError,)))
        with pytest.raises(TypeError):
            pipe.execute(wrong_error)
        assert call_count == 1  # 不應重試

    def test_retry_exponential_backoff(self):
        """重試應有指數退避延遲."""
        call_count = 0

        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("fail")
            return "ok"

        pipe = MiddlewarePipeline()
        pipe.use(RetryMiddleware(max_retries=3, delay=0.05, backoff=2.0))
        start = time.monotonic()
        result = pipe.execute(flaky)
        elapsed = time.monotonic() - start
        assert result == "ok"
        # 第一次重試 delay=0.05, 第二次 delay=0.05*2=0.1, 總共至少 0.15s
        assert elapsed >= 0.1

    def test_before_sets_retry_counter(self):
        """before 應初始化重試計數器."""
        mw = RetryMiddleware(max_retries=3)
        ctx = {}
        mw.before(ctx)
        assert ctx["_retry_count"] == 0
        assert ctx["_retry_max"] == 3

    def test_error_returns_none(self):
        """error 應返回 None（由 Pipeline 處理重試）."""
        mw = RetryMiddleware(max_retries=3)
        ctx = {"_retry_count": 0}
        result = mw.error(ctx, ValueError("test"))
        assert result is None

    def test_success_no_retry(self):
        """成功時不應重試."""
        call_count = 0

        def succeed():
            nonlocal call_count
            call_count += 1
            return "ok"

        pipe = MiddlewarePipeline()
        pipe.use(RetryMiddleware(max_retries=3, delay=0.01))
        result = pipe.execute(succeed)
        assert result == "ok"
        assert call_count == 1

    def test_retry_with_recovery_middleware(self):
        """RetryMiddleware 與 RecoveryMiddleware 共存時，Recovery 優先."""
        call_count = 0

        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("fail once")
            return "ok"

        class RecoveryMiddleware(Middleware):
            def error(self, ctx, exc):
                if isinstance(exc, ValueError):
                    return "recovered"
                return None

        pipe = MiddlewarePipeline()
        pipe.use(RecoveryMiddleware())
        pipe.use(RetryMiddleware(max_retries=3, delay=0.01))
        result = pipe.execute(flaky)
        # RecoveryMiddleware 先 intercept，所以不會觸發重試
        assert result == "recovered"
        assert call_count == 1

    def test_retry_zero_retries(self):
        """max_retries=0 時不應重試."""
        call_count = 0

        def always_fail():
            nonlocal call_count
            call_count += 1
            raise RuntimeError("fail")

        pipe = MiddlewarePipeline()
        pipe.use(RetryMiddleware(max_retries=0, delay=0.01))
        with pytest.raises(RuntimeError):
            pipe.execute(always_fail)
        assert call_count == 1


# ─── MiddlewarePipeline 整合測試 ───


class TestPipelineIntegration:
    """中間件管道組合測試."""

    def test_multiple_middlewares_order(self):
        """多中間件應按正確順序執行."""
        order = []

        class MW1(Middleware):
            def before(self, ctx):
                order.append("mw1_before")

            def after(self, ctx, result):
                order.append("mw1_after")
                return result

        class MW2(Middleware):
            def before(self, ctx):
                order.append("mw2_before")

            def after(self, ctx, result):
                order.append("mw2_after")
                return result

        pipe = MiddlewarePipeline()
        pipe.use(MW1())
        pipe.use(MW2())
        pipe.execute(lambda: order.append("func") or "done")

        assert order == [
            "mw1_before",
            "mw2_before",
            "func",
            "mw2_after",
            "mw1_after",
        ]

    def test_timing_and_retry_together(self):
        """TimingMiddleware 與 RetryMiddleware 可共存."""
        call_count = 0

        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("network")
            return "data"

        pipe = MiddlewarePipeline()
        pipe.use(TimingMiddleware())
        pipe.use(RetryMiddleware(max_retries=3, delay=0.01, backoff=1.0))
        result = pipe.execute(flaky)
        assert result == "data"
        assert call_count == 2
