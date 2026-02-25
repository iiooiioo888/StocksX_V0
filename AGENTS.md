# AGENTS.md

## Cursor Cloud specific instructions

### Project overview

StocksX_V0 is a cryptocurrency backtesting platform (通用回測平台 MVP) built with Streamlit + Python. See `README.md` for full feature description.

### Running the app

```bash
streamlit run app.py --server.port 8501 --server.headless true --server.address 0.0.0.0
```

### Key gotchas

- **Missing `src/data/` module**: The `.gitignore` originally had `data/` which excluded `src/data/` at any level. This was fixed by changing to `/data/` and adding `!src/data/`. If `src/data/` ever goes missing, check `.gitignore`.
- **Exchange geo-restrictions**: Binance and Bybit APIs return 451/403 errors in US-based cloud environments. The data layer (`src/data/sources/crypto_ccxt.py`) includes an automatic fallback mechanism that tries OKX, Gate, KuCoin, MEXC in order. If all exchanges fail, verify network access.
- **pip install path**: Use `sudo pip install -r requirements.txt` (or a virtualenv) to ensure packages install to system site-packages (`/usr/local/lib/python3.12/dist-packages/`). Without `sudo`, pip installs to `~/.local/lib/` which may not be on `sys.path`.
- **app.py syntax**: There was an escaped-quote bug on the Qwen AI error handler line (`f\"...\"` instead of `f"..."`). This has been fixed.
- **SQLite cache**: Stored in `cache/crypto_cache.sqlite` (gitignored). Delete this directory to force fresh data fetch from exchanges.

### Testing

- No automated test suite exists. Verify functionality by starting the Streamlit app and running a backtest.
- CLI smoke test: `python3 -c "from src.data.crypto import CryptoDataFetcher; print('OK')"`

### Lint

No linter configuration exists in this project. Python files can be checked with `python3 -m py_compile <file>`.
