"""pipeline.py 單元測試 — Pipeline, PipelineStep, ohlcv_clean_pipeline."""

import os
import pytest

from src.core.pipeline import Pipeline, PipelineStep, ohlcv_clean_pipeline

# ─── PipelineStep 測試 ───

class TestPipelineStep:
    """測試 PipelineStep 基本功能."""

    def test_callable(self):
        """PipelineStep 應可像函式一樣呼叫."""
        step = PipelineStep(func=lambda x: x * 2, name="double")
        assert step(5) == 10

    def test_name_defaults_to_func_name(self):
        """未指定 name 時，應使用函式名稱."""

        def my_func(x):
            return x

        step = PipelineStep(func=my_func)
        assert step.name == "my_func"

    def test_custom_name(self):
        """指定 name 時使用自訂名稱."""
        step = PipelineStep(func=lambda x: x, name="custom")
        assert step.name == "custom"

    def test_skip_on_error_flag(self):
        """skip_on_error 屬性應正確設定."""
        step = PipelineStep(func=lambda x: x, skip_on_error=True)
        assert step.skip_on_error is True

# ─── Pipeline 測試 ───

class TestPipeline:
    """測試 Pipeline 管道功能."""

    def test_empty_pipeline(self):
        """空管道應原樣返回資料."""
        p = Pipeline()
        assert p.run(42) == 42

    def test_add_step_chain(self):
        """add 應支持鏈式呼叫."""
        p = Pipeline()
        result = p.add(lambda x: x + 1).add(lambda x: x * 2)
        assert result is p

    def test_len(self):
        """__len__ 應返回步驟數量."""
        p = Pipeline()
        p.add(lambda x: x)
        p.add(lambda x: x)
        assert len(p) == 2

    def test_run_sequential(self):
        """步驟應依序執行."""
        p = Pipeline()
        p.add(lambda x: x + 1, name="add_one")
        p.add(lambda x: x * 3, name="triple")
        assert p.run(10) == 33  # (10+1)*3

    def test_run_with_list(self):
        """管道可處理列表資料."""
        p = Pipeline()
        p.add(lambda xs: [x * 2 for x in xs])
        assert p.run([1, 2, 3]) == [2, 4, 6]

    def test_step_error_raises(self):
        """非 skip_on_error 步驟出錯時應拋出異常."""
        p = Pipeline()
        p.add(lambda x: (_ for _ in ()).throw(ValueError("boom")))
        with pytest.raises(ValueError, match="boom"):
            p.run(1)

    def test_step_skip_on_error(self):
        """skip_on_error=True 時，步驟出錯應跳過."""

        def fail(x):
            raise RuntimeError("oops")

        p = Pipeline()
        p.add(lambda x: x + 1)
        p.add(fail, skip_on_error=True)
        p.add(lambda x: x * 2)
        # (1+1) → fail(跳過) → 2*2 = 4
        assert p.run(1) == 4

    def test_pipeline_name(self):
        """管道名稱應正確設定."""
        p = Pipeline(name="my_pipe")
        assert p.name == "my_pipe"

# ─── ohlcv_clean_pipeline 測試 ───

class TestOhlcvCleanPipeline:
    """測試 OHLCV 資料清洗管道."""

    def test_removes_duplicates(self):
        """去重：相同 timestamp 應只保留第一筆."""
        p = ohlcv_clean_pipeline()
        rows = [
            {"timestamp": 1, "volume": 100},
            {"timestamp": 1, "volume": 200},
            {"timestamp": 2, "volume": 300},
        ]
        result = p.run(rows)
        ts_list = [r["timestamp"] for r in result]
        assert ts_list == [1, 2]

    def test_removes_zero_volume(self):
        """去零量：volume=0 的行應被移除."""
        p = ohlcv_clean_pipeline()
        rows = [
            {"timestamp": 1, "volume": 0},
            {"timestamp": 2, "volume": 100},
            {"timestamp": 3, "volume": 0},
        ]
        result = p.run(rows)
        assert len(result) == 1
        assert result[0]["timestamp"] == 2

    def test_sorts_by_timestamp(self):
        """排序：結果應按 timestamp 升序."""
        p = ohlcv_clean_pipeline()
        rows = [
            {"timestamp": 30, "volume": 50},
            {"timestamp": 10, "volume": 100},
            {"timestamp": 20, "volume": 75},
        ]
        result = p.run(rows)
        ts_list = [r["timestamp"] for r in result]
        assert ts_list == [10, 20, 30]

    def test_combined_cleaning(self):
        """綜合測試：去重 + 去零量 + 排序."""
        p = ohlcv_clean_pipeline()
        rows = [
            {"timestamp": 5, "volume": 0},  # 零量 → 移除
            {"timestamp": 3, "volume": 100},
            {"timestamp": 3, "volume": 200},  # 重複 → 移除
            {"timestamp": 1, "volume": 50},
            {"timestamp": 10, "volume": 300},
        ]
        result = p.run(rows)
        assert [r["timestamp"] for r in result] == [1, 3, 10]
        assert all(r["volume"] > 0 for r in result)

    def test_missing_volume_defaults_to_zero(self):
        """volume 欄位不存在時視為 0，應被移除."""
        p = ohlcv_clean_pipeline()
        rows = [
            {"timestamp": 1},  # 無 volume → 視為 0 → 移除
            {"timestamp": 2, "volume": 10},
        ]
        result = p.run(rows)
        assert len(result) == 1

    def test_empty_input(self):
        """空列表應返回空列表."""
        p = ohlcv_clean_pipeline()
        assert p.run([]) == []
