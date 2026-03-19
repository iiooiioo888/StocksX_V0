"""
StocksX — 主入口點

用法：
    python -m src              # 啟動 Streamlit 主應用
    python -m src --ws         # 啟動 WebSocket 服務
    python -m src --version    # 顯示版本
"""

from __future__ import annotations

import sys


def main() -> None:
    args = sys.argv[1:]

    if "--version" in args or "-v" in args:
        from src.version import __version__

        print(f"StocksX v{__version__}")
        return

    if "--ws" in args:
        import uvicorn

        from src.websocket_server import app

        uvicorn.run(app, host="0.0.0.0", port=8001)
        return

    # 默認啟動 Streamlit
    import subprocess

    subprocess.run(["streamlit", "run", "app.py", *args], check=False)


if __name__ == "__main__":
    main()
