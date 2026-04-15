# Backtest sample scope thesis

**Status:** `active`
**Scale:** meta (applies to all other theses' testability)

## Claim

The project's backtest data — US financial series 1975-present — is a single sample from the US-ascendant, post-Bretton-Woods, disinflationary era. Empire-transition scenarios (the primary motivation for the project) are **not in the dataset**. No amount of fitting, cross-validation, or walk-forward discipline on this sample can validate a strategy meant for transition-scale shifts. Cross-national historical data is required to honestly evaluate claims at that scale.

## Rationale

Dalio-style big-cycle thinking draws on multi-century history across multiple empires: Dutch Republic peaking ~1650 and declining through the 1700s; British peaking ~1870 and declining through 1914-1945 (two world wars, gold-standard abandonment, sterling's loss of reserve status, bankruptcy after WWII). These transitions played out over 50-200 years.

Our backtest window (1975-2024) sits entirely inside the US equivalent of ~1870-1914 Britain: unambiguous hegemony, pre-transition. It contains:
- Recessions (1980, 1982, 1990, 2001, 2008, 2020, 2022) — cyclical scale
- Inflation/disinflation regimes (1970s-early-1980s inflation; 1983-2020 disinflation; 2021-2023 inflation return) — secular scale
- **Zero** reserve-currency transitions, empire transitions, or analogous institutional-adaptation crises — transition scale

Any US-only backtest result is therefore strictly bounded to "how did this work during the bull era." That's an interesting but narrow question and cannot answer the question the project is actually asking.

## Implications

- Don't present backtest numbers as validation of a big-cycle strategy's effectiveness. They validate performance during a known-favorable regime only. State this caveat on every strategy-evaluation artifact (`docs/research/*.md`) produced in this project.
- Cross-national data acquisition is load-bearing roadmap work, not a nice-to-have. Target datasets:
  - UK 1900-1980 (gilts, equities, gold-in-GBP, GBP/USD) — WWI, gold standard abandonment, interwar, WWII, 1949 / 1967 sterling devaluations, 1976 IMF bailout, end of reserve status
  - Weimar Germany 1919-1923 (hyperinflation)
  - France 1918-1928 (franc crisis)
  - Argentina (recurring defaults — mode 2/3 stress cases)
  - Japan 1990-present (mature-but-not-declined reference point)
  - Possible sources: Global Financial Data, MeasuringWorth, BIS long series
- When comparing strategies against AllWeather on US 1975-2024 data, explicitly note AllWeather's strong numbers are a product of the exact era (disinflation + US hegemony) that the project is preparing for the end of. It is not a neutral benchmark.
- Strategy evaluation under this frame is not "Sharpe ratio" — it's "does this portfolio preserve purchasing power across analogous historical transitions when stress-tested against cross-national data?" Different question, different tools.

## Current evidence

Direct evidence is the historical record: Dutch assets 1600-1800, British assets 1900-1950, Weimar assets 1919-1923 — none of which are in our dataset. The project currently operates at cyclical and secular scale only.

## What would test this

The thesis is structural, not empirical — it's a statement about what the dataset contains and doesn't contain. It's either factually correct or not about dataset composition. Testing consists of auditing whether the dataset contains the relevant events, which it does not.

## What would falsify this

- Discovery that a transition-scale event in the US 1975-present window was missed in the initial characterization. Unlikely — the period is well-documented.
- Cross-national data acquisition that brings transition-scale events into the backtest window — this *resolves* the thesis by making it moot rather than falsifying it. Should be treated as thesis retirement ("resolved by #XX") rather than falsification.

## Related

- `bond-allocation.md` — the thesis whose definitive test requires the cross-national data this thesis motivates
- `institutional-adaptation.md` — complementary transition mode (technology-driven) that the same cross-national acquisition could partially address
