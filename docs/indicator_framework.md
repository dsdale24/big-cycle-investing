# Indicator Framework

Inspired by Ray Dalio's long-view historical approach to understanding cycles of
national rise and decline, but not restricted to his specific indicators. We use
any data that helps us understand where we are in the big cycle.

## Categories

### 1. Debt & Credit Dynamics
**What it tells us:** Where we are in the long-term debt cycle. Debt growth faster
than income growth is unsustainable; the resolution (austerity, default, inflation,
restructuring) defines the next phase.

| Metric | Frequency | Source | Series ID | Coverage |
|--------|-----------|--------|-----------|----------|
| Federal Debt / GDP | Quarterly | FRED | GFDEGDQ188S | 1966– |
| Household Debt / GDP | Quarterly | FRED | HDTGPDUSQ163N | 2005– |
| Nonfinancial Corporate Debt | Quarterly | FRED | BCNSDODNS | 1952– |
| C&I Loans | Monthly | FRED | BUSLOANS | 1947– |
| Consumer Loan Delinquency | Quarterly | FRED | DRCCLACBS | 1991– |

**Derived:** Debt acceleration (YoY change in debt/GDP), credit impulse

### 2. Interest Rates & Yield Curve
**What it tells us:** The price of money, the market's view of future growth and
inflation, and stress signals from credit markets.

| Metric | Frequency | Source | Series ID | Coverage |
|--------|-----------|--------|-----------|----------|
| Federal Funds Rate | Monthly | FRED | FEDFUNDS | 1954– |
| 10-Year Treasury Yield | Daily | FRED | DGS10 | 1962– |
| 2-Year Treasury Yield | Monthly | FRED | GS2 | 1976– |
| 10Y–2Y Spread (Yield Curve) | Daily | FRED | T10Y2Y | 1976– |
| 10Y Breakeven Inflation | Daily | FRED | T10YIE | 2003– |
| BAA Corporate Spread | Daily | FRED | BAA10Y | 1986– |

**Derived:** Real interest rates, yield curve slope, credit spread z-score

### 3. Inflation & Monetary Policy
**What it tells us:** Whether the central bank is stimulating or restricting, and
whether inflation is eroding purchasing power. Money printing is the primary
mechanism for debt cycle resolution.

| Metric | Frequency | Source | Series ID | Coverage |
|--------|-----------|--------|-----------|----------|
| CPI (All Urban) | Monthly | FRED | CPIAUCSL | 1947– |
| PCE Price Index | Monthly | FRED | PCEPI | 1959– |
| M2 Money Supply | Monthly | FRED | M2SL | 1959– |
| Monetary Base | Monthly | FRED | BOGMBASE | 1918– |
| Fed Total Assets | Weekly | FRED | WALCL | 2002– |

**Derived:** YoY inflation, M2 growth rate, monetary base expansion (QE proxy),
real fed funds rate

### 4. Currency & Store of Value
**What it tells us:** Confidence in the currency as a store of value. Currency
debasement is a hallmark of late-stage debt cycles and declining empires.

| Metric | Frequency | Source | Series ID | Coverage |
|--------|-----------|--------|-----------|----------|
| Trade-Weighted USD (Broad) | Daily | FRED | DTWEXBGS | 2006– |
| Trade-Weighted USD (Major) | Monthly | FRED | TWEXMMTH | 1973–2019 |
| US Dollar Index | Daily | Yahoo | DX-Y.NYB | 1975– |
| Gold Futures | Daily | Yahoo | GC=F | 2000– |

**Derived:** Gold vs M2 (gold priced in money supply), real USD (inflation-adjusted)

### 5. Economy & Labor
**What it tells us:** The real economy's health and cyclical position.

| Metric | Frequency | Source | Series ID | Coverage |
|--------|-----------|--------|-----------|----------|
| Real GDP | Quarterly | FRED | GDPC1 | 1947– |
| Unemployment Rate | Monthly | FRED | UNRATE | 1948– |
| Initial Jobless Claims | Weekly | FRED | ICSA | 1967– |
| Industrial Production | Monthly | FRED | INDPRO | 1919– |
| Consumer Sentiment | Monthly | FRED | UMCSENT | 1952– |

### 6. Wealth Inequality & Internal Order
**What it tells us:** The health of the social contract. Rising inequality erodes
trust in institutions and increases the risk of populism, political instability,
and internal conflict. These are slow-moving but powerful forces.

