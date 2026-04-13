"""Walk-forward backtesting engine.

Core constraint: at each rebalancing date, the strategy can only see data
that would have been available on that date. No look-ahead bias.
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Protocol


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

ASSET_CLASSES = ["equities", "long_bonds", "short_bonds", "gold", "commodities", "cash"]


@dataclass
class PortfolioSnapshot:
    date: pd.Timestamp
    weights: dict[str, float]  # asset class -> weight (0-1, must sum to 1)
    signals: dict[str, float] = field(default_factory=dict)  # indicator name -> value
    regime: str = ""


@dataclass
class BacktestResult:
    """Full result of a backtest run."""
    snapshots: list[PortfolioSnapshot]
    portfolio_returns: pd.Series  # daily returns of the strategy
    portfolio_value: pd.Series  # cumulative value (starts at 1.0)
    asset_returns: pd.DataFrame  # daily returns for each asset
    weights_history: pd.DataFrame  # weights at each rebalance date
    regime_history: pd.Series  # regime label at each rebalance
    config: dict  # strategy config used


# ---------------------------------------------------------------------------
# Asset price proxies
# ---------------------------------------------------------------------------

def build_asset_returns(
    data: dict[str, pd.DataFrame],
    start: str = "1975-01-01",
) -> pd.DataFrame:
    """
    Build daily returns for investable asset classes.

    Before ETFs existed, we use index proxies:
    - equities: S&P 500 total return (price-only as proxy)
    - long_bonds: 10Y Treasury return approximation from yield changes
    - short_bonds: approximate short bond return from 2Y yield
    - gold: Gold futures (or London fix before 2000)
    - commodities: Oil futures (imperfect but available)
    - cash: Fed funds rate / 252 (daily risk-free)
    """
    start_dt = pd.Timestamp(start)

    # Equities: S&P 500 daily returns
    sp500 = data.get("^GSPC")
    if sp500 is not None:
        eq_ret = sp500["Close"].pct_change()
    else:
        eq_ret = pd.Series(dtype=float)

    # Long bonds: approximate from 10Y yield changes
    # Bond return ≈ -duration * Δyield + yield/252
    # Use duration ~ 8 for 10Y Treasury
    tnx = data.get("^TNX")
    if tnx is not None:
        y = tnx["Close"] / 100  # convert to decimal
        duration = 8.0
        bond_ret = -duration * y.diff() + y.shift(1) / 252
        bond_ret = bond_ret.clip(-0.10, 0.10)  # cap extreme moves
    else:
        bond_ret = pd.Series(dtype=float)

    # Short bonds: approximate from 2Y yield (duration ~2)
    gs2 = data.get("GS2_yield")
    if gs2 is not None:
        y2 = gs2 / 100
        short_bond_ret = -2.0 * y2.diff() + y2.shift(1) / 252
        short_bond_ret = short_bond_ret.clip(-0.05, 0.05)
    else:
        # Fall back to cash-like return
        short_bond_ret = pd.Series(dtype=float)

    # Gold
    gold = data.get("GC=F")
    if gold is not None:
        gold_ret = gold["Close"].pct_change()
    else:
        gold_ret = pd.Series(dtype=float)

    # Commodities (oil as proxy)
    oil = data.get("CL=F")
    if oil is not None:
        comm_ret = oil["Close"].pct_change()
    else:
        comm_ret = pd.Series(dtype=float)

    # Cash: fed funds daily
    ff = data.get("FEDFUNDS")
    if ff is not None:
        # Monthly rate, convert to daily
        ff_daily = ff.squeeze().resample("D").ffill() / 100 / 252
    else:
        ff_daily = pd.Series(dtype=float)

    returns = pd.DataFrame({
        "equities": eq_ret,
        "long_bonds": bond_ret,
        "short_bonds": short_bond_ret,
        "gold": gold_ret,
        "commodities": comm_ret,
        "cash": ff_daily,
    })

    # Align to common date range starting from start_dt
    returns = returns.loc[start_dt:]
    returns = returns.fillna(0)

    return returns


# ---------------------------------------------------------------------------
# Strategy protocol
# ---------------------------------------------------------------------------

class Strategy(Protocol):
    """Interface that all strategies must implement."""

    def allocate(
        self,
        date: pd.Timestamp,
        available_data: dict[str, pd.DataFrame | pd.Series],
    ) -> PortfolioSnapshot:
        """
        Given a date and all data available up to that date,
        return target portfolio weights.
        """
        ...


# ---------------------------------------------------------------------------
# Built-in strategies
# ---------------------------------------------------------------------------

class StaticStrategy:
    """Fixed allocation — useful as a benchmark."""

    def __init__(self, weights: dict[str, float], name: str = "Static"):
        total = sum(weights.values())
        self.weights = {k: v / total for k, v in weights.items()}
        self.name = name

    def allocate(self, date, available_data):
        return PortfolioSnapshot(date=date, weights=self.weights, regime=self.name)


class AllWeatherStrategy:
    """
    Simplified Bridgewater All Weather:
    30% equities, 40% long bonds, 15% short bonds, 7.5% gold, 7.5% commodities
    """

    def allocate(self, date, available_data):
        return PortfolioSnapshot(
            date=date,
            weights={
                "equities": 0.30,
                "long_bonds": 0.40,
                "short_bonds": 0.15,
                "gold": 0.075,
                "commodities": 0.075,
                "cash": 0.0,
            },
            regime="all_weather",
        )


class BigCycleStrategy:
    """
    Regime-adaptive strategy — shifts allocation based on macro indicators.
    This is the strategy to iterate on.

    Config dict controls thresholds and weights.
    """

    DEFAULT_CONFIG = {
        "base_equities": 0.30,
        "base_long_bonds": 0.25,
        "base_short_bonds": 0.10,
        "base_gold": 0.15,
        "base_commodities": 0.10,
        "base_cash": 0.10,
        # Adjustments per regime
        "overheating_gold_add": 0.10,
        "overheating_equity_sub": 0.10,
        "contraction_cash_add": 0.15,
        "contraction_equity_sub": 0.10,
        "contraction_bond_add": 0.05,
        "reflation_equity_add": 0.10,
        "reflation_cash_sub": 0.10,
        # Thresholds
        "yield_curve_inversion_threshold": 0.0,
        "inflation_high_threshold": 4.0,
        "real_rate_negative_threshold": 0.0,
    }

    def __init__(self, config: dict | None = None):
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}

    def _classify_regime(self, date, data):
        """Simple regime classification using only data available at `date`."""
        signals = {}

        # Yield curve
        yc = data.get("T10Y2Y")
        if yc is not None:
            yc_series = yc.squeeze()
            yc_val = yc_series.loc[:date].iloc[-1] if len(yc_series.loc[:date]) > 0 else None
            if yc_val is not None:
                signals["yield_curve"] = float(yc_val)

        # Inflation (YoY CPI)
        cpi = data.get("CPIAUCSL")
        if cpi is not None:
            cpi_s = cpi.squeeze().loc[:date]
            if len(cpi_s) >= 13:
                inflation = (cpi_s.iloc[-1] / cpi_s.iloc[-13] - 1) * 100
                signals["inflation_yoy"] = float(inflation)

        # Fed funds rate
        ff = data.get("FEDFUNDS")
        if ff is not None:
            ff_s = ff.squeeze().loc[:date]
            if len(ff_s) > 0:
                signals["fed_funds"] = float(ff_s.iloc[-1])

        # Real rate
        if "inflation_yoy" in signals and "fed_funds" in signals:
            signals["real_rate"] = signals["fed_funds"] - signals["inflation_yoy"]

        # Classify
        yc_val = signals.get("yield_curve")
        infl = signals.get("inflation_yoy")
        real_r = signals.get("real_rate")

        if yc_val is not None and yc_val < self.config["yield_curve_inversion_threshold"]:
            if infl is not None and infl > self.config["inflation_high_threshold"]:
                regime = "overheating"
            else:
                regime = "contraction"
        elif real_r is not None and real_r < self.config["real_rate_negative_threshold"]:
            regime = "reflation"
        else:
            regime = "expansion"

        return regime, signals

    def allocate(self, date, available_data):
        regime, signals = self._classify_regime(date, available_data)

        # Start from base allocation
        w = {
            "equities": self.config["base_equities"],
            "long_bonds": self.config["base_long_bonds"],
            "short_bonds": self.config["base_short_bonds"],
            "gold": self.config["base_gold"],
            "commodities": self.config["base_commodities"],
            "cash": self.config["base_cash"],
        }

        # Regime adjustments
        if regime == "overheating":
            w["gold"] += self.config["overheating_gold_add"]
            w["equities"] -= self.config["overheating_equity_sub"]
        elif regime == "contraction":
            w["cash"] += self.config["contraction_cash_add"]
            w["equities"] -= self.config["contraction_equity_sub"]
            w["long_bonds"] += self.config["contraction_bond_add"]
        elif regime == "reflation":
            w["equities"] += self.config["reflation_equity_add"]
            w["cash"] -= self.config["reflation_cash_sub"]

        # Clamp and normalize
        w = {k: max(0, v) for k, v in w.items()}
        total = sum(w.values())
        w = {k: v / total for k, v in w.items()}

        return PortfolioSnapshot(date=date, weights=w, signals=signals, regime=regime)


# ---------------------------------------------------------------------------
# Backtesting engine
# ---------------------------------------------------------------------------

def run_backtest(
    strategy: Strategy,
    asset_returns: pd.DataFrame,
    indicator_data: dict[str, pd.DataFrame | pd.Series],
    start: str = "1975-01-01",
    rebalance_freq: str = "QE",  # quarterly rebalancing
    config: dict | None = None,
) -> BacktestResult:
    """
    Run a walk-forward backtest.

    At each rebalance date, the strategy is called with only data available
    up to that date. Between rebalances, portfolio drifts with market returns.
    """
    start_dt = pd.Timestamp(start)

    # Generate rebalance dates
    all_dates = asset_returns.index
    rebalance_dates = asset_returns.resample(rebalance_freq).last().index
    rebalance_dates = rebalance_dates[rebalance_dates >= start_dt]

    snapshots = []
    weights_rows = []
    regime_entries = []

    # Current weights (start equal-weight)
    n_assets = len(ASSET_CLASSES)
    current_weights = {a: 1.0 / n_assets for a in ASSET_CLASSES}

    # Daily portfolio returns
    port_returns = pd.Series(0.0, index=all_dates[all_dates >= start_dt], dtype=float)

    rebal_set = set(rebalance_dates)

    for date in all_dates[all_dates >= start_dt]:
        # Rebalance?
        if date in rebal_set:
            # Truncate data to what's available on this date
            avail = {}
            for key, df in indicator_data.items():
                if isinstance(df, pd.DataFrame):
                    avail[key] = df.loc[:date]
                elif isinstance(df, pd.Series):
                    avail[key] = df.loc[:date]

            snapshot = strategy.allocate(date, avail)
            current_weights = snapshot.weights
            snapshots.append(snapshot)
            weights_rows.append({"date": date, **snapshot.weights})
            regime_entries.append({"date": date, "regime": snapshot.regime})

        # Compute portfolio return for this day
        day_ret = 0.0
        for asset, weight in current_weights.items():
            if asset in asset_returns.columns:
                day_ret += weight * asset_returns.loc[date, asset]
        port_returns.loc[date] = day_ret

        # Drift weights with returns
        new_weights = {}
        total = 0
        for asset, weight in current_weights.items():
            if asset in asset_returns.columns:
                grown = weight * (1 + asset_returns.loc[date, asset])
            else:
                grown = weight
            new_weights[asset] = grown
            total += grown
        if total > 0:
            current_weights = {k: v / total for k, v in new_weights.items()}

    # Build results
    portfolio_value = (1 + port_returns).cumprod()

    weights_df = pd.DataFrame(weights_rows)
    if len(weights_df) > 0:
        weights_df = weights_df.set_index("date")

    regime_df = pd.DataFrame(regime_entries)
    if len(regime_df) > 0:
        regime_series = regime_df.set_index("date")["regime"]
    else:
        regime_series = pd.Series(dtype=str)

    return BacktestResult(
        snapshots=snapshots,
        portfolio_returns=port_returns,
        portfolio_value=portfolio_value,
        asset_returns=asset_returns.loc[start_dt:],
        weights_history=weights_df,
        regime_history=regime_series,
        config=config or {},
    )


# ---------------------------------------------------------------------------
# Performance metrics
# ---------------------------------------------------------------------------

def compute_metrics(result: BacktestResult) -> dict:
    """Compute standard performance metrics from a backtest result."""
    ret = result.portfolio_returns
    val = result.portfolio_value

    years = (ret.index[-1] - ret.index[0]).days / 365.25
    total_return = val.iloc[-1] / val.iloc[0] - 1
    cagr = (1 + total_return) ** (1 / years) - 1

    # Volatility (annualized)
    vol = ret.std() * np.sqrt(252)

    # Sharpe (assuming 0 risk-free for simplicity)
    sharpe = cagr / vol if vol > 0 else 0

    # Max drawdown
    peak = val.cummax()
    drawdown = (val - peak) / peak
    max_dd = drawdown.min()
    max_dd_date = drawdown.idxmin()

    # Recovery: how long from max drawdown to new high
    dd_end = val.loc[max_dd_date:]
    recovery_dates = dd_end[dd_end >= peak.loc[max_dd_date]]
    if len(recovery_dates) > 0:
        recovery_days = (recovery_dates.index[0] - max_dd_date).days
    else:
        recovery_days = None  # still in drawdown

    # Calmar ratio
    calmar = cagr / abs(max_dd) if max_dd != 0 else 0

    return {
        "total_return": total_return,
        "cagr": cagr,
        "volatility": vol,
        "sharpe": sharpe,
        "max_drawdown": max_dd,
        "max_dd_date": max_dd_date,
        "recovery_days": recovery_days,
        "calmar": calmar,
        "years": years,
        "start": ret.index[0],
        "end": ret.index[-1],
    }


def format_metrics(metrics: dict) -> str:
    """Pretty-print metrics."""
    lines = [
        f"Period:        {metrics['start'].date()} → {metrics['end'].date()} ({metrics['years']:.1f} years)",
        f"Total Return:  {metrics['total_return']:.1%}",
        f"CAGR:          {metrics['cagr']:.2%}",
        f"Volatility:    {metrics['volatility']:.2%}",
        f"Sharpe Ratio:  {metrics['sharpe']:.2f}",
        f"Max Drawdown:  {metrics['max_drawdown']:.1%} ({metrics['max_dd_date'].date()})",
        f"Recovery:      {metrics['recovery_days']} days" if metrics['recovery_days'] else "Recovery:      (not recovered)",
        f"Calmar Ratio:  {metrics['calmar']:.2f}",
    ]
    return "\n".join(lines)
