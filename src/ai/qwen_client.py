from __future__ import annotations

"""
Qwen AI 客戶端封裝。

使用前請先：
    pip install dashscope
並設定環境變數：
    DASHSCOPE_API_KEY=你的金鑰
"""

from http import HTTPStatus
from typing import Dict, List, Optional
import os

try:
    import dashscope
    from dashscope import Generation  # type: ignore
except ImportError:
    dashscope = None
    Generation = None


def _ensure_ready() -> None:
    if dashscope is None or Generation is None:
        raise RuntimeError("尚未安裝 dashscope，請先執行：pip install dashscope")
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise RuntimeError("請先設定環境變數 DASHSCOPE_API_KEY 才能呼叫 Qwen。")
    dashscope.api_key = api_key


def qwen_chat(
    messages: List[Dict[str, str]],
    model: str = "qwen-turbo",
    temperature: float = 0.7,
    max_tokens: int = 512,
) -> str:
    """Qwen 聊天封裝：messages 為 role/content 列表。"""
    _ensure_ready()

    resp = Generation.call(
        model=model,
        messages=messages,
        result_format="message",
        temperature=temperature,
        max_tokens=max_tokens,
    )

    if resp.status_code != HTTPStatus.OK:
        code = getattr(resp, "code", None)
        msg = getattr(resp, "message", None)
        raise RuntimeError(f"Qwen 調用失敗：code={code}, message={msg}")

    output = resp.output or {}
    choices = output.get("choices") or []
    if not choices:
        return ""
    message = choices[0].get("message") or {}
    return message.get("content") or ""


def qwen_simple(
    prompt: str,
    system_prompt: Optional[str] = "你是量化交易與程式開發助手，請使用繁體中文、給出精簡扼要的重點分析。",
    model: str = "qwen-turbo",
    temperature: float = 0.7,
    max_tokens: int = 512,
) -> str:
    """單句封裝：給一段 prompt，選擇性附 system 提示。"""
    messages: List[Dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    return qwen_chat(messages, model=model, temperature=temperature, max_tokens=max_tokens)