| Metric | Frequency | Source | Proxy | Coverage |
|--------|-----------|--------|-------|----------|
| Top 10% Income Share | Annual | WID / FRED | WFRBST01134 | 1962– |
| Top 1% Income Share | Annual | WID | — | 1913– |
| Gini Index | Annual | World Bank / Census | GINIALLRF | 1993– |
| Median Household Income | Annual | FRED | MEHOINUSA672N | 1984– |
| Income ratio (top 20% / bottom 20%) | Annual | Census | S80/S20 | 1968– |
| Poverty Rate | Annual | Census / FRED | — | 1959– |
| Government Trust (surveys) | Periodic | Pew/Gallup | — | 1958– |
| Consumer Confidence | Monthly | FRED | UMCSENT | 1952– |

**Proxies for political polarization:**
- Congressional voting overlap (DW-NOMINATE scores, VoteView) — Annual, 1879–
- Partisan antipathy surveys (Pew) — Periodic, ~1994–
- Number/scale of protests and civil unrest — Various sources

**Notes:** Annual and periodic data is fine here. These forces move slowly — a
5-year trend in inequality matters more than monthly wiggles. We forward-fill
annual data and use it as regime context, not trading signals.

### 7. Education & Human Capital
**What it tells us:** Long-term national competitiveness. Education quality is a
leading indicator (by decades) of economic and technological strength.

| Metric | Frequency | Source | Coverage |
|--------|-----------|--------|----------|
| PISA scores | Triennial | OECD | 2000– |
| Education spending (% GDP) | Annual | World Bank | 1970– |
| Tertiary enrollment rate | Annual | World Bank | 1970– |
| R&D spending (% GDP) | Annual | World Bank / OECD | 1996– |
| Patent applications | Annual | WIPO / USPTO | 1963– |

### 8. External Order & Geopolitical Position
**What it tells us:** The US position in the global power structure. Reserve
currency status, trade dominance, and military strength relative to rising
powers (especially China) are central to the big cycle thesis.

| Metric | Frequency | Source | Proxy | Coverage |
|--------|-----------|--------|-------|----------|
| USD Share of Global Reserves | Quarterly | IMF COFER | — | 1999– |
| Trade Balance | Monthly | FRED | BOPGSTB | 1992– |
| Current Account (% GDP) | Quarterly | FRED | NETFI | 1960– |
| Military Spending (% GDP) | Annual | SIPRI | — | 1949– |
| Military Spending (vs China) | Annual | SIPRI | — | 1989– |
| US Share of World GDP | Annual | World Bank | — | 1960– |
| FDI Inflows | Annual | World Bank | — | 1970– |
| Technology balance of trade | Annual | NSF | — | various |

### 9. Asset Prices (for Portfolio Construction)
**What it tells us:** Used for backtesting allocation decisions, not as indicators.

| Metric | Frequency | Source | Series ID | Coverage |
|--------|-----------|--------|-----------|----------|
| S&P 500 | Daily | Yahoo | ^GSPC | 1950– |
| NASDAQ | Daily | Yahoo | ^IXIC | 1971– |
| Russell 2000 | Daily | Yahoo | ^RUT | 1987– |
| 20Y+ Treasury ETF | Daily | Yahoo | TLT | 2002– |
| TIPS ETF | Daily | Yahoo | TIP | 2003– |
| Gold Futures | Daily | Yahoo | GC=F | 2000– |
| Crude Oil Futures | Daily | Yahoo | CL=F | 2000– |

---

## Using Low-Frequency Data

Annual and periodic data (inequality, education, military, governance) is not a
problem — it's actually the point. Big cycles play out over decades.

**Approach:**
1. **Forward-fill** annual/periodic data to create a continuous time series
2. **Compute trends** (5-year, 10-year moving averages) rather than point values
3. **Use as regime context** — these indicators don't trigger trades directly, but
   they inform which macro regime we're in and how to weight other signals
4. **Interpolation where justified** — some series (like GDP share) move smoothly
   enough that linear interpolation between annual points is reasonable

**Walk-forward discipline:** Even with annual data, we only use values that would
have been available at the time. Most annual data is published with a 6–12 month
lag (e.g., 2024 Gini would be available mid-2025).

---

## Priority for Implementation

**Phase 1 (done):** Financial indicators — debt, rates, inflation, monetary, currency, economy
**Phase 2 (next):** Inequality & internal order proxies from FRED + freely available data
**Phase 3:** External order — reserve currency, military, trade dominance
**Phase 4:** Education & human capital — slowest-moving, lowest priority for backtesting
