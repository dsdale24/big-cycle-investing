"""Fetch and cache historical macro/financial data from FRED and Yahoo Finance."""

import os
from datetime import datetime
from pathlib import Path

import pandas as pd
import yaml
from fredapi import Fred
import yfinance as yf

DATA_DIR = Path(__file__).parent.parent / "data" / "raw"
CONFIG_PATH = Path(__file__).parent.parent / "configs" / "series.yaml"
DEFAULT_START = "1975-01-01"


def load_config(path: Path = CONFIG_PATH) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def get_fred_client() -> Fred:
    api_key = os.environ.get("FRED_API_KEY")
    if not api_key:
        env_file = Path(__file__).parent.parent / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("FRED_API_KEY="):
                    api_key = line.split("=", 1)[1].strip().strip("\"'")
                    break
    if not api_key:
        raise ValueError(
            "FRED_API_KEY not found. Set it as an environment variable or in .env file.\n"
            "Get a free key at: https://fred.stlouisfed.org/docs/api/api_key.html"
        )
    return Fred(api_key=api_key)


def fetch_fred_series(
    fred: Fred,
    series_id: str,
    meta: dict,
    start: str = DEFAULT_START,
) -> pd.Series:
    """Fetch a single FRED series."""
    actual_start = meta.get("start_override", start)
    series = fred.get_series(series_id, observation_start=actual_start)
    series.name = series_id
    series.index.name = "date"
    return series


def fetch_yahoo_series(
    symbol: str,
    meta: dict,
    start: str = DEFAULT_START,
) -> pd.DataFrame:
    """Fetch a single Yahoo Finance series (OHLCV)."""
    actual_start = meta.get("start_override", start)
    ticker = yf.Ticker(symbol)
    df = ticker.history(start=actual_start, end=datetime.now().strftime("%Y-%m-%d"))
    if df.empty:
        print(f"  WARNING: No data returned for {symbol}")
        return df
    df.index = df.index.tz_localize(None)
    df.index.name = "date"
    return df


def save_series(data: pd.Series | pd.DataFrame, source: str, series_id: str) -> Path:
    """Save a series to parquet."""
    out_dir = DATA_DIR / source
    out_dir.mkdir(parents=True, exist_ok=True)
    # Sanitize filename for symbols like ^GSPC
    safe_name = series_id.replace("^", "").replace("=", "_").replace(".", "_")
    path = out_dir / f"{safe_name}.parquet"
    if isinstance(data, pd.Series):
        data = data.to_frame()
    data.to_parquet(path)
    return path


def fetch_all(start: str = DEFAULT_START, config_path: Path = CONFIG_PATH) -> dict:
    """Fetch all configured series and cache to disk. Returns summary dict."""
    config = load_config(config_path)
    results = {"fred": {}, "yahoo": {}}

    # FRED
    fred_series = config.get("fred", {})
    if fred_series:
        fred = get_fred_client()
        for series_id, meta in fred_series.items():
            print(f"  FRED: {series_id} ({meta['name']})...", end=" ")
            try:
                data = fetch_fred_series(fred, series_id, meta, start)
                path = save_series(data, "fred", series_id)
                results["fred"][series_id] = {
                    "rows": len(data),
                    "start": str(data.index.min().date()),
                    "end": str(data.index.max().date()),
                    "path": str(path),
                }
                print(f"OK ({len(data)} rows)")
            except Exception as e:
                print(f"FAILED: {e}")
                results["fred"][series_id] = {"error": str(e)}

    # Yahoo Finance
    yahoo_series = config.get("yahoo", {})
    if yahoo_series:
        for symbol, meta in yahoo_series.items():
            print(f"  Yahoo: {symbol} ({meta['name']})...", end=" ")
            try:
                df = fetch_yahoo_series(symbol, meta, start)
                if df.empty:
                    results["yahoo"][symbol] = {"error": "No data returned"}
                    continue
                path = save_series(df, "yahoo", symbol)
                results["yahoo"][symbol] = {
                    "rows": len(df),
                    "start": str(df.index.min().date()),
                    "end": str(df.index.max().date()),
                    "path": str(path),
                }
                print(f"OK ({len(df)} rows)")
            except Exception as e:
                print(f"FAILED: {e}")
                results["yahoo"][symbol] = {"error": str(e)}

    return results


def load_series(source: str, series_id: str) -> pd.DataFrame:
    """Load a cached series from disk."""
    safe_name = series_id.replace("^", "").replace("=", "_").replace(".", "_")
    path = DATA_DIR / source / f"{safe_name}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"No cached data for {source}/{series_id}. Run fetch_all() first.")
    return pd.read_parquet(path)


def load_all_fred() -> dict[str, pd.DataFrame]:
    """Load all cached FRED series."""
    config = load_config()
    result = {}
    for series_id in config.get("fred", {}):
        try:
            result[series_id] = load_series("fred", series_id)
        except FileNotFoundError:
            pass
    return result


def load_all_yahoo() -> dict[str, pd.DataFrame]:
    """Load all cached Yahoo Finance series."""
    config = load_config()
    result = {}
    for symbol in config.get("yahoo", {}):
        try:
            result[symbol] = load_series("yahoo", symbol)
        except FileNotFoundError:
            pass
    return result
